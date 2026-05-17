import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DB
from app.models.audit import OperacjaAudit
from app.models.grupy import CzlonekGrupy, GrupaParafialna
from app.schemas.grupy import (
    CzlonekGrupyCreate, CzlonekGrupyRead,
    GrupaParafialnaCreate, GrupaParafialnaRead, GrupaParafialnaUpdate,
)
from app.services import audit as audit_svc
from app.services.permissions import wymagaj_uprawnienia

router = APIRouter(prefix="/grupy", tags=["Grupy Parafialne"])


@router.post("", response_model=GrupaParafialnaRead, status_code=status.HTTP_201_CREATED,
             dependencies=[wymagaj_uprawnienia("grupa", "tworz")])
async def create_grupa(payload: GrupaParafialnaCreate, db: DB, current_user: CurrentUser):
    obj = GrupaParafialna(**payload.model_dump())
    if not obj.parafia_id:
        obj.parafia_id = current_user.parafia_id
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="grupy_parafialne", rekord_id=obj.id,
        operacja=OperacjaAudit.UTWORZONO, uzytkownik_id=current_user.id,
        parafia_id=obj.parafia_id, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return GrupaParafialnaRead.model_validate({**obj.__dict__, "liczba_czlonkow": 0})


@router.get("", response_model=list[GrupaParafialnaRead])
async def list_grupy(
    db: DB, _: CurrentUser,
    aktywna: bool | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    q = (
        select(GrupaParafialna, func.count(CzlonekGrupy.id).label("liczba_czlonkow"))
        .outerjoin(
            CzlonekGrupy,
            (CzlonekGrupy.grupa_id == GrupaParafialna.id) & CzlonekGrupy.aktywny,
        )
        .where(GrupaParafialna.deleted_at.is_(None))
        .group_by(GrupaParafialna.id)
    )
    if aktywna is not None:
        q = q.where(GrupaParafialna.aktywna == aktywna)
    q = q.order_by(GrupaParafialna.nazwa).limit(limit).offset(offset)
    rows = await db.execute(q)
    return [GrupaParafialnaRead.model_validate({**g.__dict__, "liczba_czlonkow": cnt}) for g, cnt in rows]


@router.get("/{grupa_id}", response_model=GrupaParafialnaRead)
async def get_grupa(grupa_id: uuid.UUID, db: DB, _: CurrentUser):
    q = (
        select(GrupaParafialna, func.count(CzlonekGrupy.id).label("liczba_czlonkow"))
        .outerjoin(CzlonekGrupy, (CzlonekGrupy.grupa_id == GrupaParafialna.id) & CzlonekGrupy.aktywny)
        .where(GrupaParafialna.id == grupa_id, GrupaParafialna.deleted_at.is_(None))
        .group_by(GrupaParafialna.id)
    )
    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Grupa nie znaleziona")
    g, cnt = row
    return GrupaParafialnaRead.model_validate({**g.__dict__, "liczba_czlonkow": cnt})


@router.patch("/{grupa_id}", response_model=GrupaParafialnaRead,
              dependencies=[wymagaj_uprawnienia("grupa", "edytuj")])
async def update_grupa(
    grupa_id: uuid.UUID, payload: GrupaParafialnaUpdate, db: DB, current_user: CurrentUser
):
    obj = await db.get(GrupaParafialna, grupa_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Grupa nie znaleziona")
    stare = audit_svc.snapshot(obj)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="grupy_parafialne", rekord_id=obj.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO, uzytkownik_id=current_user.id,
        stare_wartosci=stare, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return GrupaParafialnaRead.model_validate({**obj.__dict__, "liczba_czlonkow": 0})


@router.delete("/{grupa_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[wymagaj_uprawnienia("grupa", "usun")])
async def soft_delete_grupa(grupa_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await db.get(GrupaParafialna, grupa_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Grupa nie znaleziona")
    stare = audit_svc.snapshot(obj)
    obj.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    await audit_svc.zapisz(
        db, tabela="grupy_parafialne", rekord_id=obj.id,
        operacja=OperacjaAudit.USUNIETO, uzytkownik_id=current_user.id,
        stare_wartosci=stare,
    )


# ── Członkowie grupy ─────────────────────────────────────

@router.post("/{grupa_id}/czlonkowie", response_model=CzlonekGrupyRead,
             status_code=status.HTTP_201_CREATED,
             dependencies=[wymagaj_uprawnienia("grupa", "edytuj")])
async def add_czlonek(
    grupa_id: uuid.UUID, payload: CzlonekGrupyCreate, db: DB, current_user: CurrentUser
):
    if not await db.get(GrupaParafialna, grupa_id):
        raise HTTPException(status_code=404, detail="Grupa nie znaleziona")
    obj = CzlonekGrupy(grupa_id=grupa_id, **payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("/{grupa_id}/czlonkowie", response_model=list[CzlonekGrupyRead])
async def list_czlonkowie(
    grupa_id: uuid.UUID, db: DB, _: CurrentUser,
    aktywny: bool | None = Query(None),
    limit: int = Query(100, le=500),
):
    q = select(CzlonekGrupy).where(CzlonekGrupy.grupa_id == grupa_id)
    if aktywny is not None:
        q = q.where(CzlonekGrupy.aktywny == aktywny)
    q = q.limit(limit)
    return (await db.execute(q)).scalars().all()


@router.delete("/{grupa_id}/czlonkowie/{czlonek_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[wymagaj_uprawnienia("grupa", "edytuj")])
async def remove_czlonek(
    grupa_id: uuid.UUID, czlonek_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    obj = await db.get(CzlonekGrupy, czlonek_id)
    if not obj or obj.grupa_id != grupa_id:
        raise HTTPException(status_code=404, detail="Członek nie znaleziony")
    obj.aktywny = False
    await db.flush()
