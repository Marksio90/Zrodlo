import uuid

from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DB
from app.models.audit import OperacjaAudit
from app.models.parafia import Parafia
from app.models.uzytkownicy import RolaUzytkownika
from app.schemas.parafia import ParafiaCreate, ParafiaRead, ParafiaUpdate
from app.services import audit as audit_svc
from app.services.permissions import wymagaj_uprawnienia

router = APIRouter(prefix="/parafia", tags=["Parafia"])


@router.post("", response_model=ParafiaRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(wymagaj_uprawnienia("parafia", "tworz"))])
async def create_parafia(payload: ParafiaCreate, db: DB, current_user: CurrentUser):
    obj = Parafia(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="parafie", rekord_id=obj.id,
        operacja=OperacjaAudit.UTWORZONO, uzytkownik_id=current_user.id,
        nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.get("", response_model=list[ParafiaRead])
async def list_parafie(db: DB, _: CurrentUser):
    result = await db.execute(select(Parafia).where(Parafia.aktywna.is_(True)).order_by(Parafia.nazwa))
    return result.scalars().all()


@router.get("/{parafia_id}", response_model=ParafiaRead)
async def get_parafia(parafia_id: uuid.UUID, db: DB, _: CurrentUser):
    obj = await db.get(Parafia, parafia_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Parafia nie znaleziona")
    return obj


@router.patch("/{parafia_id}", response_model=ParafiaRead,
              dependencies=[Depends(wymagaj_uprawnienia("parafia", "edytuj"))])
async def update_parafia(parafia_id: uuid.UUID, payload: ParafiaUpdate, db: DB, current_user: CurrentUser):
    obj = await db.get(Parafia, parafia_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Parafia nie znaleziona")
    stare = audit_svc.snapshot(obj)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="parafie", rekord_id=obj.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO, uzytkownik_id=current_user.id,
        stare_wartosci=stare, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj
