from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core import security

pytestmark = pytest.mark.unit


@pytest.mark.requirement("FR-03")
@pytest.mark.requirement("SEC-07")
def test_password_is_stored_as_bcrypt_hash():
    password = "safe-password-123"

    password_hash = security.hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$2")
    assert security.verify_password(password, password_hash) is True


@pytest.mark.requirement("FR-03")
@pytest.mark.requirement("ERR-03")
def test_wrong_password_does_not_match_bcrypt_hash():
    password_hash = security.hash_password("safe-password-123")

    assert security.verify_password("wrong-password", password_hash) is False


@pytest.mark.requirement("ERR-03")
def test_invalid_password_hash_is_rejected_without_internal_error():
    assert security.verify_password("safe-password-123", "not-a-bcrypt-hash") is False


@pytest.mark.requirement("FR-04")
@pytest.mark.requirement("SEC-12")
def test_created_token_contains_required_identity_and_security_claims():
    user = {"user_id": "reader-1", "role": "STUDENT", "token_version": 4}

    token = security.create_token(user)
    payload = security.decode_token(token)

    assert payload["sub"] == "reader-1"
    assert payload["role"] == "STUDENT"
    assert payload["ver"] == 4
    assert payload["iss"] == security.JWT_ISSUER
    assert payload["aud"] == security.JWT_AUDIENCE
    assert payload["jti"]
    assert payload["exp"] > payload["iat"]


@pytest.mark.requirement("SEC-12")
@pytest.mark.requirement("ERR-05")
@pytest.mark.parametrize(
    ("claim", "value"),
    [
        ("iss", "wrong-issuer"),
        ("aud", "wrong-audience"),
    ],
)
def test_token_with_wrong_issuer_or_audience_is_rejected(claim, value):
    now = datetime.now(UTC)
    payload = {
        "sub": "reader-1",
        "role": "STUDENT",
        "ver": 0,
        "iss": security.JWT_ISSUER,
        "aud": security.JWT_AUDIENCE,
        "iat": now,
        "jti": "token-id",
        "exp": now + timedelta(minutes=5),
    }
    payload[claim] = value
    token = jwt.encode(payload, security.SECRET_KEY, algorithm="HS256")

    with pytest.raises(jwt.InvalidTokenError):
        security.decode_token(token)


@pytest.mark.requirement("SEC-12")
@pytest.mark.requirement("ERR-05")
def test_expired_token_is_rejected():
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": "reader-1",
            "role": "STUDENT",
            "ver": 0,
            "iss": security.JWT_ISSUER,
            "aud": security.JWT_AUDIENCE,
            "iat": now - timedelta(minutes=10),
            "jti": "expired-token",
            "exp": now - timedelta(minutes=5),
        },
        security.SECRET_KEY,
        algorithm="HS256",
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        security.decode_token(token)
