import base64, json, re
from typing import Dict, Any, Optional
from .model_factory import ModelFactory

_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.S)


def _parse_json_only(s: str) -> Optional[dict]:
    s = (s or "").strip()
    m = _JSON_BLOCK.search(s)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    try:
        return json.loads(s)
    except Exception:
        return None


async def solve_image_json(
    image_bytes: bytes,
    ocr_hint: str | None = None,
    use_stronger_if_low_conf: bool = True,
    threshold: float = 0.6,
) -> dict:
    """
    Vision-first solver: send the image (and optional OCR hint) directly to a vision-capable LLM.
    Returns a dict with keys: steps, final_answer, difficulty, confidence, topic.
    """

    def make_prompt(hint: str | None) -> list:
        rules = (
            "You are an expert math teacher. Look at the image and solve using visual evidence.\n"
            "- If it's a shaded grid: COUNT shaded cells and total cells explicitly.\n"
            "- If it's geometry: read lengths/angles/labels from the picture before derivation.\n"
            "- If multiple choices exist, do NOT guess from options; derive from image data.\n"
            'Output ONLY JSON: {"steps":[{"title":str,"explanation":str},...],"final_answer":str,"difficulty":int,"confidence":float,"topic":str}\n'
            'If the question text is missing (only choices), output {"steps":[...],"final_answer":"","difficulty":1,"confidence":0.0,"topic":"incomplete"}.\n'
        )
        content = [{"type": "text", "text": rules}]
        return content

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    user_content = make_prompt(ocr_hint)
    user_content.append(
        {"type": "image_url", "image_url": f"data:image/png;base64,{b64}"}
    )
    if ocr_hint and ocr_hint.strip():
        user_content.append(
            {"type": "text", "text": f"OCR hint (weak):\n{ocr_hint.strip()}"}
        )

    # 1) Try default vision model
    vision = ModelFactory.vision_default()
    out = await vision.ask([{"role": "user", "content": user_content}])
    data = _parse_json_only(out) or {}

    # 2) If confidence is low and allowed, try stronger vision model
    try:
        conf = float(data.get("confidence", 0.0))
    except Exception:
        conf = 0.0

    if use_stronger_if_low_conf and conf < threshold:
        strong_vision = ModelFactory.vision_stronger()
        out2 = await strong_vision.ask([{"role": "user", "content": user_content}])
        data2 = _parse_json_only(out2)
        if data2:
            data = data2

    return data or {
        "steps": [{"title": "Explanation", "explanation": "Model returned no JSON."}],
        "final_answer": "",
        "difficulty": 1,
        "confidence": 0.0,
        "topic": "unknown",
    }
