"""Testy API kalendarza – auth enforcement i izolacja parafii.

Kalendarz był wcześniej otwarty bez JWT – te testy dokumentują poprawkę.
"""
import uuid
from datetime import datetime, timezone

import pytest

from app.models.kalendarz import Wydarzenie
from tests.conftest import PARAFIA_A_ID, PARAFIA_B_ID


def _make_wydarzenie(parafia_id, ev_id=None) -> Wydarzenie:
    obj = Wydarzenie(
        parafia_id=parafia_id,
        tytul="Spotkanie wspólnoty różańcowej",
        data_od=datetime(2025, 6, 15, 10, 0, tzinfo=timezone.utc),
        cykliczne=False,
        kolor="#3B82F6",
    )
    obj.id = ev_id or uuid.uuid4()
    obj.deleted_at = None
    obj.created_at = datetime.now(timezone.utc)
    obj.updated_at = datetime.now(timezone.utc)
    return obj


class TestAuth:
    async def test_list_events_without_token_returns_401(self, anon_client):
        """Kluczowy test: kalendarz wymagał auth (naprawione)."""
        resp = await anon_client.get("/kalendarz")
        assert resp.status_code == 401

    async def test_create_event_without_token_returns_401(self, anon_client):
        resp = await anon_client.post("/kalendarz", json={})
        assert resp.status_code == 401

    async def test_delete_event_without_token_returns_401(self, anon_client):
        resp = await anon_client.delete(f"/kalendarz/{uuid.uuid4()}")
        assert resp.status_code == 401


class TestListWydarzenia:
    async def test_list_returns_200(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([])
        resp = await client.get("/kalendarz")
        assert resp.status_code == 200

    async def test_list_query_scoped_by_parish(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([])
        await client.get("/kalendarz")
        stmt_str = str(db.stmts[0].compile())
        assert "parafia_id" in stmt_str

    async def test_parafianin_can_read_calendar(self, client_parafianin_a):
        client, db = client_parafianin_a
        db.queue([])
        resp = await client.get("/kalendarz")
        assert resp.status_code == 200


class TestCreateWydarzenie:
    async def test_proboszcz_can_create_event(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        payload = {
            "tytul": "Rekolekcje wielkopostne",
            "data_od": "2025-03-10T09:00:00Z",
        }
        resp = await client.post("/kalendarz", json=payload)
        assert resp.status_code == 201

    async def test_created_event_has_correct_parafia_id(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        payload = {
            "tytul": "Spotkanie rady parafialnej",
            "data_od": "2025-06-01T18:00:00Z",
        }
        await client.post("/kalendarz", json=payload)
        created = next((o for o in db.added if hasattr(o, "tytul")), None)
        assert created is not None
        assert str(created.parafia_id) == str(PARAFIA_A_ID)

    async def test_created_event_has_tworca_id(self, client_proboszcz_a):
        from tests.conftest import USER_A_ID
        client, db = client_proboszcz_a
        payload = {
            "tytul": "Test twórca",
            "data_od": "2025-06-15T10:00:00Z",
        }
        await client.post("/kalendarz", json=payload)
        created = next((o for o in db.added if hasattr(o, "tytul")), None)
        assert created is not None
        assert str(created.tworca_id) == str(USER_A_ID)

    async def test_parafianin_cannot_create_event(self, client_parafianin_a):
        client, db = client_parafianin_a
        payload = {
            "tytul": "Prywatne wydarzenie",
            "data_od": "2025-07-01T10:00:00Z",
        }
        resp = await client.post("/kalendarz", json=payload)
        assert resp.status_code == 403


class TestGetWydarzenie:
    async def test_own_parish_event_returns_200(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        ev = _make_wydarzenie(PARAFIA_A_ID)
        db.put(ev)
        resp = await client.get(f"/kalendarz/{ev.id}")
        assert resp.status_code == 200

    async def test_other_parish_event_returns_404(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        ev = _make_wydarzenie(PARAFIA_B_ID)
        db.put(ev)
        resp = await client.get(f"/kalendarz/{ev.id}")
        assert resp.status_code == 404


class TestDeleteWydarzenie:
    async def test_proboszcz_can_delete_own_event(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        ev = _make_wydarzenie(PARAFIA_A_ID)
        db.put(ev)
        resp = await client.delete(f"/kalendarz/{ev.id}")
        assert resp.status_code == 204

    async def test_cannot_delete_other_parish_event(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        ev = _make_wydarzenie(PARAFIA_B_ID)
        db.put(ev)
        resp = await client.delete(f"/kalendarz/{ev.id}")
        assert resp.status_code == 404
