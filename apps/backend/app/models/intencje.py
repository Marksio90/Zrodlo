import uuid
from datetime import date, datetime, time
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class TypIntencji(StrEnum):
    ZA_ZMARLEGO = "za_zmarlego"
    ZA_ZYJACEGO = "za_zyjacego"
    DZIEKCZYNNA = "dziekczynna"
    DZIEKCZYNNO_BLOGALNA = "dziekczynno_blogalna"
    ROCZNICA_SLUBU = "rocznica_slubu"
    W_CHOROBIE = "w_chorobie"
    WYPOMINKOWA = "wypominkowa"
    INNA = "inna"


class TypMszy(StrEnum):
    NIEDZIELNA = "niedzielna"
    POWSZEDNIA = "powszednia"
    POGRZEBOWA = "pogrzebowa"
    SLUBNA = "slubna"
    ZADUSZNA = "zaduszna"
    OKOLICZNOSCIOWA = "okolicznosciowa"


class Liturgia(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "liturgie"

    parafia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parafie.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tworca_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uzytkownicy.id", ondelete="SET NULL"), nullable=True
    )
    data: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    godzina: Mapped[time] = mapped_column(Time, nullable=False)
    typ: Mapped[str] = mapped_column(String(50), nullable=False, default=TypMszy.POWSZEDNIA)
    miejsce: Mapped[str] = mapped_column(String(200), nullable=False, default="Kościół parafialny")
    uwagi: Mapped[str | None] = mapped_column(Text, nullable=True)

    intencje: Mapped[list["Intencja"]] = relationship(
        "Intencja", back_populates="liturgia", cascade="all, delete-orphan"
    )
    tworca: Mapped["Uzytkownik | None"] = relationship(
        "Uzytkownik", foreign_keys=[tworca_id]
    )


class Intencja(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "intencje"

    parafia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parafie.id", ondelete="SET NULL"), nullable=True, index=True
    )
    liturgia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("liturgie.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tworca_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uzytkownicy.id", ondelete="SET NULL"), nullable=True
    )
    ofiarodawca_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parafianie.id", ondelete="SET NULL"), nullable=True, index=True
    )
    potwierdzone_przez_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uzytkownicy.id", ondelete="SET NULL"), nullable=True
    )
    typ: Mapped[str] = mapped_column(String(50), nullable=False, default=TypIntencji.INNA, index=True)
    tresc: Mapped[str] = mapped_column(Text, nullable=False)
    ofiarodawca: Mapped[str | None] = mapped_column(String(200), nullable=True)
    kwota: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    potwierdzona: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    data_potwierdzenia: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notatka_wewnetrzna: Mapped[str | None] = mapped_column(Text, nullable=True)

    liturgia: Mapped["Liturgia | None"] = relationship("Liturgia", back_populates="intencje")
    tworca: Mapped["Uzytkownik | None"] = relationship(
        "Uzytkownik", foreign_keys=[tworca_id]
    )
    potwierdzone_przez: Mapped["Uzytkownik | None"] = relationship(
        "Uzytkownik", foreign_keys=[potwierdzone_przez_id]
    )
    ofiarodawca_profil: Mapped["Parafianin | None"] = relationship(
        "Parafianin", foreign_keys=[ofiarodawca_id]
    )


from app.models.uzytkownicy import Parafianin, Uzytkownik  # noqa: E402, F401
