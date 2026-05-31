"""Zaproszenia użytkowników – invite link → aktywacja konta."""

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from app.dependencies import Cache, CurrentUser, DB
from app.models.uzytkownicy import RolaUzytkownika, Uzytkownik
from app.services.auth import hash_password
from app.services.email import send_invite_email
from app.services.permissions import wymagaj_uprawnienia

router = APIRouter(prefix="/zaproszenia", tags=["Zaproszenia"])

_INVITE_TTL = 7 * 24 * 3600  # 7 dni


class _WyslijZaproszenie(BaseModel):
    email: EmailStr
    rola: RolaUzytkownika = RolaUzytkownika.PARAFIANIN


class _AktywujKonto(BaseModel):
    token: str
    imie: str = Field(..., min_length=2, max_length=100)
    nazwisko: str = Field(..., min_length=2, max_length=100)
    haslo: str = Field(..., min_length=8, max_length=200)


class _ZaproszenieInfo(BaseModel):
    email: str
    rola: str


@router.post(
    "/wyslij",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(wymagaj_uprawnienia("uzytkownik", "tworz"))],
)
async def wyslij_zaproszenie(
    payload: _WyslijZaproszenie,
    current_user: CurrentUser,
    db: DB,
    cache: Cache,
):
    """Proboszcz/Admin wysyła zaproszenie e-mailowe do nowego użytkownika."""
    existing = await db.execute(
        select(Uzytkownik).where(Uzytkownik.email == payload.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Użytkownik z tym adresem e-mail już istnieje",
        )

    invite_data = json.dumps({
        "email": payload.email,
        "rola": payload.rola,
        "parafia_id": str(current_user.parafia_id) if current_user.parafia_id else None,
        "zaproszony_przez": str(current_user.id),
    })
    token = str(uuid.uuid4())
    await cache.set(f"invite:{token}", invite_data, ttl=_INVITE_TTL)
    await send_invite_email(to=payload.email, token=token)


@router.get("/info", response_model=_ZaproszenieInfo)
async def info_zaproszenia(token: str, cache: Cache):
    """Pobiera informacje o zaproszeniu (bez logowania)."""
    raw = await cache.get(f"invite:{token}")
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zaproszenie nie istnieje lub wygasło",
        )
    data = json.loads(raw)
    return _ZaproszenieInfo(email=data["email"], rola=data["rola"])


@router.post("/aktywuj", status_code=status.HTTP_201_CREATED)
async def aktywuj_konto(payload: _AktywujKonto, db: DB, cache: Cache):
    """Aktywacja konta na podstawie tokenu z e-maila."""
    raw = await cache.get(f"invite:{payload.token}")
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zaproszenie nie istnieje lub wygasło",
        )
    data = json.loads(raw)

    existing = await db.execute(
        select(Uzytkownik).where(Uzytkownik.email == data["email"])
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Konto już istnieje")

    parafia_id = uuid.UUID(data["parafia_id"]) if data.get("parafia_id") else None
    user = Uzytkownik(
        email=data["email"],
        haslo_hash=hash_password(payload.haslo),
        imie=payload.imie,
        nazwisko=payload.nazwisko,
        rola=data["rola"],
        parafia_id=parafia_id,
        aktywny=True,
    )
    db.add(user)
    await cache.delete(f"invite:{payload.token}")
    await db.flush()
    await db.refresh(user)

    from app.schemas.uzytkownicy import UzytkownikRead
    return UzytkownikRead.model_validate(user)
