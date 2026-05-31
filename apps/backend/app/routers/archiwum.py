"""Archiwum Dokumentów – upload, OCR, tagowanie, wyszukiwanie, archiwizacja."""
import json
import mimetypes
import uuid
from datetime import date, datetime, timezone

import structlog
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import or_, select

from app.dependencies import AI, DB, CurrentUser, Storage
from app.models.skan import SkanDokumentu
from app.models.uzytkownicy import RolaUzytkownika
from app.schemas.archiwum import SkanListItem, SkanRead, SkanUpdate
from app.services import ocr as ocr_svc

log = structlog.get_logger()

router = APIRouter(prefix="/archiwum", tags=["Archiwum – Dokumenty OCR"])

_MAKS_ROZMIAR = 10 * 1024 * 1024  # 10 MB
_MIME_DO_TYP = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
}

# ---------------------------------------------------------------------------
# Upload + OCR
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=SkanRead, status_code=status.HTTP_201_CREATED)
async def upload_dokument(
    db: DB,
    current_user: CurrentUser,
    ai: AI,
    storage: Storage,
    plik: UploadFile = File(...),
    notatki: str | None = Form(None),
):
    # Walidacja MIME
    mime_type = plik.content_type or ""
    if mime_type not in _MIME_DO_TYP:
        guessed, _ = mimetypes.guess_type(plik.filename or "")
        if guessed not in _MIME_DO_TYP:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dozwolone formaty: PDF, JPG, PNG",
            )
        mime_type = guessed
    typ_pliku = _MIME_DO_TYP[mime_type]

    # Czytanie pliku
    content = await plik.read()
    if len(content) > _MAKS_ROZMIAR:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Plik zbyt duży – maksymalnie 10 MB",
        )

    # Zapis w MinIO
    skan_id = uuid.uuid4()
    bezpieczna_nazwa = (plik.filename or "dokument").replace(" ", "_")
    klucz = f"skany/{current_user.id}/{skan_id}/{bezpieczna_nazwa}"
    try:
        storage.upload(klucz, content, mime_type)
    except Exception as e:
        log.error("archiwum_upload_storage", error=str(e))
        raise HTTPException(status_code=500, detail=f"Błąd przechowywania pliku: {e}")

    # Rekord DB – status "przetwarzanie"
    skan = SkanDokumentu(
        id=skan_id,
        parafia_id=current_user.parafia_id,
        uzytkownik_id=current_user.id,
        nazwa_pliku=plik.filename or "dokument",
        typ_pliku=typ_pliku,
        mime_type=mime_type,
        minio_klucz=klucz,
        rozmiar_bajtow=len(content),
        notatki=notatki,
        ocr_status="przetwarzanie",
    )
    db.add(skan)
    await db.flush()

    # OCR + klasyfikacja AI
    try:
        wynik = await ocr_svc.przetworz(content, typ_pliku, ai)
        skan.tresc_ocr = wynik["tresc_ocr"]
        skan.typ_dokumentu = wynik["typ_dokumentu"]
        skan.jednostka_wystawiajaca = wynik["jednostka_wystawiajaca"]
        if wynik["data_wystawienia"]:
            try:
                skan.data_wystawienia = date.fromisoformat(wynik["data_wystawienia"])
            except (ValueError, TypeError):
                pass
        skan.osoby = wynik["osoby"]
        skan.dane_kontaktowe = wynik["dane_kontaktowe"]
        skan.tagi = wynik["tagi"]
        skan.encje = wynik["encje"]
        skan.ocr_status = "gotowy"
    except Exception as e:
        log.error("archiwum_ocr_failed", skan_id=str(skan_id), error=str(e))
        skan.ocr_status = "blad"
        skan.ocr_blad = str(e)[:400]

    await db.commit()
    await db.refresh(skan)
    log.info("archiwum_uploaded", skan_id=str(skan_id), status=skan.ocr_status)
    return skan


