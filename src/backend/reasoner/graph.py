from __future__ import annotations
from typing import TypedDict, Literal, List, Dict
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
import sympy as sp
import re
import json
import structlog
from providers.model_factory import LLM, ModelFactory

log = structlog.get_logger(__name__)


# ---------- State and IR ----------
class ProblemIR(BaseModel):
    text: str = ""
    latex: List[str] = []
    task: Literal[
        "solve_equation",
        "simplify",
        "evaluate",
        "differentiate",
        "integrate",
        "limit",
        "matrix_op",
        "lin_alg",
        "number_theory",
        "coord_geometry",
        "word_problem",
        "unknown",
    ] = "unknown"
    expressions: List[str] = []
    variables: List[str] = []
    meta: Dict[str, str] = {}


class State(TypedDict, total=False):
    ir: Dict
    parsed: Dict
    work: List[Dict]
    answer: str
    verified: bool
    level: str
    locale: str
    model: Dict
    confidence: float
    difficulty: int
    original_question: str


# ---------- Helpers ----------
_SOLVE_CMD = re.compile(r"^\s*(solve|giải)\b[:\s]*", re.I)
MATRIX_BRACKETS = re.compile(r"\[\[.*?\]\]|\([^\)]*\);?\s*\([^\)]*\)")


def _strip_cmd(s: str) -> str:
    return _SOLVE_CMD.sub("", s.strip())


def _has_eq(s: str) -> bool:
    return "=" in _strip_cmd(s)


def _only_ops_numbers(s: str) -> bool:
    return bool(re.fullmatch(r"[0-9\.\s\+\-\*/\^\(\)]+", s.replace(" ", "")))


def _has_matrix(s: str) -> bool:
    return bool(MATRIX_BRACKETS.search(s)) or "matrix" in s.lower()


def _has_keywords(s: str, kws: List[str]) -> bool:
    s = s.lower()
    return any(k in s for k in kws)


def _first_var(expr: str) -> str:
    for ch in "xyzabtuvw":
        if ch in expr:
            return ch
    return "x"


def _guess_task(text: str) -> (str, Dict[str, str]):
    t = text.strip()
    meta: Dict[str, str] = {}
    if _has_eq(t):
        return "solve_equation", meta
    if _has_keywords(t, ["simplify", "factor", "expand", "reduce"]):
        return "simplify", meta
    if _has_keywords(t, ["differentiate", "derivative", "d/d"]):
        return "differentiate", meta
    if _has_keywords(t, ["integrate", "integral"]):
        return "integrate", meta
    if _has_keywords(t, ["limit", "lim "]):
        return "limit", meta
    if _has_matrix(t):
        if _has_keywords(t, ["det", "determinant"]):
            meta["matrix_op"] = "det"
        elif _has_keywords(t, ["inverse", "inv"]):
            meta["matrix_op"] = "inv"
        elif _has_keywords(t, ["rank"]):
            meta["matrix_op"] = "rank"
        elif _has_keywords(t, ["rref", "row-reduction", "row reduction"]):
            meta["matrix_op"] = "rref"
        else:
            meta["matrix_op"] = "auto"
        return "matrix_op", meta
    if _only_ops_numbers(_strip_cmd(t)):
        return "evaluate", meta
    if _has_keywords(t, ["prove", "show that", "hence", "therefore"]):
        return "word_problem", meta
    return "unknown", meta


_OPTION_RE = re.compile(r"^\(\s*(\d+)\s*\)\s*(.+)$")
_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.S)


def _extract_options(text: str) -> Dict[str, str]:
    opts = {}
    for line in text.splitlines():
        m = _OPTION_RE.match(line.strip())
        if m:
            k, v = m.group(1), m.group(2).strip()
            if v.startswith("$") and v.endswith("$"):
                v = v[1:-1].strip()
            opts[k] = v
    return opts


def _safe_json_load(s: str) -> dict | None:
    s = (s or "").strip()
    m = _JSON_BLOCK_RE.search(s)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    try:
        return json.loads(s)
    except Exception:
        return None


def _looks_like_only_choices(text: str) -> bool:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False
    choice_lines = 0
    other_lines = 0
    for ln in lines:
        if re.match(r"^\(?\d+\)?\s*[\w\.\-/\\%]+", ln):
            choice_lines += 1
        else:
            other_lines += 1
    return choice_lines >= 2 and other_lines == 0


