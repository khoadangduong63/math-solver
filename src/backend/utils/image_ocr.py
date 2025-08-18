from typing import Tuple
import re
import cv2
import numpy as np
import pytesseract

_MATH_LIKE_RE = re.compile(
    r"(=|[\+\-\*/^]|\\frac|\\sqrt|\\sum|\\int|\\lim|\\pi|\\theta|\\alpha|\\beta|\\le|\\ge|\\approx|\d)",
    re.I,
)


def _looks_like_math(text: str) -> bool:
    if not text:
        return False
    s = text.strip()
    if len(s) < 4:
        return False
    return bool(_MATH_LIKE_RE.search(s))


def _preprocess(img: np.ndarray) -> np.ndarray:
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.medianBlur(g, 3)
    thr = cv2.adaptiveThreshold(
        g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9
    )
    return thr


async def extract_text(image_bytes: bytes) -> Tuple[str, str]:
    """Lightweight OCR (Tesseract) used only as a weak hint for the Vision model."""
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return "", "decode-error"
    proc = _preprocess(img)
    text = pytesseract.image_to_string(proc, lang="eng")
    text = (text or "").strip()
    if _looks_like_math(text):
        return text, "tesseract"
    return "", "none"
