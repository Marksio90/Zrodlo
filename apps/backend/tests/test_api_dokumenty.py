"""Testy API dokumentów – dostęp i izolacja parafii."""
import uuid
from datetime import datetime, timezone

import pytest

from app.models.dokumenty import Dokument, StatusDokumentu, TypDokumentu
from tests.conftest import PARAFIA_A_ID, PARAFIA_B_ID


def _make_dokument(parafia_id, doc_id=None) -> Dokument:
    obj = Dokument(
        parafia_id=parafia_id,
        typ=TypDokumentu.METRYKA_CHRZTU,
        tytul="Metryka chrztu – Jan Kowalski",
        dane={},
        status=StatusDokumentu.SZKIC,
        wygenerowane_przez_ai=False,
    )
    obj.id = doc_id or uuid.uuid4()
    obj.deleted_at = None
    obj.created_at = datetime.now(timezone.utc)
    obj.updated_at = datetime.now(timezone.utc)
    return obj


class TestAuth:
    async def test_list_dokumenty_requires_auth(self, anon_client):
        resp = await anon_client.get("/dokumenty")
        assert resp.status_code == 401

    async def test_create_dokument_requires_auth(self, anon_client):
        resp = await anon_client.post("/dokumenty", json={})
        assert resp.status_code == 401


class TestListDokumenty:
    async def test_list_returns_200_for_authenticated(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([])
        resp = await client.get("/dokumenty")
        assert resp.status_code == 200

    async def test_list_query_scoped_by_parish(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        db.queue([])
        await client.get("/dokumenty")
        stmt_str = str(db.stmts[0].compile())
        assert "parafia_id" in stmt_str


class TestGetDokument:
    async def test_own_parish_document_returns_200(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        doc = _make_dokument(PARAFIA_A_ID)
        db.put(doc)
        resp = await client.get(f"/dokumenty/{doc.id}")
        assert resp.status_code == 200

    async def test_other_parish_document_returns_404(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        doc = _make_dokument(PARAFIA_B_ID)
        db.put(doc)
        resp = await client.get(f"/dokumenty/{doc.id}")
        assert resp.status_code == 404

    async def test_nonexistent_document_returns_404(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        resp = await client.get(f"/dokumenty/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestCreateDokument:
    async def test_proboszcz_can_create_document(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        payload = {
            "typ": TypDokumentu.METRYKA_CHRZTU,
            "tytul": "Metryka chrztu",
            "dane": {},
        }
        resp = await client.post("/dokumenty", json=payload)
        assert resp.status_code == 201

    async def test_created_document_has_correct_parafia_id(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        payload = {
            "typ": TypDokumentu.METRYKA_CHRZTU,
            "tytul": "Test dokument",
            "dane": {},
        }
        await client.post("/dokumenty", json=payload)
        created = next((o for o in db.added if hasattr(o, "tytul")), None)
        assert created is not None
        assert str(created.parafia_id) == str(PARAFIA_A_ID)

    async def test_parafianin_cannot_create_document(self, client_parafianin_a):
        client, db = client_parafianin_a
        payload = {
            "typ": TypDokumentu.METRYKA_CHRZTU,
            "tytul": "Dokument",
            "dane": {},
        }
        resp = await client.post("/dokumenty", json=payload)
        assert resp.status_code == 403


class TestApproveDokument:
    async def test_proboszcz_can_approve_own_parish_document(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        doc = _make_dokument(PARAFIA_A_ID)
        db.put(doc)
        resp = await client.post(f"/dokumenty/{doc.id}/zatwierdz")
        assert resp.status_code == 200

    async def test_proboszcz_cannot_approve_other_parish_document(self, client_proboszcz_a):
        client, db = client_proboszcz_a
        doc = _make_dokument(PARAFIA_B_ID)
        db.put(doc)
        resp = await client.post(f"/dokumenty/{doc.id}/zatwierdz")
        assert resp.status_code == 404

    async def test_wikariusz_cannot_approve_document(self, client_wikariusz_a):
        client, db = client_wikariusz_a
        doc = _make_dokument(PARAFIA_A_ID)
        db.put(doc)
        resp = await client.post(f"/dokumenty/{doc.id}/zatwierdz")
        assert resp.status_code == 403
