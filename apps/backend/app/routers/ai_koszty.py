"""Router monitorowania kosztów AI – podsumowanie i alerty per parafia."""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DB
from app.models.ai_uzycie import AiUzycie
from app.models.subskrypcja import Subskrypcja
from app.models.uzytkownicy import RolaUzytkownika
from app.schemas.ai_koszty import (
    AlertAi,
    PodsumowanieAi,
    UzycieDzienne,
    UzycieModelowe,
    UzycieWpisRead,
)
from app.services.subskrypcja import limity_dla_planu, pobierz_aktywna_subskrypcje

router = APIRouter(prefix="/ai/koszty", tags=["AI – Koszty"])


def _aktualny_miesiac() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    od = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        do = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        do = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return od, do


async def _limit_zapytan(db: DB, parafia_id) -> int | None:
    sub = await pobierz_aktywna_subskrypcje(db, parafia_id)
    if sub is None:
        return None
    return limity_dla_planu(sub.plan).max_ai_zapytan_miesiac


@router.get("/podsumowanie", response_model=PodsumowanieAi, summary="Podsumowanie kosztów AI (bieżący miesiąc)")
async def podsumowanie(current_user: CurrentUser, db: DB):
    if not current_user.parafia_id:
        raise HTTPException(status_code=400, detail="Konto nie jest przypisane do parafii")

    parafia_id = current_user.parafia_id
    od, do = _aktualny_miesiac()
    miesiac = od.strftime("%Y-%m")

    base_q = select(AiUzycie).where(
        AiUzycie.parafia_id == parafia_id,
        AiUzycie.created_at >= od,
        AiUzycie.created_at < do,
    )

    # Agregat główny
    agg = await db.execute(
        select(
            func.count(AiUzycie.id).label("zapytania"),
            func.coalesce(func.sum(AiUzycie.tokeny_wejscie + AiUzycie.tokeny_wyjscie), 0).label("tokeny"),
            func.coalesce(func.sum(AiUzycie.koszt_usd), Decimal("0")).label("koszt"),
        ).where(
            AiUzycie.parafia_id == parafia_id,
            AiUzycie.created_at >= od,
            AiUzycie.created_at < do,
        )
    )
    row = agg.first()
    zapytania = int(row.zapytania) if row else 0
    tokeny = int(row.tokeny) if row else 0
    koszt = Decimal(str(row.koszt)) if row else Decimal("0")

    # Per model
    per_model_raw = await db.execute(
        select(
            AiUzycie.model,
            func.count(AiUzycie.id).label("zapytania"),
            func.coalesce(func.sum(AiUzycie.tokeny_wejscie), 0).label("t_in"),
            func.coalesce(func.sum(AiUzycie.tokeny_wyjscie), 0).label("t_out"),
            func.coalesce(func.sum(AiUzycie.koszt_usd), Decimal("0")).label("koszt"),
        ).where(
            AiUzycie.parafia_id == parafia_id,
            AiUzycie.created_at >= od,
            AiUzycie.created_at < do,
        ).group_by(AiUzycie.model)
    )
    per_model = [
        UzycieModelowe(
            model=r.model,
            zapytania=int(r.zapytania),
            tokeny_wejscie=int(r.t_in),
            tokeny_wyjscie=int(r.t_out),
            koszt_usd=Decimal(str(r.koszt)),
        )
        for r in per_model_raw
    ]

    # Per dzień (ostatnie 30 dni)
    per_dzien_raw = await db.execute(
        select(
            func.date(AiUzycie.created_at).label("dzien"),
            func.count(AiUzycie.id).label("zapytania"),
            func.coalesce(func.sum(AiUzycie.tokeny_wejscie + AiUzycie.tokeny_wyjscie), 0).label("tokeny"),
            func.coalesce(func.sum(AiUzycie.koszt_usd), Decimal("0")).label("koszt"),
        ).where(
            AiUzycie.parafia_id == parafia_id,
            AiUzycie.created_at >= od,
            AiUzycie.created_at < do,
        ).group_by(func.date(AiUzycie.created_at))
        .order_by(func.date(AiUzycie.created_at))
    )
    per_dzien = [
        UzycieDzienne(
            data=str(r.dzien),
            zapytania=int(r.zapytania),
            tokeny=int(r.tokeny),
            koszt_usd=Decimal(str(r.koszt)),
        )
        for r in per_dzien_raw
    ]

    limit = await _limit_zapytan(db, parafia_id)
    procent = round(zapytania / limit * 100, 1) if limit and limit > 0 else None

    return PodsumowanieAi(
        miesiac=miesiac,
        zapytania_lacznie=zapytania,
        tokeny_lacznie=tokeny,
        koszt_usd_lacznie=koszt,
        limit_zapytan=limit,
        procent_limitu=procent,
        per_model=per_model,
        per_dzien=per_dzien,
    )


@router.get("/alerty", response_model=AlertAi, summary="Status alertów AI")
async def alerty(current_user: CurrentUser, db: DB):
    """Zwraca poziom alertu na podstawie % wykorzystanego limitu zapytań AI."""
    if not current_user.parafia_id:
        raise HTTPException(status_code=400, detail="Konto nie jest przypisane do parafii")

    od, do = _aktualny_miesiac()
    agg = await db.execute(
        select(func.count(AiUzycie.id).label("zapytania")).where(
            AiUzycie.parafia_id == current_user.parafia_id,
            AiUzycie.created_at >= od,
            AiUzycie.created_at < do,
        )
    )
    zapytania = int((agg.first() or [0]).zapytania)
    limit = await _limit_zapytan(db, current_user.parafia_id)

    if limit is None or limit == 0:
        return AlertAi(
            poziom="ok",
            procent_limitu=None,
            zapytania_w_miesiacu=zapytania,
            limit_zapytan=limit,
            wiadomosc="Plan bez limitu zapytań AI.",
        )

    procent = round(zapytania / limit * 100, 1)

    if procent >= 100:
        poziom, msg = "krytyczny", f"Wykorzystano {procent}% limitu ({zapytania}/{limit}). AI może być niedostępne."
    elif procent >= 80:
        poziom, msg = "ostrzezenie", f"Zbliżasz się do limitu: {procent}% ({zapytania}/{limit} zapytań)."
    else:
        poziom, msg = "ok", f"Zużyto {procent}% limitu ({zapytania}/{limit} zapytań)."

    return AlertAi(
        poziom=poziom,
        procent_limitu=procent,
        zapytania_w_miesiacu=zapytania,
        limit_zapytan=limit,
        wiadomosc=msg,
    )


@router.get("/szczegoly", response_model=list[UzycieWpisRead], summary="Szczegółowy log użycia AI")
async def szczegoly(
    current_user: CurrentUser,
    db: DB,
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    typ: str | None = Query(None),
):
    if not current_user.parafia_id:
        raise HTTPException(status_code=400, detail="Konto nie jest przypisane do parafii")
    if current_user.rola not in {RolaUzytkownika.PROBOSZCZ, RolaUzytkownika.ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Brak uprawnień")

    q = select(AiUzycie).where(AiUzycie.parafia_id == current_user.parafia_id)
    if typ:
        q = q.where(AiUzycie.typ == typ)
    q = q.order_by(AiUzycie.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()
