import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Plan(StrEnum):
    TRIAL     = "trial"
    PODSTAWOWY = "podstawowy"
    STANDARD  = "standard"
    PREMIUM   = "premium"


class Subskrypcja(Base, UUIDMixin, TimestampMixin):
    """Subskrypcja parafii – plan cenowy i jego limity operacyjne."""

    __tablename__ = "subskrypcje"

    parafia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parafie.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan: Mapped[str] = mapped_column(
        String(20), nullable=False, default=Plan.TRIAL, index=True
    )
    aktywna: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    okres_probny: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    data_rozpoczecia: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    data_zakonczenia: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    anulowana_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Kto aktywował (admin platformy lub proboszcz dla triala)
    aktywowana_przez: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uzytkownicy.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Limity zapisane przy tworzeniu (snapshot planu)
    limit_uzytkownikow: Mapped[int | None] = mapped_column(Integer, nullable=True)
    limit_intencji_miesiac: Mapped[int | None] = mapped_column(Integer, nullable=True)
    limit_dokumentow: Mapped[int | None] = mapped_column(Integer, nullable=True)
    limit_ai_zapytan_miesiac: Mapped[int | None] = mapped_column(Integer, nullable=True)
