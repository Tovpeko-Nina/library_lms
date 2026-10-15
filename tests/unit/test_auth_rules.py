from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services import auth
from tests.unit.fakes import install_database

pytestmark = pytest.mark.unit


def registration(**changes):
    result = {
        "login": "reader",
        "email": "reader@example.com",
        "password": "safe-password-123",
        "first_name": "Иван",
        "last_name": "Иванов",
        "role": "STUDENT",
    }
    result.update(changes)
    return SimpleNamespace(**result)


@pytest.mark.requirement("FR-01")
@pytest.mark.requirement("BR-01")
@pytest.mark.parametrize("role", ["STUDENT", "EMPLOYEE"])
def test_reader_roles_can_self_register(monkeypatch, role):
    database = install_database(monkeypatch, auth, [None, None])
    monkeypatch.setattr(auth, "hash_password", lambda password: f"hashed:{password}")

    result = auth.register_user(registration(role=role))

    assert result["message"] == "Регистрация выполнена"
    insert_params = next(params for query, params in database.calls if "INSERT INTO users" in query)
    assert insert_params[3] == "hashed:safe-password-123"
    assert insert_params[6] == role
    database.assert_finished()


@pytest.mark.requirement("BR-01")
@pytest.mark.requirement("ERR-08")
@pytest.mark.parametrize("role", ["ADMIN", "LIBRARIAN", "ROOT"])
def test_admin_and_librarian_cannot_self_register(role):
    with pytest.raises(HTTPException) as error:
        auth.register_user(registration(role=role))

    assert error.value.status_code == 400
    assert error.value.detail == "Регистрация доступна только читателям"


@pytest.mark.requirement("FR-01")
@pytest.mark.requirement("ERR-09")
def test_duplicate_login_or_email_is_rejected(monkeypatch):
    database = install_database(monkeypatch, auth, [{"exists": 1}])

    with pytest.raises(HTTPException) as error:
        auth.register_user(registration())

    assert error.value.status_code == 400
    assert error.value.detail == "Логин или email уже занят"
    assert not any("INSERT INTO users" in query for query, _ in database.calls)
    database.assert_finished()


@pytest.mark.requirement("FR-02")
@pytest.mark.requirement("FR-04")
def test_valid_credentials_return_access_token(monkeypatch):
    user = {
        "user_id": "reader-1",
        "role": "STUDENT",
        "password_hash": "stored-hash",
        "token_version": 0,
    }
    database = install_database(monkeypatch, auth, [user, None])
    monkeypatch.setattr(auth, "verify_password", lambda password, password_hash: True)
    monkeypatch.setattr(auth, "create_token", lambda current_user: "signed-token")

    result = auth.login_user(SimpleNamespace(login="reader", password="correct-password"))

    assert result == {
        "access_token": "signed-token",
        "token_type": "bearer",
        "role": "STUDENT",
    }
    assert any("SET last_login=CURRENT_TIMESTAMP" in query for query, _ in database.calls)
    database.assert_finished()


@pytest.mark.requirement("FR-02")
@pytest.mark.requirement("ERR-03")
def test_invalid_password_is_rejected_with_generic_message(monkeypatch):
    user = {
        "user_id": "reader-1",
        "role": "STUDENT",
        "password_hash": "stored-hash",
        "token_version": 0,
    }
    database = install_database(monkeypatch, auth, [user])
    monkeypatch.setattr(auth, "verify_password", lambda password, password_hash: False)

    with pytest.raises(HTTPException) as error:
        auth.login_user(SimpleNamespace(login="reader", password="wrong-password"))

    assert error.value.status_code == 401
    assert error.value.detail == "Неверный логин или пароль"
    database.assert_finished()


@pytest.mark.requirement("FR-02")
@pytest.mark.requirement("ERR-03")
def test_unknown_login_uses_dummy_hash_and_returns_generic_message(monkeypatch):
    database = install_database(monkeypatch, auth, [None])
    checked = []

    def record_verification(password, password_hash):
        checked.append((password, password_hash))
        return False

    monkeypatch.setattr(auth, "verify_password", record_verification)

    with pytest.raises(HTTPException) as error:
        auth.login_user(SimpleNamespace(login="unknown", password="some-password"))

    assert error.value.status_code == 401
    assert error.value.detail == "Неверный логин или пароль"
    assert checked == [("some-password", auth.DUMMY_PASSWORD_HASH)]
    database.assert_finished()
