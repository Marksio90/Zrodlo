import uuid
from datetime import datetime, timezone

from fastapi import Depends, APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DB
from app.models.audit import OperacjaAudit
from app.models.ogloszenia import Ogloszenie, StatusOgloszenia
from app.schemas.ogloszenia import OgloszenieCreate, OgloszenieRead, OgloszenieUpdate
from app.services import audit as audit_svc
from app.services.permissions import wymagaj_uprawnienia

router = APIRouter(prefix="/ogloszenia", tags=["Ogłoszenia"])


@router.post("", response_model=OgloszenieRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(wymagaj_uprawnienia("ogloszenie", "tworz"))])
async def create_ogloszenie(payload: OgloszenieCreate, db: DB, current_user: CurrentUser):
    obj = Ogloszenie(**payload.model_dump(), tworca_id=current_user.id)
    if not obj.parafia_id:
        obj.parafia_id = current_user.parafia_id
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="ogloszenia", rekord_id=obj.id,
        operacja=OperacjaAudit.UTWORZONO, uzytkownik_id=current_user.id,
        parafia_id=obj.parafia_id, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.get("", response_model=list[OgloszenieRead])
async def list_ogloszenia(
    db: DB, _: CurrentUser,
    status_filter: StatusOgloszenia | None = Query(None, alias="status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    q = select(Ogloszenie).where(Ogloszenie.deleted_at.is_(None))
    if status_filter:
        q = q.where(Ogloszenie.status == status_filter)
    q = q.order_by(Ogloszenie.created_at.desc()).limit(limit).offset(offset)
    return (await db.execute(q)).scalars().all()


@router.get("/{ogloszenie_id}", response_model=OgloszenieRead)
async def get_ogloszenie(ogloszenie_id: uuid.UUID, db: DB, _: CurrentUser):
    obj = await db.get(Ogloszenie, ogloszenie_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Ogłoszenie nie znalezione")
    return obj


@router.patch("/{ogloszenie_id}", response_model=OgloszenieRead,
              dependencies=[Depends(wymagaj_uprawnienia("ogloszenie", "edytuj"))])
async def update_ogloszenie(
    ogloszenie_id: uuid.UUID, payload: OgloszenieUpdate, db: DB, current_user: CurrentUser
):
    obj = await db.get(Ogloszenie, ogloszenie_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Ogłoszenie nie znalezione")
    stare = audit_svc.snapshot(obj)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="ogloszenia", rekord_id=obj.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO, uzytkownik_id=current_user.id,
        stare_wartosci=stare, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.post("/{ogloszenie_id}/zatwierdz", response_model=OgloszenieRead,
             dependencies=[Depends(wymagaj_uprawnienia("ogloszenie", "zatwierdz"))])
async def zatwierdz_ogloszenie(ogloszenie_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await db.get(Ogloszenie, ogloszenie_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Ogłoszenie nie znalezione")
    stare = audit_svc.snapshot(obj)
    obj.status = StatusOgloszenia.ZATWIERDZONY
    obj.zatwierdzone_przez_id = current_user.id
    obj.data_zatwierdzenia = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="ogloszenia", rekord_id=obj.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO, uzytkownik_id=current_user.id,
        stare_wartosci=stare, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.delete("/{ogloszenie_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(wymagaj_uprawnienia("ogloszenie", "usun"))])
async def soft_delete_ogloszenie(ogloszenie_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await db.get(Ogloszenie, ogloszenie_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Ogłoszenie nie znalezione")
    stare = audit_svc.snapshot(obj)
    obj.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    await audit_svc.zapisz(
        db, tabela="ogloszenia", rekord_id=obj.id,
        operacja=OperacjaAudit.USUNIETO, uzytkownik_id=current_user.id,
        stare_wartosci=stare,
    )
