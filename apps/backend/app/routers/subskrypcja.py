"""Router subskrypcji – zarządzanie planami parafii."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DB
from app.models.subskrypcja import Plan, Subskrypcja
from app.models.uzytkownicy import RolaUzytkownika
from app.schemas.subskrypcja import (
    PlanInfo,
    SubskrypcjaCreate,
    SubskrypcjaRead,
    SubskrypcjaStatus,
    TrialRequest,
    plan_info,
)
from app.services.subskrypcja import PLAN_LIMITY, limity_dla_planu, pobierz_aktywna_subskrypcje

router = APIRouter(prefix="/subskrypcja", tags=["Subskrypcja"])

_TRIAL_DNI = 30
_ROLE_ZARZADZANIA = {RolaUzytkownika.ADMIN, RolaUzytkownika.PROBOSZCZ}


# ── Publiczne ──────────────────────────────────────────────────────────────────

@router.get("/plany", response_model=list[PlanInfo], summary="Lista dostępnych planów")
async def lista_planow():
    """Zwraca wszystkie dostępne plany z cenami i limitami. Endpoint publiczny."""
    return [plan_info(p) for p in Plan]


@router.get("/plany/{plan}", response_model=PlanInfo, summary="Szczegóły planu")
async def get_plan(plan: Plan):
    if plan not in PLAN_LIMITY:
        raise HTTPException(status_code=404, detail="Nieznany plan")
    return plan_info(plan)


# ── Zalogowany użytkownik ──────────────────────────────────────────────────────

@router.get("/status", response_model=SubskrypcjaStatus, summary="Status subskrypcji parafii")
async def status_subskrypcji(current_user: CurrentUser, db: DB):
    """Zwraca aktywny plan i limity dla parafii zalogowanego użytkownika."""
    if not current_user.parafia_id:
        raise HTTPException(status_code=400, detail="Konto nie jest przypisane do parafii")

    sub = await pobierz_aktywna_subskrypcje(db, current_user.parafia_id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Brak aktywnej subskrypcji. Aktywuj okres próbny lub wybierz plan.",
        )

    now = datetime.now(timezone.utc)
    dni_do_konca: int | None = None
    if sub.data_zakonczenia:
        delta = sub.data_zakonczenia - now
        dni_do_konca = max(0, delta.days)

    limity = limity_dla_planu(sub.plan)
    return SubskrypcjaStatus(
        parafia_id=sub.parafia_id,
        plan=sub.plan,
        aktywna=sub.aktywna,
        okres_probny=sub.okres_probny,
        data_zakonczenia=sub.data_zakonczenia,
        dni_do_konca=dni_do_konca,
        limity=plan_info(sub.plan),
        wymaga_odnowienia=dni_do_konca is not None and dni_do_konca <= 7,
    )


@router.post(
    "/trial",
    response_model=SubskrypcjaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Aktywuj 30-dniowy okres próbny",
)
async def aktywuj_trial(
    _: TrialRequest,
    current_user: CurrentUser,
    db: DB,
):
    """Jednorazowa aktywacja 30-dniowego okresu próbnego przez proboszcza.

    Każda parafia może skorzystać z triala tylko raz.
    """
    if current_user.rola not in {RolaUzytkownika.PROBOSZCZ, RolaUzytkownika.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tylko proboszcz może aktywować okres próbny",
        )
    if not current_user.parafia_id:
        raise HTTPException(status_code=400, detail="Konto nie jest przypisane do parafii")

    # Sprawdź czy parafia nie miała już triala
    result = await db.execute(
        select(Subskrypcja).where(
            Subskrypcja.parafia_id == current_user.parafia_id,
            Subskrypcja.okres_probny.is_(True),
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Parafia wykorzystała już bezpłatny okres próbny",
        )

    # Sprawdź czy nie ma już aktywnej subskrypcji
    istniejaca = await pobierz_aktywna_subskrypcje(db, current_user.parafia_id)
    if istniejaca is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Parafia ma już aktywną subskrypcję",
        )

    now = datetime.now(timezone.utc)
    limity = limity_dla_planu(Plan.TRIAL)

    sub = Subskrypcja(
        parafia_id=current_user.parafia_id,
        plan=Plan.TRIAL,
        aktywna=True,
        okres_probny=True,
        data_rozpoczecia=now,
        data_zakonczenia=now + timedelta(days=_TRIAL_DNI),
        aktywowana_przez=current_user.id,
        limit_uzytkownikow=limity.max_uzytkownikow,
        limit_intencji_miesiac=limity.max_intencji_miesiac,
        limit_dokumentow=limity.max_dokumentow,
        limit_ai_zapytan_miesiac=limity.max_ai_zapytan_miesiac,
    )
    db.add(sub)
    await db.flush()
    await db.refresh(sub)
    return sub


# ── Admin platformy ────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=SubskrypcjaRead,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Utwórz subskrypcję dla parafii",
)
async def utworz_subskrypcje(
    payload: SubskrypcjaCreate,
    current_user: CurrentUser,
    db: DB,
):
    """Tylko administrator platformy. Służy do ręcznego przypisania planu po opłaceniu."""
    if current_user.rola != RolaUzytkownika.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tylko administrator platformy może zarządzać subskrypcjami",
        )

    # Dezaktywuj poprzednią aktywną subskrypcję
    poprzednia = await pobierz_aktywna_subskrypcje(db, payload.parafia_id)
    if poprzednia:
        poprzednia.aktywna = False

    now = datetime.now(timezone.utc)
    limity = limity_dla_planu(payload.plan)

    sub = Subskrypcja(
        parafia_id=payload.parafia_id,
        plan=payload.plan,
        aktywna=True,
        okres_probny=payload.okres_probny,
        data_rozpoczecia=now,
        data_zakonczenia=payload.data_zakonczenia,
        aktywowana_przez=current_user.id,
        limit_uzytkownikow=limity.max_uzytkownikow,
        limit_intencji_miesiac=limity.max_intencji_miesiac,
        limit_dokumentow=limity.max_dokumentow,
        limit_ai_zapytan_miesiac=limity.max_ai_zapytan_miesiac,
    )
    db.add(sub)
    await db.flush()
    await db.refresh(sub)
    return sub


@router.get(
    "/lista",
    response_model=list[SubskrypcjaRead],
    summary="[Admin] Lista wszystkich subskrypcji",
)
async def lista_subskrypcji(current_user: CurrentUser, db: DB):
    if current_user.rola != RolaUzytkownika.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Brak uprawnień")
    result = await db.execute(
        select(Subskrypcja).order_by(Subskrypcja.created_at.desc())
    )
    return result.scalars().all()
