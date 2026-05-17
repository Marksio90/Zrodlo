import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DB
from app.models.audit import OperacjaAudit
from app.models.uzytkownicy import Parafianin, Proboszcz, RolaUzytkownika, Uzytkownik, Wikariusz
from app.schemas.uzytkownicy import (
    ParafianinCreate, ParafianinRead, ParafianinUpdate,
    ProboszczCreate, ProboszczRead,
    UzytkownikRead, UzytkownikUpdate,
    WikariuszCreate, WikariuszRead,
)
from app.services import audit as audit_svc
from app.services.permissions import wymagaj_uprawnienia

router = APIRouter(prefix="/uzytkownicy", tags=["Użytkownicy"])


# ── Użytkownicy ───────────────────────────────────────────

@router.get("", response_model=list[UzytkownikRead],
            dependencies=[wymagaj_uprawnienia("uzytkownik", "czytaj")])
async def list_uzytkownicy(
    db: DB, _: CurrentUser,
    rola: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    q = select(Uzytkownik).where(Uzytkownik.deleted_at.is_(None))
    if rola:
        q = q.where(Uzytkownik.rola == rola)
    q = q.order_by(Uzytkownik.nazwisko, Uzytkownik.imie).limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{user_id}", response_model=UzytkownikRead,
            dependencies=[wymagaj_uprawnienia("uzytkownik", "czytaj")])
async def get_uzytkownik(user_id: uuid.UUID, db: DB, _: CurrentUser):
    obj = await db.get(Uzytkownik, user_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
    return obj


@router.patch("/{user_id}", response_model=UzytkownikRead,
              dependencies=[wymagaj_uprawnienia("uzytkownik", "edytuj")])
async def update_uzytkownik(
    user_id: uuid.UUID, payload: UzytkownikUpdate, db: DB, current_user: CurrentUser
):
    obj = await db.get(Uzytkownik, user_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
    stare = audit_svc.snapshot(obj)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="uzytkownicy", rekord_id=obj.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO, uzytkownik_id=current_user.id,
        parafia_id=current_user.parafia_id,
        stare_wartosci=stare, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[wymagaj_uprawnienia("uzytkownik", "usun")])
async def soft_delete_uzytkownik(user_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await db.get(Uzytkownik, user_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
    stare = audit_svc.snapshot(obj)
    obj.deleted_at = datetime.now(timezone.utc)
    obj.aktywny = False
    await db.flush()
    await audit_svc.zapisz(
        db, tabela="uzytkownicy", rekord_id=obj.id,
        operacja=OperacjaAudit.USUNIETO, uzytkownik_id=current_user.id,
        stare_wartosci=stare,
    )


# ── Proboszczowie ────────────────────────────────────────

@router.post("/proboszczowie", response_model=ProboszczRead, status_code=status.HTTP_201_CREATED,
             dependencies=[wymagaj_uprawnienia("uzytkownik", "tworz")])
async def create_proboszcz(payload: ProboszczCreate, db: DB, current_user: CurrentUser):
    uzytkownik = await db.get(Uzytkownik, payload.uzytkownik_id)
    if not uzytkownik:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
    uzytkownik.rola = RolaUzytkownika.PROBOSZCZ
    obj = Proboszcz(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="proboszczowie", rekord_id=obj.id,
        operacja=OperacjaAudit.UTWORZONO, uzytkownik_id=current_user.id,
        nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.post("/wikariusze", response_model=WikariuszRead, status_code=status.HTTP_201_CREATED,
             dependencies=[wymagaj_uprawnienia("uzytkownik", "tworz")])
async def create_wikariusz(payload: WikariuszCreate, db: DB, current_user: CurrentUser):
    uzytkownik = await db.get(Uzytkownik, payload.uzytkownik_id)
    if not uzytkownik:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
    uzytkownik.rola = RolaUzytkownika.WIKARIUSZ
    obj = Wikariusz(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="wikariusze", rekord_id=obj.id,
        operacja=OperacjaAudit.UTWORZONO, uzytkownik_id=current_user.id,
        nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


# ── Parafianie ────────────────────────────────────────────

@router.get("/parafianie", response_model=list[ParafianinRead],
            dependencies=[wymagaj_uprawnienia("parafianin", "czytaj")])
async def list_parafianie(
    db: DB, current_user: CurrentUser,
    limit: int = Query(50, le=500),
    offset: int = Query(0),
):
    q = (
        select(Parafianin)
        .where(Parafianin.deleted_at.is_(None))
        .order_by(Parafianin.nazwisko, Parafianin.imie)
        .limit(limit).offset(offset)
    )
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/parafianie", response_model=ParafianinRead, status_code=status.HTTP_201_CREATED,
             dependencies=[wymagaj_uprawnienia("parafianin", "tworz")])
async def create_parafianin(payload: ParafianinCreate, db: DB, current_user: CurrentUser):
    obj = Parafianin(**payload.model_dump())
    if not obj.parafia_id:
        obj.parafia_id = current_user.parafia_id
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="parafianie", rekord_id=obj.id,
        operacja=OperacjaAudit.UTWORZONO, uzytkownik_id=current_user.id,
        parafia_id=obj.parafia_id, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.get("/parafianie/{parafianin_id}", response_model=ParafianinRead,
            dependencies=[wymagaj_uprawnienia("parafianin", "czytaj")])
async def get_parafianin(parafianin_id: uuid.UUID, db: DB, _: CurrentUser):
    obj = await db.get(Parafianin, parafianin_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Parafianin nie znaleziony")
    return obj


@router.patch("/parafianie/{parafianin_id}", response_model=ParafianinRead,
              dependencies=[wymagaj_uprawnienia("parafianin", "edytuj")])
async def update_parafianin(
    parafianin_id: uuid.UUID, payload: ParafianinUpdate, db: DB, current_user: CurrentUser
):
    obj = await db.get(Parafianin, parafianin_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Parafianin nie znaleziony")
    stare = audit_svc.snapshot(obj)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="parafianie", rekord_id=obj.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO, uzytkownik_id=current_user.id,
        stare_wartosci=stare, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.delete("/parafianie/{parafianin_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[wymagaj_uprawnienia("parafianin", "usun")])
async def soft_delete_parafianin(parafianin_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await db.get(Parafianin, parafianin_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Parafianin nie znaleziony")
    stare = audit_svc.snapshot(obj)
    obj.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    await audit_svc.zapisz(
        db, tabela="parafianie", rekord_id=obj.id,
        operacja=OperacjaAudit.USUNIETO, uzytkownik_id=current_user.id,
        stare_wartosci=stare,
    )
