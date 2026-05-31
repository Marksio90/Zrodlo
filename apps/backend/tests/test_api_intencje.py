"""Testy API intencji – CRUD i izolacja multi-tenancy."""
import uuid
from datetime import date, datetime, timezone

import pytest

from app.models.intencje import Intencja, TypIntencji
from app.models.uzytkownicy import RolaUzytkownika
from tests.conftest import PARAFIA_A_ID, PARAFIA_B_ID, _make_user


def _make_intencja(parafia_id, intencja_id=None) -> Intencja:
    """Tworzy obiekt Intencja z prawidłową inicjalizacją SQLAlchemy."""
    obj = Intencja(
        parafia_id=parafia_id,
        typ=TypIntencji.INNA,
        tresc="Za spokój duszy Jana Kowalskiego",
        ofiarodawca="Maria Kowalska",
        potwierdzona=False,
    )
    obj.id = intencja_id or uuid.uuid4()
    obj.deleted_at = None
    obj.created_at = datetime.now(timezone.utc)
    obj.updated_at = datetime.now(timezone.utc)
    return obj


class TestAuth:
    async def test_list_intencje_without_token_returns_401(self, anon_client):
        resp = await anon_client.get("/intencje")
        assert resp.status_code == 401

    async def test_create_intencja_without_token_returns_401(self, anon_client):
        resp = await anon_client.post("/intencje", json={})
        assert resp.status_code == 401


class TestListIntencje:
    async def test_list_returns_200(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([])  # pusta lista
        resp = await client.get("/intencje")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_query_contains_parafia_id_filter(self, client_proboszcz_a):
        """Weryfikuje że query zawiera filtr parafia_id."""
        client, db = client_proboszcz_a
        db.queue([])
        await client.get("/intencje")
        assert db.stmts, "Powinno być co najmniej jedno wywołanie execute()"
        stmt_str = str(db.stmts[0].compile())
        assert "parafia_id" in stmt_str


class TestGetIntencja:
    async def test_own_parish_intencja_returns_200(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        intencja = _make_intencja(PARAFIA_A_ID)
        db.put(intencja)
        resp = await client.get(f"/intencje/{intencja.id}")
        assert resp.status_code == 200

    async def test_other_parish_intencja_returns_404(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        intencja = _make_intencja(PARAFIA_B_ID)  # inra parafia!
        db.put(intencja)
        resp = await client.get(f"/intencje/{intencja.id}")
        assert resp.status_code == 404

    async def test_nonexistent_intencja_returns_404(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        resp = await client.get(f"/intencje/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestCreateIntencja:
    async def test_proboszcz_can_create_intencja(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        payload = {"tresc": "Za zdrowie rodziny Nowak", "typ": "inna"}
        resp = await client.post("/intencje", json=payload)
        assert resp.status_code == 201

    async def test_created_intencja_has_correct_parafia_id(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        payload = {"tresc": "Testowa intencja", "typ": "inna"}
        await client.post("/intencje", json=payload)
        created = next((o for o in db.added if hasattr(o, "tresc")), None)
        assert created is not None
        assert str(created.parafia_id) == str(PARAFIA_A_ID)

    async def test_parafianin_can_create_intencja(self, client_parafianin_a):
        client, db = client_parafianin_a
        payload = {"tresc": "Intencja parafianina", "typ": "inna"}
        resp = await client.post("/intencje", json=payload)
        assert resp.status_code == 201

    async def test_wikariusz_can_create_intencja(self, client_wikariusz_a):
        client, db = client_wikariusz_a
        payload = {"tresc": "Intencja wikariusza", "typ": "inna"}
        resp = await client.post("/intencje", json=payload)
        assert resp.status_code == 201


class TestDeleteIntencja:
    async def test_proboszcz_can_delete_own_parish_intencja(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        intencja = _make_intencja(PARAFIA_A_ID)
        db.put(intencja)
        resp = await client.delete(f"/intencje/{intencja.id}")
        assert resp.status_code == 204

    async def test_proboszcz_cannot_delete_other_parish_intencja(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        intencja = _make_intencja(PARAFIA_B_ID)
        db.put(intencja)
        resp = await client.delete(f"/intencje/{intencja.id}")
        assert resp.status_code == 404

    async def test_parafianin_cannot_delete_intencja(self, client_parafianin_a):
        client, db = client_parafianin_a
        intencja = _make_intencja(PARAFIA_A_ID)
        db.put(intencja)
        resp = await client.delete(f"/intencje/{intencja.id}")
        assert resp.status_code == 403

    async def test_wikariusz_cannot_delete_intencja(self, client_wikariusz_a):
        client, db = client_wikariusz_a
        intencja = _make_intencja(PARAFIA_A_ID)
        db.put(intencja)
        resp = await client.delete(f"/intencje/{intencja.id}")
        assert resp.status_code == 403


class TestConfirmIntencja:
    async def test_proboszcz_can_confirm_intencja(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        intencja = _make_intencja(PARAFIA_A_ID)
        db.put(intencja)
        resp = await client.post(f"/intencje/{intencja.id}/potwierdz")
        assert resp.status_code == 200

    async def test_parafianin_cannot_confirm_intencja(self, client_parafianin_a):
        client, db = client_parafianin_a
        intencja = _make_intencja(PARAFIA_A_ID)
        db.put(intencja)
        resp = await client.post(f"/intencje/{intencja.id}/potwierdz")
        assert resp.status_code == 403
