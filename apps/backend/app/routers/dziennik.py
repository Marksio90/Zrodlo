"""Dziennik kancleryjny – rejestr korespondencji (L.dz. XX/YYYY)."""
import csv
import io
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DB
from app.models.audit import OperacjaAudit
from app.models.dziennik import StatusWpisu, TypWpisu, WpisDziennika
from app.models.uzytkownicy import RolaUzytkownika
from app.schemas.dziennik import (
    StatystykiDziennika,
    WpisDziennikCreate,
    WpisDziennikRead,
    WpisDziennikUpdate,
)
from app.services import audit as audit_svc

router = APIRouter(prefix="/dziennik", tags=["Dziennik kancleryjny"])

_ROLE_ZAPIS = {RolaUzytkownika.PROBOSZCZ, RolaUzytkownika.WIKARIUSZ, RolaUzytkownika.ADMIN}
_ROLE_ADMIN = {RolaUzytkownika.PROBOSZCZ, RolaUzytkownika.ADMIN}


def _wymagaj_parafie(user) -> uuid.UUID:
    if not user.parafia_id:
        raise HTTPException(status_code=400, detail="Konto nie jest przypisane do parafii")
    return user.parafia_id


async def _nastepny_numer(db: DB, parafia_id: uuid.UUID, rok: int) -> int:
    """Wyznacza następny numer sekwencyjny dla danej parafii i roku."""
    result = await db.execute(
        select(func.coalesce(func.max(WpisDziennika.kolejny_numer), 0)).where(
            WpisDziennika.parafia_id == parafia_id,
            WpisDziennika.rok == rok,
            WpisDziennika.deleted_at.is_(None),
        )
    )
    return (result.scalar_one_or_none() or 0) + 1


# ── Stałe/statystyki – MUSZĄ być przed /{wpis_id} ──────────────────────────

@router.get("/statystyki", response_model=StatystykiDziennika, summary="Statystyki dziennika (bieżący rok)")
async def statystyki(current_user: CurrentUser, db: DB):
    parafia_id = _wymagaj_parafie(current_user)
    rok = datetime.now(timezone.utc).year

    base = select(WpisDziennika).where(
        WpisDziennika.parafia_id == parafia_id,
        WpisDziennika.rok == rok,
        WpisDziennika.deleted_at.is_(None),
    )

    agg = await db.execute(
        select(
            func.count(WpisDziennika.id).label("lacznie"),
            func.count(WpisDziennika.id).filter(WpisDziennika.typ == TypWpisu.PRZYCHODZACE).label("przychodzace"),
            func.count(WpisDziennika.id).filter(WpisDziennika.typ == TypWpisu.WYCHODZACE).label("wychodzace"),
            func.count(WpisDziennika.id).filter(WpisDziennika.typ == TypWpisu.WEWNETRZNE).label("wewnetrzne"),
            func.coalesce(func.max(WpisDziennika.kolejny_numer), 0).label("ostatni_numer"),
        ).where(
            WpisDziennika.parafia_id == parafia_id,
            WpisDziennika.rok == rok,
            WpisDziennika.deleted_at.is_(None),
        )
    )
    row = agg.first()
    return StatystykiDziennika(
        rok=rok,
        lacznie=row.lacznie if row else 0,
        przychodzace=row.przychodzace if row else 0,
        wychodzace=row.wychodzace if row else 0,
        wewnetrzne=row.wewnetrzne if row else 0,
        ostatni_numer=row.ostatni_numer if row else 0,
    )


@router.get("/export/csv", summary="Eksport dziennika do CSV")
async def eksport_csv(
    current_user: CurrentUser,
    db: DB,
    rok: int = Query(default=None),
):
    if current_user.rola not in _ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Brak uprawnień")
    parafia_id = _wymagaj_parafie(current_user)
    rok = rok or datetime.now(timezone.utc).year

    q = (
        select(WpisDziennika)
        .where(
            WpisDziennika.parafia_id == parafia_id,
            WpisDziennika.rok == rok,
            WpisDziennika.deleted_at.is_(None),
        )
        .order_by(WpisDziennika.kolejny_numer)
    )
    result = await db.execute(q)
    wpisy = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Numer", "Typ", "Status", "Data wpisu", "Data pisma",
        "Nadawca", "Odbiorca", "Przedmiot", "Uwagi",
    ])
    for w in wpisy:
        writer.writerow([
            w.numer_pelny, w.typ, w.status,
            w.data_wpisu.isoformat(), w.data_pisma.isoformat() if w.data_pisma else "",
            w.nadawca or "", w.odbiorca or "", w.przedmiot, w.uwagi or "",
        ])

    output.seek(0)
    filename = f"dziennik_{rok}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── CRUD ────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[WpisDziennikRead], summary="Lista wpisów dziennika")
