"""Demo seeder – generuje realistyczne dane parafialne do prezentacji systemu Źródło.

Uruchomienie: POST /demo/seed (wymaga roli ADMIN lub PROBOSZCZ).
Idempotentny – jeśli parafia już istnieje, zwraca {"status": "already_seeded"}.
"""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dokumenty import Dokument, StatusDokumentu, TypDokumentu
from app.models.intencje import Intencja, Liturgia, TypIntencji, TypMszy
from app.models.kalendarz import Wydarzenie
from app.models.ogloszenia import Ogloszenie, PriorytetOgloszenia, StatusOgloszenia
from app.models.parafia import Parafia
from app.models.powiadomienia import Powiadomienie, TypPowiadomienia
from app.models.uzytkownicy import (
    Parafianin,
    Proboszcz,
    RolaUzytkownika,
    Uzytkownik,
    Wikariusz,
)
from app.models.wiedza import KategoriaWiedzy, NotatkaWiedzy
from app.models.wspolnoty import CzlonekWspolnoty, Wspolnota
from app.services.auth import hash_password

# ---------------------------------------------------------------------------
# Stałe
# ---------------------------------------------------------------------------

PARAFIA_NAZWA = "Parafia pw. Wniebowzięcia NMP w Krakowie"
DEMO_PASSWORD = "Demo1234!"

# Dane osobowe – Polskie imiona i nazwiska
IMIONA_MESKIE = [
    "Adam", "Andrzej", "Bartłomiej", "Bogdan", "Czesław", "Damian", "Dariusz",
    "Edmund", "Filip", "Grzegorz", "Henryk", "Jacek", "Jakub", "Jan", "Józef",
    "Kamil", "Krzysztof", "Leszek", "Łukasz", "Marek", "Mariusz", "Michał",
    "Mirosław", "Paweł", "Piotr", "Rafał", "Robert", "Roman", "Sławomir",
    "Stanisław", "Stefan", "Szymon", "Tadeusz", "Tomasz", "Waldemar", "Witold",
    "Wojciech", "Zbigniew", "Zdzisław", "Zenon",
]
IMIONA_ZENSKIE = [
    "Agnieszka", "Aleksandra", "Alicja", "Anna", "Barbara", "Beata", "Bożena",
    "Celina", "Danuta", "Dorota", "Edyta", "Elżbieta", "Ewa", "Grażyna",
    "Halina", "Irena", "Iwona", "Jadwiga", "Joanna", "Jolanta", "Julia",
    "Justyna", "Katarzyna", "Krystyna", "Lidia", "Lucyna", "Magdalena",
    "Małgorzata", "Maria", "Marta", "Monika", "Natalia", "Olga", "Renata",
    "Róża", "Sylwia", "Teresa", "Urszula", "Wanda", "Zofia",
]
NAZWISKA = [
    "Adamczyk", "Andrzejewski", "Brzezińska", "Chmielewski", "Czarnecka",
    "Dąbrowski", "Dudek", "Górska", "Jabłońska", "Jaworski", "Kamińska",
    "Kołodziej", "Kowalska", "Kowalski", "Kozłowski", "Krajewski", "Laskowski",
    "Lewandowski", "Malinowski", "Mazur", "Michalska", "Michalski", "Nowak",
    "Nowakowski", "Nowicki", "Olszewski", "Pietrzak", "Piotrowska", "Piotrowski",
    "Sikora", "Sobieraj", "Stępień", "Szymański", "Szymańska", "Tomaszewski",
    "Wiśniewski", "Wojtyla", "Wróbel", "Wróblewski", "Zając", "Zawadzki",
    "Ziółkowski", "Zielińska", "Zielński", "Żak",
]

ULICE_KRAKOW = [
    "ul. Floriańska", "ul. Grodzka", "ul. Kanonicza", "ul. Karmelicka",
    "ul. Długa", "ul. Szeroka", "ul. Basztowa", "ul. Sławkowska",
    "ul. Sw. Anny", "ul. Bracka", "ul. Mikołajska", "ul. Szewska",
    "ul. Piłsudskiego", "al. Krasińskiego", "ul. Dietla", "ul. Starowiślna",
    "ul. Westerplatte", "ul. Wielopole", "ul. Sienna", "ul. Poselska",
    "ul. Krakowska", "ul. Mostowa", "ul. Józefa", "ul. Estery",
    "ul. Meiselsa", "ul. Berka Joselewicza", "ul. Dajwór",
    "ul. Miodowa", "ul. Brzozowa", "ul. Augustiańska",
]


def _rng() -> random.Random:
    return random.Random(42)


def _dt(d: date, h: int = 9, m: int = 0) -> datetime:
    """Tworzy datetime ze strefą UTC."""
    return datetime(d.year, d.month, d.day, h, m, tzinfo=timezone.utc)


def _backdate(rng: random.Random, start: date, end: date) -> datetime:
    """Losowa data w przedziale [start, end]."""
    delta = (end - start).days
    chosen = start + timedelta(days=rng.randint(0, delta))
    return _dt(chosen, rng.randint(7, 20), rng.randint(0, 59))


def _set_timestamps(obj: object, created: datetime, updated: datetime | None = None) -> None:
    """Ustawia created_at i updated_at z pominięciem server_default."""
    obj.created_at = created  # type: ignore[attr-defined]
    obj.updated_at = updated or created  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Główna funkcja
# ---------------------------------------------------------------------------


