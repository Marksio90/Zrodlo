"""Autoryzacja – rejestracja, logowanie, odświeżanie sesji."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DB, get_client_ip
from app.models.audit import OperacjaAudit
from app.models.uzytkownicy import RolaUzytkownika, Uzytkownik
from app.schemas.uzytkownicy import LoginRequest, TokenResponse, UzytkownikCreate, UzytkownikRead
from app.services import audit as audit_svc
from app.services.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Autoryzacja"])


@router.post("/token", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: DB):
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

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "rola": user.rola,
        "parafia_id": str(user.parafia_id) if user.parafia_id else None,
    })
    return TokenResponse(access_token=token, user=UzytkownikRead.model_validate(user))


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
