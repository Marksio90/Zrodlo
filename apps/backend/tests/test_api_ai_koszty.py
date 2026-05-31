"""Testy API monitorowania kosztów AI (/ai/koszty/*)."""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.models.ai_uzycie import AiUzycie
from app.models.subskrypcja import Plan
from tests.conftest import PARAFIA_A_ID, USER_A_ID


# ── Helpers ────────────────────────────────────────────────────────────────────

def _agg_row(zapytania=5, tokeny=1000, koszt="0.00010000"):
    return SimpleNamespace(
        zapytania=zapytania,
        tokeny=tokeny,
        koszt=Decimal(koszt),
    )


def _make_sub(plan=Plan.STANDARD, limit_ai=300, dni_do_konca=30):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        plan=plan,
        aktywna=True,
        data_zakonczenia=now + timedelta(days=dni_do_konca),
        limit_ai_zapytan_miesiac=limit_ai,
    )


def _make_wpis():
    wpis = AiUzycie(
        parafia_id=PARAFIA_A_ID,
        uzytkownik_id=USER_A_ID,
        model="gpt-4o-mini",
        typ="chat",
        tokeny_wejscie=100,
        tokeny_wyjscie=50,
        koszt_usd=Decimal("0.00001000"),
        czas_ms=None,
    )
    wpis.id = uuid.uuid4()
    wpis.created_at = datetime.now(timezone.utc)
    return wpis


# ── /ai/koszty/podsumowanie ────────────────────────────────────────────────────

class TestPodsumowanie:
    async def test_wymaga_auth(self, anon_client):
        resp = await anon_client.get("/ai/koszty/podsumowanie")
        assert resp.status_code == 401

    async def test_zwraca_podsumowanie_bez_subskrypcji(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        # execute kolejno: agg, per_model(iteracja), per_dzien(iteracja), subskrypcja
        db.queue(_agg_row(10, 2000), [], [], None)
        resp = await client.get("/ai/koszty/podsumowanie")
        assert resp.status_code == 200
        data = resp.json()
        assert data["zapytania_lacznie"] == 10
        assert data["tokeny_lacznie"] == 2000
        assert data["limit_zapytan"] is None
        assert data["procent_limitu"] is None

    async def test_oblicza_procent_z_subskrypcja(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        sub = _make_sub(plan=Plan.STANDARD, limit_ai=300)
        db.queue(_agg_row(60, 5000), [], [], sub)
        resp = await client.get("/ai/koszty/podsumowanie")
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit_zapytan"] == 300
        assert data["procent_limitu"] == pytest.approx(20.0, abs=0.1)

    async def test_zawiera_miesiac(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue(_agg_row(), [], [], None)
        resp = await client.get("/ai/koszty/podsumowanie")
        data = resp.json()
        assert len(data["miesiac"]) == 7  # "YYYY-MM"
        assert "-" in data["miesiac"]


# ── /ai/koszty/alerty ─────────────────────────────────────────────────────────

class TestAlerty:
    async def test_wymaga_auth(self, anon_client):
        resp = await anon_client.get("/ai/koszty/alerty")
        assert resp.status_code == 401

    async def test_bez_subskrypcji_poziom_ok(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue(SimpleNamespace(zapytania=10), None)
        resp = await client.get("/ai/koszty/alerty")
        assert resp.status_code == 200
        data = resp.json()
        assert data["poziom"] == "ok"
        assert data["procent_limitu"] is None
        assert data["zapytania_w_miesiacu"] == 10

    async def test_poziom_ok_ponizej_80(self, client_proboszcz_a):
        # TRIAL limit = 30; 20/30 = 66.7% → "ok"
        client, db = client_proboszcz_a
        sub = _make_sub(plan=Plan.TRIAL)
        db.queue(SimpleNamespace(zapytania=20), sub)
        resp = await client.get("/ai/koszty/alerty")
        data = resp.json()
        assert data["poziom"] == "ok"
        assert data["procent_limitu"] < 80.0

    async def test_poziom_ostrzezenie_80_99(self, client_proboszcz_a):
        # TRIAL limit = 30; 25/30 = 83.3% → "ostrzezenie"
        client, db = client_proboszcz_a
        sub = _make_sub(plan=Plan.TRIAL)
        db.queue(SimpleNamespace(zapytania=25), sub)
        resp = await client.get("/ai/koszty/alerty")
        data = resp.json()
        assert data["poziom"] == "ostrzezenie"
        assert 80.0 <= data["procent_limitu"] < 100.0

    async def test_poziom_krytyczny_100(self, client_proboszcz_a):
        # TRIAL limit = 30; 30/30 = 100% → "krytyczny"
        client, db = client_proboszcz_a
        sub = _make_sub(plan=Plan.TRIAL)
        db.queue(SimpleNamespace(zapytania=30), sub)
        resp = await client.get("/ai/koszty/alerty")
        data = resp.json()
        assert data["poziom"] == "krytyczny"

    async def test_poziom_krytyczny_ponad_100(self, client_proboszcz_a):
        # TRIAL limit = 30; 35/30 = 116.7% → "krytyczny"
        client, db = client_proboszcz_a
        sub = _make_sub(plan=Plan.TRIAL)
        db.queue(SimpleNamespace(zapytania=35), sub)
        resp = await client.get("/ai/koszty/alerty")
        data = resp.json()
        assert data["poziom"] == "krytyczny"


# ── /ai/koszty/szczegoly ──────────────────────────────────────────────────────

class TestSzczegoly:
    async def test_wymaga_auth(self, anon_client):
        resp = await anon_client.get("/ai/koszty/szczegoly")
        assert resp.status_code == 401

    async def test_parafianin_dostaje_403(self, client_parafianin_a):
        client, db = client_parafianin_a
        resp = await client.get("/ai/koszty/szczegoly")
        assert resp.status_code == 403

    async def test_proboszcz_dostaje_liste(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([_make_wpis()])
        resp = await client.get("/ai/koszty/szczegoly")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["model"] == "gpt-4o-mini"
        assert data[0]["typ"] == "chat"

    async def test_pusta_lista(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([])
        resp = await client.get("/ai/koszty/szczegoly")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_limit_parametr(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([])
        resp = await client.get("/ai/koszty/szczegoly?limit=10&offset=0")
        assert resp.status_code == 200