async def seed_demo(db: AsyncSession) -> dict:
    """Wypełnia bazę danych demo danymi parafii. Idempotentna."""
    rng = _rng()

    # Sprawdź idempotentność
    result = await db.execute(select(Parafia).where(Parafia.nazwa == PARAFIA_NAZWA))
    if result.scalar_one_or_none():
        return {"status": "already_seeded"}

    try:
        stats: dict[str, int] = {}

        # ------------------------------------------------------------------ #
        # 1. Parafia                                                           #
        # ------------------------------------------------------------------ #
        parafia = Parafia(
            nazwa=PARAFIA_NAZWA,
            wezwanie="Wniebowzięcia Najświętszej Maryi Panny",
            adres="ul. Mariacka 5",
            miasto="Kraków",
            kod_pocztowy="31-042",
            diecezja="Archidiecezja Krakowska",
            dekanat="Dekanat Śródmiejski",
            email="parafia@nmp-krakow.pl",
            telefon="+48 12 422 00 21",
            strona_www="www.nmp-krakow.pl",
            data_erygowania=date(1226, 6, 4),
            aktywna=True,
        )
        _set_timestamps(parafia, datetime(2025, 8, 20, 10, 0, tzinfo=timezone.utc))
        db.add(parafia)
        await db.flush()
        stats["parafia"] = 1

        # ------------------------------------------------------------------ #
        # 2. Admin – zaktualizuj istniejącego admina                          #
        # ------------------------------------------------------------------ #
        admin_result = await db.execute(
            select(Uzytkownik).where(Uzytkownik.email == "admin@zrodlo.pl")
        )
        admin = admin_result.scalar_one_or_none()
        if admin:
            admin.parafia_id = parafia.id

        # ------------------------------------------------------------------ #
        # 3. Konta pracowników kościoła                                        #
        # ------------------------------------------------------------------ #
        hashed = hash_password(DEMO_PASSWORD)

        # Proboszcz
        proboszcz_user = Uzytkownik(
            email="proboszcz@nmp-krakow.pl",
            haslo_hash=hashed,
            imie="Tomasz",
            nazwisko="Marek",
            rola=RolaUzytkownika.PROBOSZCZ,
            parafia_id=parafia.id,
            aktywny=True,
        )
        _set_timestamps(proboszcz_user, datetime(2025, 8, 25, 9, 0, tzinfo=timezone.utc))
        db.add(proboszcz_user)
        await db.flush()

        proboszcz_profil = Proboszcz(
            uzytkownik_id=proboszcz_user.id,
            parafia_id=parafia.id,
            numer_dekretu="DEK/2019/145",
            data_nominacji=date(2019, 9, 1),
        )
        _set_timestamps(proboszcz_profil, datetime(2025, 8, 25, 9, 5, tzinfo=timezone.utc))
        db.add(proboszcz_profil)

        # Wikariusz 1
        wiki1_user = Uzytkownik(
            email="wikariusz1@nmp-krakow.pl",
            haslo_hash=hashed,
            imie="Piotr",
            nazwisko="Nowak",
            rola=RolaUzytkownika.WIKARIUSZ,
            parafia_id=parafia.id,
            aktywny=True,
        )
        _set_timestamps(wiki1_user, datetime(2025, 8, 26, 10, 0, tzinfo=timezone.utc))
        db.add(wiki1_user)
        await db.flush()

        wiki1_profil = Wikariusz(
            uzytkownik_id=wiki1_user.id,
            parafia_id=parafia.id,
            specjalizacja="Duszpasterstwo młodzieży",
            data_nominacji=date(2022, 8, 15),
        )
        _set_timestamps(wiki1_profil, datetime(2025, 8, 26, 10, 5, tzinfo=timezone.utc))
        db.add(wiki1_profil)

        # Wikariusz 2
        wiki2_user = Uzytkownik(
            email="wikariusz2@nmp-krakow.pl",
            haslo_hash=hashed,
            imie="Marcin",
            nazwisko="Wiśniewski",
            rola=RolaUzytkownika.WIKARIUSZ,
            parafia_id=parafia.id,
            aktywny=True,
        )
        _set_timestamps(wiki2_user, datetime(2025, 8, 27, 10, 0, tzinfo=timezone.utc))
        db.add(wiki2_user)
        await db.flush()

        wiki2_profil = Wikariusz(
            uzytkownik_id=wiki2_user.id,
            parafia_id=parafia.id,
            specjalizacja="Katecheza i liturgia",
            data_nominacji=date(2023, 6, 1),
        )
        _set_timestamps(wiki2_profil, datetime(2025, 8, 27, 10, 5, tzinfo=timezone.utc))
        db.add(wiki2_profil)
        await db.flush()
        stats["staff_users"] = 3

        # ------------------------------------------------------------------ #
        # 4. Parafianie (300 rekordów)                                         #
        # ------------------------------------------------------------------ #
        parafianie_list: list[Parafianin] = []
        uwagi_opcje = [
            "organista", "lektor", "ministrant", "nadzwyczajny szafarz",
            "członek Rady Parafialnej", "chorystka – schola", "katechetka",
            "animator grup młodzieżowych", "wolontariusz Caritas",
            "zakrystianin", "kościelny", "opiekun Żywego Różańca",
        ]

        seed_start = date(2025, 9, 1)
        seed_end = date(2026, 5, 17)

        for i in range(300):
            is_male = rng.random() < 0.48
            imie = rng.choice(IMIONA_MESKIE if is_male else IMIONA_ZENSKIE)
            nazwisko = rng.choice(NAZWISKA)
            numer = f"2025/{(i + 1):03d}"

            has_adres = rng.random() < 0.7
            has_telefon = rng.random() < 0.55
            has_email_p = rng.random() < 0.4
            has_birth = rng.random() < 0.65
            has_chrzest = rng.random() < 0.5
            has_uwagi = rng.random() < 0.15

            adres_str = None
            if has_adres:
                ulica = rng.choice(ULICE_KRAKOW)
                nr = rng.randint(1, 80)
                adres_str = f"{ulica} {nr}, 31-{rng.randint(100, 999):03d} Kraków"

            telefon_str = None
            if has_telefon:
                telefon_str = f"+48 {rng.randint(500, 799):03d} {rng.randint(100, 999):03d} {rng.randint(100, 999):03d}"

            email_str = None
            if has_email_p:
                imie_lower = imie.lower().replace("ą", "a").replace("ę", "e").replace(
                    "ó", "o").replace("ś", "s").replace("ł", "l").replace(
                    "ż", "z").replace("ź", "z").replace("ć", "c").replace("ń", "n")
                nazwisko_lower = nazwisko.lower().replace("ą", "a").replace("ę", "e").replace(
                    "ó", "o").replace("ś", "s").replace("ł", "l").replace(
                    "ż", "z").replace("ź", "z").replace("ć", "c").replace("ń", "n").replace(
                    "ź", "z")
                domains = ["gmail.com", "wp.pl", "onet.pl", "interia.pl", "poczta.fm"]
                email_str = f"{imie_lower}.{nazwisko_lower}{rng.randint(1, 99)}@{rng.choice(domains)}"

            birth_date = None
            if has_birth:
                birth_year = rng.randint(1935, 2008)
                birth_month = rng.randint(1, 12)
                birth_day = rng.randint(1, 28)
                birth_date = date(birth_year, birth_month, birth_day)

            chrzest_date = None
            if has_chrzest and birth_date:
                chrzest_date = birth_date + timedelta(days=rng.randint(14, 90))

            uwagi_str = None
            if has_uwagi:
                uwagi_str = rng.choice(uwagi_opcje)

            p = Parafianin(
                parafia_id=parafia.id,
                imie=imie,
                nazwisko=nazwisko,
                numer_parafialny=numer,
                adres=adres_str,
                telefon=telefon_str,
                email=email_str,
                data_urodzenia=birth_date,
                data_chrztu=chrzest_date,
                uwagi=uwagi_str,
            )
            created = _backdate(rng, seed_start, seed_end)
            _set_timestamps(p, created)
            db.add(p)
            parafianie_list.append(p)

        await db.flush()
        stats["parafianie"] = 300

        # ------------------------------------------------------------------ #
        # 5. Liturgie + Intencje                                              #
        # ------------------------------------------------------------------ #
        today = date(2026, 5, 17)
        liturgia_start = date(2025, 9, 1)
        liturgia_end = date(2026, 6, 30)

        # Specjalne daty
        special_dates = {
            date(2025, 11, 1): ("Uroczystość Wszystkich Świętych", TypMszy.OKOLICZNOSCIOWA),
            date(2025, 11, 2): ("Wspomnienie Wszystkich Wiernych Zmarłych", TypMszy.ZADUSZNA),
            date(2025, 12, 8): ("Niepokalane Poczęcie NMP", TypMszy.OKOLICZNOSCIOWA),
            date(2025, 12, 25): ("Boże Narodzenie – Dzień I", TypMszy.OKOLICZNOSCIOWA),
            date(2025, 12, 26): ("Boże Narodzenie – Dzień II", TypMszy.OKOLICZNOSCIOWA),
            date(2026, 1, 1): ("Uroczystość Świętej Bożej Rodzicielki", TypMszy.OKOLICZNOSCIOWA),
            date(2026, 4, 5): ("Niedziela Palmowa", TypMszy.NIEDZIELNA),
            date(2026, 4, 9): ("Wielki Czwartek", TypMszy.OKOLICZNOSCIOWA),
            date(2026, 4, 10): ("Wielki Piątek – Liturgia Męki Pańskiej", TypMszy.OKOLICZNOSCIOWA),
            date(2026, 4, 12): ("Niedziela Wielkanocna", TypMszy.OKOLICZNOSCIOWA),
            date(2026, 6, 4): ("Uroczystość Wniebowstąpienia Pańskiego", TypMszy.OKOLICZNOSCIOWA),
            date(2026, 6, 11): ("Zesłanie Ducha Świętego", TypMszy.OKOLICZNOSCIOWA),
        }

        # Teksty intencji
        intencja_templates = [
            (TypIntencji.ZA_ZMARLEGO, "Za + {imie} {nazwisko} w {n}. rocznicę śmierci"),
            (TypIntencji.ZA_ZMARLEGO, "Za spokój duszy śp. {imie} {nazwisko}"),
            (TypIntencji.ZA_ZMARLEGO, "Za wszystkich zmarłych z rodziny {nazwisko}"),
            (TypIntencji.ZA_ZYJACEGO, "Za zdrowie i Boże błogosławieństwo dla {imie} z okazji urodzin"),
            (TypIntencji.ZA_ZYJACEGO, "Za {imie} {nazwisko} w intencji pomyślności i łaski Bożej"),
            (TypIntencji.ZA_ZYJACEGO, "Za zdrowie dzieci i wnuków rodziny {nazwisko}"),
            (TypIntencji.DZIEKCZYNNA, "Dziękczynna za pomyślnie zdane egzaminy przez {imie}"),
            (TypIntencji.DZIEKCZYNNA, "Dziękczynna za szczęśliwy poród i zdrowie matki {imie} {nazwisko}"),
            (TypIntencji.DZIEKCZYNNA, "Dziękczynna za 50 lat kapłaństwa ks. {imie}"),
            (TypIntencji.ROCZNICA_SLUBU, "W {n}. rocznicę ślubu Państwa {nazwisko}"),
            (TypIntencji.ROCZNICA_SLUBU, "Z okazji {n}. rocznicy małżeństwa {imie} i Marii {nazwisko}"),
            (TypIntencji.W_CHOROBIE, "Za chorą {imie} {nazwisko} o powrót do zdrowia"),
            (TypIntencji.W_CHOROBIE, "W intencji wyzdrowienia {imie} {nazwisko} po operacji"),
            (TypIntencji.WYPOMINKOWA, "Wypominkowa za wszystkich zmarłych z rodziny {nazwisko}"),
            (TypIntencji.WYPOMINKOWA, "Za dusze czyśćcowe – wypominek za śp. {imie} {nazwisko}"),
            (TypIntencji.DZIEKCZYNNO_BLOGALNA, "Dziękczynno-błagalna za rodzinę {nazwisko} i jej pomyślność"),
            (TypIntencji.INNA, "W intencji nawrócenia {imie}"),
            (TypIntencji.INNA, "Za żołnierzy Wojska Polskiego i wszystkich obrońców Ojczyzny"),
        ]

        liturgie_added = 0
        intencje_added = 0
        current = liturgia_start

        # Spis celebransów
        tworca_ids = [proboszcz_user.id, wiki1_user.id, wiki2_user.id]

        while current <= liturgia_end:
            weekday = current.weekday()  # 0=Mon … 6=Sun
            is_sunday = weekday == 6
            is_special = current in special_dates

            masses_today: list[tuple[time, str]] = []

            if is_special:
                special_name, special_typ = special_dates[current]
                masses_today.append((time(7, 0), TypMszy.POWSZEDNIA))
                masses_today.append((time(11, 0), special_typ))
                if is_sunday:
                    masses_today.append((time(10, 0), TypMszy.NIEDZIELNA))
                    masses_today.append((time(12, 0), TypMszy.NIEDZIELNA))
            elif is_sunday:
                masses_today = [
                    (time(8, 0), TypMszy.NIEDZIELNA),
                    (time(10, 0), TypMszy.NIEDZIELNA),
                    (time(12, 0), TypMszy.NIEDZIELNA),
                ]
            else:
                masses_today.append((time(7, 0), TypMszy.POWSZEDNIA))
                if weekday in (1, 3, 4):  # wt, czw, pt
                    masses_today.append((time(18, 0), TypMszy.POWSZEDNIA))

            for godzina, typ in masses_today:
                liturgia = Liturgia(
                    parafia_id=parafia.id,
                    tworca_id=rng.choice(tworca_ids),
                    data=current,
                    godzina=godzina,
                    typ=typ,
                    miejsce="Kościół parafialny",
                )
                created_lit = _dt(current - timedelta(days=rng.randint(1, 14)))
                _set_timestamps(liturgia, created_lit)
                db.add(liturgia)
                await db.flush()
                liturgie_added += 1

                # Intencje do liturgii
                n_intencji = rng.randint(1, 3)
                for _ in range(n_intencji):
                    typ_int, tmpl = rng.choice(intencja_templates)
                    imie_r = rng.choice(IMIONA_MESKIE + IMIONA_ZENSKIE)
                    nazwisko_r = rng.choice(NAZWISKA)
                    n_val = rng.randint(1, 50)
                    tresc = tmpl.format(imie=imie_r, nazwisko=nazwisko_r, n=n_val)

                    is_past = current < today
                    potwierdzona = is_past and (rng.random() < 0.70)
                    kwota = None
                    if potwierdzona and rng.random() < 0.80:
                        kwota = Decimal(str(rng.randint(5, 15) * 10))  # 50-150

                    data_potw = None
                    if potwierdzona:
                        data_potw = _dt(current - timedelta(days=rng.randint(0, 3)))

                    ofiarodawca_obj = rng.choice(parafianie_list) if rng.random() < 0.6 else None

                    intencja = Intencja(
                        parafia_id=parafia.id,
                        liturgia_id=liturgia.id,
                        tworca_id=rng.choice(tworca_ids),
                        ofiarodawca_id=ofiarodawca_obj.id if ofiarodawca_obj else None,
                        ofiarodawca=f"{imie_r} {nazwisko_r}",
                        typ=typ_int,
                        tresc=tresc,
                        kwota=kwota,
                        potwierdzona=potwierdzona,
                        data_potwierdzenia=data_potw,
                        potwierdzone_przez_id=proboszcz_user.id if potwierdzona else None,
                    )
                    created_int = _dt(current - timedelta(days=rng.randint(1, 30)))
                    _set_timestamps(intencja, created_int)
                    db.add(intencja)
                    intencje_added += 1

            current += timedelta(days=1)

        await db.flush()
        stats["liturgie"] = liturgie_added
        stats["intencje"] = intencje_added

        # ------------------------------------------------------------------ #
        # 6. Dokumenty (25 rekordów)                                          #
        # ------------------------------------------------------------------ #
        dokument_defs = [
            # metryki chrztu (8)
            (TypDokumentu.METRYKA_CHRZTU, StatusDokumentu.WYDANY,
             "Metryka chrztu – Jan Kowalski", False,
             {"imie": "Jan", "nazwisko": "Kowalski", "data_chrztu": "2025-10-12", "rodzice": "Adam i Anna Kowalscy"},
             "Parafia pw. Wniebowzięcia NMP w Krakowie zaświadcza, że Jan Kowalski przyjął Sakrament Chrztu Świętego w dniu 12 października 2025 roku."),
            (TypDokumentu.METRYKA_CHRZTU, StatusDokumentu.WYDANY,
             "Metryka chrztu – Maria Nowak", False,
             {"imie": "Maria", "nazwisko": "Nowak", "data_chrztu": "2025-11-02", "rodzice": "Piotr i Katarzyna Nowakowie"},
             None),
            (TypDokumentu.METRYKA_CHRZTU, StatusDokumentu.ZATWIERDZONY,
             "Metryka chrztu – Tomasz Wiśniewski", False,
             {"imie": "Tomasz", "nazwisko": "Wiśniewski", "data_chrztu": "2026-01-19", "rodzice": "Marcin i Ewa Wiśniewscy"},
             None),
            (TypDokumentu.METRYKA_CHRZTU, StatusDokumentu.ZATWIERDZONY,
             "Metryka chrztu – Zofia Dąbrowska", False,
             {"imie": "Zofia", "nazwisko": "Dąbrowska", "data_chrztu": "2026-02-08", "rodzice": "Grzegorz i Barbara Dąbrowscy"},
             None),
            (TypDokumentu.METRYKA_CHRZTU, StatusDokumentu.WYDANY,
             "Metryka chrztu – Paweł Lewandowski", False,
             {"imie": "Paweł", "nazwisko": "Lewandowski", "data_chrztu": "2025-12-07", "rodzice": "Krzysztof i Joanna Lewandowscy"},
             None),
            (TypDokumentu.METRYKA_CHRZTU, StatusDokumentu.WYDANY,
             "Metryka chrztu – Anna Mazur", False,
             {"imie": "Anna", "nazwisko": "Mazur", "data_chrztu": "2026-03-15", "rodzice": "Wojciech i Agnieszka Mazurowie"},
             None),
            (TypDokumentu.METRYKA_CHRZTU, StatusDokumentu.DO_ZATWIERDZENIA,
             "Metryka chrztu – Piotr Zając", False,
             {"imie": "Piotr", "nazwisko": "Zając", "data_chrztu": "2026-04-26", "rodzice": "Tomasz i Marta Zającowie"},
             None),
            (TypDokumentu.METRYKA_CHRZTU, StatusDokumentu.DO_ZATWIERDZENIA,
             "Metryka chrztu – Julia Sikora", False,
             {"imie": "Julia", "nazwisko": "Sikora", "data_chrztu": "2026-05-10", "rodzice": "Robert i Monika Sikorowie"},
             None),
            # metryki ślubu (4)
            (TypDokumentu.METRYKA_SLUBU, StatusDokumentu.WYDANY,
             "Metryka ślubu – Andrzejewski / Kamińska", False,
             {"maz": "Andrzejewski Jakub", "zona": "Kamińska Aleksandra", "data_slubu": "2025-09-20"},
             "Parafia pw. Wniebowzięcia NMP w Krakowie zaświadcza, że w dniu 20 września 2025 roku został zawarty Sakrament Małżeństwa."),
            (TypDokumentu.METRYKA_SLUBU, StatusDokumentu.WYDANY,
             "Metryka ślubu – Mazur / Wróbel", False,
             {"maz": "Mazur Stanisław", "zona": "Wróbel Katarzyna", "data_slubu": "2025-10-04"},
             None),
            (TypDokumentu.METRYKA_SLUBU, StatusDokumentu.ZATWIERDZONY,
             "Metryka ślubu – Kowalski / Piotrowska", False,
             {"maz": "Kowalski Michał", "zona": "Piotrowska Natalia", "data_slubu": "2026-04-18"},
             None),
            (TypDokumentu.METRYKA_SLUBU, StatusDokumentu.DO_ZATWIERDZENIA,
             "Metryka ślubu – Jabłoński / Górecka", False,
             {"maz": "Jabłoński Rafał", "zona": "Górecka Izabela", "data_slubu": "2026-06-13"},
             None),
            # zaświadczenia bierzmowania (3)
            (TypDokumentu.ZASWIADCZENIE_BIERZMOWANIA, StatusDokumentu.WYDANY,
             "Zaświadczenie bierzmowania – Paweł Kołodziej", False,
             {"imie": "Paweł", "nazwisko": "Kołodziej", "data_bierzmowania": "2025-10-18", "imie_bierzmowania": "Franciszek"},
             None),
            (TypDokumentu.ZASWIADCZENIE_BIERZMOWANIA, StatusDokumentu.WYDANY,
             "Zaświadczenie bierzmowania – Karolina Zielińska", False,
             {"imie": "Karolina", "nazwisko": "Zielińska", "data_bierzmowania": "2025-10-18", "imie_bierzmowania": "Teresa"},
             None),
            (TypDokumentu.ZASWIADCZENIE_BIERZMOWANIA, StatusDokumentu.ZATWIERDZONY,
             "Zaświadczenie bierzmowania – Bartosz Michalski", False,
             {"imie": "Bartosz", "nazwisko": "Michalski", "data_bierzmowania": "2025-10-18", "imie_bierzmowania": "Jan"},
             None),
            # zaświadczenia komunii (3)
            (TypDokumentu.ZASWIADCZENIE_KOMUNII, StatusDokumentu.WYDANY,
             "Zaświadczenie I Komunii – Zofia Nowak", False,
             {"imie": "Zofia", "nazwisko": "Nowak", "data_komunii": "2025-05-18"},
             None),
            (TypDokumentu.ZASWIADCZENIE_KOMUNII, StatusDokumentu.WYDANY,
             "Zaświadczenie I Komunii – Adam Wróbel", False,
             {"imie": "Adam", "nazwisko": "Wróbel", "data_komunii": "2025-05-18"},
             None),
            (TypDokumentu.ZASWIADCZENIE_KOMUNII, StatusDokumentu.ZATWIERDZONY,
             "Zaświadczenie I Komunii – Marta Szymańska", False,
             {"imie": "Marta", "nazwisko": "Szymańska", "data_komunii": "2026-05-24"},
             None),
            # zaświadczenia do ślubu (2)
            (TypDokumentu.ZASWIADCZENIE_DO_SLUBU, StatusDokumentu.ZATWIERDZONY,
             "Zaświadczenie do ślubu – Tomasz Czarnecki", False,
             {"imie": "Tomasz", "nazwisko": "Czarnecki", "planowana_data_slubu": "2026-06-13"},
             "Niniejszym zaświadczam, że wymieniony jest wolny od przeszkód kanonicznych do zawarcia sakramentu małżeństwa."),
            (TypDokumentu.ZASWIADCZENIE_DO_SLUBU, StatusDokumentu.DO_ZATWIERDZENIA,
             "Zaświadczenie do ślubu – Karolina Dąbrowska", False,
             {"imie": "Karolina", "nazwisko": "Dąbrowska", "planowana_data_slubu": "2026-08-22"},
             None),
            # odpisy zgonu (2)
            (TypDokumentu.ODPIS_ZGONU, StatusDokumentu.WYDANY,
             "Odpis zgonu – Józef Wiśniewski", False,
             {"imie": "Józef", "nazwisko": "Wiśniewski", "data_zgonu": "2025-11-14"},
             None),
            (TypDokumentu.ODPIS_ZGONU, StatusDokumentu.WYDANY,
             "Odpis zgonu – Helena Kowalczyk", False,
             {"imie": "Helena", "nazwisko": "Kowalczyk", "data_zgonu": "2026-01-28"},
             None),
            # pisma ogólne (2)
            (TypDokumentu.PISMO_OGOLNE, StatusDokumentu.ZATWIERDZONY,
             "Pismo w sprawie remontu dachu – do Kurii", False,
             {"adresat": "Kuria Metropolitalna w Krakowie", "temat": "Remont dachu kościoła"},
             "Zwracam się z uprzejmą prośbą o wyrażenie zgody na przeprowadzenie prac remontowych dachu głównej nawy kościoła."),
            (TypDokumentu.PISMO_OGOLNE, StatusDokumentu.DO_ZATWIERDZENIA,
             "Pismo w sprawie organizacji pielgrzymki 2026", False,
             {"adresat": "Parafianie", "temat": "Pielgrzymka do Częstochowy 2026"},
             None),
            # homilia (1, AI)
            (TypDokumentu.HOMILIA, StatusDokumentu.ZATWIERDZONY,
             "Homilia na Niedzielę Zmartwychwstania 2026 (AI)", True,
             {"data": "2026-04-12", "czytania": ["Dz 10,34a.37-43", "Kol 3,1-4", "J 20,1-9"]},
             "Bracia i Siostry! Zmartwychwstanie Chrystusa to nie tylko fakt historyczny – to wydarzenie, które nieustannie przemienia nasze serca. Pusty grób, który zobaczył Jan w ten poranny czas, jest zaproszeniem do głębokiej wiary. Nie chodzi o widzenie, ale o wierzenie. Chrystus Zmartwychwstały mówi do każdego z nas: nie lękaj się! Jak Maria Magdalena pobiegła zwiastować Dobrą Nowinę, tak i my jesteśmy posłani, by czynić z naszego życia świadectwo Bożej miłości. Alleluja!"),
        ]

        for (
            typ_dok, status_dok, tytul_dok, ai_dok, dane_dok, tresc_dok
        ) in dokument_defs:
            offset_days = rng.randint(0, (today - seed_start).days)
            dok_date = seed_start + timedelta(days=offset_days)
            dok_created = _dt(dok_date, rng.randint(8, 16))

            data_zatw = None
            zatw_przez = None
            if status_dok in (StatusDokumentu.ZATWIERDZONY, StatusDokumentu.WYDANY):
                data_zatw = dok_created + timedelta(hours=rng.randint(1, 48))
                zatw_przez = "ks. Tomasz Marek"

            dok = Dokument(
                parafia_id=parafia.id,
                tworca_id=rng.choice(tworca_ids),
                parafianin_id=rng.choice(parafianie_list).id if rng.random() < 0.6 else None,
                zatwierdzone_przez_id=proboszcz_user.id if data_zatw else None,
                typ=typ_dok,
                status=status_dok,
                tytul=tytul_dok,
                dane=dane_dok,
                tresc=tresc_dok,
                wygenerowane_przez_ai=ai_dok,
                data_zatwierdzenia=data_zatw,
                zatwierdzone_przez=zatw_przez,
            )
            _set_timestamps(dok, dok_created, dok_created + timedelta(hours=1))
            db.add(dok)

        await db.flush()
        stats["dokumenty"] = len(dokument_defs)

        # ------------------------------------------------------------------ #
        # 7. Wspólnoty + członkowie                                           #
        # ------------------------------------------------------------------ #
        wspolnoty_defs = [
            {
                "nazwa": "Schola parafialna",
                "opis": "Schola liturgiczna śpiewająca podczas Mszy Świętych niedzielnych i uroczystości. Próby w każdy czwartek o godz. 18:00.",
                "opiekun": "ks. Marcin Wiśniewski",
                "kontakt_email": "schola@nmp-krakow.pl",
                "n": 30,
            },
            {
                "nazwa": "Żywy Różaniec",
                "opis": "Wspólnota modlitewna odmawiająca różaniec. Podzielona na 20 kółek różańcowych. Spotkania w pierwsze soboty miesiąca.",
                "opiekun": "Maria Kowalska",
                "kontakt_email": "rozaniec@nmp-krakow.pl",
                "n": 25,
            },
            {
                "nazwa": "Ministranci",
                "opis": "Służba liturgiczna przy ołtarzu. Spotkania formacyjne co dwa tygodnie w niedzielę po Mszy o 12:00.",
                "opiekun": "ks. Piotr Nowak",
                "kontakt_email": "ministranci@nmp-krakow.pl",
                "n": 20,
            },
            {
                "nazwa": "Caritas parafialna",
                "opis": "Parafialna gałąź Caritas zajmująca się pomocą ubogim, zbiórkami żywności i odwiedzinami chorych.",
                "opiekun": "Anna Dąbrowska",
                "kontakt_email": "caritas@nmp-krakow.pl",
                "n": 15,
            },
            {
                "nazwa": "Krąg Biblijny",
                "opis": "Cotygodniowe spotkania z Pismem Świętym – lectio divina, dzielenie się refleksją, modlitwa. Środy o 19:00.",
                "opiekun": "ks. Tomasz Marek",
                "kontakt_email": "biblia@nmp-krakow.pl",
                "n": 12,
            },
            {
                "nazwa": "Ruch Światło-Życie (Oaza)",
                "opis": "Wspólnota oazowa – formacja młodzieży i rodzin przez rekolekcje, spotkania i służbę liturgiczną.",
                "opiekun": "ks. Piotr Nowak",
                "kontakt_email": "oaza@nmp-krakow.pl",
                "n": 18,
            },
        ]

        role_czlonka = ["lider", "sekretarz", "skarbnik", "katecheta", "animator", None, None, None]

        for wdef in wspolnoty_defs:
            wsp = Wspolnota(
                nazwa=wdef["nazwa"],
                opis=wdef["opis"],
                opiekun=wdef["opiekun"],
                kontakt_email=wdef.get("kontakt_email"),
                aktywna=True,
            )
            w_created = _backdate(rng, seed_start, date(2025, 10, 1))
            _set_timestamps(wsp, w_created)
            db.add(wsp)
            await db.flush()

            for j in range(wdef["n"]):
                is_male_m = rng.random() < 0.5
                c = CzlonekWspolnoty(
                    wspolnota_id=wsp.id,
                    imie=rng.choice(IMIONA_MESKIE if is_male_m else IMIONA_ZENSKIE),
                    nazwisko=rng.choice(NAZWISKA),
                    telefon=f"+48 {rng.randint(500,799):03d} {rng.randint(100,999):03d} {rng.randint(100,999):03d}" if rng.random() < 0.5 else None,
                    email=None,
                    rola=rng.choice(role_czlonka),
                    aktywny=True,
                )
                c_created = _backdate(rng, seed_start, seed_end)
                _set_timestamps(c, c_created)
                db.add(c)

        await db.flush()
        stats["wspolnoty"] = len(wspolnoty_defs)

        # ------------------------------------------------------------------ #
        # 8. Kalendarz / Wydarzenie (35 wydarzeń)                             #
        # ------------------------------------------------------------------ #
        events_defs: list[dict] = [
            # Przeszłe
            {
                "tytul": "Dożynki Parafialne",
                "opis": "Uroczyste dziękczynienie za plony. Msza Święta o godz. 11:00, następnie procesja i festyn parafialny na placu kościelnym.",
                "data_od": datetime(2025, 9, 7, 11, 0, tzinfo=timezone.utc),
                "data_do": datetime(2025, 9, 7, 16, 0, tzinfo=timezone.utc),
                "miejsce": "Plac przy kościele NMP",
                "kolor": "#F97316",
            },
            {
                "tytul": "Spotkanie Rady Parafialnej – październik",
                "opis": "Miesięczne spotkanie Rady Parafialnej. Omówienie planu remontowego i budżetu na rok 2026.",
                "data_od": datetime(2025, 10, 6, 19, 0, tzinfo=timezone.utc),
                "data_do": datetime(2025, 10, 6, 21, 0, tzinfo=timezone.utc),
                "miejsce": "Sala parafialna",
                "kolor": "#6B7280",
            },
            {
                "tytul": "Nabożeństwo Fatimskie – październik",
                "opis": "Nabożeństwo fatimskie z procesją różańcową wokół kościoła.",
                "data_od": datetime(2025, 10, 13, 18, 30, tzinfo=timezone.utc),
                "data_do": datetime(2025, 10, 13, 20, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#3B82F6",
            },
            {
                "tytul": "Adoracja Najświętszego Sakramentu",
                "opis": "Całodzienna adoracja Najświętszego Sakramentu w pierwszy piątek miesiąca.",
                "data_od": datetime(2025, 10, 3, 8, 0, tzinfo=timezone.utc),
                "data_do": datetime(2025, 10, 3, 20, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#3B82F6",
                "cykliczne": True,
                "cykl_opis": "Pierwszy piątek miesiąca",
            },
            {
                "tytul": "Różaniec – październik (cykl dzienny)",
                "opis": "Codzienne nabożeństwo różańcowe w październiku o godz. 17:30.",
                "data_od": datetime(2025, 10, 1, 17, 30, tzinfo=timezone.utc),
                "data_do": datetime(2025, 10, 31, 18, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#3B82F6",
                "cykliczne": True,
                "cykl_opis": "Codziennie w październiku",
            },
            {
                "tytul": "Msza za Ojczyznę – Święto Niepodległości",
                "opis": "Msza Święta w intencji Ojczyzny z okazji 107. rocznicy odzyskania niepodległości.",
                "data_od": datetime(2025, 11, 11, 11, 0, tzinfo=timezone.utc),
                "data_do": datetime(2025, 11, 11, 12, 30, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#EF4444",
            },
            {
                "tytul": "Wszystkich Świętych – procesja na cmentarz",
                "opis": "Uroczysta procesja z kościoła na cmentarz Rakowicki. Msza Święta przy grobach poległych.",
                "data_od": datetime(2025, 11, 1, 14, 0, tzinfo=timezone.utc),
                "data_do": datetime(2025, 11, 1, 16, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół → Cmentarz Rakowicki",
                "kolor": "#8B5CF6",
            },
            {
                "tytul": "Spotkanie ministrantów",
                "opis": "Spotkanie formacyjne ministrantów – liturgia adwentowa.",
                "data_od": datetime(2025, 11, 16, 16, 0, tzinfo=timezone.utc),
                "data_do": datetime(2025, 11, 16, 18, 0, tzinfo=timezone.utc),
                "miejsce": "Sala parafialna",
                "kolor": "#10B981",
                "cykliczne": True,
                "cykl_opis": "Co dwa tygodnie",
            },
            {
                "tytul": "Spotkanie Rady Parafialnej – listopad",
                "opis": "Miesięczne spotkanie Rady Parafialnej. Omówienie kalendarza adwentowego.",
                "data_od": datetime(2025, 11, 3, 19, 0, tzinfo=timezone.utc),
                "data_do": datetime(2025, 11, 3, 21, 0, tzinfo=timezone.utc),
                "miejsce": "Sala parafialna",
                "kolor": "#6B7280",
            },
            {
                "tytul": "Rekolekcje Adwentowe",
                "opis": "Trzydniowe rekolekcje adwentowe prowadzone przez o. Michała Krzyżanowskiego OP. Temat: 'Czuwajcie, bo nie wiecie dnia ani godziny'.",
                "data_od": datetime(2025, 12, 8, 18, 0, tzinfo=timezone.utc),
                "data_do": datetime(2025, 12, 10, 21, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#8B5CF6",
            },
            {
                "tytul": "Spotkanie Rady Parafialnej – grudzień",
                "opis": "Ostatnie w roku spotkanie Rady Parafialnej. Podsumowanie roku i plan na 2026.",
                "data_od": datetime(2025, 12, 1, 19, 0, tzinfo=timezone.utc),
                "data_do": datetime(2025, 12, 1, 21, 0, tzinfo=timezone.utc),
                "miejsce": "Sala parafialna",
                "kolor": "#6B7280",
            },
            {
                "tytul": "Kolęda – rejon I (Stare Miasto)",
                "opis": "Wizyta duszpasterska Kolęda w rejonie I – ulice Floriańska, Sławkowska, Długa.",
                "data_od": datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 1, 5, 18, 0, tzinfo=timezone.utc),
                "miejsce": "Rejon ul. Floriańska i okolice",
                "kolor": "#F59E0B",
            },
            {
                "tytul": "Kolęda – rejon II (Kazimierz)",
                "opis": "Wizyta duszpasterska Kolęda w rejonie II – ulice Szeroka, Józefa, Miodowa.",
                "data_od": datetime(2026, 1, 12, 9, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 1, 12, 18, 0, tzinfo=timezone.utc),
                "miejsce": "Rejon ul. Szeroka i okolice",
                "kolor": "#F59E0B",
            },
            {
                "tytul": "Kolęda – rejon III (Wawel i okolice)",
                "opis": "Wizyta duszpasterska Kolęda w rejonie III – ulice Grodzka, Kanonicza, Poselska.",
                "data_od": datetime(2026, 1, 19, 9, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 1, 19, 18, 0, tzinfo=timezone.utc),
                "miejsce": "Rejon ul. Grodzka i okolice",
                "kolor": "#F59E0B",
            },
            {
                "tytul": "Spotkanie Rady Parafialnej – styczeń",
                "opis": "Spotkanie Rady Parafialnej. Podsumowanie kolędy i plan na I kwartał 2026.",
                "data_od": datetime(2026, 1, 26, 19, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 1, 26, 21, 0, tzinfo=timezone.utc),
                "miejsce": "Sala parafialna",
                "kolor": "#6B7280",
            },
            {
                "tytul": "Nabożeństwo Fatimskie – październik 2025",
                "opis": "Nabożeństwo fatimskie – ostatnie w sezonie 2025.",
                "data_od": datetime(2025, 10, 13, 18, 30, tzinfo=timezone.utc),
                "data_do": datetime(2025, 10, 13, 20, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#3B82F6",
            },
            {
                "tytul": "Rekolekcje Wielkopostne",
                "opis": "Trzydniowe rekolekcje wielkopostne prowadzone przez ks. Adama Bonieckiego MIC. Temat: 'Nawróćcie się i wierzcie w Ewangelię'.",
                "data_od": datetime(2026, 3, 9, 18, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 3, 11, 21, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#8B5CF6",
            },
            {
                "tytul": "Droga Krzyżowa – I piątek Wielkiego Postu",
                "opis": "Nabożeństwo Drogi Krzyżowej z rozważaniami.",
                "data_od": datetime(2026, 2, 20, 17, 30, tzinfo=timezone.utc),
                "data_do": datetime(2026, 2, 20, 19, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#8B5CF6",
                "cykliczne": True,
                "cykl_opis": "Piątki Wielkiego Postu",
            },
            {
                "tytul": "Droga Krzyżowa – II piątek Wielkiego Postu",
                "opis": "Nabożeństwo Drogi Krzyżowej z rozważaniami dla dzieci przygotowujących się do Komunii.",
                "data_od": datetime(2026, 2, 27, 17, 30, tzinfo=timezone.utc),
                "data_do": datetime(2026, 2, 27, 19, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#8B5CF6",
            },
            {
                "tytul": "Spotkanie Rady Parafialnej – marzec",
                "opis": "Spotkanie Rady Parafialnej. Omówienie przygotowań do Triduum Paschalnego.",
                "data_od": datetime(2026, 3, 2, 19, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 3, 2, 21, 0, tzinfo=timezone.utc),
                "miejsce": "Sala parafialna",
                "kolor": "#6B7280",
            },
            {
                "tytul": "Adoracja Najświętszego Sakramentu – kwiecień",
                "opis": "Całodzienna adoracja Najświętszego Sakramentu w pierwszy piątek miesiąca.",
                "data_od": datetime(2026, 4, 3, 8, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 4, 3, 20, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#3B82F6",
            },
            {
                "tytul": "Spotkanie Rady Parafialnej – kwiecień",
                "opis": "Spotkanie Rady Parafialnej. Plan na maj – Pierwsza Komunia i Bierzmowanie.",
                "data_od": datetime(2026, 4, 13, 19, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 4, 13, 21, 0, tzinfo=timezone.utc),
                "miejsce": "Sala parafialna",
                "kolor": "#6B7280",
            },
            # Przyszłe
            {
                "tytul": "Pierwsza Komunia Święta",
                "opis": "Uroczysta Msza Święta z udzieleniem Pierwszej Komunii Świętej. Dzieci z klasy III szkoły podstawowej nr 5 i nr 12.",
                "data_od": datetime(2026, 5, 24, 11, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 5, 24, 13, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#8B5CF6",
            },
            {
                "tytul": "Nabożeństwo Fatimskie – maj 2026",
                "opis": "Pierwsze nabożeństwo fatimskie w sezonie 2026. Procesja różańcowa.",
                "data_od": datetime(2026, 5, 13, 18, 30, tzinfo=timezone.utc),
                "data_do": datetime(2026, 5, 13, 20, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#3B82F6",
            },
            {
                "tytul": "Adoracja Najświętszego Sakramentu – maj",
                "opis": "Całodzienna adoracja w pierwszy piątek maja.",
                "data_od": datetime(2026, 5, 1, 8, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 5, 1, 20, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#3B82F6",
            },
            {
                "tytul": "Spotkanie Rady Parafialnej – maj",
                "opis": "Spotkanie Rady Parafialnej. Finalizacja przygotowań do Bierzmowania i Festynu Parafialnego.",
                "data_od": datetime(2026, 5, 25, 19, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 5, 25, 21, 0, tzinfo=timezone.utc),
                "miejsce": "Sala parafialna",
                "kolor": "#6B7280",
            },
            {
                "tytul": "Bierzmowanie",
                "opis": "Udzielenie Sakramentu Bierzmowania przez Arcybiskupa Krakowskiego. Kandydaci z klas 8 i szkół ponadpodstawowych.",
                "data_od": datetime(2026, 6, 6, 11, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 6, 6, 13, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#EF4444",
            },
            {
                "tytul": "Boże Ciało – procesja",
                "opis": "Uroczysta procesja Bożego Ciała ulicami Starego Miasta. Cztery ołtarze przy: Rynku Głównym, ul. Grodzkiej, pl. Wszystkich Świętych i kościele.",
                "data_od": datetime(2026, 6, 4, 10, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 6, 4, 13, 0, tzinfo=timezone.utc),
                "miejsce": "Trasa procesji – Stare Miasto",
                "kolor": "#EF4444",
            },
            {
                "tytul": "Festyn Parafialny",
                "opis": "Coroczny festyn parafialny z kiermaszem, lotterią fantową, występami scholii i atrakcjami dla dzieci. Dochód na remont dachu.",
                "data_od": datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc),
                "miejsce": "Plac przy kościele NMP",
                "kolor": "#F97316",
            },
            {
                "tytul": "Wakacyjny obóz ministrantów",
                "opis": "Tygodniowy obóz formacyjno-wypoczynkowy ministrantów w Zakopanem. Liczba miejsc: 25.",
                "data_od": datetime(2026, 7, 13, 8, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 7, 19, 20, 0, tzinfo=timezone.utc),
                "miejsce": "Zakopane",
                "kolor": "#10B981",
            },
            {
                "tytul": "Pielgrzymka do Częstochowy",
                "opis": "Piesza pielgrzymka z Krakowa na Jasną Górę. Zapis w kancelarii parafialnej do 15 lipca 2026.",
                "data_od": datetime(2026, 8, 6, 5, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 8, 14, 20, 0, tzinfo=timezone.utc),
                "miejsce": "Trasa Kraków – Częstochowa",
                "kolor": "#EF4444",
            },
            {
                "tytul": "Nabożeństwo Fatimskie – czerwiec",
                "opis": "Nabożeństwo fatimskie z procesją.",
                "data_od": datetime(2026, 6, 13, 18, 30, tzinfo=timezone.utc),
                "data_do": datetime(2026, 6, 13, 20, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#3B82F6",
            },
            {
                "tytul": "Spotkanie ministrantów – czerwiec",
                "opis": "Spotkanie formacyjne ministrantów – przygotowanie do obozu.",
                "data_od": datetime(2026, 6, 21, 16, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 6, 21, 18, 0, tzinfo=timezone.utc),
                "miejsce": "Sala parafialna",
                "kolor": "#10B981",
            },
            {
                "tytul": "Adoracja Najświętszego Sakramentu – czerwiec",
                "opis": "Całodzienna adoracja w pierwszy piątek czerwca.",
                "data_od": datetime(2026, 6, 5, 8, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 6, 5, 20, 0, tzinfo=timezone.utc),
                "miejsce": "Kościół parafialny",
                "kolor": "#3B82F6",
            },
            {
                "tytul": "Dożynki Parafialne 2026",
                "opis": "Uroczyste dziękczynienie za plony. Msza Święta, procesja i piknik parafialny.",
                "data_od": datetime(2026, 9, 6, 11, 0, tzinfo=timezone.utc),
                "data_do": datetime(2026, 9, 6, 17, 0, tzinfo=timezone.utc),
                "miejsce": "Plac przy kościele NMP",
                "kolor": "#F97316",
            },
        ]

        for edef in events_defs:
            e = Wydarzenie(
                parafia_id=parafia.id,
                tworca_id=rng.choice(tworca_ids),
                tytul=edef["tytul"],
                opis=edef.get("opis"),
                data_od=edef["data_od"],
                data_do=edef.get("data_do"),
                miejsce=edef.get("miejsce"),
                kolor=edef.get("kolor", "#3B82F6"),
                cykliczne=edef.get("cykliczne", False),
                cykl_opis=edef.get("cykl_opis"),
            )
            e_created = edef["data_od"] - timedelta(days=rng.randint(3, 21))
            if e_created.tzinfo is None:
                e_created = e_created.replace(tzinfo=timezone.utc)
            _set_timestamps(e, e_created)
            db.add(e)

        await db.flush()
        stats["wydarzenia"] = len(events_defs)

        # ------------------------------------------------------------------ #
        # 9. Notatki wiedzy (20 notatek)                                      #
        # ------------------------------------------------------------------ #
        notatki_defs = [
            # Historia
            (
                "Historia kościoła pw. Wniebowzięcia NMP w Krakowie",
                KategoriaWiedzy.HISTORIA_PARAFII,
                True,
                ["historia", "kościół", "NMP"],
                "Kościół Wniebowzięcia Najświętszej Maryi Panny, zwany Kościołem Mariackim, jest jednym z najważniejszych zabytków Krakowa i Małopolski. Erygowany w 1226 roku z inicjatywy biskupa Iwona Odrowąża, pełni od stuleci rolę głównego kościoła miejskiego. W prezbiterium mieści się słynny ołtarz Wita Stwosza z 1489 roku – największy gotycki ołtarz drewniany na świecie.",
            ),
            (
                "Konsekracja kościoła w 1226 roku",
                KategoriaWiedzy.HISTORIA_PARAFII,
                True,
                ["historia", "konsekracja", "1226"],
                "Pierwotny kościół na obecnym miejscu istniał już w XII wieku. Nowa, gotycka świątynia została konsekrowana 4 czerwca 1226 roku przez biskupa krakowskiego. W XIV wieku kościół był wielokrotnie rozbudowywany – obecna forma pochodzi głównie z XV wieku.",
            ),
            (
                "Remont głównej nawy w 2015 roku",
                KategoriaWiedzy.HISTORIA_PARAFII,
                False,
                ["remont", "nawa", "2015"],
                "W roku 2015 przeprowadzono gruntowny remont głównej nawy kościoła. Prace objęły konserwację polichromii Jana Matejki (1889-1891), renowację posadzki oraz modernizację systemu ogrzewania podłogowego. Łączny koszt remontu wyniósł 2,4 mln PLN, z czego 60% pokryło Ministerstwo Kultury i Dziedzictwa Narodowego.",
            ),
            # Liturgia
            (
                "Godziny Mszy Świętych",
                KategoriaWiedzy.LITURGIA,
                True,
                ["msze", "godziny", "plan"],
                "NIEDZIELE I ŚWIĘTA:\n- 8:00 – Msza Święta (dla starszych i chorych)\n- 10:00 – Uroczysta Msza Święta z udziałem scholii\n- 12:00 – Msza Święta (suma)\n\nDNI POWSZEDNIE:\n- 7:00 – Msza Święta poranna\n- 18:00 – Msza Święta wieczorna (wtorek, czwartek, piątek)\n\nNABOŻEŃSTWA SZCZEGÓLNE:\n- Pierwsze piątki miesiąca: Adoracja od 8:00 do 20:00\n- Każda niedziela o 17:30: Nieszpory\n- Maj i październik: Różaniec codziennie o 17:30",
            ),
            (
                "Plan liturgii na Adwent 2025",
                KategoriaWiedzy.LITURGIA,
                False,
                ["adwent", "2025", "liturgia"],
                "Adwent 2025 rozpoczyna się 30 listopada. Plan nabożeństw:\n\n- Roraty: codziennie o 7:00 (z lampionami dla dzieci)\n- Rekolekcje Adwentowe: 8-10 grudnia (prowadzi o. M. Krzyżanowski OP)\n- Spowiedź adwentowa: 20-21 grudnia od 15:00 do 20:00\n- Pasterka: 24/25 grudnia o północy\n- Msza Bożonarodzeniowa: 25 XII o 8:00, 10:00, 12:00",
            ),
            (
                "Schola – repertuar na Boże Narodzenie",
                KategoriaWiedzy.LITURGIA,
                False,
                ["schola", "kolędy", "Boże Narodzenie"],
                "Planowany repertuar scholii na Boże Narodzenie 2025:\n\n1. Lulajże Jezuniu (arr. F. Chopin)\n2. Dzisiaj w Betlejem\n3. Gdy się Chrystus rodzi\n4. Bóg się rodzi (z organami)\n5. Wśród nocnej ciszy\n6. Cicha noc (wersja polska)\n7. Adeste Fideles (łacina)\n\nPróby: czwartki 18:00-20:00, od 1 listopada.",
            ),
            (
                "Zasady organizacji ślubu kościelnego",
                KategoriaWiedzy.LITURGIA,
                False,
                ["ślub", "sakrament", "małżeństwo"],
                "Narzeczeni planujący ślub kościelny powinni zgłosić się do kancelarii parafialnej co najmniej 3 miesiące przed planowaną datą. Wymagane dokumenty:\n- Metryki chrztu (nie starsze niż 6 miesięcy)\n- Zaświadczenie o bierzmowaniu\n- Dowody osobiste\n- Zaświadczenie z USC (jeśli ślub konkordatowy)\n- Zaświadczenie o ukończeniu kursu przedmałżeńskiego\n\nKurs przedmałżeński odbywa się w parafii w każdą sobotę o 9:00 (8 spotkań).",
            ),
            # Duszpasterstwo
            (
                "Pielgrzymka do Częstochowy 2025 – relacja",
                KategoriaWiedzy.DUSZPASTERSTWO,
                False,
                ["pielgrzymka", "Częstochowa", "2025"],
                "W dniach 6-14 sierpnia 2025 roku 47 parafian wzięło udział w pieszej pielgrzymce krakowskiej do Częstochowy. Pielgrzymi pokonali trasę 250 km w 9 dni. Hasło pielgrzymki: 'Maryjo, prowadź nas do Jezusa'. Kapłanem towarzyszącym był ks. Piotr Nowak. Pielgrzymi dotarli na Jasną Górę 14 sierpnia, w wigilię uroczystości Wniebowzięcia NMP.",
            ),
            (
                "Rekolekcje wielkopostne 2026 – uwagi i wnioski",
                KategoriaWiedzy.DUSZPASTERSTWO,
                False,
                ["rekolekcje", "Wielki Post", "2026"],
                "Rekolekcje wielkopostne 9-11 marca 2026 (ks. Adam Boniecki MIC). Frekwencja: śr. 180 osób/nabożeństwo. Spowiedź podczas rekolekcji: 85 osób. Wnioski na przyszłość: 1) Wcześniejsze ogłoszenie (min. 6 tygodni). 2) Lepsze nagłośnienie. 3) Rozważyć rekolekcje dla młodzieży osobno. Ocena ogólna: bardzo dobra.",
            ),
            (
                "Liczba wiernych na Mszy Niedzielnej – dane 2025-2026",
                KategoriaWiedzy.DUSZPASTERSTWO,
                False,
                ["frekwencja", "Msza", "statystyki"],
                "Szacunkowa liczba wiernych na Mszach Niedzielnych (2025-2026):\n\n- Msza 8:00: ok. 80-100 osób\n- Msza 10:00: ok. 250-300 osób (najliczniejsza)\n- Msza 12:00: ok. 180-220 osób\n\nRazem: ok. 510-620 osób tygodniowo.\nUroczystości (Boże Narodzenie, Wielkanoc): do 900 osób łącznie.",
            ),
            # Administracja
            (
                "Godziny kancelarii parafialnej",
                KategoriaWiedzy.ADMINISTRACJA,
                True,
                ["kancelaria", "godziny", "kontakt"],
                "GODZINY OTWARCIA KANCELARII:\n\n- Wtorek: 9:00 – 12:00 i 16:00 – 18:00\n- Czwartek: 9:00 – 12:00 i 16:00 – 18:00\n- Piątek: 9:00 – 12:00\n- Sobota: 9:00 – 11:00\n\nKancelaria zamknięta w poniedziałki i środy.\n\nKontakt: parafia@nmp-krakow.pl | +48 12 422 00 21",
            ),
            (
                "Kontakty do firm remontowych – lista zaufanych wykonawców",
                KategoriaWiedzy.ADMINISTRACJA,
                False,
                ["remont", "firmy", "kontakty"],
                "Lista sprawdzonych wykonawców remontowych (stan na 2025):\n\n1. RESTO Konserwacja Zabytków sp. z o.o. – tel. 604 123 456 – konserwacja polichromii i fresków\n2. Zakład Kamieniarski Kowalczyk – tel. 608 987 654 – prace kamieniarskie, nagrobki\n3. Elektro-Serwis Mazur – tel. 512 345 678 – instalacje elektryczne, certyfikat SEP\n4. Dach-Pro Kraków – tel. 693 456 789 – pokrycia dachowe, blacharstwo",
            ),
            (
                "Dane do deklaracji podatkowej 2025",
                KategoriaWiedzy.ADMINISTRACJA,
                False,
                ["podatki", "finanse", "2025"],
                "NIP parafii: 676-123-45-67\nREGON: 040012345\nNumer konta bankowego (PKO BP): 12 1020 2892 0000 5802 0590 1234\n\nOsoba odpowiedzialna za sprawy finansowe: ks. Tomasz Marek (proboszcz)\nBiuro rachunkowe: Rachmistrz sp. z o.o., ul. Szewska 12, Kraków, tel. 12 345 67 89",
            ),
            # Katecheza
            (
                "Program przygotowania do Bierzmowania 2026",
                KategoriaWiedzy.KATECHEZA,
                False,
                ["bierzmowanie", "katecheza", "2026"],
                "Kandydaci do Bierzmowania 2026 – liczba: 38 osób (klasy 8 i szkoły ponadpodstawowe).\n\nHarmonogram spotkań (co 2 tygodnie, wtorek 17:00):\n- Wrzesień 2025 – maj 2026: 18 spotkań grupowych\n- Rekolekcje bierzmowankowe: 27-29 marca 2026 (Dom Rekolekcyjny w Tyńcu)\n- Indywidualne rozmowy z księdzem: kwiecień-maj 2026\n- Data bierzmowania: 6 czerwca 2026 (udziela Arcybiskup Krakowski)\n\nKatecheta prowadzący: ks. Marcin Wiśniewski",
            ),
            (
                "Liczba dzieci przygotowujących się do I Komunii 2026",
                KategoriaWiedzy.KATECHEZA,
                False,
                ["komunia", "katecheza", "dzieci"],
                "I Komunia Święta 2026 – data: 24 maja 2026 (niedziela)\n\nLiczba dzieci: 42 (z SP nr 5 – 24 dzieci, SP nr 12 – 18 dzieci)\n\nKatecheza parafialna: soboty 9:00-10:00 (ks. Piotr Nowak)\nSpowiedź przygotowawcza: 16-17 maja 2026\nPróba do Komunii: 23 maja 2026 o 15:00\n\nRodzice proszeni o kontakt: wikariusz1@nmp-krakow.pl",
            ),
            # Prawo kanoniczne
            (
                "Wymagane dokumenty do ślubu kościelnego",
                KategoriaWiedzy.PRAWO_KANONICZNE,
                False,
                ["ślub", "dokumenty", "prawo kanoniczne"],
                "Dokumenty wymagane do zawarcia małżeństwa sakramentalnego:\n\n1. Metryka chrztu (wydana max. 6 miesięcy temu, z adnotacją o bierzmowaniu)\n2. Zaświadczenie o stanie wolnym (z parafii chrztu, jeśli inna)\n3. Dowody osobiste\n4. Zaświadczenie z USC o braku przeszkód (jeśli ślub konkordatowy)\n5. Świadectwo ukończenia kursu przedmałżeńskiego\n6. Zaświadczenie ze spotkań u duszpasterza (3 spotkania narzeczonych)\n\nKan. 1066-1072 KPK reguluje badanie kanoniczne narzeczonych.",
            ),
            (
                "Procedura udzielania dyspensy kanonicznej",
                KategoriaWiedzy.PRAWO_KANONICZNE,
                False,
                ["dyspensa", "prawo kanoniczne", "procedura"],
                "Dyspensa od przeszkód małżeńskich (kan. 1078 KPK):\n\nPrzeszkody dyspensowane przez biskupa diecezjalnego:\n- Pokrewieństwo w linii bocznej 3. stopnia (siostrzeniec/bratanek i stryjenka/ciotka)\n- Powinowactwo w linii prostej\n- Przyzwoitość publiczna w 1. stopniu linii prostej\n\nProcedura: złożenie pisemnej prośby do Kurii Metropolitalnej z uzasadnieniem. Czas oczekiwania: ok. 4-6 tygodni. Kontakt do Kurii: kuria@diecezja.pl",
            ),
            # Inne
            (
                "Telefony alarmowe i kontakty interwencyjne",
                KategoriaWiedzy.INNE,
                False,
                ["kontakty", "alarmy", "bezpieczeństwo"],
                "TELEFONY ALARMOWE:\n- Policja: 997\n- Straż pożarna: 998\n- Pogotowie: 999\n- Numer alarmowy: 112\n\nKONTAKTY PARAFIALNE:\n- Ksiądz dyżurny (tel. całodobowy): +48 602 111 222\n- Kancelaria: +48 12 422 00 21\n- Zakrystia: +48 12 422 00 22\n- Dom parafialny (portiernia): +48 12 422 00 23\n\nADRES DO KORESPONDENCJI:\nParafia pw. Wniebowzięcia NMP\nul. Mariacka 5\n31-042 Kraków",
            ),
            (
                "Lista organistów i kantorów",
                KategoriaWiedzy.INNE,
                False,
                ["organiści", "kantorzy", "muzyka"],
                "ORGANIŚCI PARAFII (2025-2026):\n\n1. Stanisław Kędzierski (organista główny) – niedziela 10:00 i 12:00, uroczystości\n   Tel: +48 605 123 456\n\n2. Jadwiga Mrózek (organistka zastępca) – niedziela 8:00, dni powszednie\n   Tel: +48 607 234 567\n\nKANTOR / PSAŁTERZYSTA:\n- Marek Rutkowski – prowadzi śpiew na Mszach powszednich\n  Tel: +48 601 345 678\n\nHonorarim za organy na ślub/pogrzeb: 400 PLN (do uzgodnienia).",
            ),
            (
                "Instrukcja obsługi systemu Źródło – skrót",
                KategoriaWiedzy.INNE,
                False,
                ["system", "instrukcja", "Źródło"],
                "System Źródło – podstawowe funkcje:\n\n1. INTENCJE: Dodaj → wypełnij formularz (typ, treść, data, ofiarodawca) → zatwierdź. Zatwierdzone intencje pojawią się w kalendarzu liturgii.\n\n2. DOKUMENTY: Nowy dokument → wybierz typ → wprowadź dane → wyślij do zatwierdzenia. Proboszcz zatwierdza w zakładce Dokumenty.\n\n3. OGŁOSZENIA: Nowe ogłoszenie → treść → ustaw datę publikacji → wyślij do zatwierdzenia.\n\n4. ASYSTENT AI: Zadaj pytanie w języku naturalnym – asystent korzysta z bazy wiedzy parafii.\n\nKontakt techniczny: admin@zrodlo.pl",
            ),
        ]

        for (tytul_n, kat_n, pub_n, tagi_n, tresc_n) in notatki_defs:
            n_date = _backdate(rng, seed_start, seed_end)
            nw = NotatkaWiedzy(
                parafia_id=parafia.id,
                tytul=tytul_n,
                tresc=tresc_n,
                kategoria=kat_n,
                tagi=tagi_n,
                publiczna=pub_n,
                tworca_id=proboszcz_user.id,
            )
            _set_timestamps(nw, n_date)
            db.add(nw)

        await db.flush()
        stats["notatki_wiedzy"] = len(notatki_defs)

        # ------------------------------------------------------------------ #
        # 10. Ogłoszenia (15 ogłoszeń)                                        #
        # ------------------------------------------------------------------ #
        now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)

        ogloszenia_defs = [
            # Archiwalne
            (
                "Zbiórka darów dla potrzebujących – Caritas",
                "W niedzielę 5 października 2025 r. po każdej Mszy Świętej odbędzie się zbiórka żywności i środków czystości dla rodzin potrzebujących ze śródmieścia Krakowa. Prosimy o przyniesienie makaronu, ryżu, konserw i kawy.",
                StatusOgloszenia.ARCHIWALNY,
                PriorytetOgloszenia.NORMALNY,
                datetime(2025, 10, 3, 12, 0, tzinfo=timezone.utc),
                datetime(2025, 10, 6, 23, 59, tzinfo=timezone.utc),
            ),
            (
                "Rekolekcje Adwentowe – zaproszenie",
                "Serdecznie zapraszamy na Rekolekcje Adwentowe w dniach 8-10 grudnia 2025 r. Rekolekcje poprowadzi o. Michał Krzyżanowski OP. Nabożeństwa o godz. 18:00. Zachęcamy do uczestnictwa całe rodziny.",
                StatusOgloszenia.ARCHIWALNY,
                PriorytetOgloszenia.WAZNY,
                datetime(2025, 11, 30, 12, 0, tzinfo=timezone.utc),
                datetime(2025, 12, 11, 23, 59, tzinfo=timezone.utc),
            ),
            (
                "Kolęda 2026 – harmonogram wizyt duszpasterskich",
                "Uprzejmie informujemy, że w dniach 5-26 stycznia 2026 r. odbywa się wizyta duszpasterska (Kolęda). Harmonogram dostępny w gablotce parafialnej i na stronie www. Prosimy o wywieszkę na drzwiach w przypadku nieobecności.",
                StatusOgloszenia.ARCHIWALNY,
                PriorytetOgloszenia.WAZNY,
                datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 1, 27, 23, 59, tzinfo=timezone.utc),
            ),
            (
                "Rekolekcje Wielkopostne – zaproszenie",
                "Zapraszamy na Rekolekcje Wielkopostne w dniach 9-11 marca 2026 r. Temat: 'Nawróćcie się i wierzcie w Ewangelię'. Prowadzi ks. Adam Boniecki MIC. Nabożeństwa o godz. 18:00.",
                StatusOgloszenia.ARCHIWALNY,
                PriorytetOgloszenia.WAZNY,
                datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 3, 12, 23, 59, tzinfo=timezone.utc),
            ),
            (
                "Triduum Paschalne 2026 – szczegółowy program",
                "Triduum Paschalne: Wielki Czwartek (9 IV) – Msza Wieczerzy Pańskiej godz. 19:00. Wielki Piątek (10 IV) – Liturgia Męki Pańskiej godz. 15:00 i 19:00. Wielka Sobota (11 IV) – Wigilia Paschalna godz. 20:00. Niedziela Wielkanocna (12 IV) – Msze o 8:00, 10:00, 12:00.",
                StatusOgloszenia.ARCHIWALNY,
                PriorytetOgloszenia.PILNY,
                datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 4, 13, 23, 59, tzinfo=timezone.utc),
            ),
            # Zatwierdzony / bieżące
            (
                "Pierwsza Komunia Święta – 24 maja 2026",
                "Z radością ogłaszamy, że Pierwsza Komunia Święta odbędzie się w niedzielę 24 maja 2026 r. o godz. 11:00. Do Stołu Pańskiego przystąpi 42 dzieci z naszej parafii. Prosimy o modlitwę w intencji pierwszokomunistów. Zapisy na fotografa parafialnego w kancelarii.",
                StatusOgloszenia.ZATWIERDZONY,
                PriorytetOgloszenia.WAZNY,
                datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 5, 25, 23, 59, tzinfo=timezone.utc),
            ),
            (
                "Bierzmowanie – 6 czerwca 2026",
                "Sakrament Bierzmowania zostanie udzielony w sobotę 6 czerwca 2026 r. przez Arcybiskupa Metropolitę Krakowskiego. Msza Święta z bierzmowaniem o godz. 11:00. Kandydaci proszeni o przybycie o godz. 10:15. Strój: biały lub elegancki.",
                StatusOgloszenia.ZATWIERDZONY,
                PriorytetOgloszenia.PILNY,
                datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 6, 7, 23, 59, tzinfo=timezone.utc),
            ),
            (
                "Ogłoszenia niedzielne – 17 maja 2026",
                "1. W tym tygodniu intencje Mszy Świętych jak w karteczce. 2. W środę 20 maja o godz. 18:00 spotkanie Krągu Biblijnego. 3. W piątek 22 maja o godz. 8:00 Msza za Ojczyznę z okazji Dnia Flagi. 4. Zapisy na pielgrzymkę do Częstochowy w kancelarii do 15 lipca.",
                StatusOgloszenia.ZATWIERDZONY,
                PriorytetOgloszenia.NORMALNY,
                datetime(2026, 5, 17, 10, 0, tzinfo=timezone.utc),
                datetime(2026, 5, 24, 23, 59, tzinfo=timezone.utc),
            ),
            (
                "Festyn Parafialny – 14 czerwca 2026",
                "Serdecznie zapraszamy na coroczny Festyn Parafialny w niedzielę 14 czerwca 2026 r. od godz. 12:00. W programie: loteria fantowa, kiermasz, gry i zabawy dla dzieci, występy scholii, grochówka parafialna. Dochód przeznaczony na remont dachu kościoła.",
                StatusOgloszenia.ZATWIERDZONY,
                PriorytetOgloszenia.WAZNY,
                datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 6, 15, 23, 59, tzinfo=timezone.utc),
            ),
            (
                "Procesja Bożego Ciała – 4 czerwca 2026",
                "Uroczystość Bożego Ciała – procesja ulicami Starego Miasta w czwartek 4 czerwca 2026 r. Msza Święta o godz. 10:00, procesja ok. godz. 11:30. Cztery ołtarze: Rynek Główny, ul. Grodzka, pl. Wszystkich Świętych i kościół. Zapraszamy wszystkich wiernych w strojach odświętnych.",
                StatusOgloszenia.ZATWIERDZONY,
                PriorytetOgloszenia.WAZNY,
                datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 6, 5, 23, 59, tzinfo=timezone.utc),
            ),
            (
                "Pielgrzymka do Częstochowy – sierpień 2026",
                "Piesza Pielgrzymka Krakowska na Jasną Górę odbędzie się w dniach 6-14 sierpnia 2026 r. Zapisy w kancelarii parafialnej do 15 lipca 2026 r. Koszt organizacyjny: 250 PLN. Więcej informacji u ks. Piotra Nowaka.",
                StatusOgloszenia.ZATWIERDZONY,
                PriorytetOgloszenia.NORMALNY,
                datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 7, 16, 23, 59, tzinfo=timezone.utc),
            ),
            (
                "PILNE: Zmiana godziny Mszy Świętej w poniedziałek 18 maja",
                "Uprzejmie informujemy, że Msza Święta w poniedziałek 18 maja 2026 r. odbędzie się wyjątkowo o godz. 8:00 (zamiast 7:00) z powodu spotkania duszpasterskiego duchowieństwa diecezjalnego.",
                StatusOgloszenia.ZATWIERDZONY,
                PriorytetOgloszenia.PILNY,
                datetime(2026, 5, 16, 20, 0, tzinfo=timezone.utc),
                datetime(2026, 5, 18, 9, 0, tzinfo=timezone.utc),
            ),
            (
                "Wakacyjny obóz ministrantów – Zakopane",
                "Ministranci naszej parafii zapraszają do zapisu na wakacyjny obóz w Zakopanem (13-19 lipca 2026 r.). Liczba miejsc ograniczona – 25 osób. Koszt: 800 PLN. Zapisy u ks. Piotra Nowaka do 15 czerwca 2026 r.",
                StatusOgloszenia.ZATWIERDZONY,
                PriorytetOgloszenia.NORMALNY,
                datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 6, 16, 23, 59, tzinfo=timezone.utc),
            ),
            (
                "Spowiedź przed Pierwszą Komunią – 16-17 maja 2026",
                "Spowiedź Święta dla dzieci przygotowujących się do I Komunii odbędzie się w piątek 22 maja i sobotę 23 maja 2026 r. od godz. 9:00 do 11:00. Dzieci przychodzą z rodzicem lub opiekunem. Strój do spowiedzi: biały.",
                StatusOgloszenia.ZATWIERDZONY,
                PriorytetOgloszenia.WAZNY,
                datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 5, 24, 23, 59, tzinfo=timezone.utc),
            ),
            (
                "Nabożeństwo Majowe – codziennie o 18:00",
                "W maju 2026 roku codziennie o godz. 18:00 odprawiane jest nabożeństwo majowe ku czci Najświętszej Maryi Panny (litania do NMP i śpiew pieśni maryjnych). Zapraszamy całe rodziny.",
                StatusOgloszenia.ZATWIERDZONY,
                PriorytetOgloszenia.NORMALNY,
                datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 5, 31, 23, 59, tzinfo=timezone.utc),
            ),
        ]

        for (
            tytul_og, tresc_og, status_og, priorytet_og, pub_og, wygasniecie_og
        ) in ogloszenia_defs:
            og_created = pub_og - timedelta(hours=rng.randint(1, 48))
            data_zatw_og = None
            if status_og in (StatusOgloszenia.ZATWIERDZONY, StatusOgloszenia.ARCHIWALNY):
                data_zatw_og = og_created + timedelta(hours=rng.randint(1, 24))

            og = Ogloszenie(
                parafia_id=parafia.id,
                tytul=tytul_og,
                tresc=tresc_og,
                status=status_og,
                priorytet=priorytet_og,
                data_publikacji=pub_og,
                data_wygasniecia=wygasniecie_og,
                tworca_id=rng.choice(tworca_ids),
                zatwierdzone_przez_id=proboszcz_user.id if data_zatw_og else None,
                data_zatwierdzenia=data_zatw_og,
            )
            _set_timestamps(og, og_created, data_zatw_og or og_created)
            db.add(og)

        await db.flush()
        stats["ogloszenia"] = len(ogloszenia_defs)

        # ------------------------------------------------------------------ #
        # 11. Powiadomienia (20 powiadomień dla proboszcza)                   #
        # ------------------------------------------------------------------ #
        powiad_defs = [
            (TypPowiadomienia.INTENCJA, "Nowa intencja do zatwierdzenia",
             "Wpłynęła intencja za + Józef Kowalski. Ofiara: 100 PLN. Prosimy o zatwierdzenie.", False),
            (TypPowiadomienia.INTENCJA, "Nowa intencja do zatwierdzenia",
             "Wpłynęła intencja za zdrowie Marii Nowak w chorobie. Prosimy o zatwierdzenie.", False),
            (TypPowiadomienia.INTENCJA, "Nowa intencja do zatwierdzenia",
             "Wpłynęła intencja dziękczynna za szczęśliwe zdanie matury. Ofiara: 50 PLN.", False),
            (TypPowiadomienia.DOKUMENT, "Dokument oczekuje na zatwierdzenie",
             "Metryka chrztu – Piotr Zając (data: 2026-04-26) wymaga zatwierdzenia.", False),
            (TypPowiadomienia.DOKUMENT, "Dokument oczekuje na zatwierdzenie",
             "Zaświadczenie do ślubu – Karolina Dąbrowska. Prosimy o weryfikację i zatwierdzenie.", False),
            (TypPowiadomienia.DOKUMENT, "Dokument oczekuje na zatwierdzenie",
             "Metryka ślubu – Jabłoński / Górecka (planowany ślub 13.06.2026). Do zatwierdzenia.", False),
            (TypPowiadomienia.SUKCES, "Intencja potwierdzona",
             "Intencja za + Henryk Wiśniewski (10. rocznica śmierci) została potwierdzona.", True),
            (TypPowiadomienia.SUKCES, "Dokument wydany",
             "Metryka ślubu Mazur/Wróbel została wydana parafianom.", True),
            (TypPowiadomienia.WYDARZENIE, "Zbliżające się wydarzenie: Pierwsza Komunia",
             "Za 7 dni odbędzie się Pierwsza Komunia Święta (24.05.2026). Sprawdź listę dzieci.", False),
            (TypPowiadomienia.WYDARZENIE, "Zbliżające się wydarzenie: Bierzmowanie",
             "Za 20 dni – Bierzmowanie (6.06.2026). Upewnij się, że lista kandydatów jest kompletna.", False),
            (TypPowiadomienia.INFO, "Nowy parafianin zarejestrowany",
             "Jan Kowalski (numer 2025/301) został zarejestrowany w systemie przez ks. Piotra Nowaka.", True),
            (TypPowiadomienia.INFO, "Aktualizacja danych Wspólnoty",
             "Schola parafialna – dodano 3 nowych członków przez ks. Marcina Wiśniewskiego.", True),
            (TypPowiadomienia.INTENCJA, "Nowa intencja do zatwierdzenia",
             "Intencja rocznicowa – 25. rocznica ślubu Państwa Kowalskich. Ofiara: 150 PLN.", False),
            (TypPowiadomienia.INTENCJA, "Nowa intencja – brak ofiarodawcy",
             "Wpłynęła intencja wypominkowa bez wskazanego ofiarodawcy. Wymaga weryfikacji.", False),
            (TypPowiadomienia.DOKUMENT, "Przeterminowany szkic dokumentu",
             "Szkic pisma ogólnego z dnia 2026-04-10 nie został wysłany do zatwierdzenia od 30 dni.", False),
            (TypPowiadomienia.SUKCES, "Ogłoszenie opublikowane",
             "Ogłoszenie 'Pierwsza Komunia Święta – 24 maja 2026' zostało opublikowane pomyślnie.", True),
            (TypPowiadomienia.WYDARZENIE, "Spotkanie Rady Parafialnej – przypomnienie",
             "Jutro o godz. 19:00 – Spotkanie Rady Parafialnej. Agenda: Bierzmowanie i Festyn.", False),
            (TypPowiadomienia.INFO, "Raport miesięczny – kwiecień 2026",
             "Intencje: 48 zatwierdzonych, 6 oczekujących. Dokumenty: 5 wydanych. Nowi parafianie: 3.", True),
            (TypPowiadomienia.INTENCJA, "Intencja oczekuje ponad 14 dni",
             "Intencja za chorą Helenę Malinowską oczekuje na potwierdzenie od 16 dni.", False),
            (TypPowiadomienia.SUKCES, "Notatka wiedzy zsynchronizowana",
             "Notatka 'Godziny Mszy Świętych' została zaktualizowana i zsynchronizowana z asystentem AI.", True),
        ]

        for i, (typ_p, tytul_p, tresc_p, przeczytane_p) in enumerate(powiad_defs):
            days_ago = rng.randint(0, 60)
            p_date = now - timedelta(days=days_ago, hours=rng.randint(0, 23))
            dr = None
            if przeczytane_p:
                dr = p_date + timedelta(hours=rng.randint(1, 24))

            pw = Powiadomienie(
                odbiorca_id=proboszcz_user.id,
                typ=typ_p,
                tytul=tytul_p,
                tresc=tresc_p,
                przeczytane=przeczytane_p,
                data_przeczytania=dr,
            )
            pw.created_at = p_date  # type: ignore[attr-defined]
            db.add(pw)

        await db.flush()
        stats["powiadomienia"] = len(powiad_defs)

        # ------------------------------------------------------------------ #
        # Commit
        # ------------------------------------------------------------------ #
        await db.commit()
        return {"status": "ok", "stats": stats}

    except Exception:
        await db.rollback()
        raise
