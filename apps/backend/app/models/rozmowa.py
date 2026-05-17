import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Rozmowa(Base):
    __tablename__ = "rozmowy"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uzytkownik_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uzytkownicy.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tytul: Mapped[str] = mapped_column(String(200), nullable=False, default="Nowa rozmowa")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    wiadomosci: Mapped[list["WiadomoscRozmowy"]] = relationship(
        "WiadomoscRozmowy", back_populates="rozmowa", cascade="all, delete-orphan", order_by="WiadomoscRozmowy.created_at"
    )


class WiadomoscRozmowy(Base):
    __tablename__ = "wiadomosci_rozmowy"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rozmowa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rozmowy.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rola: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" | "assistant"
    tresc: Mapped[str] = mapped_column(Text, nullable=False)
    model_uzyty: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zrodla: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tokens_uzyte: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rozmowa: Mapped["Rozmowa"] = relationship("Rozmowa", back_populates="wiadomosci")
