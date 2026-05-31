"""Router RODO – zarządzanie Umową Powierzenia Danych (art. 28 RODO)."""
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DB
from app.models.rodo import AkceptacjaUmowy
from app.models.uzytkownicy import RolaUzytkownika
from app.schemas.rodo import (
    AKTUALNA_WERSJA,
    AkceptacjaRead,
    AkceptacjaRequest,
    StatusRodo,
    UmowaInfo,
)

router = APIRouter(prefix="/rodo", tags=["RODO"])

_UMOWA_PATH = Path(__file__).parent.parent.parent.parent.parent.parent / \
    "infra" / "legal" / "umowa_powierzenia_danych.md"

_ROLE_MOZE_AKCEPTOWAC = {RolaUzytkownika.PROBOSZCZ, RolaUzytkownika.ADMIN}


async def _ostatnia_akceptacja(
    db: DB, parafia_id, wersja: str | None = None
) -> AkceptacjaUmowy | None:
    q = (
        select(AkceptacjaUmowy)
        .where(AkceptacjaUmowy.parafia_id == parafia_id)
        .order_by(AkceptacjaUmowy.zaakceptowano_at.desc())
        .limit(1)
    )
    if wersja:
        q = q.where(AkceptacjaUmowy.wersja == wersja)
    result = await db.execute(q)
    return result.scalar_one_or_none()


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/umowa", response_model=UmowaInfo, summary="Informacja o aktualnej umowie")
async def get_umowa_info():
    """Zwraca metadane aktualnej wersji Umowy Powierzenia Danych.
    Endpoint publiczny – dostępny bez logowania, by parafia mogła zapoznać się z umową przed rejestracją.
    """
    return UmowaInfo()


@router.get("/umowa/tresc", summary="Treść umowy (Markdown)")
async def get_umowa_tresc():
    """Zwraca pełną treść Umowy Powierzenia Danych w formacie Markdown."""
    try:
        tresc = _UMOWA_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Treść umowy niedostępna")
    return {"wersja": AKTUALNA_WERSJA, "tresc": tresc}


@router.get("/status", response_model=StatusRodo, summary="Status akceptacji dla parafii")
async def get_status(current_user: CurrentUser, db: DB):
    """Zwraca czy parafia zaakceptowała aktualną wersję umowy."""
    if not current_user.parafia_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Konto nie jest przypisane do parafii",
        )

    akceptacja = await _ostatnia_akceptacja(db, current_user.parafia_id)
    zaakceptowana = akceptacja is not None and akceptacja.wersja == AKTUALNA_WERSJA

    return StatusRodo(
        parafia_id=current_user.parafia_id,
        zaakceptowana=zaakceptowana,
        wersja_zaakceptowana=akceptacja.wersja if akceptacja else None,
        zaakceptowano_at=akceptacja.zaakceptowano_at if akceptacja else None,
        wymaga_akceptacji=not zaakceptowana,
    )


@router.post(
    "/akceptuj",
    response_model=AkceptacjaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Zaakceptuj umowę powierzenia danych",
)
async def akceptuj_umowe(
    payload: AkceptacjaRequest,
    current_user: CurrentUser,
    db: DB,
    request: Request,
):
    """Rejestruje akceptację Umowy Powierzenia Danych przez proboszcza lub admina.

    Tworzy niemodyfikowalny wpis audytowy z adresem IP, user-agentem i timestampem.
    Tylko proboszcz lub administrator może akceptować umowę w imieniu parafii.
    """
    if current_user.rola not in _ROLE_MOZE_AKCEPTOWAC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tylko proboszcz lub administrator może akceptować umowę",
        )
    if not current_user.parafia_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Konto nie jest przypisane do parafii",
        )
    if payload.wersja != AKTUALNA_WERSJA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Nieznana wersja umowy: {payload.wersja}. Aktualna: {AKTUALNA_WERSJA}",
        )

    # Pobierz IP i user-agent ze standardowych nagłówków (nginx ustawia X-Forwarded-For)
    forwarded = request.headers.get("X-Forwarded-For")
    ip = forwarded.split(",")[0].strip() if forwarded else (
        request.client.host if request.client else None
    )
    ua = request.headers.get("User-Agent", "")[:500]

    wpis = AkceptacjaUmowy(
        parafia_id=current_user.parafia_id,
        zaakceptowana_przez=current_user.id,
        wersja=payload.wersja,
        zaakceptowano_at=datetime.now(timezone.utc),
        ip_adres=ip,
        user_agent=ua or None,
    )
    db.add(wpis)
    await db.flush()
    await db.refresh(wpis)
    return wpis


@router.get(
    "/historia",
    response_model=list[AkceptacjaRead],
    summary="Historia akceptacji umowy dla parafii",
)
async def historia_akceptacji(current_user: CurrentUser, db: DB):
    """Zwraca historię akceptacji umów dla parafii (wyłącznie proboszcz/admin)."""
    if current_user.rola not in _ROLE_MOZE_AKCEPTOWAC:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Brak uprawnień")
    if not current_user.parafia_id:
        raise HTTPException(status_code=400, detail="Konto nie jest przypisane do parafii")

    result = await db.execute(
        select(AkceptacjaUmowy)
        .where(AkceptacjaUmowy.parafia_id == current_user.parafia_id)
        .order_by(AkceptacjaUmowy.zaakceptowano_at.desc())
    )
    return result.scalars().all()
