import json
import base64
from typing import Optional

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Header, HTTPException, status

from core.config import settings


def _init_firebase() -> None:
    """Initialize the Firebase app if it hasn't been already."""
    if not firebase_admin._apps:
        raw = settings.firebase_service_account_json
        if not raw:
            raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON is not set")
        if raw.strip().startswith("{"):
            cred_info = json.loads(raw)
        else:
            cred_info = json.loads(base64.b64decode(raw))
        cred = credentials.Certificate(cred_info)
        firebase_admin.initialize_app(cred)


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Validate the Authorization header and return the user's UID."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    _init_firebase()

    token = authorization.split(" ", 1)[1]
    try:
        decoded = auth.verify_id_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from None
    uid = decoded.get("uid")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return uid
