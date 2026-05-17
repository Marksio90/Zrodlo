from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from app.database import async_session_factory
from app.services.cache import get_cache
from app.services.storage import get_storage
from app.services.ai import get_ai

router = APIRouter()


@router.get("/health")
async def health():
    checks: dict[str, str] = {}

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"

    try:
        cache = await get_cache()
        checks["redis"] = "ok" if await cache.ping() else "error"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    try:
        storage = get_storage()
        checks["minio"] = "ok" if storage.ping() else "error"
    except Exception as e:
        checks["minio"] = f"error: {e}"

    try:
        ai = get_ai()
        checks["openai"] = "ok" if await ai.is_available() else "unavailable"
    except Exception as e:
        checks["openai"] = f"error: {e}"

    all_critical = all(
        v == "ok" for k, v in checks.items() if k in ("postgres", "redis")
    )

    return {
        "status": "ok" if all_critical else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": checks,
    }
