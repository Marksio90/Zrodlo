"""Logika biznesowa subskrypcji – plany, limity, feature gating."""
from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.subskrypcja import Plan, Subskrypcja
from app.models.uzytkownicy import Uzytkownik


# ── Definicja limitów per plan ─────────────────────────────────────────────────

@dataclass(frozen=True)
class LimityPlanu:
    max_uzytkownikow: int | None      # None = brak limitu
    max_intencji_miesiac: int | None
    max_dokumentow: int | None
    max_ai_zapytan_miesiac: int | None

    # Feature flags
    ai_asystent: bool = False
    baza_wiedzy: bool = False
    komunikacja_masowa: bool = False
    dokumenty_ai: bool = False
    eksport_danych: bool = False
    api_integracje: bool = False

    # Metadane handlowe
    cena_miesiac_pln: int = 0
    nazwa: str = ""
    opis: str = ""


PLAN_LIMITY: dict[str, LimityPlanu] = {
    Plan.TRIAL: LimityPlanu(
        nazwa="Okres próbny",
        opis="30 dni bezpłatnie — pełna funkcjonalność planu Standard.",
        cena_miesiac_pln=0,
        max_uzytkownikow=5,
        max_intencji_miesiac=100,
        max_dokumentow=30,
        max_ai_zapytan_miesiac=30,
        ai_asystent=True,
        baza_wiedzy=True,
        komunikacja_masowa=False,
        dokumenty_ai=True,
        eksport_danych=False,
        api_integracje=False,
    ),
    Plan.PODSTAWOWY: LimityPlanu(
        nazwa="Podstawowy",
        opis="Kalendarz, intencje, dokumenty, ewidencja wiernych.",
        cena_miesiac_pln=49,
        max_uzytkownikow=10,
        max_intencji_miesiac=300,
        max_dokumentow=200,
        max_ai_zapytan_miesiac=0,
        ai_asystent=False,
        baza_wiedzy=False,
        komunikacja_masowa=False,
        dokumenty_ai=False,
        eksport_danych=True,
        api_integracje=False,
    ),
    Plan.STANDARD: LimityPlanu(
        nazwa="Standard",
        opis="Wszystko z Podstawowego + asystent AI, baza wiedzy, komunikacja masowa.",
        cena_miesiac_pln=99,
        max_uzytkownikow=30,
        max_intencji_miesiac=None,
        max_dokumentow=None,
        max_ai_zapytan_miesiac=300,
        ai_asystent=True,
        baza_wiedzy=True,
        komunikacja_masowa=True,
        dokumenty_ai=True,
        eksport_danych=True,
        api_integracje=False,
    ),
    Plan.PREMIUM: LimityPlanu(
        nazwa="Premium",
        opis="Wszystko bez limitów + integracje API + priorytetowe wsparcie.",
        cena_miesiac_pln=199,
        max_uzytkownikow=None,
        max_intencji_miesiac=None,
        max_dokumentow=None,
        max_ai_zapytan_miesiac=None,
        ai_asystent=True,
        baza_wiedzy=True,
        komunikacja_masowa=True,
        dokumenty_ai=True,
        eksport_danych=True,
        api_integracje=True,
    ),
}


# ── Pomocnicze ─────────────────────────────────────────────────────────────────

async def pobierz_aktywna_subskrypcje(
    db: AsyncSession, parafia_id
) -> Subskrypcja | None:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Subskrypcja)
        .where(
            Subskrypcja.parafia_id == parafia_id,
            Subskrypcja.aktywna.is_(True),
            Subskrypcja.anulowana_at.is_(None),
        )
        .order_by(Subskrypcja.data_rozpoczecia.desc())
        .limit(1)
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        return None
    # Automatyczne wygasanie
    if sub.data_zakonczenia and sub.data_zakonczenia < now:
        sub.aktywna = False
        await db.commit()
        return None
    return sub


def limity_dla_planu(plan: str) -> LimityPlanu:
    return PLAN_LIMITY.get(plan, PLAN_LIMITY[Plan.TRIAL])


# ── FastAPI dependency factory ─────────────────────────────────────────────────

def wymagaj_planu(funkcja: str):
    """Factory dependency – wymaga aktywnej subskrypcji z dostępem do danej funkcji.

    Przykład użycia w routerze:
        @router.post("/ai/chat", dependencies=[Depends(wymagaj_planu("ai_asystent"))])

    Zwraca 402 Payment Required jeśli brak subskrypcji lub plan nie obejmuje funkcji.
    """

    async def _check(
        db: AsyncSession = Depends(get_db),
        current_user: Uzytkownik = Depends(get_current_user),
    ) -> Subskrypcja:
        # Admin platformy omija sprawdzenie
        if current_user.rola == "admin" and not current_user.parafia_id:
            return None

        if not current_user.parafia_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Konto nie jest przypisane do parafii",
            )

        sub = await pobierz_aktywna_subskrypcje(db, current_user.parafia_id)
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Brak aktywnej subskrypcji. Aktywuj plan lub okres próbny.",
            )

        limity = limity_dla_planu(sub.plan)
        if not getattr(limity, funkcja, False):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(
                    f"Funkcja '{funkcja}' niedostępna w planie {sub.plan.upper()}. "
                    f"Przejdź na wyższy plan."
                ),
            )

        return sub

    return _check
