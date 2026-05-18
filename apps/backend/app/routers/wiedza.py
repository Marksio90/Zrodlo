"""Baza Wiedzy Parafii – CRUD z auto-embeddingiem i wyszukiwaniem semantycznym."""
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import Depends, APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_, select

from app.config import settings
from app.dependencies import AI, CurrentUser, DB
from app.models.audit import OperacjaAudit
from app.models.uzytkownicy import RolaUzytkownika
from app.models.wiedza import NotatkaWiedzy
from app.schemas.wiedza import NotatkaWiedzyCreate, NotatkaWiedzyRead, NotatkaWiedzyUpdate
from app.services import audit as audit_svc
from app.services.ai import SYSTEM_PROMPT_DUSZPASTERSKI
from app.services.permissions import wymagaj_uprawnienia

log = structlog.get_logger()

router = APIRouter(prefix="/wiedza", tags=["Baza Wiedzy"])


# ---------------------------------------------------------------------------
# Helpers – Qdrant
# ---------------------------------------------------------------------------

async def _embed_i_zapisz(obj: NotatkaWiedzy, ai) -> str | None:
    """Generuje embedding i zapisuje w Qdrant. Zwraca point_id lub None."""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, PointStruct, VectorParams

        tekst = f"{obj.tytul}\n\n{obj.tresc}"[:8000]
        vector = await ai.embed(tekst)

        qc = QdrantClient(url=settings.qdrant_url, timeout=10)
        collections = [c.name for c in qc.get_collections().collections]
        if settings.qdrant_collection not in collections:
            qc.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )

        point_id = str(obj.id)
        kat = obj.kategoria if isinstance(obj.kategoria, str) else obj.kategoria.value
        qc.upsert(
            collection_name=settings.qdrant_collection,
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "notatka_id": str(obj.id),
                    "tytul": obj.tytul,
                    "tresc": obj.tresc[:500],
                    "typ": "wiedza",
                    "kategoria": kat,
                },
            )],
        )
        log.info("embed_done", notatka_id=str(obj.id))
        return point_id
    except Exception as e:
        log.warning("embed_error", notatka_id=str(obj.id), error=str(e))
        return None


async def _usun_z_qdrant(notatka_id: str) -> None:
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointIdsList

        qc = QdrantClient(url=settings.qdrant_url, timeout=5)
        qc.delete(
            collection_name=settings.qdrant_collection,
            points_selector=PointIdsList(points=[notatka_id]),
        )
    except Exception as e:
        log.warning("qdrant_delete_error", notatka_id=notatka_id, error=str(e))


# ---------------------------------------------------------------------------
# Semantic search (before parameterized routes to avoid path conflict)
# ---------------------------------------------------------------------------

class SzukajRequest(BaseModel):
    pytanie: str
    limit: int = 5


class WynikSzukania(BaseModel):
    id: str
    tytul: str
    fragment: str
    kategoria: str
    score: float | None


class SzukajResponse(BaseModel):
    odpowiedz: str
    wyniki: list[WynikSzukania]
    model_uzyty: str


@router.post("/szukaj", response_model=SzukajResponse)
async def szukaj_semantycznie(body: SzukajRequest, db: DB, current_user: CurrentUser, ai: AI):
    """Semantyczne wyszukiwanie w bazie wiedzy parafii z odpowiedzią AI."""
    wyniki: list[WynikSzukania] = []

    # 1. Qdrant – wyszukiwanie semantyczne
    try:
        from qdrant_client import QdrantClient

        embedding = await ai.embed(body.pytanie)
        qc = QdrantClient(url=settings.qdrant_url, timeout=5)
        hits = qc.search(
            collection_name=settings.qdrant_collection,
            query_vector=embedding,
            limit=body.limit + 2,
            score_threshold=0.45,
        )
        ids_znalezione: set[str] = set()
        for hit in hits:
            if hit.payload.get("typ") != "wiedza":
                continue
            nid = hit.payload.get("notatka_id", "")
            ids_znalezione.add(nid)
            wyniki.append(WynikSzukania(
                id=nid,
                tytul=hit.payload.get("tytul", ""),
                fragment=hit.payload.get("tresc", "")[:300],
                kategoria=hit.payload.get("kategoria", "inne"),
                score=round(hit.score, 3),
            ))
            if len(wyniki) >= body.limit:
                break
    except Exception as e:
        log.warning("qdrant_search_error", error=str(e))

    # 2. Fallback fulltext jeśli Qdrant zwrócił za mało
    if len(wyniki) < 2:
        try:
            pattern = f"%{body.pytanie[:60]}%"
            q_filter = [
                NotatkaWiedzy.deleted_at.is_(None),
                or_(
                    NotatkaWiedzy.tytul.ilike(pattern),
                    NotatkaWiedzy.tresc.ilike(pattern),
                ),
            ]
            if current_user.rola == RolaUzytkownika.PARAFIANIN:
                q_filter.append(NotatkaWiedzy.publiczna.is_(True))
            rows = (
                await db.execute(select(NotatkaWiedzy).where(*q_filter).limit(3))
            ).scalars().all()
            znane = {w.id for w in wyniki}
            for r in rows:
                if str(r.id) not in znane:
                    kat = r.kategoria if isinstance(r.kategoria, str) else r.kategoria.value
                    wyniki.append(WynikSzukania(
                        id=str(r.id),
                        tytul=r.tytul,
                        fragment=r.tresc[:300],
                        kategoria=kat,
                        score=None,
                    ))
        except Exception as e:
            log.warning("fulltext_search_error", error=str(e))

    # 3. Generuj odpowiedź AI
    odpowiedz = "Niestety nie znalazłem informacji na ten temat w bazie wiedzy parafii."
    model_uzyty = "brak"
    if wyniki:
        kontekst = "\n\n".join(f"[{w.tytul}]\n{w.fragment}" for w in wyniki)
        prompt = (
            "Odpowiedz na pytanie na podstawie poniższej bazy wiedzy parafii.\n"
            "Jeśli informacje są niepełne, wskaż to. Odpowiadaj po polsku, zwięźle.\n\n"
            f"BAZA WIEDZY:\n{kontekst}\n\n"
            f"PYTANIE: {body.pytanie}"
        )
        try:
            odpowiedz, model_uzyty = await ai.chat(
                [
                    {"role": "system", "content": SYSTEM_PROMPT_DUSZPASTERSKI},
                    {"role": "user", "content": prompt},
                ]
            )
        except Exception as e:
            log.warning("ai_answer_error", error=str(e))
            odpowiedz = "\n".join(f"• {w.tytul}: {w.fragment}" for w in wyniki)
            model_uzyty = "error"

    return SzukajResponse(odpowiedz=odpowiedz, wyniki=wyniki, model_uzyty=model_uzyty)


