"""Dependency injection – współdzielone zależności dla wszystkich routerów."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.uzytkownicy import RolaUzytkownika, Uzytkownik
from app.services.ai import OllamaService, get_ai
from app.services.auth import decode_token
from app.services.cache import RedisCache, get_cache
from app.services.storage import MinioStorage, get_storage

DB = Annotated[AsyncSession, Depends(get_db)]
Cache = Annotated[RedisCache, Depends(get_cache)]
Storage = Annotated[MinioStorage, Depends(get_storage)]
AI = Annotated[OllamaService, Depends(get_ai)]

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Uzytkownik:
    """Wymagane uwierzytelnienie – 401 jeśli brak lub niepoprawny token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Brak tokena autoryzacyjnego",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload["sub"]
    except (JWTError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Niepoprawny lub wygasły token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await db.get(Uzytkownik, uuid.UUID(user_id))
    if not user or not user.aktywny or user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Konto nieaktywne")
    return user


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Uzytkownik | None:
    """Opcjonalne uwierzytelnienie – None jeśli brak tokena."""
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload["sub"]
        user = await db.get(Uzytkownik, uuid.UUID(user_id))
        return user if (user and user.aktywny and user.deleted_at is None) else None
    except Exception:
        return None


def wymagaj_role(*role: RolaUzytkownika):
    """Factory dependency – wymaga jednej z podanych ról."""

    async def _check(current_user: Uzytkownik = Depends(get_current_user)) -> Uzytkownik:
        if current_user.rola not in [str(r) for r in role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Wymagana rola: {', '.join(role)}",
            )
        return current_user

    return _check


CurrentUser = Annotated[Uzytkownik, Depends(get_current_user)]
OptionalUser = Annotated[Uzytkownik | None, Depends(get_current_user_optional)]


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    return forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
