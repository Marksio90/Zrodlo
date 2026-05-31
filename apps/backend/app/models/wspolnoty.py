import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Wspolnota(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "wspolnoty"
    __table_args__ = (UniqueConstraint("parafia_id", "nazwa", name="uq_wspolnoty_parafia_nazwa"),)

    parafia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parafie.id", ondelete="CASCADE"), nullable=True, index=True
    )
    nazwa: Mapped[str] = mapped_column(String(200), nullable=False)
    opis: Mapped[str | None] = mapped_column(Text, nullable=True)
    opiekun: Mapped[str | None] = mapped_column(String(200), nullable=True)
    kontakt_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    kontakt_telefon: Mapped[str | None] = mapped_column(String(30), nullable=True)
    aktywna: Mapped[bool] = mapped_column(default=True, nullable=False)

    czlonkowie: Mapped[list["CzlonekWspolnoty"]] = relationship(
        "CzlonekWspolnoty", back_populates="wspolnota", cascade="all, delete-orphan"
    )


class CzlonekWspolnoty(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "czlonkowie_wspolnot"

    wspolnota_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wspolnoty.id", ondelete="CASCADE"), nullable=False, index=True
    )
    imie: Mapped[str] = mapped_column(String(100), nullable=False)
    nazwisko: Mapped[str] = mapped_column(String(100), nullable=False)
    telefon: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rola: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aktywny: Mapped[bool] = mapped_column(default=True, nullable=False)

    wspolnota: Mapped["Wspolnota"] = relationship("Wspolnota", back_populates="czlonkowie")
