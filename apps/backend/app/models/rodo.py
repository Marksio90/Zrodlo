import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AkceptacjaUmowy(Base, UUIDMixin, TimestampMixin):
    """Ślad audytowy akceptacji Umowy Powierzenia Danych (art. 28 RODO).

    Jedna parafia może mieć wiele rekordów — każda wersja umowy i każde
    ponowne zaakceptowanie tworzy nowy wpis.
    """

    __tablename__ = "akceptacje_umowy_rodo"

    parafia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parafie.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    zaakceptowana_przez: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uzytkownicy.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    wersja: Mapped[str] = mapped_column(String(20), nullable=False)
    zaakceptowano_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ip_adres: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
