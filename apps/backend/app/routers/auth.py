"""Autoryzacja – rejestracja, logowanie, odświeżanie sesji."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Response, status
from jose import JWTError
from sqlalchemy import select

from app.config import settings
from app.dependencies import Cache, CurrentUser, DB, get_client_ip
from app.models.audit import OperacjaAudit
from app.models.uzytkownicy import RolaUzytkownika, Uzytkownik
from app.schemas.uzytkownicy import LoginRequest, TokenResponse, UzytkownikCreate, UzytkownikRead
from app.services import audit as audit_svc
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Autoryzacja"])

_REFRESH_TTL = 7 * 24 * 3600  # 7 days in seconds
_REFRESH_PATH = "/api/auth"


@router.post("/token", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, response: Response, db: DB, cache: Cache):
    result = await db.execute(
        select(Uzytkownik).where(
            Uzytkownik.email == payload.email,
            Uzytkownik.deleted_at.is_(None),
        )
    )
    user: Uzytkownik | None = result.scalar_one_or_none()

    if not user or not verify_password(payload.haslo, user.haslo_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Niepoprawny email lub hasło",
        )
    if not user.aktywny:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Konto nieaktywne")

    user.ostatnie_logowanie = datetime.now(timezone.utc)
    await db.flush()

    await audit_svc.zapisz(
        db,
        tabela="uzytkownicy",
        rekord_id=user.id,
        operacja=OperacjaAudit.ZALOGOWANO,
        uzytkownik_id=user.id,
        parafia_id=user.parafia_id,
        ip_adres=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    # Generate tokens
    jti = str(uuid.uuid4())
    await cache.set(f"refresh:{jti}", str(user.id), ttl=_REFRESH_TTL)
    refresh_jwt = create_refresh_token(str(user.id), jti)

    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "rola": user.rola,
        "parafia_id": str(user.parafia_id) if user.parafia_id else None,
        "imie": user.imie,
        "nazwisko": user.nazwisko,
    })

    response.set_cookie(
        "refresh_token",
        refresh_jwt,
        httponly=True,
        samesite="lax",
        max_age=_REFRESH_TTL,
        path=_REFRESH_PATH,
        secure=settings.environment == "production",
    )

    return TokenResponse(access_token=access_token, user=UzytkownikRead.model_validate(user))


@router.post("/refresh")
async def refresh_token(request: Request, response: Response, db: DB, cache: Cache):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Brak tokena odświeżania",
        )

    try:
        claims = decode_refresh_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Niepoprawny lub wygasły token odświeżania",
        )

    jti = claims.get("jti")
    user_id = claims.get("sub")

    stored_user_id = await cache.get(f"refresh:{jti}")
    if stored_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token odświeżania wygasł lub został unieważniony",
        )

    user: Uzytkownik | None = await db.get(Uzytkownik, uuid.UUID(user_id))
    if not user or not user.aktywny or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Konto nieaktywne lub nie istnieje",
        )

    # Rotate: delete old JTI, create new one
    await cache.delete(f"refresh:{jti}")
    new_jti = str(uuid.uuid4())
    await cache.set(f"refresh:{new_jti}", str(user.id), ttl=_REFRESH_TTL)
    new_refresh_jwt = create_refresh_token(str(user.id), new_jti)

    new_access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "rola": user.rola,
        "parafia_id": str(user.parafia_id) if user.parafia_id else None,
        "imie": user.imie,
        "nazwisko": user.nazwisko,
    })

    response.set_cookie(
        "refresh_token",
        new_refresh_jwt,
        httponly=True,
        samesite="lax",
        max_age=_REFRESH_TTL,
        path=_REFRESH_PATH,
        secure=settings.environment == "production",
    )

    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, cache: Cache):
    token = request.cookies.get("refresh_token")
    if token:
        try:
            claims = decode_refresh_token(token)
            jti = claims.get("jti")
            if jti:
                await cache.delete(f"refresh:{jti}")
        except JWTError:
            pass  # Token invalid/expired – still clear the cookie

    response.delete_cookie("refresh_token", path=_REFRESH_PATH)


@router.post("/rejestracja", response_model=UzytkownikRead, status_code=status.HTTP_201_CREATED)
async def rejestracja(payload: UzytkownikCreate, request: Request, db: DB):
    """
    Rejestracja nowego konta.
    - Pierwsze konto w systemie automatycznie otrzymuje rolę ADMIN.
    - Kolejne konta PROBOSZCZ/ADMIN wymagają autoryzacji (sprawdzane poniżej).
    """
    existing = await db.execute(
        select(Uzytkownik).where(Uzytkownik.email == payload.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email jest już zajęty")

    liczba_uzytkownikow = await db.execute(select(Uzytkownik))
    is_first = not liczba_uzytkownikow.first()

    rola = RolaUzytkownika.ADMIN if is_first else payload.rola

    user = Uzytkownik(
        email=payload.email,
        haslo_hash=hash_password(payload.haslo),
        imie=payload.imie,
        nazwisko=payload.nazwisko,
        rola=rola,
        parafia_id=payload.parafia_id,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    await audit_svc.zapisz(
        db,
        tabela="uzytkownicy",
        rekord_id=user.id,
        operacja=OperacjaAudit.UTWORZONO,
        uzytkownik_id=user.id,
        nowe_wartosci=audit_svc.snapshot(user),
        ip_adres=get_client_ip(request),
    )
    return UzytkownikRead.model_validate(user)


@router.get("/mnie", response_model=UzytkownikRead)
async def moje_konto(current_user: CurrentUser):
    return UzytkownikRead.model_validate(current_user)