async def lista_wpisow(
    current_user: CurrentUser,
    db: DB,
    rok: int = Query(default=None),
    typ: str | None = Query(None),
    status: str | None = Query(None),
    szukaj: str | None = Query(None, max_length=100),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    parafia_id = _wymagaj_parafie(current_user)
    rok = rok or datetime.now(timezone.utc).year

    q = select(WpisDziennika).where(
        WpisDziennika.parafia_id == parafia_id,
        WpisDziennika.rok == rok,
        WpisDziennika.deleted_at.is_(None),
    )
    if typ:
        q = q.where(WpisDziennika.typ == typ)
    if status:
        q = q.where(WpisDziennika.status == status)
    if szukaj:
        pattern = f"%{szukaj}%"
        q = q.where(
            WpisDziennika.przedmiot.ilike(pattern)
            | WpisDziennika.nadawca.ilike(pattern)
            | WpisDziennika.odbiorca.ilike(pattern)
            | WpisDziennika.numer_pelny.ilike(pattern)
        )
    q = q.order_by(WpisDziennika.kolejny_numer.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=WpisDziennikRead, status_code=201, summary="Nowy wpis w dzienniku")
async def nowy_wpis(body: WpisDziennikCreate, current_user: CurrentUser, db: DB):
    if current_user.rola not in _ROLE_ZAPIS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Brak uprawnień")
    parafia_id = _wymagaj_parafie(current_user)

    rok = body.data_wpisu.year
    numer = await _nastepny_numer(db, parafia_id, rok)

    wpis = WpisDziennika(
        parafia_id=parafia_id,
        uzytkownik_id=current_user.id,
        dokument_id=body.dokument_id,
        rok=rok,
        kolejny_numer=numer,
        numer_pelny=f"L.dz. {numer}/{rok}",
        typ=body.typ,
        status=body.status,
        data_wpisu=body.data_wpisu,
        data_pisma=body.data_pisma,
        nadawca=body.nadawca,
        odbiorca=body.odbiorca,
        przedmiot=body.przedmiot,
        uwagi=body.uwagi,
    )
    db.add(wpis)
    await db.flush()
    await db.refresh(wpis)
    await audit_svc.zapisz(
        db,
        tabela="wpisy_dziennika",
        rekord_id=wpis.id,
        operacja=OperacjaAudit.UTWORZONO,
        uzytkownik_id=current_user.id,
        parafia_id=parafia_id,
        nowe_wartosci=audit_svc.snapshot(wpis),
    )
    await db.commit()
    return wpis


@router.get("/{wpis_id}", response_model=WpisDziennikRead, summary="Szczegóły wpisu")
async def pobierz_wpis(wpis_id: uuid.UUID, current_user: CurrentUser, db: DB):
    parafia_id = _wymagaj_parafie(current_user)
    wpis = await db.get(WpisDziennika, wpis_id)
    if not wpis or wpis.deleted_at or wpis.parafia_id != parafia_id:
        raise HTTPException(status_code=404, detail="Wpis nie znaleziony")
    return wpis


@router.patch("/{wpis_id}", response_model=WpisDziennikRead, summary="Aktualizacja wpisu")
async def aktualizuj_wpis(
    wpis_id: uuid.UUID,
    body: WpisDziennikUpdate,
    current_user: CurrentUser,
    db: DB,
):
    if current_user.rola not in _ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Brak uprawnień")
    parafia_id = _wymagaj_parafie(current_user)
    wpis = await db.get(WpisDziennika, wpis_id)
    if not wpis or wpis.deleted_at or wpis.parafia_id != parafia_id:
        raise HTTPException(status_code=404, detail="Wpis nie znaleziony")

    stare = audit_svc.snapshot(wpis)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(wpis, field, value)
    wpis.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(wpis)
    await audit_svc.zapisz(
        db,
        tabela="wpisy_dziennika",
        rekord_id=wpis.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO,
        uzytkownik_id=current_user.id,
        parafia_id=parafia_id,
        stare_wartosci=stare,
        nowe_wartosci=audit_svc.snapshot(wpis),
    )
    await db.commit()
    return wpis


@router.delete("/{wpis_id}", status_code=204, summary="Usuń wpis (soft delete)")
async def usun_wpis(wpis_id: uuid.UUID, current_user: CurrentUser, db: DB):
    if current_user.rola not in _ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Brak uprawnień")
    parafia_id = _wymagaj_parafie(current_user)
    wpis = await db.get(WpisDziennika, wpis_id)
    if not wpis or wpis.deleted_at or wpis.parafia_id != parafia_id:
        raise HTTPException(status_code=404, detail="Wpis nie znaleziony")
    wpis.deleted_at = datetime.now(timezone.utc)
    await audit_svc.zapisz(
        db,
        tabela="wpisy_dziennika",
        rekord_id=wpis.id,
        operacja=OperacjaAudit.USUNIETO,
        uzytkownik_id=current_user.id,
        parafia_id=parafia_id,
    )
    await db.commit()
