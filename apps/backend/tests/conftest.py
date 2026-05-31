"""Wspólne fixtures dla testów backendu Źródło."""
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_ai, get_cache, get_current_user, get_db, get_storage
from app.main import app
from app.models.uzytkownicy import RolaUzytkownika, Uzytkownik
from app.services.auth import hash_password

# ── Stałe ─────────────────────────────────────────────────────────────────────

PARAFIA_A_ID = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
PARAFIA_B_ID = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000002")

USER_A_ID = uuid.UUID("aaaaaaaa-1111-0000-0000-000000000001")
USER_B_ID = uuid.UUID("bbbbbbbb-2222-0000-0000-000000000002")
USER_WIK_ID = uuid.UUID("cccccccc-3333-0000-0000-000000000003")
USER_PAR_ID = uuid.UUID("dddddddd-4444-0000-0000-000000000004")


# ── MockDB ─────────────────────────────────────────────────────────────────────

class MockResult:
    """Imituje wynik SQLAlchemy execute()."""

    def __init__(self, data):
        if data is None:
            data = []
        self._data = data if isinstance(data, list) else [data]

    def scalars(self):
        return self

    def all(self):
        return self._data

    def first(self):
        return self._data[0] if self._data else None

    def scalar_one_or_none(self):
        return self._data[0] if self._data else None

    def __iter__(self):
        return iter(self._data)


class MockDB:
    """Minimalna imitacja AsyncSession SQLAlchemy."""

    def __init__(self):
        self.store: dict[str, object] = {}
        self._queue: list = []          # wyniki execute() w kolejności
        self.added: list = []
        self.deleted: list = []
        self.stmts: list = []           # przechwycone query statements

    # ── konfiguracja ──────────────────────────────────────────────────────────

    def put(self, *objs) -> "MockDB":
        """Wstaw obiekty do store (dostępne przez get())."""
        for obj in objs:
            self.store[str(obj.id)] = obj
        return self

    def queue(self, *results) -> "MockDB":
        """Kolejkuj wyniki execute() – zwracane po kolei."""
        self._queue.extend(results)
        return self

    # ── AsyncSession API ───────────────────────────────────────────────────────

    async def get(self, model, id_):
        return self.store.get(str(id_))

    async def execute(self, stmt):
        self.stmts.append(stmt)
        data = self._queue.pop(0) if self._queue else []
        return MockResult(data)

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def refresh(self, obj):
        """Aplikuje domyślne wartości kolumn SQLAlchemy (symulacja DB round-trip)."""
        now = datetime.now(timezone.utc)
        if not hasattr(obj, "__table__"):
            return
        for col in obj.__table__.columns:
            attr = col.name
            val = getattr(obj, attr, None)
            if val is not None:
                continue
            # Python-side default
            if col.default is not None:
                try:
                    arg = col.default.arg
                    setattr(obj, attr, arg() if callable(arg) else arg)
                except Exception:
                    pass
            # server_default timestamps
            elif col.server_default is not None and attr in ("created_at", "updated_at"):
                setattr(obj, attr, now)

    def add(self, obj):
        if not getattr(obj, "id", None):
            obj.id = uuid.uuid4()
        if not getattr(obj, "created_at", None):
            obj.created_at = datetime.now(timezone.utc)
        if not getattr(obj, "updated_at", None):
            obj.updated_at = datetime.now(timezone.utc)
        self.store[str(obj.id)] = obj
        self.added.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)
        self.store.pop(str(getattr(obj, "id", "")), None)

    # ── context manager (dla with db: ...) ───────────────────────────────────

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass


# ── Fabryki użytkowników ───────────────────────────────────────────────────────

def _make_user(
    uid: uuid.UUID,
    parafia_id: uuid.UUID | None,
    rola: str = RolaUzytkownika.PROBOSZCZ,
    email: str | None = None,
    haslo: str = "TestHaslo1!",
) -> Uzytkownik:
    u = Uzytkownik(
        email=email or f"user-{str(uid)[:8]}@parafia.pl",
        haslo_hash=hash_password(haslo),
        imie="Jan",
        nazwisko="Testowy",
        rola=rola,
        parafia_id=parafia_id,
        aktywny=True,
    )
    u.id = uid  # nadpisz auto-UUID po prawidłowej inicjalizacji
    u.deleted_at = None
    u.ostatnie_logowanie = None
    u.created_at = datetime.now(timezone.utc)
    u.updated_at = datetime.now(timezone.utc)
    return u


# ── Fixtures – użytkownicy ─────────────────────────────────────────────────────

@pytest.fixture
def proboszcz_a() -> Uzytkownik:
    return _make_user(USER_A_ID, PARAFIA_A_ID, RolaUzytkownika.PROBOSZCZ, "prob@parafia-a.pl")


@pytest.fixture
def proboszcz_b() -> Uzytkownik:
    return _make_user(USER_B_ID, PARAFIA_B_ID, RolaUzytkownika.PROBOSZCZ, "prob@parafia-b.pl")


@pytest.fixture
def wikariusz_a() -> Uzytkownik:
    return _make_user(USER_WIK_ID, PARAFIA_A_ID, RolaUzytkownika.WIKARIUSZ, "wik@parafia-a.pl")


@pytest.fixture
def parafianin_a() -> Uzytkownik:
    return _make_user(USER_PAR_ID, PARAFIA_A_ID, RolaUzytkownika.PARAFIANIN, "par@parafia-a.pl")


# ── Fixtures – MockDB ──────────────────────────────────────────────────────────

@pytest.fixture
def mock_db() -> MockDB:
    return MockDB()


# ── Fixtures – mock services ───────────────────────────────────────────────────

@pytest.fixture
def mock_ai():
    ai = MagicMock()
    ai.chat = MagicMock(return_value=("Mock odpowiedź", "gpt-4o-mini"))
    ai.embed = MagicMock(return_value=[0.1] * 1536)
    return ai


@pytest.fixture
def mock_storage():
    s = MagicMock()
    s.presigned_url.return_value = "https://minio.test/file"
    s.upload.return_value = None
    s.delete.return_value = None
    return s


@pytest.fixture
def mock_cache():
    return MagicMock()


# ── Fixtures – klienty HTTP ────────────────────────────────────────────────────

def _make_client_fixture(user_fixture_name: str):
    """Factory tworząca fixture AsyncClient dla danego użytkownika."""

    @pytest.fixture
    async def _client(request, mock_db, mock_ai, mock_storage, mock_cache) -> AsyncGenerator:
        user = request.getfixturevalue(user_fixture_name)

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_ai] = lambda: mock_ai
        app.dependency_overrides[get_storage] = lambda: mock_storage
        app.dependency_overrides[get_cache] = lambda: mock_cache

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac, mock_db

        app.dependency_overrides.clear()

    return _client


client_proboszcz_a = _make_client_fixture("proboszcz_a")
client_proboszcz_b = _make_client_fixture("proboszcz_b")
client_wikariusz_a = _make_client_fixture("wikariusz_a")
client_parafianin_a = _make_client_fixture("parafianin_a")


@pytest.fixture
async def anon_client(mock_db, mock_ai, mock_storage, mock_cache) -> AsyncGenerator:
    """Klient bez uwierzytelnienia – sprawdzanie 401."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_ai] = lambda: mock_ai
    app.dependency_overrides[get_storage] = lambda: mock_storage
    app.dependency_overrides[get_cache] = lambda: mock_cache

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
