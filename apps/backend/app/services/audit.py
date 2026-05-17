"""Serwis audit log – zapisuje każdą zmianę danych."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog, OperacjaAudit


async def zapisz(
    db: AsyncSession,
    *,
    tabela: str,
    rekord_id: str | uuid.UUID,
    operacja: OperacjaAudit,
    uzytkownik_id: str | uuid.UUID | None = None,
    parafia_id: str | uuid.UUID | None = None,
    stare_wartosci: dict[str, Any] | None = None,
    nowe_wartosci: dict[str, Any] | None = None,
    ip_adres: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    log = AuditLog(
        tabela=tabela,
        rekord_id=str(rekord_id),
        operacja=operacja,
        uzytkownik_id=str(uzytkownik_id) if uzytkownik_id else None,
        parafia_id=str(parafia_id) if parafia_id else None,
        stare_wartosci=stare_wartosci,
        nowe_wartosci=nowe_wartosci,
        ip_adres=ip_adres,
        user_agent=user_agent,
    )
    db.add(log)
    return log


def serializable(obj: Any) -> Any:
    """Konwertuje typy nieseriazalizowalne do JSON-owych odpowiedników."""
    import uuid
    from datetime import date, datetime
    from decimal import Decimal

    if isinstance(obj, (uuid.UUID,)):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serializable(i) for i in obj]
    return obj


def snapshot(model_instance: Any, exclude: set[str] | None = None) -> dict[str, Any]:
    """Tworzy serializowalny snapshot rekordu do audit logu."""
    _exclude = exclude or {"haslo_hash"}
    data = {}
    for col in model_instance.__table__.columns:
        if col.name in _exclude:
            continue
        data[col.name] = serializable(getattr(model_instance, col.name, None))
    return data
