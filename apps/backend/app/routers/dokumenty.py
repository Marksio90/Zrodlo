import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.dependencies import DB, Storage
from app.models.dokumenty import Dokument, StatusDokumentu, TypDokumentu
from app.schemas.dokumenty import DokumentCreate, DokumentRead, DokumentUpdate

router = APIRouter(prefix="/dokumenty", tags=["Dokumenty"])


@router.post("", response_model=DokumentRead, status_code=status.HTTP_201_CREATED)
async def create_dokument(payload: DokumentCreate, db: DB):
    obj = Dokument(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("", response_model=list[DokumentRead])
async def list_dokumenty(
    db: DB,
    typ: TypDokumentu | None = Query(None),
    status: StatusDokumentu | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
):
    q = select(Dokument)
    if typ:
        q = q.where(Dokument.typ == typ)
    if status:
        q = q.where(Dokument.status == status)
    q = q.order_by(Dokument.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{dokument_id}", response_model=DokumentRead)
async def get_dokument(dokument_id: uuid.UUID, db: DB):
    obj = await db.get(Dokument, dokument_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Dokument nie znaleziony")
    return obj


@router.patch("/{dokument_id}", response_model=DokumentRead)
async def update_dokument(dokument_id: uuid.UUID, payload: DokumentUpdate, db: DB):
    obj = await db.get(Dokument, dokument_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Dokument nie znaleziony")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.delete("/{dokument_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dokument(dokument_id: uuid.UUID, db: DB, storage: Storage):
    obj = await db.get(Dokument, dokument_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Dokument nie znaleziony")
    if obj.plik_klucz:
        storage.delete(obj.plik_klucz)
    await db.delete(obj)


@router.get("/{dokument_id}/pobierz")
async def download_url(dokument_id: uuid.UUID, db: DB, storage: Storage):
    obj = await db.get(Dokument, dokument_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Dokument nie znaleziony")
    if not obj.plik_klucz:
        raise HTTPException(status_code=404, detail="Plik nie jest dołączony do dokumentu")
    url = storage.presigned_url(obj.plik_klucz, expires_seconds=1800)
    return {"url": url, "expires_in": 1800}
