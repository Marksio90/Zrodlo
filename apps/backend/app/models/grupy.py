import uuid
from datetime import date
from enum import StrEnum

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class TypGrupy(StrEnum):
    WSPOLNOTA = "wspolnota"
    SCHOLA = "schola"
    MINISTRANTURIA = "ministranturia"
    CARITAS = "caritas"
    ROZA_ROZANCOWA = "roza_rozancowa"
    TERCJARZE = "tercjarze"
    MLODZIE = "mlodzie"
    INNE = "inne"


class RolaWGrupie(StrEnum):
    LIDER = "lider"
    CZLONEK = "czlonek"
    KANDYDAT = "kandydat"


class GrupaParafialna(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Grupy i wspólnoty parafialne. Zastępuje i rozszerza model Wspolnota.
    Wspolnota pozostaje dla kompatybilności wstecznej.
    """

    __tablename__ = "grupy_parafialne"

    parafia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parafie.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    nazwa: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    opis: Mapped[str | None] = mapped_column(Text, nullable=True)
    typ: Mapped[str] = mapped_column(
        String(50), nullable=False, default=TypGrupy.WSPOLNOTA, index=True
    )
    opiekun_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uzytkownicy.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    kontakt_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    kontakt_telefon: Mapped[str | None] = mapped_column(String(30), nullable=True)
    aktywna: Mapped[bool] = mapped_column(default=True, nullable=False)

    czlonkowie: Mapped[list["CzlonekGrupy"]] = relationship(
        "CzlonekGrupy", back_populates="grupa", cascade="all, delete-orphan"
    )
    opiekun: Mapped["Uzytkownik | None"] = relationship(
        "Uzytkownik", foreign_keys=[opiekun_id]
    )


class CzlonekGrupy(Base, UUIDMixin, TimestampMixin):
    """Przynależność parafianina do grupy parafialnej."""

    __tablename__ = "czlonkowie_grup"

    grupa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grupy_parafialne.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parafianin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parafianie.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rola: Mapped[str] = mapped_column(
        String(30), nullable=False, default=RolaWGrupie.CZLONEK
    )
    data_dolaczenia: Mapped[date | None] = mapped_column(Date, nullable=True)
    aktywny: Mapped[bool] = mapped_column(default=True, nullable=False)

    grupa: Mapped["GrupaParafialna"] = relationship("GrupaParafialna", back_populates="czlonkowie")
    parafianin: Mapped["Parafianin"] = relationship("Parafianin")


from app.models.uzytkownicy import Parafianin, Uzytkownik  # noqa: E402, F401
