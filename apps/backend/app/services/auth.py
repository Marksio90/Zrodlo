"""JWT authentication + bcrypt password service."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_EXPIRE_MINUTES = 15
REFRESH_EXPIRE_DAYS = 7
ALGORITHM = "HS256"

# Keep backward-compatible alias used in tests
TOKEN_EXPIRE_HOURS = ACCESS_EXPIRE_MINUTES / 60


def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


def create_access_token(payload: dict[str, Any]) -> str:
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRE_MINUTES)
    data["iat"] = datetime.now(timezone.utc)
    return jwt.encode(data, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Raises JWTError on invalid/expired token."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def create_refresh_token(user_id: str, jti: str) -> str:
    """Creates a refresh JWT signed with the refresh secret."""
    data = {
        "sub": user_id,
        "jti": jti,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(data, settings.refresh_secret, algorithm=ALGORITHM)


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Verifies the refresh JWT with refresh secret. Raises JWTError if invalid/expired."""
    payload = jwt.decode(token, settings.refresh_secret, algorithms=[ALGORITHM])
    if payload.get("type") != "refresh":
        raise JWTError("Not a refresh token")
    return payload
