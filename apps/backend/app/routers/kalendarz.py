import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.dependencies import DB
from app.models.kalendarz import Wydarzenie
from app.schemas.kalendarz import WydarzenieCreate, WydarzenieRead, WydarzenieUpdate

router = APIRouter(prefix="/kalendarz", tags=["Kalendarz"])


@router.post("", response_model=WydarzenieRead, status_code=status.HTTP_201_CREATED)
async def create_wydarzenie(payload: WydarzenieCreate, db: DB):
    obj = Wydarzenie(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("", response_model=list[WydarzenieRead])
async def list_wydarzenia(
    db: DB,
    od: datetime | None = Query(None),
    do: datetime | None = Query(None),
    wspolnota_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    q = select(Wydarzenie)
    if od:
        q = q.where(Wydarzenie.data_od >= od)
    if do:
        q = q.where(Wydarzenie.data_od <= do)
    if wspolnota_id:
        q = q.where(Wydarzenie.wspolnota_id == wspolnota_id)
    q = q.order_by(Wydarzenie.data_od).limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{wydarzenie_id}", response_model=WydarzenieRead)
async def get_wydarzenie(wydarzenie_id: uuid.UUID, db: DB):
    obj = await db.get(Wydarzenie, wydarzenie_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Wydarzenie nie znalezione")
    return obj


@router.patch("/{wydarzenie_id}", response_model=WydarzenieRead)
async def update_wydarzenie(wydarzenie_id: uuid.UUID, payload: WydarzenieUpdate, db: DB):
    obj = await db.get(Wydarzenie, wydarzenie_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Wydarzenie nie znalezione")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.delete("/{wydarzenie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wydarzenie(wydarzenie_id: uuid.UUID, db: DB):
    obj = await db.get(Wydarzenie, wydarzenie_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Wydarzenie nie znalezione")
    await db.delete(obj)
