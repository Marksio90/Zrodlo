import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Wydarzenie(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wydarzenia"

    tytul: Mapped[str] = mapped_column(String(300), nullable=False)
    opis: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_od: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    data_do: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    miejsce: Mapped[str | None] = mapped_column(String(300), nullable=True)
    wspolnota_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wspolnoty.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    cykliczne: Mapped[bool] = mapped_column(default=False, nullable=False)
    cykl_opis: Mapped[str | None] = mapped_column(String(100), nullable=True)
    kolor: Mapped[str] = mapped_column(String(7), nullable=False, default="#3B82F6")

    wspolnota: Mapped["Wspolnota | None"] = relationship("Wspolnota")


# Avoid circular import
from app.models.wspolnoty import Wspolnota  # noqa: E402, F401
