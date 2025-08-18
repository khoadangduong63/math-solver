from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator


class TextSolveRequest(BaseModel):
    question: str = Field(..., description="Math question in plain text.")
    level: Optional[str] = "auto"
    locale: Optional[str] = "en"

    @field_validator("question")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if v is None or not str(v).strip():
            raise ValueError("question must not be empty")
        return str(v).strip()


class Step(BaseModel):
    title: str
    explanation: str


class ModelInfo(BaseModel):
    provider: str
    name: str


class SolveResponse(BaseModel):
    final_answer: str
    steps: List[Step]
    verified: bool
    latex: Optional[str] = None
    level: Optional[str] = "auto"
    confidence: Optional[float] = None
    difficulty: Optional[int] = None
    model: Optional[ModelInfo] = None

    @classmethod
    def from_state(cls, state: Dict):
        steps_in = state.get("work", []) or []
        steps = [
            Step(**s)
            for s in steps_in
            if isinstance(s, dict) and "title" in s and "explanation" in s
        ]
        ir = state.get("ir", {}) or {}
        latex = None
        if isinstance(ir.get("latex"), list) and ir["latex"]:
            latex = ir["latex"][0]
        model = state.get("model") or {}
        return cls(
            final_answer=str(state.get("answer", "")),
            steps=steps,
            verified=bool(state.get("verified", False)),
            latex=latex,
            level=state.get("level", "auto"),
            confidence=state.get("confidence"),
            difficulty=state.get("difficulty"),
            model=ModelInfo(
                provider=model.get("provider", "unknown"),
                name=model.get("name", "unknown"),
            ),
        )


class ImageSolveResponse(BaseModel):
    ocr_text: str
    result: Dict
