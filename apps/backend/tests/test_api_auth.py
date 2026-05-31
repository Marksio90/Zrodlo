"""Testy API endpointów autoryzacji."""
import uuid
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_db
from app.main import app
from app.models.uzytkownicy import RolaUzytkownika
from app.services.auth import create_access_token, hash_password
from tests.conftest import PARAFIA_A_ID, MockDB, _make_user


def _db_with_user(user=None):
    """Zwraca MockDB z kolejką dostosowaną do logowania."""
    db = MockDB()
    if user is not None:
        db.queue(user)     # execute() → szukanie po email
    else:
        db.queue(None)     # execute() → brak użytkownika
    db.queue([])           # execute() → audit log nie blokuje
    return db


@pytest.fixture
def existing_user():
    return _make_user(
        uid=uuid.uuid4(),
        parafia_id=PARAFIA_A_ID,
        rola=RolaUzytkownika.PROBOSZCZ,
        email="proboszcz@test.pl",
        haslo="Haslo1234!",
    )


class TestLogin:
    async def test_correct_credentials_return_token(self, existing_user):
        db = _db_with_user(existing_user)
        app.dependency_overrides[get_db] = lambda: db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/token", json={"email": "proboszcz@test.pl", "haslo": "Haslo1234!"})
        app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "proboszcz@test.pl"

    async def test_wrong_password_returns_401(self, existing_user):
        db = _db_with_user(existing_user)
        app.dependency_overrides[get_db] = lambda: db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/token", json={"email": "proboszcz@test.pl", "haslo": "ZleHaslo!"})
        app.dependency_overrides.clear()

        assert resp.status_code == 401

    async def test_nonexistent_user_returns_401(self):
        db = _db_with_user(None)
        app.dependency_overrides[get_db] = lambda: db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/token", json={"email": "brak@test.pl", "haslo": "Haslo1!"})
        app.dependency_overrides.clear()

        assert resp.status_code == 401

    async def test_inactive_user_returns_403(self, existing_user):
        existing_user.aktywny = False
        db = _db_with_user(existing_user)
        app.dependency_overrides[get_db] = lambda: db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/token", json={"email": "proboszcz@test.pl", "haslo": "Haslo1234!"})
        app.dependency_overrides.clear()

        assert resp.status_code == 403


class TestProtectedEndpoints:
    async def test_get_me_without_token_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/auth/mnie")
        assert resp.status_code == 401

    async def test_get_me_with_invalid_token_returns_401(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/auth/mnie", headers={"Authorization": "Bearer niepoprawny.token.jwt"})
        assert resp.status_code == 401

    async def test_get_me_with_valid_token_returns_user(self, existing_user):
        token = create_access_token({
            "sub": str(existing_user.id),
            "email": existing_user.email,
            "rola": existing_user.rola,
            "parafia_id": str(existing_user.parafia_id),
        })
        db = MockDB()
        db.put(existing_user)
        app.dependency_overrides[get_db] = lambda: db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/auth/mnie", headers={"Authorization": f"Bearer {token}"})
        app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert resp.json()["email"] == existing_user.email
