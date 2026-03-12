"""JWT helpers."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt as pyjwt

from app.utils.time import utcnow


JWT_ALGORITHM = "HS256"


class JWTError(Exception):
    """Raised when JWT encoding or decoding fails."""



def encode_jwt(payload: Dict[str, Any], secret_key: str, expires_delta: timedelta) -> str:
    now = utcnow()
    claims = dict(payload)
    claims.setdefault("iat", int(now.timestamp()))
    claims["exp"] = int((now + expires_delta).timestamp())
    return pyjwt.encode(claims, secret_key, algorithm=JWT_ALGORITHM)



def decode_jwt(token: str, secret_key: str) -> Dict[str, Any]:
    try:
        return pyjwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
    except pyjwt.PyJWTError as exc:  # pragma: no cover - library-specific branches
        raise JWTError(str(exc)) from exc
