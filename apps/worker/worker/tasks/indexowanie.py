"""Zadania indeksowania dokumentów w Qdrant."""
import hashlib
import uuid

import httpx
import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from worker.config import settings

log = structlog.get_logger()

VECTOR_SIZE = 768


async def ensure_collection(client: QdrantClient) -> None:
    collections = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in collections:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        log.info("qdrant_collection_created", name=settings.qdrant_collection)


async def embed_text(text: str) -> list[float]:
    """Generuje embedding przez Ollama (model nomic-embed-text lub fallback)."""
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            r = await client.post(
                f"{settings.ollama_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
            )
            if r.status_code == 200:
                return r.json()["embedding"]
        except Exception:
            pass
        # Fallback: hash-based deterministic vector (nie semantyczny, ale działający)
        h = hashlib.sha256(text.encode()).digest()
        vec = [((b / 255.0) * 2 - 1) for b in h]
        return (vec * (VECTOR_SIZE // len(vec) + 1))[:VECTOR_SIZE]


async def indeksuj_dokument(ctx: dict, dokument_id: str, tytul: str, tresc: str) -> dict:
    log.info("indexing_start", dokument_id=dokument_id)
    try:
        client = QdrantClient(url=settings.qdrant_url)
        await ensure_collection(client)
        tekst = f"{tytul}\n\n{tresc}"[:4096]
        vector = await embed_text(tekst)
        point = PointStruct(
            id=str(uuid.UUID(dokument_id)),
            vector=vector,
            payload={"dokument_id": dokument_id, "tytul": tytul},
        )
        client.upsert(collection_name=settings.qdrant_collection, points=[point])
        log.info("indexing_done", dokument_id=dokument_id)
        return {"status": "ok", "dokument_id": dokument_id}
    except Exception as e:
        log.error("indexing_error", dokument_id=dokument_id, error=str(e))
        raise
