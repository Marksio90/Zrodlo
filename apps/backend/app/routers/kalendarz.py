import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DB
from app.models.audit import OperacjaAudit
from app.models.kalendarz import Wydarzenie
from app.schemas.kalendarz import WydarzenieCreate, WydarzenieRead, WydarzenieUpdate
from app.services import audit as audit_svc
from app.services.permissions import wymagaj_uprawnienia

router = APIRouter(prefix="/kalendarz", tags=["Kalendarz"])


def _or_404_tenant(obj, current_user, detail: str):
    if not obj:
        raise HTTPException(status_code=404, detail=detail)
    if obj.parafia_id and current_user.parafia_id and obj.parafia_id != current_user.parafia_id:
        raise HTTPException(status_code=404, detail=detail)


@router.post("", response_model=WydarzenieRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(wymagaj_uprawnienia("wydarzenie", "tworz"))])
async def create_wydarzenie(payload: WydarzenieCreate, db: DB, current_user: CurrentUser):
    obj = Wydarzenie(**payload.model_dump())
    obj.parafia_id = current_user.parafia_id
    obj.tworca_id = current_user.id
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db,
        tabela="wydarzenia",
        rekord_id=obj.id,
        operacja=OperacjaAudit.UTWORZONO,
        uzytkownik_id=current_user.id,
        parafia_id=current_user.parafia_id,
        nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.get("", response_model=list[WydarzenieRead])
async def list_wydarzenia(
    db: DB,
    current_user: CurrentUser,
    od: datetime | None = Query(None),
    do: datetime | None = Query(None),
    wspolnota_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    q = select(Wydarzenie).where(Wydarzenie.parafia_id == current_user.parafia_id)
    if od:
        q = q.where(Wydarzenie.data_od >= od)
    if do:
        q = q.where(Wydarzenie.data_od <= do)
    if wspolnota_id:
        q = q.where(Wydarzenie.wspolnota_id == wspolnota_id)
    q = q.order_by(Wydarzenie.data_od).limit(limit).offset(offset)
    return (await db.execute(q)).scalars().all()


@router.get("/{wydarzenie_id}", response_model=WydarzenieRead)
async def get_wydarzenie(wydarzenie_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await db.get(Wydarzenie, wydarzenie_id)
    _or_404_tenant(obj, current_user, "Wydarzenie nie znalezione")
    return obj


@router.patch("/{wydarzenie_id}", response_model=WydarzenieRead,
              dependencies=[Depends(wymagaj_uprawnienia("wydarzenie", "edytuj"))])
async def update_wydarzenie(wydarzenie_id: uuid.UUID, payload: WydarzenieUpdate, db: DB, current_user: CurrentUser):
    obj = await db.get(Wydarzenie, wydarzenie_id)
    _or_404_tenant(obj, current_user, "Wydarzenie nie znalezione")
    stare = audit_svc.snapshot(obj)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db,
        tabela="wydarzenia",
        rekord_id=obj.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO,
        uzytkownik_id=current_user.id,
        parafia_id=current_user.parafia_id,
        stare_wartosci=stare,
        nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.delete("/{wydarzenie_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(wymagaj_uprawnienia("wydarzenie", "usun"))])
async def delete_wydarzenie(wydarzenie_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await db.get(Wydarzenie, wydarzenie_id)
    _or_404_tenant(obj, current_user, "Wydarzenie nie znalezione")
    await audit_svc.zapisz(
        db,
        tabela="wydarzenia",
        rekord_id=obj.id,
        operacja=OperacjaAudit.USUNIETO,
        uzytkownik_id=current_user.id,
        parafia_id=current_user.parafia_id,
    )
    await db.delete(obj)
