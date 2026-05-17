import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.database import engine
from app.models.base import Base
from app.routers import health, intencje, dokumenty, wspolnoty, kalendarz, ai as ai_router

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", environment=settings.environment, model=settings.ollama_model)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("database_tables_ready")
    yield
    await engine.dispose()
    log.info("shutdown")


app = FastAPI(
    title="Źródło API",
    description="Inteligentny system wspierający pracę parafii",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(intencje.router)
app.include_router(dokumenty.router)
app.include_router(wspolnoty.router)
app.include_router(kalendarz.router)
app.include_router(ai_router.router)
