"""Asystent Źródła – wieloturowy czat z RAG."""
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.dependencies import AI, DB, CurrentUser
from app.models.intencje import Liturgia
from app.models.kalendarz import Wydarzenie
from app.models.rozmowa import Rozmowa, WiadomoscRozmowy
from app.models.wiedza import NotatkaWiedzy
from app.schemas.asystent import RozmowaCreate, RozmowaRead, WiadomoscRead, WyslijWiadomoscRequest
from app.services.ai import SYSTEM_PROMPT_DUSZPASTERSKI, _czy_trudne

log = structlog.get_logger()

router = APIRouter(prefix="/asystent", tags=["Asystent Źródła"])

_LIMIT_HISTORII = 10  # ostatnich par wiadomości do kontekstu


# ---------------------------------------------------------------------------
# Rozmowy – CRUD
# ---------------------------------------------------------------------------

@router.post("/rozmowy", response_model=RozmowaRead, status_code=201)
async def stworz_rozmowe(body: RozmowaCreate, db: DB, current_user: CurrentUser):
    rozmowa = Rozmowa(uzytkownik_id=current_user.id, tytul=body.tytul)
    db.add(rozmowa)
    await db.commit()
    await db.refresh(rozmowa)
    return rozmowa


@router.get("/rozmowy", response_model=list[RozmowaRead])
async def lista_rozmow(db: DB, current_user: CurrentUser):
    result = await db.execute(
        select(Rozmowa)
        .where(Rozmowa.uzytkownik_id == current_user.id)
        .order_by(Rozmowa.updated_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.delete("/rozmowy/{rozmowa_id}", status_code=204)
async def usun_rozmowe(rozmowa_id: uuid.UUID, db: DB, current_user: CurrentUser):
    rozmowa = await db.get(Rozmowa, rozmowa_id)
    if not rozmowa or rozmowa.uzytkownik_id != current_user.id:
        raise HTTPException(status_code=404, detail="Rozmowa nie znaleziona")
    await db.delete(rozmowa)
    await db.commit()


@router.get("/rozmowy/{rozmowa_id}/wiadomosci", response_model=list[WiadomoscRead])
async def lista_wiadomosci(rozmowa_id: uuid.UUID, db: DB, current_user: CurrentUser):
    rozmowa = await db.get(Rozmowa, rozmowa_id)
    if not rozmowa or rozmowa.uzytkownik_id != current_user.id:
        raise HTTPException(status_code=404, detail="Rozmowa nie znaleziona")
    result = await db.execute(
        select(WiadomoscRozmowy)
        .where(WiadomoscRozmowy.rozmowa_id == rozmowa_id)
        .order_by(WiadomoscRozmowy.created_at)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Wysyłanie wiadomości z RAG
# ---------------------------------------------------------------------------

@router.post("/rozmowy/{rozmowa_id}/wiadomosci", response_model=WiadomoscRead)
async def wyslij_wiadomosc(
    rozmowa_id: uuid.UUID,
    body: WyslijWiadomoscRequest,
    db: DB,
    current_user: CurrentUser,
    ai: AI,
):
    rozmowa = await db.get(Rozmowa, rozmowa_id)
    if not rozmowa or rozmowa.uzytkownik_id != current_user.id:
        raise HTTPException(status_code=404, detail="Rozmowa nie znaleziona")

    # Zapisz wiadomość użytkownika
    msg_user = WiadomoscRozmowy(
        rozmowa_id=rozmowa_id,
        rola="user",
        tresc=body.tresc,
    )
    db.add(msg_user)
    await db.flush()

    # Wyszukaj kontekst RAG
    zrodla = await _szukaj_kontekstu(body.tresc, db, ai)
    kontekst_str = _formatuj_kontekst(zrodla)

    # Buduj historię do kontekstu LLM
    historia = await _pobierz_historie(rozmowa_id, db)
    messages = _buduj_messages(historia, body.tresc, kontekst_str)

    # Wywołaj AI
    try:
        jest_trudne = _czy_trudne(body.tresc)
        odpowiedz, model_uzyty = await ai.chat(messages, complex=jest_trudne)
    except Exception as e:
        log.error("asystent_error", error=str(e))
        odpowiedz = "Niestety nie mam tej informacji."
        model_uzyty = "error"

    # Zapisz odpowiedź asystenta
    zrodla_serializowane = [z.__dict__ if hasattr(z, '__dict__') else z for z in zrodla]
    msg_ai = WiadomoscRozmowy(
        rozmowa_id=rozmowa_id,
        rola="assistant",
        tresc=odpowiedz,
        model_uzyty=model_uzyty,
        zrodla=zrodla_serializowane,
    )
    db.add(msg_ai)

    # Aktualizuj tytuł rozmowy przy pierwszej wiadomości
    result = await db.execute(
        select(func.count(WiadomoscRozmowy.id))
        .where(WiadomoscRozmowy.rozmowa_id == rozmowa_id)
    )
    count = result.scalar_one()
    if count <= 2 and rozmowa.tytul == "Nowa rozmowa":
        rozmowa.tytul = body.tresc[:60] + ("..." if len(body.tresc) > 60 else "")
    rozmowa.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(msg_ai)
    return msg_ai


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _szukaj_kontekstu(pytanie: str, db, ai) -> list[dict]:
    """RAG: szuka w Qdrant (semantycznie) i PostgreSQL (słowami kluczowymi)."""
    zrodla: list[dict] = []

    # 1. Qdrant – wyszukiwanie semantyczne
    try:
        from qdrant_client import QdrantClient
        from app.config import settings as cfg

        embedding = await ai.embed(pytanie)
        qc = QdrantClient(url=cfg.qdrant_url, timeout=5)
        hits = qc.search(
            collection_name=cfg.qdrant_collection,
            query_vector=embedding,
            limit=3,
            score_threshold=0.5,
        )
        for hit in hits:
            zrodla.append({
                "typ": "wiedza",
                "id": hit.payload.get("dokument_id") or hit.payload.get("notatka_id"),
                "tytul": hit.payload.get("tytul", "Baza wiedzy"),
                "fragment": hit.payload.get("tresc", "")[:300],
                "score": round(hit.score, 3),
            })
    except Exception as e:
        log.warning("qdrant_unavailable", error=str(e))

    # 2. PostgreSQL – notatki wiedzy pełnotekstowo
    try:
        kw = pytanie.lower()
        wyniki = await db.execute(
            select(NotatkaWiedzy)
            .where(
                NotatkaWiedzy.deleted_at.is_(None),
                NotatkaWiedzy.publiczna.is_(True),
                (NotatkaWiedzy.tytul.ilike(f"%{kw[:40]}%")) | (NotatkaWiedzy.tresc.ilike(f"%{kw[:40]}%")),
            )
            .limit(2)
        )
        for n in wyniki.scalars().all():
            if not any(z.get("id") == str(n.id) for z in zrodla):
                zrodla.append({
                    "typ": "wiedza",
                    "id": str(n.id),
                    "tytul": n.tytul,
                    "fragment": n.tresc[:300],
                    "score": None,
                })
    except Exception as e:
        log.warning("knowledge_search_error", error=str(e))

    # 3. Godziny Mszy – jeśli pytanie o msze
    if any(w in pytanie.lower() for w in ["msz", "liturgi", "nabo", "godzin", "kiedy"]):
        try:
            dzis = datetime.now(timezone.utc).date()
            msze = await db.execute(
                select(Liturgia)
                .where(
                    Liturgia.deleted_at.is_(None),
                    Liturgia.data >= dzis,
                )
                .order_by(Liturgia.data, Liturgia.godzina)
                .limit(5)
            )
            for msza in msze.scalars().all():
                zrodla.append({
                    "typ": "msza",
                    "id": str(msza.id),
                    "tytul": f"Msza {msza.data} {msza.godzina.strftime('%H:%M')}",
                    "fragment": f"{msza.typ}, {msza.miejsce}{(', ' + msza.uwagi) if msza.uwagi else ''}",
                    "score": None,
                })
        except Exception as e:
            log.warning("msze_search_error", error=str(e))

    # 4. Wydarzenia – jeśli pytanie o wydarzenia
    if any(w in pytanie.lower() for w in ["wydarzen", "spotkani", "rekolekcj", "pielgrzym", "kiedy", "plan"]):
        try:
            dzis = datetime.now(timezone.utc)
            wydarzenia = await db.execute(
                select(Wydarzenie)
                .where(
                    Wydarzenie.deleted_at.is_(None),
                    Wydarzenie.data_od >= dzis,
                )
                .order_by(Wydarzenie.data_od)
                .limit(3)
            )
            for w in wydarzenia.scalars().all():
                zrodla.append({
                    "typ": "wydarzenie",
                    "id": str(w.id),
                    "tytul": w.tytul,
                    "fragment": f"{w.data_od.strftime('%d.%m.%Y %H:%M')}{(', ' + w.miejsce) if w.miejsce else ''}",
                    "score": None,
                })
        except Exception as e:
            log.warning("wydarzenia_search_error", error=str(e))

    return zrodla[:6]


def _formatuj_kontekst(zrodla: list[dict]) -> str:
    if not zrodla:
        return ""
    czesci = []
    for z in zrodla:
        naglowek = f"[{z['typ'].upper()}] {z['tytul']}"
        fragment = z.get("fragment", "")
        czesci.append(f"{naglowek}\n{fragment}" if fragment else naglowek)
    return "KONTEKST Z BAZY WIEDZY PARAFII:\n" + "\n\n".join(czesci)


async def _pobierz_historie(rozmowa_id: uuid.UUID, db) -> list[WiadomoscRozmowy]:
    result = await db.execute(
        select(WiadomoscRozmowy)
        .where(WiadomoscRozmowy.rozmowa_id == rozmowa_id)
        .order_by(WiadomoscRozmowy.created_at.desc())
        .limit(_LIMIT_HISTORII * 2)
    )
    msgs = result.scalars().all()
    return list(reversed(msgs))


def _buduj_messages(historia: list[WiadomoscRozmowy], nowe_pytanie: str, kontekst: str) -> list[dict]:
    system = SYSTEM_PROMPT_DUSZPASTERSKI
    if kontekst:
        system += f"\n\n{kontekst}"
    messages: list[dict] = [{"role": "system", "content": system}]
    for msg in historia:
        if msg.rola in ("user", "assistant"):
            messages.append({"role": msg.rola, "content": msg.tresc})
    messages.append({"role": "user", "content": nowe_pytanie})
    return messages
