import uuid
from datetime import datetime, timezone

from fastapi import Depends, APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DB, Storage
from app.models.audit import OperacjaAudit
from app.models.dokumenty import Dokument, StatusDokumentu, TypDokumentu
from app.schemas.dokumenty import DokumentCreate, DokumentRead, DokumentUpdate
from app.services import audit as audit_svc
from app.services.permissions import wymagaj_uprawnienia

router = APIRouter(prefix="/dokumenty", tags=["Dokumenty"])


@router.post("", response_model=DokumentRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(wymagaj_uprawnienia("dokument", "tworz"))])
async def create_dokument(payload: DokumentCreate, db: DB, current_user: CurrentUser):
    obj = Dokument(**payload.model_dump(), tworca_id=current_user.id)
    if not obj.parafia_id:
        obj.parafia_id = current_user.parafia_id
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="dokumenty", rekord_id=obj.id,
        operacja=OperacjaAudit.UTWORZONO, uzytkownik_id=current_user.id,
        parafia_id=obj.parafia_id, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.get("", response_model=list[DokumentRead])
async def list_dokumenty(
    db: DB, _: CurrentUser,
    typ: TypDokumentu | None = Query(None),
    status_filter: StatusDokumentu | None = Query(None, alias="status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    q = select(Dokument).where(Dokument.deleted_at.is_(None))
    if typ:
        q = q.where(Dokument.typ == typ)
    if status_filter:
        q = q.where(Dokument.status == status_filter)
    q = q.order_by(Dokument.created_at.desc()).limit(limit).offset(offset)
    return (await db.execute(q)).scalars().all()


@router.get("/{dokument_id}", response_model=DokumentRead)
async def get_dokument(dokument_id: uuid.UUID, db: DB, _: CurrentUser):
    obj = await db.get(Dokument, dokument_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Dokument nie znaleziony")
    return obj


@router.patch("/{dokument_id}", response_model=DokumentRead,
              dependencies=[Depends(wymagaj_uprawnienia("dokument", "edytuj"))])
async def update_dokument(dokument_id: uuid.UUID, payload: DokumentUpdate, db: DB, current_user: CurrentUser):
    obj = await db.get(Dokument, dokument_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Dokument nie znaleziony")
    stare = audit_svc.snapshot(obj)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="dokumenty", rekord_id=obj.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO, uzytkownik_id=current_user.id,
        stare_wartosci=stare, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.post("/{dokument_id}/zatwierdz", response_model=DokumentRead,
             dependencies=[Depends(wymagaj_uprawnienia("dokument", "zatwierdz"))])
async def zatwierdz_dokument(dokument_id: uuid.UUID, db: DB, current_user: CurrentUser):
    obj = await db.get(Dokument, dokument_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Dokument nie znaleziony")
    stare = audit_svc.snapshot(obj)
    obj.status = StatusDokumentu.ZATWIERDZONY
    obj.zatwierdzone_przez_id = current_user.id
    obj.data_zatwierdzenia = datetime.now(timezone.utc)
    obj.zatwierdzone_przez = f"{current_user.imie} {current_user.nazwisko}"
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="dokumenty", rekord_id=obj.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO, uzytkownik_id=current_user.id,
        stare_wartosci=stare, nowe_wartosci=audit_svc.snapshot(obj),
    )
    return obj


@router.delete("/{dokument_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(wymagaj_uprawnienia("dokument", "usun"))])
async def soft_delete_dokument(dokument_id: uuid.UUID, db: DB, current_user: CurrentUser, storage: Storage):
    obj = await db.get(Dokument, dokument_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Dokument nie znaleziony")
    stare = audit_svc.snapshot(obj)
    if obj.plik_klucz:
        storage.delete(obj.plik_klucz)
    obj.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    await audit_svc.zapisz(
        db, tabela="dokumenty", rekord_id=obj.id,
        operacja=OperacjaAudit.USUNIETO, uzytkownik_id=current_user.id,
        stare_wartosci=stare,
    )


@router.get("/{dokument_id}/pobierz")
async def download_url(dokument_id: uuid.UUID, db: DB, _: CurrentUser, storage: Storage):
    obj = await db.get(Dokument, dokument_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Dokument nie znaleziony")
    if not obj.plik_klucz:
        raise HTTPException(status_code=404, detail="Brak pliku dołączonego do dokumentu")
    url = storage.presigned_url(obj.plik_klucz, expires_seconds=1800)
    return {"url": url, "expires_in": 1800}
