"""Testy API endpointów autoryzacji."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_cache, get_db
from app.main import app
from app.models.uzytkownicy import RolaUzytkownika
from app.services.auth import create_access_token, create_refresh_token, hash_password
from tests.conftest import PARAFIA_A_ID, MockDB, _make_user


def _make_cache():
    """Returns an async-capable mock cache."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    cache.ping = AsyncMock(return_value=True)
    return cache


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
        cache = _make_cache()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_cache] = lambda: cache
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/token", json={"email": "proboszcz@test.pl", "haslo": "Haslo1234!"})
        app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "proboszcz@test.pl"

    async def test_login_sets_refresh_cookie(self, existing_user):
        db = _db_with_user(existing_user)
        cache = _make_cache()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_cache] = lambda: cache
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/token", json={"email": "proboszcz@test.pl", "haslo": "Haslo1234!"})
        app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert "refresh_token" in resp.cookies
        # cache.set should have been called to store the jti
        cache.set.assert_called_once()
        call_args = cache.set.call_args
        assert call_args[0][0].startswith("refresh:")

    async def test_wrong_password_returns_401(self, existing_user):
        db = _db_with_user(existing_user)
        cache = _make_cache()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_cache] = lambda: cache
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/token", json={"email": "proboszcz@test.pl", "haslo": "ZleHaslo!"})
        app.dependency_overrides.clear()

        assert resp.status_code == 401

    async def test_nonexistent_user_returns_401(self):
        db = _db_with_user(None)
        cache = _make_cache()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_cache] = lambda: cache
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/token", json={"email": "brak@test.pl", "haslo": "Haslo1!"})
        app.dependency_overrides.clear()

        assert resp.status_code == 401

    async def test_inactive_user_returns_403(self, existing_user):
        existing_user.aktywny = False
        db = _db_with_user(existing_user)
        cache = _make_cache()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_cache] = lambda: cache
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/token", json={"email": "proboszcz@test.pl", "haslo": "Haslo1234!"})
        app.dependency_overrides.clear()

        assert resp.status_code == 403


class TestRefresh:
    async def test_refresh_without_cookie_returns_401(self):
        cache = _make_cache()
        db = MockDB()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_cache] = lambda: cache
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/refresh")
        app.dependency_overrides.clear()

        assert resp.status_code == 401
        assert "Brak tokena" in resp.json()["detail"]

    async def test_refresh_with_valid_token_returns_new_access_token(self, existing_user):
        jti = str(uuid.uuid4())
        refresh_jwt = create_refresh_token(str(existing_user.id), jti)

        cache = _make_cache()
        # Simulate that jti is stored for this user
        cache.get = AsyncMock(return_value=str(existing_user.id))

        db = MockDB()
        db.put(existing_user)

        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_cache] = lambda: cache
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/refresh", headers={"Cookie": f"refresh_token={refresh_jwt}"})
        app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Old JTI should be deleted
        cache.delete.assert_called_once_with(f"refresh:{jti}")
        # New JTI should be stored
        cache.set.assert_called_once()

    async def test_refresh_with_invalid_token_returns_401(self):
        cache = _make_cache()
        db = MockDB()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_cache] = lambda: cache
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/refresh", headers={"Cookie": "refresh_token=invalid.jwt.token"})
        app.dependency_overrides.clear()

        assert resp.status_code == 401

    async def test_refresh_with_revoked_jti_returns_401(self, existing_user):
        jti = str(uuid.uuid4())
        refresh_jwt = create_refresh_token(str(existing_user.id), jti)

        cache = _make_cache()
        # Simulate that jti is NOT in Redis (revoked/expired)
        cache.get = AsyncMock(return_value=None)

        db = MockDB()
        db.put(existing_user)

        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_cache] = lambda: cache
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/refresh", headers={"Cookie": f"refresh_token={refresh_jwt}"})
        app.dependency_overrides.clear()

        assert resp.status_code == 401
        assert "unieważniony" in resp.json()["detail"]


class TestLogout:
    async def test_logout_clears_cookie(self, existing_user):
        jti = str(uuid.uuid4())
        refresh_jwt = create_refresh_token(str(existing_user.id), jti)

        cache = _make_cache()
        db = MockDB()

        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_cache] = lambda: cache
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/logout", headers={"Cookie": f"refresh_token={refresh_jwt}"})
        app.dependency_overrides.clear()

        assert resp.status_code == 204
        cache.delete.assert_called_once_with(f"refresh:{jti}")

    async def test_logout_without_cookie_returns_204(self):
        cache = _make_cache()
        db = MockDB()

        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_cache] = lambda: cache
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/auth/logout")
        app.dependency_overrides.clear()

        assert resp.status_code == 204


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
            "imie": existing_user.imie,
            "nazwisko": existing_user.nazwisko,
        })
        db = MockDB()
        db.put(existing_user)
        app.dependency_overrides[get_db] = lambda: db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/auth/mnie", headers={"Authorization": f"Bearer {token}"})
        app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert resp.json()["email"] == existing_user.email