def _looks_like_equation(text: str) -> bool:
    t = text.strip()
    return "=" in t and not t.lower().strip().endswith("?")


def _can_sympy_verify(question: str, final_answer: str) -> bool:
    q = question.strip()
    if _looks_like_equation(q):
        return True
    if re.fullmatch(r"[\d\.\s\+\-\*/\^\(\)]+", q.replace(" ", "")):
        return True
    return False


def _sympy_verify(question: str, final_answer: str) -> bool:
    try:
        q = question.strip()
        ans = final_answer.strip()
        if "=" in ans:
            ans = ans.split("=", 1)[-1].strip()
        if _looks_like_equation(q):
            lhs_str, rhs_str = q.split("=", 1)
            var = _first_var(q)
            x = sp.symbols(var)
            lhs = sp.sympify(lhs_str)
            rhs = sp.sympify(rhs_str)
            try:
                ans_sym = sp.nsimplify(ans)
            except Exception:
                m = re.search(rf"{var}\s*=\s*([^\s]+)", ans)
                if not m:
                    return False
                ans_sym = sp.nsimplify(m.group(1))
            return bool(sp.simplify(lhs.subs(x, ans_sym) - rhs.subs(x, ans_sym)) == 0)
        if re.fullmatch(r"[\d\.\s\+\-\*/\^\(\)]+", q.replace(" ", "")):
            expr = sp.sympify(q)
            res = sp.simplify(expr)
            try:
                ans_sym = sp.nsimplify(ans)
            except Exception:
                return False
            return bool(sp.simplify(res - ans_sym) == 0)
    except Exception:
        return False
    return False


LLM_SOLVE_SYSTEM_PROMPT = (
    "You are an expert math teacher. Solve the user's problem step-by-step with small, clear steps.\n"
    "Always output ONLY a compact JSON object with keys:\n"
    "{\n"
    '  "steps": [ {"title": str, "explanation": str}, ... ],\n'
    '  "final_answer": str,\n'
    '  "difficulty": int,\n'
    '  "confidence": float,\n'
    '  "topic": str\n'
    "}\n"
    "Rules:\n"
    "- Keep steps concise and didactic.\n"
    "- Put the actual result in final_answer (e.g., 'x = 3', '33/7', or '(3)').\n"
    "- Do NOT include any extra commentary outside the JSON.\n"
)


# ---------- Nodes ----------
async def ingest(state: State) -> State:
    text = (
        (state.get("question") or "")
        or (state.get("original_question") or "")
        or (state.get("ir", {}).get("text") or "")
        or (state.get("text") or "")
    ).strip()
    log.info("ingest.text", preview=text[:120])
    if not text:
        return {
            "ir": {"text": ""},
            "work": [
                {"title": "Input error", "explanation": "No question text provided."}
            ],
            "answer": "",
            "verified": False,
            "confidence": 0.0,
            "difficulty": 0,
        }
    ir = ProblemIR(text=text, latex=[]).model_dump()
    return {"ir": ir}


async def parse_node(state: State) -> State:
    ir = state["ir"]
    text = ir.get("text", "")
    task, meta = _guess_task(text)
    parsed = ProblemIR(
        text=text,
        latex=ir.get("latex", []),
        task=task,
        expressions=[],
        variables=[],
        meta=meta,
    ).model_dump()
    log.info("parse", task=task, meta=meta)
    return {"parsed": parsed}


async def route(state: State) -> str:
    log.info("route", to="solve_llm", task=state["parsed"]["task"])
    return "solve_llm"


