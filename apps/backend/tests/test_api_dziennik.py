"""Testy API dziennika kancleryjnego (/dziennik/*)."""
import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from app.models.dziennik import StatusWpisu, TypWpisu, WpisDziennika
from tests.conftest import PARAFIA_A_ID, PARAFIA_B_ID, USER_A_ID


# ── Helpers ────────────────────────────────────────────────────────────────────

TODAY = date.today()
ROK = TODAY.year


def _make_wpis(
    numer=1,
    typ=TypWpisu.PRZYCHODZACE,
    status=StatusWpisu.ZAREJESTROWANE,
    parafia_id=PARAFIA_A_ID,
    przedmiot="Pismo próbne",
) -> WpisDziennika:
    w = WpisDziennika(
        parafia_id=parafia_id,
        uzytkownik_id=USER_A_ID,
        rok=ROK,
        kolejny_numer=numer,
        numer_pelny=f"L.dz. {numer}/{ROK}",
        typ=typ,
        status=status,
        data_wpisu=TODAY,
        data_pisma=None,
        nadawca="Kuria Metropolitalna",
        odbiorca=None,
        przedmiot=przedmiot,
        uwagi=None,
    )
    w.id = uuid.uuid4()
    w.deleted_at = None
    w.created_at = datetime.now(timezone.utc)
    w.updated_at = datetime.now(timezone.utc)
    return w


def _body(**kwargs):
    defaults = {
        "typ": "przychodzace",
        "data_wpisu": str(TODAY),
        "przedmiot": "Pismo testowe",
        "status": "robocze",
    }
    defaults.update(kwargs)
    return defaults


# ── GET /dziennik ──────────────────────────────────────────────────────────────

