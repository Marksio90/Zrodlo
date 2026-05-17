import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory, engine
from app.models.base import Base
from app.models.uzytkownicy import RolaUzytkownika, Uzytkownik
import app.models  # noqa: F401 – rejestruje wszystkie modele
from app.routers import (
    auth, parafia, uzytkownicy, grupy,
    intencje, dokumenty, wspolnoty, kalendarz,
    ogloszenia, powiadomienia, wiedza,
    health, ai as ai_router, asystent as asystent_router,
    homilia as homilia_router,
)

log = structlog.get_logger()

_SEED_EMAIL = "admin@zrodlo.pl"
_SEED_HASLO = "Admin1234!"


async def _seed_admin() -> None:
    """Tworzy domyślne konto administratora jeśli baza jest pusta."""
    from app.services.auth import hash_password

    async with async_session_factory() as session:
        existing = await session.execute(select(Uzytkownik).limit(1))
        if existing.first():
            return

        admin = Uzytkownik(
            email=_SEED_EMAIL,
            haslo_hash=hash_password(_SEED_HASLO),
            imie="Administrator",
            nazwisko="Systemu",
            rola=RolaUzytkownika.ADMIN,
            aktywny=True,
        )
        session.add(admin)
        await session.commit()
        log.info("seed_admin_created", email=_SEED_EMAIL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", environment=settings.environment)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("database_tables_ready")

    if settings.is_development:
        await _seed_admin()

    yield
    await engine.dispose()
    log.info("shutdown")


app = FastAPI(
    title="Źródło API",
    description=(
        "Inteligentny system wspierający pracę parafii. "
        "AI wspiera człowieka – nie zastępuje kapłana."
    ),
    version="0.2.0",
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

# Publiczne
app.include_router(health.router)
app.include_router(auth.router)

# Domeny
app.include_router(parafia.router)
app.include_router(uzytkownicy.router)
app.include_router(grupy.router)
app.include_router(intencje.router)
app.include_router(dokumenty.router)
app.include_router(wspolnoty.router)
app.include_router(kalendarz.router)
app.include_router(ogloszenia.router)
app.include_router(powiadomienia.router)
app.include_router(wiedza.router)
app.include_router(ai_router.router)
app.include_router(asystent_router.router)
app.include_router(homilia_router.router)
