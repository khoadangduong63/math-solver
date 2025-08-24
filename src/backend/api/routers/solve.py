from fastapi import APIRouter, UploadFile, File, HTTPException, status, Request, Depends
from core.schemas import (
    TextSolveRequest,
    SolveResponse,
    ImageSolveResponse,
    Step,
    ModelInfo,
)
from reasoner.graph import get_workflow
from providers.vision import solve_image_json
from utils.image_ocr import extract_text
from api.deps import get_current_user
import structlog
import io
import os
from PIL import Image, UnidentifiedImageError

log = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/solve-text", response_model=SolveResponse)
async def solve_text(
    req: TextSolveRequest, request: Request, uid: str = Depends(get_current_user)
):
    log.debug(
        "solve_text.request",
        uid=uid,
        content_length=request.headers.get("content-length"),
        user_agent=request.headers.get("user-agent"),
    )

    q = (req.question or "").strip()
    if not q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="question must not be empty"
        )

    state = {
        "question": q,
        "original_question": q,
        "ir": {"text": q, "latex": []},
        "level": req.level or "auto",
        "locale": req.locale or "en",
    }
    wf = get_workflow()
    result = await wf.ainvoke(state)
    return SolveResponse.from_state(result)


@router.post("/solve-image", response_model=ImageSolveResponse)
async def solve_image(
    file: UploadFile = File(...), uid: str = Depends(get_current_user)
):
    log.debug(
        "solve_image.request",
        uid=uid,
        filename=file.filename,
        content_type=file.content_type,
    )
    max_size = 5 * 1024 * 1024  # 5MB limit
    file_size = getattr(file, "size", None)
    if file_size is None:
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
    if file_size and file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="file too large",
        )

    img_bytes = await file.read()

    try:
        with Image.open(io.BytesIO(img_bytes)) as img:
            mime_type = Image.MIME.get(img.format, "")
    except UnidentifiedImageError:
        mime_type = ""

    if not mime_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="file must be an image"
        )

    # 1) OCR hint (weak)
    ocr_text, _ = await extract_text(img_bytes)

    # 2) Vision-first: ask the model to solve from pixels
    data = await solve_image_json(
        img_bytes, ocr_hint=ocr_text, use_stronger_if_low_conf=True
    )
    if data and isinstance(data, dict) and "steps" in data and "final_answer" in data:
        steps = data.get("steps") or []
        steps = [
            Step(title=s.get("title", "Step"), explanation=s.get("explanation", ""))
            for s in steps
            if isinstance(s, dict)
        ]
        resp = SolveResponse(
            final_answer=str(data.get("final_answer", "")),
            steps=steps if steps else [Step(title="Explanation", explanation="")],
            verified=False,  # you can verify on FE or extend here for special cases
            latex=None,
            level="auto",
            confidence=float(data.get("confidence", 0.6) or 0.0),
            difficulty=int(data.get("difficulty", 2) or 0),
            model=ModelInfo(provider="auto", name="vision"),
        )
        return ImageSolveResponse(ocr_text=ocr_text or "", result=resp.model_dump())

    # 3) Fallback: if Vision returns nothing AND OCR found text → try text pipeline
    if not ocr_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract a valid math question from image. Please upload a clearer photo or re-type the question.",
        )

    state = {
        "question": ocr_text.strip(),
        "original_question": ocr_text.strip(),
        "ir": {"text": ocr_text.strip(), "latex": []},
        "level": "auto",
        "locale": "en",
    }
    wf = get_workflow()
    result = await wf.ainvoke(state)
    return ImageSolveResponse(
        ocr_text=ocr_text, result=SolveResponse.from_state(result).model_dump()
    )
