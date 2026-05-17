"""Zadania indeksowania dokumentów w Qdrant (OpenAI text-embedding-3-small)."""
import uuid

import structlog
from openai import AsyncOpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from worker.config import settings

log = structlog.get_logger()

VECTOR_SIZE = 1536  # text-embedding-3-small


async def ensure_collection(client: QdrantClient) -> None:
    collections = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in collections:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        log.info("qdrant_collection_created", name=settings.qdrant_collection)


async def embed_text(text: str) -> list[float]:
    """Generuje embedding przez OpenAI text-embedding-3-small (1536 wymiarów)."""
    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=30.0)
    response = await client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text[:8000],
    )
    return response.data[0].embedding


async def indeksuj_dokument(ctx: dict, dokument_id: str, tytul: str, tresc: str) -> dict:
    log.info("indexing_start", dokument_id=dokument_id)
    try:
        client = QdrantClient(url=settings.qdrant_url)
        await ensure_collection(client)
        tekst = f"{tytul}\n\n{tresc}"[:8000]
        vector = await embed_text(tekst)
        point = PointStruct(
            id=str(uuid.UUID(dokument_id)),
            vector=vector,
            payload={
                "dokument_id": dokument_id,
                "tytul": tytul,
                "tresc": tresc[:500],
                "typ": "dokument",
            },
        )
        client.upsert(collection_name=settings.qdrant_collection, points=[point])
        log.info("indexing_done", dokument_id=dokument_id)
        return {"status": "ok", "dokument_id": dokument_id}
    except Exception as e:
        log.error("indexing_error", dokument_id=dokument_id, error=str(e))
        raise


async def indeksuj_notatke_wiedzy(ctx: dict, notatka_id: str, tytul: str, tresc: str) -> dict:
    log.info("indexing_notatka_start", notatka_id=notatka_id)
    try:
        client = QdrantClient(url=settings.qdrant_url)
        await ensure_collection(client)
        tekst = f"{tytul}\n\n{tresc}"[:8000]
        vector = await embed_text(tekst)
        point = PointStruct(
            id=str(uuid.UUID(notatka_id)),
            vector=vector,
            payload={
                "notatka_id": notatka_id,
                "tytul": tytul,
                "tresc": tresc[:500],
                "typ": "wiedza",
            },
        )
        client.upsert(collection_name=settings.qdrant_collection, points=[point])
        log.info("indexing_notatka_done", notatka_id=notatka_id)
        return {"status": "ok", "notatka_id": notatka_id}
    except Exception as e:
        log.error("indexing_notatka_error", notatka_id=notatka_id, error=str(e))
        raise
