"""Testy izolacji multi-tenancy – weryfikacja że dane parafii A są niewidoczne dla parafii B.

Każdy test sprawdza inny moduł systemu z perspektywy cross-tenant access.
"""
import uuid
from datetime import datetime, timezone

import pytest

from app.models.dokumenty import Dokument, StatusDokumentu, TypDokumentu
from app.models.intencje import Intencja, TypIntencji
from app.models.kalendarz import Wydarzenie
from app.models.wiedza import KategoriaWiedzy, NotatkaWiedzy
from app.models.wspolnoty import Wspolnota
from tests.conftest import PARAFIA_A_ID, PARAFIA_B_ID


# ── Fabryki obiektów ──────────────────────────────────────────────────────────

def _intencja(parafia_id) -> Intencja:
    obj = Intencja(
        parafia_id=parafia_id,
        typ=TypIntencji.INNA,
        tresc="Intencja testowa",
        potwierdzona=False,
    )
    obj.id = uuid.uuid4()
    obj.deleted_at = None
    obj.created_at = datetime.now(timezone.utc)
    obj.updated_at = datetime.now(timezone.utc)
    return obj


def _dokument(parafia_id) -> Dokument:
    obj = Dokument(
        parafia_id=parafia_id,
        typ=TypDokumentu.METRYKA_CHRZTU,
        tytul="Dokument parafii A",
        dane={},
        status=StatusDokumentu.SZKIC,
        wygenerowane_przez_ai=False,
    )
    obj.id = uuid.uuid4()
    obj.deleted_at = None
    obj.created_at = datetime.now(timezone.utc)
    obj.updated_at = datetime.now(timezone.utc)
    return obj


def _wydarzenie(parafia_id) -> Wydarzenie:
    obj = Wydarzenie(
        parafia_id=parafia_id,
        tytul="Wydarzenie",
        data_od=datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc),
    )
    obj.id = uuid.uuid4()
    obj.deleted_at = None
    obj.created_at = datetime.now(timezone.utc)
    obj.updated_at = datetime.now(timezone.utc)
    return obj


def _notatka(parafia_id) -> NotatkaWiedzy:
    obj = NotatkaWiedzy(
        parafia_id=parafia_id,
        tytul="Notatka wiedzy parafii A",
        tresc="Treść notatki",
        kategoria=KategoriaWiedzy.INNE,
    )
    obj.id = uuid.uuid4()
    obj.deleted_at = None
    obj.created_at = datetime.now(timezone.utc)
    obj.updated_at = datetime.now(timezone.utc)
    return obj


def _wspolnota(parafia_id) -> Wspolnota:
    obj = Wspolnota(
        parafia_id=parafia_id,
        nazwa="Koło Różańcowe",
    )
    obj.id = uuid.uuid4()
    obj.created_at = datetime.now(timezone.utc)
    obj.updated_at = datetime.now(timezone.utc)
    return obj


# ── Testy izolacji ────────────────────────────────────────────────────────────

class TestIntencjeIzolacja:
    async def test_parafia_b_cannot_read_parafia_a_intencja(
        self, client_proboszcz_a, client_proboszcz_b
    ):
        _, db_a = client_proboszcz_a
        client_b, db_b = client_proboszcz_b

        intencja = _intencja(PARAFIA_A_ID)
        db_b.put(intencja)  # obiekt jest w db_b ale należy do PARAFIA_A

        resp = await client_b.get(f"/intencje/{intencja.id}")
        assert resp.status_code == 404, \
            "Proboszcz parafii B nie może czytać intencji parafii A"

    async def test_parafia_b_cannot_delete_parafia_a_intencja(
        self, client_proboszcz_b
    ):
        client_b, db_b = client_proboszcz_b
        intencja = _intencja(PARAFIA_A_ID)
        db_b.put(intencja)

        resp = await client_b.delete(f"/intencje/{intencja.id}")
        assert resp.status_code == 404

    async def test_parafia_b_cannot_confirm_parafia_a_intencja(
        self, client_proboszcz_b
    ):
        client_b, db_b = client_proboszcz_b
        intencja = _intencja(PARAFIA_A_ID)
        db_b.put(intencja)

        resp = await client_b.post(f"/intencje/{intencja.id}/potwierdz")
        assert resp.status_code == 404


class TestDokumentyIzolacja:
    async def test_parafia_b_cannot_read_parafia_a_document(self, client_proboszcz_b):
        client_b, db_b = client_proboszcz_b
        doc = _dokument(PARAFIA_A_ID)
        db_b.put(doc)

        resp = await client_b.get(f"/dokumenty/{doc.id}")
        assert resp.status_code == 404

    async def test_parafia_b_cannot_update_parafia_a_document(self, client_proboszcz_b):
        client_b, db_b = client_proboszcz_b
        doc = _dokument(PARAFIA_A_ID)
        db_b.put(doc)

        resp = await client_b.patch(
            f"/dokumenty/{doc.id}",
            json={"tytul": "Zhakowany dokument"},
        )
        assert resp.status_code == 404

    async def test_parafia_b_cannot_approve_parafia_a_document(self, client_proboszcz_b):
        client_b, db_b = client_proboszcz_b
        doc = _dokument(PARAFIA_A_ID)
        db_b.put(doc)

        resp = await client_b.post(f"/dokumenty/{doc.id}/zatwierdz")
        assert resp.status_code == 404


class TestKalendarzIzolacja:
    async def test_parafia_b_cannot_read_parafia_a_event(self, client_proboszcz_b):
        client_b, db_b = client_proboszcz_b
        ev = _wydarzenie(PARAFIA_A_ID)
        db_b.put(ev)

        resp = await client_b.get(f"/kalendarz/{ev.id}")
        assert resp.status_code == 404

    async def test_parafia_b_cannot_delete_parafia_a_event(self, client_proboszcz_b):
        client_b, db_b = client_proboszcz_b
        ev = _wydarzenie(PARAFIA_A_ID)
        db_b.put(ev)

        resp = await client_b.delete(f"/kalendarz/{ev.id}")
        assert resp.status_code == 404


class TestWiedzaIzolacja:
    async def test_parafia_b_cannot_read_parafia_a_note(self, client_proboszcz_b):
        client_b, db_b = client_proboszcz_b
        notatka = _notatka(PARAFIA_A_ID)
        db_b.put(notatka)

        resp = await client_b.get(f"/wiedza/{notatka.id}")
        assert resp.status_code == 404

    async def test_parafia_b_cannot_update_parafia_a_note(self, client_proboszcz_b):
        client_b, db_b = client_proboszcz_b
        notatka = _notatka(PARAFIA_A_ID)
        db_b.put(notatka)

        resp = await client_b.patch(
            f"/wiedza/{notatka.id}",
            json={"tytul": "Zmieniony tytuł"},
        )
        assert resp.status_code == 404

    async def test_parafia_b_cannot_delete_parafia_a_note(self, client_proboszcz_b):
        client_b, db_b = client_proboszcz_b
        notatka = _notatka(PARAFIA_A_ID)
        db_b.put(notatka)

        resp = await client_b.delete(f"/wiedza/{notatka.id}")
        assert resp.status_code == 404


class TestWspolnotyIzolacja:
    async def test_parafia_b_cannot_delete_parafia_a_wspolnota(self, client_proboszcz_b):
        client_b, db_b = client_proboszcz_b
        ws = _wspolnota(PARAFIA_A_ID)
        db_b.put(ws)

        resp = await client_b.delete(f"/wspolnoty/{ws.id}")
        assert resp.status_code == 404
