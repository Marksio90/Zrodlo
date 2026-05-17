import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.dependencies import DB
from app.models.wspolnoty import CzlonekWspolnoty, Wspolnota
from app.schemas.wspolnoty import CzlonekCreate, CzlonekRead, WspolnotaCreate, WspolnotaRead

router = APIRouter(prefix="/wspolnoty", tags=["Wspólnoty"])


@router.post("", response_model=WspolnotaRead, status_code=status.HTTP_201_CREATED)
async def create_wspolnota(payload: WspolnotaCreate, db: DB):
    obj = Wspolnota(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return WspolnotaRead.model_validate({**obj.__dict__, "liczba_czlonkow": 0})


@router.get("", response_model=list[WspolnotaRead])
async def list_wspolnoty(
    db: DB,
    aktywna: bool | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    q = select(
        Wspolnota,
        func.count(CzlonekWspolnoty.id).label("liczba_czlonkow"),
    ).outerjoin(
        CzlonekWspolnoty,
        (CzlonekWspolnoty.wspolnota_id == Wspolnota.id) & CzlonekWspolnoty.aktywny,
    ).group_by(Wspolnota.id)
    if aktywna is not None:
        q = q.where(Wspolnota.aktywna == aktywna)
    q = q.order_by(Wspolnota.nazwa).limit(limit).offset(offset)
    rows = await db.execute(q)
    return [
        WspolnotaRead.model_validate({**w.__dict__, "liczba_czlonkow": count})
        for w, count in rows
    ]


@router.get("/{wspolnota_id}", response_model=WspolnotaRead)
async def get_wspolnota(wspolnota_id: uuid.UUID, db: DB):
    q = select(
        Wspolnota,
        func.count(CzlonekWspolnoty.id).label("liczba_czlonkow"),
    ).outerjoin(
        CzlonekWspolnoty,
        (CzlonekWspolnoty.wspolnota_id == Wspolnota.id) & CzlonekWspolnoty.aktywny,
    ).where(Wspolnota.id == wspolnota_id).group_by(Wspolnota.id)
    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Wspólnota nie znaleziona")
    w, count = row
    return WspolnotaRead.model_validate({**w.__dict__, "liczba_czlonkow": count})


@router.delete("/{wspolnota_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wspolnota(wspolnota_id: uuid.UUID, db: DB):
    obj = await db.get(Wspolnota, wspolnota_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Wspólnota nie znaleziona")
    await db.delete(obj)


@router.post("/{wspolnota_id}/czlonkowie", response_model=CzlonekRead, status_code=status.HTTP_201_CREATED)
async def add_czlonek(wspolnota_id: uuid.UUID, payload: CzlonekCreate, db: DB):
    if not await db.get(Wspolnota, wspolnota_id):
        raise HTTPException(status_code=404, detail="Wspólnota nie znaleziona")
    obj = CzlonekWspolnoty(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("/{wspolnota_id}/czlonkowie", response_model=list[CzlonekRead])
async def list_czlonkowie(
    wspolnota_id: uuid.UUID,
    db: DB,
    aktywny: bool | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    q = select(CzlonekWspolnoty).where(CzlonekWspolnoty.wspolnota_id == wspolnota_id)
    if aktywny is not None:
        q = q.where(CzlonekWspolnoty.aktywny == aktywny)
    q = q.order_by(CzlonekWspolnoty.nazwisko, CzlonekWspolnoty.imie).limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()
