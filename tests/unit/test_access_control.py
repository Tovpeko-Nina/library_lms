from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.v1 import deps
from app.services import user as user_service
from tests.unit.fakes import install_database

pytestmark = pytest.mark.unit


@pytest.mark.requirement("SEC-08")
def test_public_user_response_never_contains_authentication_fields():
    result = user_service.public_user(
        {
            "user_id": "reader-1",
            "login": "reader",
            "password_hash": "secret-hash",
            "token_version": 7,
        }
    )

    assert result == {"user_id": "reader-1", "login": "reader"}
    assert "password_hash" not in result
    assert "token_version" not in result


@pytest.mark.requirement("ERR-04")
@pytest.mark.requirement("SEC-12")
def test_protected_operation_without_token_returns_401():
    with pytest.raises(HTTPException) as error:
        deps.current_user(None)

    assert error.value.status_code == 401
    assert error.value.detail == "Требуется Bearer JWT"


@pytest.mark.requirement("ERR-05")
@pytest.mark.requirement("SEC-12")
def test_invalid_token_returns_401(monkeypatch):
    def invalid_token(_token):
        raise ValueError("invalid token")

    monkeypatch.setattr(deps, "decode_token", invalid_token)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="broken")

    with pytest.raises(HTTPException) as error:
        deps.current_user(credentials)

    assert error.value.status_code == 401
    assert error.value.detail == "Недействительный токен"


@pytest.mark.requirement("SEC-10")
@pytest.mark.requirement("SEC-11")
@pytest.mark.requirement("ERR-05")
def test_revoked_token_version_returns_401(monkeypatch):
    monkeypatch.setattr(
        deps,
        "decode_token",
        lambda token: {"sub": "reader-1", "ver": 2},
    )
    monkeypatch.setattr(
        deps,
        "get_current_user",
        lambda user_id: {"user_id": user_id, "role": "STUDENT", "token_version": 3},
    )
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="old-token")

    with pytest.raises(HTTPException) as error:
        deps.current_user(credentials)

    assert error.value.status_code == 401
    assert error.value.detail == "Токен отозван"


@pytest.mark.requirement("SEC-12")
def test_current_user_accepts_matching_token_version(monkeypatch):
    expected_user = {"user_id": "reader-1", "role": "STUDENT", "token_version": 3}
    monkeypatch.setattr(
        deps,
        "decode_token",
        lambda token: {"sub": "reader-1", "ver": 3},
    )
    monkeypatch.setattr(deps, "get_current_user", lambda user_id: expected_user)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

    assert deps.current_user(credentials) is expected_user


@pytest.mark.requirement("FR-05")
@pytest.mark.requirement("SEC-13")
@pytest.mark.requirement("ERR-06")
def test_reader_cannot_call_librarian_operation():
    require_staff = deps.roles("ADMIN", "LIBRARIAN")

    with pytest.raises(HTTPException) as error:
        require_staff({"user_id": "reader-1", "role": "STUDENT"})

    assert error.value.status_code == 403
    assert error.value.detail == "Недостаточно прав"


@pytest.mark.requirement("FR-05")
@pytest.mark.requirement("SEC-13")
@pytest.mark.parametrize("role", ["ADMIN", "LIBRARIAN"])
def test_staff_role_can_call_librarian_operation(role):
    require_staff = deps.roles("ADMIN", "LIBRARIAN")
    current_user = {"user_id": "staff-1", "role": role}

    assert require_staff(current_user) is current_user


@pytest.mark.requirement("SEC-10")
def test_password_change_hashes_password_and_increments_token_version(monkeypatch):
    database = install_database(monkeypatch, user_service, [None])
    monkeypatch.setattr(user_service, "verify_password", lambda password, password_hash: True)
    monkeypatch.setattr(user_service, "hash_password", lambda password: f"hashed:{password}")

    result = user_service.change_password(
        {"user_id": "reader-1", "password_hash": "old-hash"},
        SimpleNamespace(current_password="old-password", new_password="new-password-123"),
    )

    assert result == {"message": "Пароль изменён"}
    query, params = database.calls[0]
    assert "token_version=token_version+1" in query
    assert params == ("hashed:new-password-123", "reader-1")
    database.assert_finished()


@pytest.mark.requirement("SEC-11")
def test_logout_increments_token_version(monkeypatch):
    database = install_database(monkeypatch, user_service, [None])

    result = user_service.revoke_tokens("reader-1")

    assert result == {"message": "Сеанс завершён"}
    query, params = database.calls[0]
    assert "token_version=token_version+1" in query
    assert params == ("reader-1",)
    database.assert_finished()
