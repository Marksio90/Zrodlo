"""Testy API onboardingu – dynamiczne obliczanie statusu konfiguracji parafii."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.parafia import Parafia
from app.models.rodo import AkceptacjaUmowy
from app.models.subskrypcja import Plan, Subskrypcja
from app.models.uzytkownicy import Uzytkownik
from app.schemas.rodo import AKTUALNA_WERSJA
from tests.conftest import PARAFIA_A_ID, USER_A_ID, _make_user


def _make_parafia(z_danymi: bool = True) -> Parafia:
    obj = Parafia(
        nazwa="Parafia Testowa",
        adres="ul. Testowa 1",
        miasto="Warszawa",
        email="biuro@parafia.pl" if z_danymi else None,
        telefon="123456789" if z_danymi else None,
    )
    obj.id = PARAFIA_A_ID
    obj.aktywna = True
    obj.created_at = datetime.now(timezone.utc)
    obj.updated_at = datetime.now(timezone.utc)
    return obj


def _make_akceptacja() -> AkceptacjaUmowy:
    obj = AkceptacjaUmowy(
        parafia_id=PARAFIA_A_ID,
        zaakceptowana_przez=USER_A_ID,
        wersja=AKTUALNA_WERSJA,
        zaakceptowano_at=datetime.now(timezone.utc),
    )
    obj.id = uuid.uuid4()
    obj.created_at = datetime.now(timezone.utc)
    obj.updated_at = datetime.now(timezone.utc)
    return obj


def _make_sub() -> Subskrypcja:
    now = datetime.now(timezone.utc)
    obj = Subskrypcja(
        parafia_id=PARAFIA_A_ID,
        plan=Plan.TRIAL,
        aktywna=True,
        okres_probny=True,
        data_rozpoczecia=now,
        data_zakonczenia=now + timedelta(days=30),
    )
    obj.id = uuid.uuid4()
    obj.anulowana_at = None
    obj.aktywowana_przez = USER_A_ID
    obj.limit_uzytkownikow = 5
    obj.limit_intencji_miesiac = 100
    obj.limit_dokumentow = 30
    obj.limit_ai_zapytan_miesiac = 30
    obj.created_at = now
    obj.updated_at = now
    return obj


def _make_user2() -> Uzytkownik:
    from app.models.uzytkownicy import RolaUzytkownika
    return _make_user(
        uuid.uuid4(), PARAFIA_A_ID, RolaUzytkownika.WIKARIUSZ, "wik2@parafia.pl"
    )


class TestStatusWymaga:
    async def test_status_wymaga_auth(self, anon_client):
        resp = await anon_client.get("/onboarding/status")
        assert resp.status_code == 401


class TestStatusKroki:
    async def test_zwraca_cztery_kroki(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        # parafia
        db.put(_make_parafia(z_danymi=True))
        # RODO
        db.queue([_make_akceptacja()])
        # sub
        db.queue([_make_sub()])
        # users
        db.queue([_make_user2()])
        resp = await client.get("/onboarding/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["wszystkich_krokow"] == 4
        assert len(data["kroki"]) == 4

    async def test_gotowy_gdy_wszystkie_kroki(self, client_proboszcz_a):
        from tests.conftest import USER_A_ID
        from app.models.uzytkownicy import RolaUzytkownika
        client, db = client_proboszcz_a
        db.put(_make_parafia(z_danymi=True))
        db.queue([_make_akceptacja()])
        db.queue([_make_sub()])
        # konto_ok wymaga >= 2 userów w parafii
        proboszcz = _make_user(USER_A_ID, PARAFIA_A_ID, RolaUzytkownika.PROBOSZCZ, "prob@a.pl")
        db.queue([proboszcz, _make_user2()])
        resp = await client.get("/onboarding/status")
        assert resp.status_code == 200
        assert resp.json()["gotowy"] is True

    async def test_nieukonczone_gdy_brak_danych_parafii(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.put(_make_parafia(z_danymi=False))
        db.queue([_make_akceptacja()])
        db.queue([_make_sub()])
        db.queue([_make_user2()])
        resp = await client.get("/onboarding/status")
        data = resp.json()
        assert data["gotowy"] is False
        dane_krok = next(k for k in data["kroki"] if k["id"] == "dane_parafii")
        assert dane_krok["ukonczone"] is False

    async def test_rodo_nieukonczone_gdy_brak_akceptacji(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.put(_make_parafia())
        db.queue([None])   # brak akceptacji RODO
        db.queue([_make_sub()])
        db.queue([_make_user2()])
        resp = await client.get("/onboarding/status")
        data = resp.json()
        rodo_krok = next(k for k in data["kroki"] if k["id"] == "rodo")
        assert rodo_krok["ukonczone"] is False

    async def test_sub_nieukonczone_gdy_brak_subskrypcji(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.put(_make_parafia())
        db.queue([_make_akceptacja()])
        db.queue([None])   # brak subskrypcji
        db.queue([_make_user2()])
        resp = await client.get("/onboarding/status")
        data = resp.json()
        sub_krok = next(k for k in data["kroki"] if k["id"] == "subskrypcja")
        assert sub_krok["ukonczone"] is False

    async def test_konto_nieukonczone_gdy_jeden_uzytkownik(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.put(_make_parafia())
        db.queue([_make_akceptacja()])
        db.queue([_make_sub()])
        db.queue([])   # tylko jeden user (sam proboszcz = 0 w queue, bo users_result to lista)
        resp = await client.get("/onboarding/status")
        data = resp.json()
        konto_krok = next(k for k in data["kroki"] if k["id"] == "pierwsze_konto")
        assert konto_krok["ukonczone"] is False

    async def test_ukonczone_kroki_licznik(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.put(_make_parafia(z_danymi=True))
        db.queue([_make_akceptacja()])
        db.queue([_make_sub()])
        db.queue([])  # brak drugiego usera
        resp = await client.get("/onboarding/status")
        data = resp.json()
        assert data["ukonczone_kroki"] == 3  # dane + rodo + sub
        assert data["gotowy"] is False

    async def test_parafia_id_w_odpowiedzi(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.put(_make_parafia())
        db.queue([_make_akceptacja()])
        db.queue([_make_sub()])
        db.queue([_make_user2()])
        resp = await client.get("/onboarding/status")
        assert str(resp.json()["parafia_id"]) == str(PARAFIA_A_ID)
