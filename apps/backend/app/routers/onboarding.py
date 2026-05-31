"""Router onboardingu – status konfiguracji parafii po rejestracji."""
from sqlalchemy import select

from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser, DB
from app.models.rodo import AkceptacjaUmowy
from app.models.uzytkownicy import Uzytkownik
from app.models.parafia import Parafia
from app.schemas.onboarding import KrokOnboarding, OnboardingStatus
from app.schemas.rodo import AKTUALNA_WERSJA
from app.services.subskrypcja import pobierz_aktywna_subskrypcje

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

_DEFINICJE_KROKOW = [
    ("dane_parafii",     "Dane parafii",             "Uzupełnij kontakt i dane administracyjne"),
    ("rodo",             "Umowa RODO",                "Zaakceptuj Umowę Powierzenia Danych (art. 28 RODO)"),
    ("subskrypcja",      "Plan i subskrypcja",        "Aktywuj 30-dniowy bezpłatny okres próbny"),
    ("pierwsze_konto",   "Zaproś współpracownika",    "Dodaj wikariusza lub sekretarkę do systemu"),
]


@router.get("/status", response_model=OnboardingStatus, summary="Status onboardingu parafii")
async def get_status(current_user: CurrentUser, db: DB):
    """Oblicza dynamicznie które kroki onboardingu zostały ukończone.

    Nie wymaga oddzielnej tabeli – sprawdza stan w istniejących tabelach:
    - dane_parafii:   parafia.email is not None
    - rodo:           akceptacje_umowy_rodo dla aktualnej wersji
    - subskrypcja:    aktywna subskrypcja
    - pierwsze_konto: ≥ 2 aktywnych użytkowników w parafii
    """
    if not current_user.parafia_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Konto nie jest przypisane do parafii",
        )

    parafia_id = current_user.parafia_id

    # Krok 1: dane parafii
    parafia = await db.get(Parafia, parafia_id)
    dane_ok = parafia is not None and bool(parafia.email and parafia.telefon)

    # Krok 2: RODO
    rodo_result = await db.execute(
        select(AkceptacjaUmowy)
        .where(
            AkceptacjaUmowy.parafia_id == parafia_id,
            AkceptacjaUmowy.wersja == AKTUALNA_WERSJA,
        )
        .limit(1)
    )
    rodo_ok = rodo_result.scalar_one_or_none() is not None

    # Krok 3: subskrypcja
    sub = await pobierz_aktywna_subskrypcje(db, parafia_id)
    sub_ok = sub is not None

    # Krok 4: pierwsze konto (≥ 2 aktywnych userów)
    users_result = await db.execute(
        select(Uzytkownik).where(
            Uzytkownik.parafia_id == parafia_id,
            Uzytkownik.aktywny.is_(True),
            Uzytkownik.deleted_at.is_(None),
        )
    )
    konto_ok = len(users_result.scalars().all()) >= 2

    wartosci = [dane_ok, rodo_ok, sub_ok, konto_ok]
    kroki = [
        KrokOnboarding(id=id_, tytul=tytul, opis=opis, ukonczone=val)
        for (id_, tytul, opis), val in zip(_DEFINICJE_KROKOW, wartosci)
    ]

    return OnboardingStatus(
        parafia_id=parafia_id,
        gotowy=all(wartosci),
        ukonczone_kroki=sum(wartosci),
        wszystkich_krokow=len(kroki),
        kroki=kroki,
    )
