import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func

from app.dependencies import DB
from app.models.intencje import Intencja, Liturgia
from app.schemas.intencje import (
    IntencjaCreate, IntencjaRead, IntencjaUpdate,
    LiturgiaCreate, LiturgiaRead,
)

router = APIRouter(prefix="/intencje", tags=["Intencje"])


# --- Liturgie ---

@router.post("/liturgie", response_model=LiturgiaRead, status_code=status.HTTP_201_CREATED)
async def create_liturgia(payload: LiturgiaCreate, db: DB):
    obj = Liturgia(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("/liturgie", response_model=list[LiturgiaRead])
async def list_liturgie(
    db: DB,
    od: date | None = Query(None),
    do: date | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    q = select(Liturgia)
    if od:
        q = q.where(Liturgia.data >= od)
    if do:
        q = q.where(Liturgia.data <= do)
    q = q.order_by(Liturgia.data, Liturgia.godzina).limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/liturgie/{liturgia_id}", response_model=LiturgiaRead)
async def get_liturgia(liturgia_id: uuid.UUID, db: DB):
    obj = await db.get(Liturgia, liturgia_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Liturgia nie znaleziona")
    return obj


# --- Intencje ---

@router.post("", response_model=IntencjaRead, status_code=status.HTTP_201_CREATED)
async def create_intencja(payload: IntencjaCreate, db: DB):
    if payload.liturgia_id:
        liturgia = await db.get(Liturgia, payload.liturgia_id)
        if not liturgia:
            raise HTTPException(status_code=404, detail="Liturgia nie znaleziona")
    obj = Intencja(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("", response_model=list[IntencjaRead])
async def list_intencje(
    db: DB,
    liturgia_id: uuid.UUID | None = Query(None),
    potwierdzona: bool | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    q = select(Intencja)
    if liturgia_id:
        q = q.where(Intencja.liturgia_id == liturgia_id)
    if potwierdzona is not None:
        q = q.where(Intencja.potwierdzona == potwierdzona)
    q = q.order_by(Intencja.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{intencja_id}", response_model=IntencjaRead)
async def get_intencja(intencja_id: uuid.UUID, db: DB):
    obj = await db.get(Intencja, intencja_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Intencja nie znaleziona")
    return obj


@router.patch("/{intencja_id}", response_model=IntencjaRead)
async def update_intencja(intencja_id: uuid.UUID, payload: IntencjaUpdate, db: DB):
    obj = await db.get(Intencja, intencja_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Intencja nie znaleziona")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.delete("/{intencja_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_intencja(intencja_id: uuid.UUID, db: DB):
    obj = await db.get(Intencja, intencja_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Intencja nie znaleziona")
    await db.delete(obj)