async def solve_llm(state: State, base_llm: LLM, strong_llm: LLM) -> State:
    p = state.get("parsed") or {}
    text = (p.get("text", "") or state.get("question", "")).strip()
    if not text:
        return {
            "work": [
                {"title": "Input error", "explanation": "No question text provided."}
            ],
            "answer": "",
            "verified": False,
            "confidence": 0.0,
            "difficulty": 0,
            "model": {"provider": "unknown", "name": "unknown"},
        }
    if _looks_like_only_choices(text):
        return {
            "work": [
                {
                    "title": "Input error",
                    "explanation": "Only answer choices detected. Please include the actual question.",
                }
            ],
            "answer": "",
            "verified": False,
            "confidence": 0.0,
            "difficulty": 0,
            "model": {"provider": "unknown", "name": "unknown"},
        }

    options = _extract_options(text)
    threshold = 0.6

    async def _call(llm: LLM, user_text: str, critique: str | None = None) -> dict:
        sys = LLM_SOLVE_SYSTEM_PROMPT
        user = (
            user_text
            if not critique
            else f"{user_text}\n\n---\nSelf-correction hint: {critique}\nPlease output JSON."
        )
        out = await llm.ask(
            [{"role": "system", "content": sys}, {"role": "user", "content": user}]
        )
        data = _safe_json_load(out)
        if not data:
            # fallback: try to split/plain parse
            steps = [{"title": "Explanation", "explanation": out}]
            return {
                "steps": steps,
                "final_answer": "",
                "difficulty": 3,
                "confidence": 0.4,
            }

        steps = data.get("steps") or [
            {"title": "Explanation", "explanation": "(empty)"}
        ]
        fa = str(data.get("final_answer", "")).strip()
        diff = int(data.get("difficulty", 3))
        conf = float(data.get("confidence", 0.4))
        return {
            "steps": steps,
            "final_answer": fa,
            "difficulty": diff,
            "confidence": conf,
        }

    # 1) First pass with base model
    res = await _call(base_llm, text)
    steps, fa, diff, conf = (
        res["steps"],
        res["final_answer"],
        res["difficulty"],
        res["confidence"],
    )
    verified = False
    used_model = getattr(base_llm, "name", "unknown")
    used_provider = getattr(base_llm, "provider", "unknown")

    # 2) Verify if possible (equations/expressions)
    if _can_sympy_verify(text, fa):
        verified = _sympy_verify(text, fa)
        if not verified:
            res2 = await _call(
                base_llm,
                text,
                critique="Your final answer does not check out symbolically. Fix arithmetic/logic and re-output JSON.",
            )
            steps, fa, diff, conf = (
                res2["steps"],
                res2["final_answer"],
                res2["difficulty"],
                res2["confidence"],
            )
            if _can_sympy_verify(text, fa):
                verified = _sympy_verify(text, fa)

    # 3) Escalate to stronger model if needed
    if (not verified and _can_sympy_verify(text, fa)) or conf < threshold:
        res3 = await _call(
            strong_llm,
            text,
            critique="Produce a more rigorous, carefully verified solution.",
        )
        steps, fa, diff, conf = (
            res3["steps"],
            res3["final_answer"],
            res3["difficulty"],
            res3["confidence"],
        )
        used_model = getattr(strong_llm, "name", used_model)
        used_provider = getattr(strong_llm, "provider", used_provider)
        if _can_sympy_verify(text, fa):
            verified = _sympy_verify(text, fa)

    return {
        "work": steps,
        "answer": fa,
        "verified": bool(verified),
        "confidence": float(conf),
        "difficulty": int(diff),
        "model": {"provider": used_provider, "name": used_model},
    }


async def finalize(state: State, base_llm: LLM) -> State:
    return {
        "model": {
            "provider": getattr(base_llm, "provider", "unknown"),
            "name": getattr(base_llm, "name", "unknown"),
        }
    }


def get_workflow(base_llm: LLM | None = None, strong_llm: LLM | None = None):
    """Build the LangGraph with injected models (DI-friendly)."""
    base = base_llm or ModelFactory.text_default()
    stronger = strong_llm or ModelFactory.text_stronger()

    g = StateGraph(State)

    async def solve_node(s: State) -> State:
        return await solve_llm(s, base, stronger)

    async def finalize_node(s: State) -> State:
        return await finalize(s, base)

    g.add_node("ingest", ingest)
    g.add_node("parse", parse_node)
    g.add_node("solve_llm", solve_node)
    g.add_node("finalize", finalize_node)

    g.add_edge(START, "ingest")
    g.add_edge("ingest", "parse")
    g.add_conditional_edges("parse", route, {"solve_llm": "solve_llm"})
    g.add_edge("solve_llm", "finalize")
    g.add_edge("finalize", END)
    return g.compile()
