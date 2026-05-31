"""Śledzenie i kalkulacja kosztów wywołań OpenAI."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_UP

import structlog

from app.models.ai_uzycie import AiUzycie, TypAiUzycia

log = structlog.get_logger()

# Ceny w USD za 1 000 000 tokenów (na dzień 2025-06-01, OpenAI pricing)
# format: model → (cena_input, cena_output)
CENNIK_USD_PER_1M: dict[str, tuple[float, float]] = {
    "gpt-4o-mini":              (0.15,  0.60),
    "gpt-4o-mini-2024-07-18":   (0.15,  0.60),
    "gpt-4o":                   (2.50, 10.00),
    "gpt-4o-2024-11-20":        (2.50, 10.00),
    "text-embedding-3-small":   (0.02,  0.00),
    "text-embedding-3-large":   (0.13,  0.00),
    "text-embedding-ada-002":   (0.10,  0.00),
}

_DOMYSLNY_CENNIK = (1.00, 4.00)  # ostrożna wartość domyślna dla nieznanego modelu


def oblicz_koszt(model: str, tokeny_wejscie: int, tokeny_wyjscie: int) -> Decimal:
    """Oblicza koszt wywołania w USD na podstawie modelu i liczby tokenów."""
    cena_in, cena_out = CENNIK_USD_PER_1M.get(model, _DOMYSLNY_CENNIK)
    koszt = (tokeny_wejscie * cena_in + tokeny_wyjscie * cena_out) / 1_000_000
    return Decimal(str(koszt)).quantize(Decimal("0.00000001"), rounding=ROUND_UP)


async def zapisz_uzycie(
    db,
    *,
    model: str,
    typ: str,
    tokeny_wejscie: int,
    tokeny_wyjscie: int,
    parafia_id: uuid.UUID | None = None,
    uzytkownik_id: uuid.UUID | None = None,
    czas_ms: int | None = None,
) -> AiUzycie:
    """Zapisuje wpis o użyciu AI do bazy. Błąd logowania nie przerywa żądania."""
    koszt = oblicz_koszt(model, tokeny_wejscie, tokeny_wyjscie)
    wpis = AiUzycie(
        parafia_id=parafia_id,
        uzytkownik_id=uzytkownik_id,
        model=model,
        typ=typ,
        tokeny_wejscie=tokeny_wejscie,
        tokeny_wyjscie=tokeny_wyjscie,
        koszt_usd=koszt,
        czas_ms=czas_ms,
        created_at=datetime.now(timezone.utc),
    )
    try:
        db.add(wpis)
        await db.flush()
    except Exception as exc:
        log.warning("ai_koszt_zapis_blad", error=str(exc))
    log.debug(
        "ai_uzycie",
        model=model, typ=typ,
        tokens_in=tokeny_wejscie, tokens_out=tokeny_wyjscie,
        koszt_usd=float(koszt),
    )
    return wpis
