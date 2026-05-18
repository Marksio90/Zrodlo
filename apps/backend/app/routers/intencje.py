import uuid
from datetime import date, datetime, timezone

from fastapi import Depends, APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DB
from app.models.audit import OperacjaAudit
from app.models.intencje import Intencja, Liturgia
from app.schemas.intencje import (
    IntencjaCreate, IntencjaRead, IntencjaUpdate,
    LiturgiaCreate, LiturgiaRead,
)
from app.services import audit as audit_svc
from app.services.permissions import wymagaj_uprawnienia

router = APIRouter(prefix="/intencje", tags=["Intencje"])


# ── Liturgie ─────────────────────────────────────────────

@router.post("/liturgie", response_model=LiturgiaRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(wymagaj_uprawnienia("liturgia", "tworz"))])
async def create_liturgia(payload: LiturgiaCreate, db: DB, current_user: CurrentUser):
    obj = Liturgia(**payload.model_dump(), tworca_id=current_user.id)
    obj.parafia_id = current_user.parafia_id
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="liturgie", rekord_id=obj.id,
        operacja=OperacjaAudit.UTWORZONO, uzytkownik_id=current_user.id,
        parafia_id=obj.parafia_id, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.get("/liturgie", response_model=list[LiturgiaRead])
async def list_liturgie(
    db: DB, _: CurrentUser,
    od: date | None = Query(None),
    do: date | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    q = select(Liturgia).where(Liturgia.deleted_at.is_(None))
    if od:
        q = q.where(Liturgia.data >= od)
    if do:
        q = q.where(Liturgia.data <= do)
    q = q.order_by(Liturgia.data, Liturgia.godzina).limit(limit).offset(offset)
    return (await db.execute(q)).scalars().all()


@router.get("/liturgie/{liturgia_id}", response_model=LiturgiaRead)
async def get_liturgia(liturgia_id: uuid.UUID, db: DB, _: CurrentUser):
    obj = await db.get(Liturgia, liturgia_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Liturgia nie znaleziona")
    return obj


# ── Intencje ─────────────────────────────────────────────

@router.post("", response_model=IntencjaRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(wymagaj_uprawnienia("intencja", "tworz"))])
async def create_intencja(payload: IntencjaCreate, db: DB, current_user: CurrentUser):
    if payload.liturgia_id:
        liturgia = await db.get(Liturgia, payload.liturgia_id)
        if not liturgia or liturgia.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Liturgia nie znaleziona")
    obj = Intencja(**payload.model_dump(), tworca_id=current_user.id)
    obj.parafia_id = current_user.parafia_id
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="intencje", rekord_id=obj.id,
        operacja=OperacjaAudit.UTWORZONO, uzytkownik_id=current_user.id,
        parafia_id=obj.parafia_id, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.get("", response_model=list[IntencjaRead])
async def list_intencje(
    db: DB, _: CurrentUser,
    liturgia_id: uuid.UUID | None = Query(None),
    potwierdzona: bool | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    q = select(Intencja).where(Intencja.deleted_at.is_(None))
    if liturgia_id:
        q = q.where(Intencja.liturgia_id == liturgia_id)
    if potwierdzona is not None:
        q = q.where(Intencja.potwierdzona == potwierdzona)
    q = q.order_by(Intencja.created_at.desc()).limit(limit).offset(offset)
    return (await db.execute(q)).scalars().all()


@router.get("/{intencja_id}", response_model=IntencjaRead)
async def get_intencja(intencja_id: uuid.UUID, db: DB, _: CurrentUser):
    obj = await db.get(Intencja, intencja_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Intencja nie znaleziona")
    return obj


@router.patch("/{intencja_id}", response_model=IntencjaRead,
              dependencies=[Depends(wymagaj_uprawnienia("intencja", "edytuj"))])
async def update_intencja(intencja_id: uuid.UUID, payload: IntencjaUpdate, db: DB, current_user: CurrentUser):
    obj = await db.get(Intencja, intencja_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Intencja nie znaleziona")
    stare = audit_svc.snapshot(obj)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="intencje", rekord_id=obj.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO, uzytkownik_id=current_user.id,
        stare_wartosci=stare, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.post("/{intencja_id}/potwierdz", response_model=IntencjaRead,
             dependencies=[Depends(wymagaj_uprawnienia("intencja", "zatwierdz"))])
async def potwierdz_intencje(intencja_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await db.get(Intencja, intencja_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Intencja nie znaleziona")
    stare = audit_svc.snapshot(obj)
    obj.potwierdzona = True
    obj.potwierdzone_przez_id = current_user.id
    obj.data_potwierdzenia = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="intencje", rekord_id=obj.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO, uzytkownik_id=current_user.id,
        stare_wartosci=stare, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.delete("/{intencja_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(wymagaj_uprawnienia("intencja", "usun"))])
async def soft_delete_intencja(intencja_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await db.get(Intencja, intencja_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Intencja nie znaleziona")
    stare = audit_svc.snapshot(obj)
    obj.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    await audit_svc.zapisz(
        db, tabela="intencje", rekord_id=obj.id,
        operacja=OperacjaAudit.USUNIETO, uzytkownik_id=current_user.id,
        stare_wartosci=stare,
    )
