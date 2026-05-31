import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class TypAiUzycia(StrEnum):
    CHAT      = "chat"
    EMBED     = "embed"
    DOKUMENT  = "dokument"
    HOMILIA   = "homilia"
    KOMUNIKACJA = "komunikacja"


class AiUzycie(Base, UUIDMixin):
    """Ślad użycia AI – każde wywołanie OpenAI zapisane z kosztem."""

    __tablename__ = "ai_uzycia"

    parafia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parafie.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    uzytkownik_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uzytkownicy.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    typ: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    tokeny_wejscie: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokeny_wyjscie: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    koszt_usd: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False, default=Decimal("0"))
    czas_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