class TestListaDziennika:
    async def test_wymaga_auth(self, anon_client):
        resp = await anon_client.get("/dziennik")
        assert resp.status_code == 401

    async def test_pusta_lista(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue(0)   # COUNT query
        db.queue([])  # items query
        resp = await client.get("/dziennik")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0
        assert body["page"] == 1
        assert body["pages"] == 1

    async def test_zwraca_wpisy(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        wpis = _make_wpis()
        db.queue(1)      # COUNT = 1
        db.queue([wpis]) # items
        resp = await client.get("/dziennik")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert len(body["items"]) == 1
        assert body["items"][0]["numer_pelny"] == f"L.dz. 1/{ROK}"
        assert body["items"][0]["typ"] == "przychodzace"

    async def test_wielotenancy(self, client_proboszcz_b):
        client, db = client_proboszcz_b
        db.queue(0)   # COUNT
        db.queue([])  # items
        resp = await client.get("/dziennik")
        assert resp.status_code == 200
        assert resp.json()["items"] == []


# ── POST /dziennik ─────────────────────────────────────────────────────────────

class TestNowyWpis:
    async def test_wymaga_auth(self, anon_client):
        resp = await anon_client.post("/dziennik", json=_body())
        assert resp.status_code == 401

    async def test_parafianin_dostaje_403(self, client_parafianin_a):
        client, db = client_parafianin_a
        resp = await client.post("/dziennik", json=_body())
        assert resp.status_code == 403

    async def test_proboszcz_tworzy_wpis(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        # _nastepny_numer query, flush/refresh
        db.queue(0)  # MAX(kolejny_numer) = 0, so next = 1
        resp = await client.post("/dziennik", json=_body(
            typ="wychodzace",
            przedmiot="Odpowiedź na pismo kurii",
            status="zarejestrowane",
        ))
        assert resp.status_code == 201
        data = resp.json()
        assert data["typ"] == "wychodzace"
        assert data["przedmiot"] == "Odpowiedź na pismo kurii"
        assert data["numer_pelny"] == f"L.dz. 1/{ROK}"

    async def test_wikariusz_moze_tworzyc(self, client_wikariusz_a):
        client, db = client_wikariusz_a
        db.queue(5)  # numer 6 będzie następny
        resp = await client.post("/dziennik", json=_body())
        assert resp.status_code == 201
        assert resp.json()["kolejny_numer"] == 6

    async def test_brak_przedmiotu_zwraca_422(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        resp = await client.post("/dziennik", json={"typ": "przychodzace", "data_wpisu": str(TODAY)})
        assert resp.status_code == 422

    async def test_zly_typ_zwraca_422(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        resp = await client.post("/dziennik", json=_body(typ="niepoprawny"))
        assert resp.status_code == 422


# ── GET /dziennik/{id} ─────────────────────────────────────────────────────────

class TestSzczegoly:
    async def test_pobiera_wpis(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        wpis = _make_wpis()
        db.put(wpis)
        resp = await client.get(f"/dziennik/{wpis.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(wpis.id)

    async def test_nieistniejacy_404(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        resp = await client.get(f"/dziennik/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_innej_parafii_404(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        wpis = _make_wpis(parafia_id=PARAFIA_B_ID)
        db.put(wpis)
        resp = await client.get(f"/dziennik/{wpis.id}")
        assert resp.status_code == 404


# ── PATCH /dziennik/{id} ───────────────────────────────────────────────────────

class TestAktualizacja:
    async def test_proboszcz_moze_aktualizowac(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        wpis = _make_wpis()
        db.put(wpis)
        resp = await client.patch(f"/dziennik/{wpis.id}", json={"status": "zarchiwizowane"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "zarchiwizowane"

    async def test_wikariusz_nie_moze_edytowac(self, client_wikariusz_a):
        client, db = client_wikariusz_a
        wpis = _make_wpis()
        db.put(wpis)
        resp = await client.patch(f"/dziennik/{wpis.id}", json={"status": "zarchiwizowane"})
        assert resp.status_code == 403

    async def test_nieistniejacy_404(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        resp = await client.patch(f"/dziennik/{uuid.uuid4()}", json={"status": "wyslane"})
        assert resp.status_code == 404


# ── DELETE /dziennik/{id} ──────────────────────────────────────────────────────

class TestUsuwanie:
    async def test_proboszcz_usuwa(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        wpis = _make_wpis()
        db.put(wpis)
        resp = await client.delete(f"/dziennik/{wpis.id}")
        assert resp.status_code == 204

    async def test_wikariusz_nie_moze_usunac(self, client_wikariusz_a):
        client, db = client_wikariusz_a
        wpis = _make_wpis()
        db.put(wpis)
        resp = await client.delete(f"/dziennik/{wpis.id}")
        assert resp.status_code == 403


# ── GET /dziennik/statystyki ───────────────────────────────────────────────────

class TestStatystyki:
    async def test_zwraca_statystyki(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        row = SimpleNamespace(lacznie=10, przychodzace=5, wychodzace=3, wewnetrzne=2, ostatni_numer=10)
        db.queue(row)
        resp = await client.get("/dziennik/statystyki")
        assert resp.status_code == 200
        data = resp.json()
        assert data["lacznie"] == 10
        assert data["przychodzace"] == 5
        assert data["rok"] == ROK


# ── GET /dziennik/export/csv ───────────────────────────────────────────────────

class TestEksport:
    async def test_parafianin_403(self, client_parafianin_a):
        client, _ = client_parafianin_a
        resp = await client.get("/dziennik/export/csv")
        assert resp.status_code == 403

    async def test_proboszcz_dostaje_csv(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([_make_wpis()])
        resp = await client.get("/dziennik/export/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        lines = resp.text.strip().split("\n")
        assert lines[0].startswith("Numer")  # header
        assert "L.dz." in lines[1]

    async def test_pusta_lista_csv(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([])
        resp = await client.get("/dziennik/export/csv")
        assert resp.status_code == 200
        lines = resp.text.strip().split("\n")
        assert len(lines) == 1  # tylko nagłówek
