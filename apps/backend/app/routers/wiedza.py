import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_, select

from app.dependencies import CurrentUser, DB
from app.models.audit import OperacjaAudit
from app.models.uzytkownicy import RolaUzytkownika
from app.models.wiedza import NotatkaWiedzy
from app.schemas.wiedza import NotatkaWiedzyCreate, NotatkaWiedzyRead, NotatkaWiedzyUpdate
from app.services import audit as audit_svc
from app.services.permissions import wymagaj_uprawnienia

router = APIRouter(prefix="/wiedza", tags=["Baza Wiedzy"])


@router.post("", response_model=NotatkaWiedzyRead, status_code=status.HTTP_201_CREATED,
             dependencies=[wymagaj_uprawnienia("wiedza", "tworz")])
async def create_notatka(payload: NotatkaWiedzyCreate, db: DB, current_user: CurrentUser):
    obj = NotatkaWiedzy(**payload.model_dump(), tworca_id=current_user.id)
    if not obj.parafia_id:
        obj.parafia_id = current_user.parafia_id
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="notatki_wiedzy", rekord_id=obj.id,
        operacja=OperacjaAudit.UTWORZONO, uzytkownik_id=current_user.id,
        parafia_id=obj.parafia_id, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.get("", response_model=list[NotatkaWiedzyRead])
async def list_notatki(
    db: DB,
    current_user: CurrentUser,
    kategoria: str | None = Query(None),
    szukaj: str | None = Query(None, description="Wyszukiwanie w tytule i treści"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    q = select(NotatkaWiedzy).where(NotatkaWiedzy.deleted_at.is_(None))

    # Parafianie widzą tylko publiczne notatki
    if current_user.rola == RolaUzytkownika.PARAFIANIN:
        q = q.where(NotatkaWiedzy.publiczna.is_(True))

    if kategoria:
        q = q.where(NotatkaWiedzy.kategoria == kategoria)

    if szukaj:
        pattern = f"%{szukaj}%"
        q = q.where(
            or_(
                NotatkaWiedzy.tytul.ilike(pattern),
                NotatkaWiedzy.tresc.ilike(pattern),
            )
        )

    q = q.order_by(NotatkaWiedzy.updated_at.desc()).limit(limit).offset(offset)
    return (await db.execute(q)).scalars().all()


@router.get("/{notatka_id}", response_model=NotatkaWiedzyRead)
async def get_notatka(notatka_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await db.get(NotatkaWiedzy, notatka_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Notatka nie znaleziona")
    if current_user.rola == RolaUzytkownika.PARAFIANIN and not obj.publiczna:
        raise HTTPException(status_code=403, detail="Brak dostępu do tej notatki")
    return obj


@router.patch("/{notatka_id}", response_model=NotatkaWiedzyRead,
              dependencies=[wymagaj_uprawnienia("wiedza", "edytuj")])
async def update_notatka(
    notatka_id: uuid.UUID, payload: NotatkaWiedzyUpdate, db: DB, current_user: CurrentUser
):
    obj = await db.get(NotatkaWiedzy, notatka_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Notatka nie znaleziona")
    stare = audit_svc.snapshot(obj)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="notatki_wiedzy", rekord_id=obj.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO, uzytkownik_id=current_user.id,
        stare_wartosci=stare, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.delete("/{notatka_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[wymagaj_uprawnienia("wiedza", "usun")])
async def soft_delete_notatka(notatka_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await db.get(NotatkaWiedzy, notatka_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Notatka nie znaleziona")
    stare = audit_svc.snapshot(obj)
    obj.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    await audit_svc.zapisz(
        db, tabela="notatki_wiedzy", rekord_id=obj.id,
        operacja=OperacjaAudit.USUNIETO, uzytkownik_id=current_user.id,
        stare_wartosci=stare,
    )
