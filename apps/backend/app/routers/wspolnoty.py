import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DB
from app.models.audit import OperacjaAudit
from app.models.wspolnoty import CzlonekWspolnoty, Wspolnota
from app.schemas.wspolnoty import CzlonekCreate, CzlonekRead, WspolnotaCreate, WspolnotaRead
from app.services import audit as audit_svc
from app.services.permissions import wymagaj_uprawnienia

router = APIRouter(prefix="/wspolnoty", tags=["Wspólnoty"])


async def _get_wspolnota_or_404(db: DB, wspolnota_id: uuid.UUID, current_user) -> Wspolnota:
    obj = await db.get(Wspolnota, wspolnota_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Wspólnota nie znaleziona")
    if obj.parafia_id and current_user.parafia_id and obj.parafia_id != current_user.parafia_id:
        raise HTTPException(status_code=404, detail="Wspólnota nie znaleziona")
    return obj


@router.post("", response_model=WspolnotaRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(wymagaj_uprawnienia("wspolnota", "tworz"))])
async def create_wspolnota(payload: WspolnotaCreate, db: DB, current_user: CurrentUser):
    obj = Wspolnota(**payload.model_dump())
    obj.parafia_id = current_user.parafia_id
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db,
        tabela="wspolnoty",
        rekord_id=obj.id,
        operacja=OperacjaAudit.UTWORZONO,
        uzytkownik_id=current_user.id,
        parafia_id=current_user.parafia_id,
        nowe_wartosci=audit_svc.snapshot(obj),
    )
    return WspolnotaRead.model_validate({**obj.__dict__, "liczba_czlonkow": 0})


@router.get("", response_model=list[WspolnotaRead])
async def list_wspolnoty(
    db: DB,
    current_user: CurrentUser,
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
    ).where(Wspolnota.parafia_id == current_user.parafia_id).group_by(Wspolnota.id)
    if aktywna is not None:
        q = q.where(Wspolnota.aktywna == aktywna)
    q = q.order_by(Wspolnota.nazwa).limit(limit).offset(offset)
    rows = await db.execute(q)
    return [
        WspolnotaRead.model_validate({**w.__dict__, "liczba_czlonkow": count})
        for w, count in rows
    ]


@router.get("/{wspolnota_id}", response_model=WspolnotaRead)
async def get_wspolnota(wspolnota_id: uuid.UUID, db: DB, current_user: CurrentUser):
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
    if w.parafia_id and current_user.parafia_id and w.parafia_id != current_user.parafia_id:
        raise HTTPException(status_code=404, detail="Wspólnota nie znaleziona")
    return WspolnotaRead.model_validate({**w.__dict__, "liczba_czlonkow": count})


@router.delete("/{wspolnota_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(wymagaj_uprawnienia("wspolnota", "usun"))])
async def delete_wspolnota(wspolnota_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await _get_wspolnota_or_404(db, wspolnota_id, current_user)
    await audit_svc.zapisz(
        db,
        tabela="wspolnoty",
        rekord_id=obj.id,
        operacja=OperacjaAudit.USUNIETO,
        uzytkownik_id=current_user.id,
        parafia_id=current_user.parafia_id,
    )
    await db.delete(obj)


@router.post("/{wspolnota_id}/czlonkowie", response_model=CzlonekRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(wymagaj_uprawnienia("wspolnota", "tworz"))])
async def add_czlonek(wspolnota_id: uuid.UUID, payload: CzlonekCreate, db: DB, current_user: CurrentUser):
    await _get_wspolnota_or_404(db, wspolnota_id, current_user)
    obj = CzlonekWspolnoty(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db,
        tabela="czlonkowie_wspolnot",
        rekord_id=obj.id,
        operacja=OperacjaAudit.UTWORZONO,
        uzytkownik_id=current_user.id,
        parafia_id=current_user.parafia_id,
        nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.get("/{wspolnota_id}/czlonkowie", response_model=list[CzlonekRead])
async def list_czlonkowie(
    wspolnota_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    aktywny: bool | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    await _get_wspolnota_or_404(db, wspolnota_id, current_user)
    q = select(CzlonekWspolnoty).where(CzlonekWspolnoty.wspolnota_id == wspolnota_id)
    if aktywny is not None:
        q = q.where(CzlonekWspolnoty.aktywny == aktywny)
    q = q.order_by(CzlonekWspolnoty.nazwisko, CzlonekWspolnoty.imie).limit(limit).offset(offset)
    return (await db.execute(q)).scalars().all()
