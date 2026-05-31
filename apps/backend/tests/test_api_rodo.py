"""Testy API RODO – akceptacja Umowy Powierzenia Danych (art. 28 RODO)."""
import uuid
from datetime import datetime, timezone

import pytest

from app.models.rodo import AkceptacjaUmowy
from app.schemas.rodo import AKTUALNA_WERSJA
from tests.conftest import PARAFIA_A_ID, PARAFIA_B_ID


def _make_akceptacja(parafia_id, user_id, wersja=AKTUALNA_WERSJA) -> AkceptacjaUmowy:
    obj = AkceptacjaUmowy(
        parafia_id=parafia_id,
        zaakceptowana_przez=user_id,
        wersja=wersja,
        zaakceptowano_at=datetime.now(timezone.utc),
        ip_adres="127.0.0.1",
        user_agent="TestAgent/1.0",
    )
    obj.id = uuid.uuid4()
    obj.created_at = datetime.now(timezone.utc)
    obj.updated_at = datetime.now(timezone.utc)
    return obj


class TestPublicEndpoints:
    async def test_get_umowa_info_no_auth_required(self, anon_client):
        """Metadane umowy dostępne bez logowania."""
        resp = await anon_client.get("/rodo/umowa")
        assert resp.status_code == 200
        data = resp.json()
        assert data["wersja"] == AKTUALNA_WERSJA
        assert "tytul" in data

    async def test_get_umowa_info_returns_version(self, anon_client):
        resp = await anon_client.get("/rodo/umowa")
        assert resp.json()["wersja"] == "1.0"


class TestStatus:
    async def test_status_requires_auth(self, anon_client):
        resp = await anon_client.get("/rodo/status")
        assert resp.status_code == 401

    async def test_status_nie_zaakceptowana(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([])  # brak akceptacji w historii
        resp = await client.get("/rodo/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["zaakceptowana"] is False
        assert data["wymaga_akceptacji"] is True
        assert data["wersja_zaakceptowana"] is None

    async def test_status_zaakceptowana(self, client_proboszcz_a):
        from tests.conftest import USER_A_ID
        client, db = client_proboszcz_a
        akceptacja = _make_akceptacja(PARAFIA_A_ID, USER_A_ID)
        db.queue([akceptacja])
        resp = await client.get("/rodo/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["zaakceptowana"] is True
        assert data["wymaga_akceptacji"] is False
        assert data["wersja_zaakceptowana"] == AKTUALNA_WERSJA


class TestAkceptuj:
    async def test_akceptuj_requires_auth(self, anon_client):
        resp = await anon_client.post("/rodo/akceptuj", json={"wersja": AKTUALNA_WERSJA})
        assert resp.status_code == 401

    async def test_proboszcz_moze_zaakceptowac(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        resp = await client.post("/rodo/akceptuj", json={"wersja": AKTUALNA_WERSJA})
        assert resp.status_code == 201
        data = resp.json()
        assert data["wersja"] == AKTUALNA_WERSJA
        assert str(data["parafia_id"]) == str(PARAFIA_A_ID)

    async def test_akceptacja_zapisuje_parafia_id(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        await client.post("/rodo/akceptuj", json={"wersja": AKTUALNA_WERSJA})
        zapisany = next((o for o in db.added if isinstance(o, AkceptacjaUmowy)), None)
        assert zapisany is not None
        assert str(zapisany.parafia_id) == str(PARAFIA_A_ID)

    async def test_akceptacja_zapisuje_user_id(self, client_proboszcz_a):
        from tests.conftest import USER_A_ID
        client, db = client_proboszcz_a
        await client.post("/rodo/akceptuj", json={"wersja": AKTUALNA_WERSJA})
        zapisany = next((o for o in db.added if isinstance(o, AkceptacjaUmowy)), None)
        assert zapisany is not None
        assert str(zapisany.zaakceptowana_przez) == str(USER_A_ID)

    async def test_parafianin_nie_moze_zaakceptowac(self, client_parafianin_a):
        client, db = client_parafianin_a
        resp = await client.post("/rodo/akceptuj", json={"wersja": AKTUALNA_WERSJA})
        assert resp.status_code == 403

    async def test_wikariusz_nie_moze_zaakceptowac(self, client_wikariusz_a):
        client, db = client_wikariusz_a
        resp = await client.post("/rodo/akceptuj", json={"wersja": AKTUALNA_WERSJA})
        assert resp.status_code == 403

    async def test_nieprawidlowa_wersja_returns_422(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        resp = await client.post("/rodo/akceptuj", json={"wersja": "99.9"})
        assert resp.status_code == 422


class TestHistoria:
    async def test_historia_requires_auth(self, anon_client):
        resp = await anon_client.get("/rodo/historia")
        assert resp.status_code == 401

    async def test_proboszcz_widzi_swoja_historie(self, client_proboszcz_a):
        from tests.conftest import USER_A_ID
        client, db = client_proboszcz_a
        a1 = _make_akceptacja(PARAFIA_A_ID, USER_A_ID, "1.0")
        db.queue([a1])
        resp = await client.get("/rodo/historia")
        assert resp.status_code == 200

    async def test_parafianin_nie_widzi_historii(self, client_parafianin_a):
        client, db = client_parafianin_a
        resp = await client.get("/rodo/historia")
        assert resp.status_code == 403

    async def test_wikariusz_nie_widzi_historii(self, client_wikariusz_a):
        client, db = client_wikariusz_a
        resp = await client.get("/rodo/historia")
        assert resp.status_code == 403
