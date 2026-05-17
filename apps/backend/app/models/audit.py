"""Audit log – immutable, never deleted."""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OperacjaAudit(StrEnum):
    UTWORZONO = "UTWORZONO"
    ZAKTUALIZOWANO = "ZAKTUALIZOWANO"
    USUNIETO = "USUNIETO"
    PRZYWROCONO = "PRZYWROCONO"
    ZALOGOWANO = "ZALOGOWANO"
    WYLOGOWANO = "WYLOGOWANO"


class AuditLog(Base):
    """Niemodyfikowalny log zmian. Brak soft delete, brak updated_at."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tabela: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    rekord_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    operacja: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    uzytkownik_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    parafia_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    stare_wartosci: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    nowe_wartosci: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_adres: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