@router.post("/embed-wszystkie", status_code=200,
             dependencies=[Depends(wymagaj_uprawnienia("wiedza", "tworz"))])
async def embed_wszystkie(db: DB, current_user: CurrentUser, ai: AI):
    """Batch embedding wszystkich notatek bez qdrant_id (np. po migracji)."""
    rows = (await db.execute(
        select(NotatkaWiedzy).where(
            NotatkaWiedzy.deleted_at.is_(None),
            NotatkaWiedzy.qdrant_id.is_(None),
        )
    )).scalars().all()

    ok = 0
    bledy = 0
    for obj in rows:
        qdrant_id = await _embed_i_zapisz(obj, ai)
        if qdrant_id:
            obj.qdrant_id = qdrant_id
            ok += 1
        else:
            bledy += 1
    return {"osadzone": ok, "bledy": bledy, "lacznie": len(rows)}


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.post("", response_model=NotatkaWiedzyRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(wymagaj_uprawnienia("wiedza", "tworz"))])
async def create_notatka(payload: NotatkaWiedzyCreate, db: DB, current_user: CurrentUser, ai: AI):
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
    qdrant_id = await _embed_i_zapisz(obj, ai)
    if qdrant_id:
        obj.qdrant_id = qdrant_id
        await db.flush()
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
              dependencies=[Depends(wymagaj_uprawnienia("wiedza", "edytuj"))])
async def update_notatka(
    notatka_id: uuid.UUID, payload: NotatkaWiedzyUpdate, db: DB, current_user: CurrentUser, ai: AI
):
    obj = await db.get(NotatkaWiedzy, notatka_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Notatka nie znaleziona")
    stare = audit_svc.snapshot(obj)
    zmiany = payload.model_dump(exclude_unset=True)
    for field, value in zmiany.items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    await audit_svc.zapisz(
        db, tabela="notatki_wiedzy", rekord_id=obj.id,
        operacja=OperacjaAudit.ZAKTUALIZOWANO, uzytkownik_id=current_user.id,
        stare_wartosci=stare, nowe_wartosci=audit_svc.snapshot(obj),
    )
    if "tytul" in zmiany or "tresc" in zmiany:
        qdrant_id = await _embed_i_zapisz(obj, ai)
        if qdrant_id:
            obj.qdrant_id = qdrant_id
            await db.flush()
    return obj


@router.delete("/{notatka_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(wymagaj_uprawnienia("wiedza", "usun"))])
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
    if obj.qdrant_id:
        await _usun_z_qdrant(obj.qdrant_id)


@router.post("/{notatka_id}/embed", response_model=NotatkaWiedzyRead,
             dependencies=[Depends(wymagaj_uprawnienia("wiedza", "edytuj"))])
async def embed_notatke(notatka_id: uuid.UUID, db: DB, current_user: CurrentUser, ai: AI):
    """Ręczne embedowanie pojedynczej notatki (naprawa po błędzie)."""
    obj = await db.get(NotatkaWiedzy, notatka_id)
    if not obj or obj.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Notatka nie znaleziona")
    qdrant_id = await _embed_i_zapisz(obj, ai)
    if not qdrant_id:
        raise HTTPException(status_code=503, detail="Błąd embeddingu – sprawdź logi serwera")
    obj.qdrant_id = qdrant_id
    await db.flush()
    return obj
