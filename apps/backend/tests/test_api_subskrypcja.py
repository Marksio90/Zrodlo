"""Testy API subskrypcji – plany, trial, feature gating."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.subskrypcja import Plan, Subskrypcja
from app.schemas.subskrypcja import PLAN_LIMITY
from app.services.subskrypcja import PLAN_LIMITY, limity_dla_planu
from tests.conftest import PARAFIA_A_ID, PARAFIA_B_ID, USER_A_ID


def _make_subskrypcja(
    parafia_id,
    plan=Plan.STANDARD,
    aktywna=True,
    okres_probny=False,
    dni_do_konca: int | None = 30,
) -> Subskrypcja:
    now = datetime.now(timezone.utc)
    obj = Subskrypcja(
        parafia_id=parafia_id,
        plan=plan,
        aktywna=aktywna,
        okres_probny=okres_probny,
        data_rozpoczecia=now - timedelta(days=1),
        data_zakonczenia=now + timedelta(days=dni_do_konca) if dni_do_konca else None,
    )
    obj.id = uuid.uuid4()
    obj.anulowana_at = None
    obj.aktywowana_przez = USER_A_ID
    obj.limit_uzytkownikow = 30
    obj.limit_intencji_miesiac = None
    obj.limit_dokumentow = None
    obj.limit_ai_zapytan_miesiac = 300
    obj.created_at = now
    obj.updated_at = now
    return obj


# ── Plany (publiczne) ──────────────────────────────────────────────────────────

class TestListaPlanov:
    async def test_lista_planow_bez_auth(self, anon_client):
        resp = await anon_client.get("/subskrypcja/plany")
        assert resp.status_code == 200

    async def test_zwraca_cztery_plany(self, anon_client):
        resp = await anon_client.get("/subskrypcja/plany")
        plany = resp.json()
        assert len(plany) == 4

    async def test_plany_zawieraja_ceny(self, anon_client):
        resp = await anon_client.get("/subskrypcja/plany")
        plany = {p["plan"]: p for p in resp.json()}
        assert plany["trial"]["cena_miesiac_pln"] == 0
        assert plany["podstawowy"]["cena_miesiac_pln"] == 49
        assert plany["standard"]["cena_miesiac_pln"] == 99
        assert plany["premium"]["cena_miesiac_pln"] == 199

    async def test_premium_bez_limitow(self, anon_client):
        resp = await anon_client.get("/subskrypcja/plany")
        premium = next(p for p in resp.json() if p["plan"] == "premium")
        assert premium["max_uzytkownikow"] is None
        assert premium["max_ai_zapytan_miesiac"] is None

    async def test_podstawowy_bez_ai(self, anon_client):
        resp = await anon_client.get("/subskrypcja/plany")
        pods = next(p for p in resp.json() if p["plan"] == "podstawowy")
        assert pods["ai_asystent"] is False
        assert pods["baza_wiedzy"] is False

    async def test_standard_ma_ai(self, anon_client):
        resp = await anon_client.get("/subskrypcja/plany")
        std = next(p for p in resp.json() if p["plan"] == "standard")
        assert std["ai_asystent"] is True
        assert std["baza_wiedzy"] is True

    async def test_get_plan_szczegoly(self, anon_client):
        resp = await anon_client.get("/subskrypcja/plany/premium")
        assert resp.status_code == 200
        assert resp.json()["api_integracje"] is True

    async def test_get_nieznany_plan_404(self, anon_client):
        resp = await anon_client.get("/subskrypcja/plany/cosmic")
        assert resp.status_code == 422  # FastAPI waliduje enum


# ── Status subskrypcji ─────────────────────────────────────────────────────────

class TestStatus:
    async def test_status_wymaga_auth(self, anon_client):
        resp = await anon_client.get("/subskrypcja/status")
        assert resp.status_code == 401

    async def test_status_aktywna_subskrypcja(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        sub = _make_subskrypcja(PARAFIA_A_ID, plan=Plan.STANDARD)
        db.queue([sub])
        resp = await client.get("/subskrypcja/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] == "standard"
        assert data["aktywna"] is True
        assert data["limity"]["ai_asystent"] is True

    async def test_status_brak_subskrypcji_zwraca_402(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([None])
        resp = await client.get("/subskrypcja/status")
        assert resp.status_code == 402

    async def test_status_wymaga_odnowienia_gdy_malo_dni(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        sub = _make_subskrypcja(PARAFIA_A_ID, dni_do_konca=3)
        db.queue([sub])
        resp = await client.get("/subskrypcja/status")
        assert resp.status_code == 200
        assert resp.json()["wymaga_odnowienia"] is True

    async def test_status_nie_wymaga_odnowienia_gdy_duzo_dni(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        sub = _make_subskrypcja(PARAFIA_A_ID, dni_do_konca=60)
        db.queue([sub])
        resp = await client.get("/subskrypcja/status")
        assert resp.status_code == 200
        assert resp.json()["wymaga_odnowienia"] is False


# ── Trial ──────────────────────────────────────────────────────────────────────

class TestTrial:
    async def test_trial_wymaga_auth(self, anon_client):
        resp = await anon_client.post("/subskrypcja/trial", json={})
        assert resp.status_code == 401

    async def test_proboszcz_moze_aktywowac_trial(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        # Brak poprzedniego triala i brak aktywnej sub
        db.queue([None])   # poprzedni trial check
        db.queue([None])   # aktywna sub check
        resp = await client.post("/subskrypcja/trial", json={})
        assert resp.status_code == 201
        data = resp.json()
        assert data["plan"] == "trial"
        assert data["okres_probny"] is True

    async def test_trial_zapisuje_parafia_id(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([None])
        db.queue([None])
        await client.post("/subskrypcja/trial", json={})
        zapisana = next((o for o in db.added if isinstance(o, Subskrypcja)), None)
        assert zapisana is not None
        assert str(zapisana.parafia_id) == str(PARAFIA_A_ID)

    async def test_parafianin_nie_moze_aktywowac_triala(self, client_parafianin_a):
        client, db = client_parafianin_a
        resp = await client.post("/subskrypcja/trial", json={})
        assert resp.status_code == 403

    async def test_drugi_trial_zwraca_409(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        poprzedni = _make_subskrypcja(PARAFIA_A_ID, plan=Plan.TRIAL, okres_probny=True)
        db.queue([poprzedni])   # był już trial
        resp = await client.post("/subskrypcja/trial", json={})
        assert resp.status_code == 409

    async def test_trial_przy_aktywnej_sub_409(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([None])   # brak poprzedniego triala
        istniejaca = _make_subskrypcja(PARAFIA_A_ID, plan=Plan.STANDARD)
        db.queue([istniejaca])   # ale jest aktywna sub
        resp = await client.post("/subskrypcja/trial", json={})
        assert resp.status_code == 409


# ── Admin – zarządzanie ────────────────────────────────────────────────────────

class TestAdmin:
    async def test_admin_moze_tworzyc_subskrypcje(self, client_proboszcz_a):
        """Proboszcz NIE jest adminem platformy — 403."""
        client, db = client_proboszcz_a
        payload = {
            "parafia_id": str(PARAFIA_B_ID),
            "plan": "premium",
        }
        resp = await client.post("/subskrypcja/", json=payload)
        assert resp.status_code == 403

    async def test_admin_lista_subskrypcji_403_dla_proboszcza(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        resp = await client.get("/subskrypcja/lista")
        assert resp.status_code == 403


# ── Jednostkowe: limity ────────────────────────────────────────────────────────

class TestLimityBiznesowe:
    def test_trial_ma_ai_asystent(self):
        assert limity_dla_planu(Plan.TRIAL).ai_asystent is True

    def test_podstawowy_nie_ma_ai(self):
        assert limity_dla_planu(Plan.PODSTAWOWY).ai_asystent is False

    def test_standard_ma_komunikacje_masowa(self):
        assert limity_dla_planu(Plan.STANDARD).komunikacja_masowa is True

    def test_premium_brak_limitow_uzytkownikow(self):
        assert limity_dla_planu(Plan.PREMIUM).max_uzytkownikow is None

    def test_premium_ma_api_integracje(self):
        assert limity_dla_planu(Plan.PREMIUM).api_integracje is True

    def test_podstawowy_ma_eksport(self):
        assert limity_dla_planu(Plan.PODSTAWOWY).eksport_danych is True

    def test_trial_nie_ma_eksportu(self):
        assert limity_dla_planu(Plan.TRIAL).eksport_danych is False
