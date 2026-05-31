"""Testy jednostkowe serwisu auth (JWT, bcrypt) – bez bazy danych."""
import time
from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError, jwt

from app.services.auth import (
    TOKEN_EXPIRE_HOURS,
    ALGORITHM,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import settings


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("tajne123")
        assert hashed != "tajne123"
        assert len(hashed) > 30

    def test_correct_password_verifies(self):
        hashed = hash_password("MojeHaslo!")
        assert verify_password("MojeHaslo!", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("MojeHaslo!")
        assert verify_password("ZleHaslo!", hashed) is False

    def test_empty_string_hashes_and_verifies(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("x", hashed) is False

    def test_each_hash_is_unique(self):
        h1 = hash_password("to_samo")
        h2 = hash_password("to_samo")
        assert h1 != h2  # bcrypt stosuje losowy salt


class TestJwtTokens:
    def test_token_decodes_correctly(self):
        payload = {"sub": "abc-123", "rola": "proboszcz", "parafia_id": "xyz"}
        token = create_access_token(payload)
        decoded = decode_token(token)
        assert decoded["sub"] == "abc-123"
        assert decoded["rola"] == "proboszcz"
        assert decoded["parafia_id"] == "xyz"

    def test_token_has_expiry_field(self):
        token = create_access_token({"sub": "user"})
        decoded = decode_token(token)
        assert "exp" in decoded
        assert "iat" in decoded

    def test_token_expires_correctly(self):
        token = create_access_token({"sub": "user"})
        decoded = decode_token(token)
        exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        iat = datetime.fromtimestamp(decoded["iat"], tz=timezone.utc)
        delta = exp - iat
        assert abs(delta.total_seconds() - TOKEN_EXPIRE_HOURS * 3600) < 5

    def test_tampered_token_raises(self):
        token = create_access_token({"sub": "user"})
        bad_token = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_token(bad_token)

    def test_expired_token_raises(self):
        past = datetime.now(timezone.utc) - timedelta(seconds=1)
        expired_token = jwt.encode(
            {"sub": "user", "exp": past, "iat": past},
            settings.secret_key,
            algorithm=ALGORITHM,
        )
        with pytest.raises(JWTError):
            decode_token(expired_token)

    def test_wrong_secret_raises(self):
        token = jwt.encode({"sub": "u", "exp": time.time() + 3600}, "inny_sekret", algorithm=ALGORITHM)
        with pytest.raises(JWTError):
            decode_token(token)