# ---------------------------------------------------------------------------
# Lista z wyszukiwaniem
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[SkanListItem])
async def lista_skanow(
    db: DB,
    current_user: CurrentUser,
    q: str | None = Query(None, description="Szukaj w tekście OCR, nazwie pliku, notatkach"),
    typ: str | None = Query(None),
    tag: str | None = Query(None),
    zarchiwizowany: bool = Query(False),
    limit: int = Query(30, le=100),
    offset: int = Query(0, ge=0),
):
    # Proboszcz/admin widzi wszystkie skany parafii, pozostali tylko swoje
    _widzi_wszystkie = current_user.rola in (
        RolaUzytkownika.PROBOSZCZ, RolaUzytkownika.ADMIN
    )
    if _widzi_wszystkie and current_user.parafia_id:
        _scope = SkanDokumentu.parafia_id == current_user.parafia_id
    else:
        _scope = SkanDokumentu.uzytkownik_id == current_user.id

    query = select(SkanDokumentu).where(
        SkanDokumentu.deleted_at.is_(None),
        _scope,
        SkanDokumentu.zarchiwizowany == zarchiwizowany,
    )
    if q:
        term = f"%{q}%"
        query = query.where(
            or_(
                SkanDokumentu.nazwa_pliku.ilike(term),
                SkanDokumentu.tresc_ocr.ilike(term),
                SkanDokumentu.notatki.ilike(term),
                SkanDokumentu.jednostka_wystawiajaca.ilike(term),
            )
        )
    if typ:
        query = query.where(SkanDokumentu.typ_dokumentu == typ)
    if tag:
        query = query.where(SkanDokumentu.tagi.op("@>")(json.dumps([tag])))
    query = query.order_by(SkanDokumentu.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Szczegóły
# ---------------------------------------------------------------------------

@router.get("/{skan_id}", response_model=SkanRead)
async def pobierz_skan(skan_id: uuid.UUID, db: DB, current_user: CurrentUser):
    skan = await _get_or_404(db, skan_id, current_user)
    return skan


# ---------------------------------------------------------------------------
# Aktualizacja tagów / notatek / metadanych
# ---------------------------------------------------------------------------

@router.patch("/{skan_id}", response_model=SkanRead)
async def aktualizuj_skan(
    skan_id: uuid.UUID,
    payload: SkanUpdate,
    db: DB,
    current_user: CurrentUser,
):
    skan = await _get_or_404(db, skan_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(skan, field, value)
    await db.commit()
    await db.refresh(skan)
    return skan


# ---------------------------------------------------------------------------
# Archiwizacja / przywrócenie
# ---------------------------------------------------------------------------

@router.post("/{skan_id}/archiwizuj", response_model=SkanRead)
async def archiwizuj(skan_id: uuid.UUID, db: DB, current_user: CurrentUser):
    skan = await _get_or_404(db, skan_id, current_user)
    skan.zarchiwizowany = not skan.zarchiwizowany
    await db.commit()
    await db.refresh(skan)
    return skan


# ---------------------------------------------------------------------------
# Ponowne OCR
# ---------------------------------------------------------------------------

@router.post("/{skan_id}/ponow-ocr", response_model=SkanRead)
async def ponow_ocr(
    skan_id: uuid.UUID,
    db: DB,
    current_user: CurrentUser,
    ai: AI,
    storage: Storage,
):
    skan = await _get_or_404(db, skan_id, current_user)
    try:
        content = storage.download(skan.minio_klucz)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd pobierania pliku: {e}")

    skan.ocr_status = "przetwarzanie"
    await db.flush()
    try:
        wynik = await ocr_svc.przetworz(content, skan.typ_pliku, ai)
        skan.tresc_ocr = wynik["tresc_ocr"]
        skan.typ_dokumentu = wynik["typ_dokumentu"]
        skan.jednostka_wystawiajaca = wynik["jednostka_wystawiajaca"]
        if wynik["data_wystawienia"]:
            try:
                skan.data_wystawienia = date.fromisoformat(wynik["data_wystawienia"])
            except (ValueError, TypeError):
                pass
        skan.osoby = wynik["osoby"]
        skan.dane_kontaktowe = wynik["dane_kontaktowe"]
        skan.tagi = wynik["tagi"]
        skan.encje = wynik["encje"]
        skan.ocr_status = "gotowy"
        skan.ocr_blad = None
    except Exception as e:
        skan.ocr_status = "blad"
        skan.ocr_blad = str(e)[:400]

    await db.commit()
    await db.refresh(skan)
    return skan


# ---------------------------------------------------------------------------
# Pobieranie (pre-signed URL)
# ---------------------------------------------------------------------------

@router.get("/{skan_id}/pobierz")
async def url_pobierania(skan_id: uuid.UUID, db: DB, current_user: CurrentUser, storage: Storage):
    skan = await _get_or_404(db, skan_id, current_user)
    url = storage.presigned_url(skan.minio_klucz, expires_seconds=1800)
    return {"url": url, "expires_in": 1800, "nazwa_pliku": skan.nazwa_pliku}


# ---------------------------------------------------------------------------
# Usunięcie (miękkie)
# ---------------------------------------------------------------------------

@router.delete("/{skan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def usun_skan(skan_id: uuid.UUID, db: DB, current_user: CurrentUser, storage: Storage):
    skan = await _get_or_404(db, skan_id, current_user)
    try:
        storage.delete(skan.minio_klucz)
    except Exception:
        pass
    skan.deleted_at = datetime.now(timezone.utc)
    await db.commit()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _get_or_404(db, skan_id: uuid.UUID, current_user) -> SkanDokumentu:
    skan = await db.get(SkanDokumentu, skan_id)
    if not skan or skan.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Dokument nie znaleziony")
    widzi_wszystkie = current_user.rola in (RolaUzytkownika.PROBOSZCZ, RolaUzytkownika.ADMIN)
    if widzi_wszystkie:
        if skan.parafia_id and current_user.parafia_id and skan.parafia_id != current_user.parafia_id:
            raise HTTPException(status_code=404, detail="Dokument nie znaleziony")
    else:
        if skan.uzytkownik_id != current_user.id:
            raise HTTPException(status_code=404, detail="Dokument nie znaleziony")
    return skan
