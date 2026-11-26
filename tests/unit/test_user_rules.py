from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services import user as user_service
from tests.unit.fakes import install_database

pytestmark = pytest.mark.unit


@pytest.mark.requirement("SEC-08")
def test_user_list_removes_authentication_fields(monkeypatch):
    database = install_database(
        monkeypatch,
        user_service,
        [[{"user_id": "reader-1", "password_hash": "hash", "token_version": 3}]],
    )

    result = user_service.list_users(role="STUDENT", verified=True)

    assert result == [{"user_id": "reader-1"}]
    query, params = database.calls[0]
    assert "role=?" in query
    assert "is_verified=?" in query
    assert params == ["STUDENT", True]
    database.assert_finished()


@pytest.mark.requirement("FR-13")
def test_librarian_can_verify_reader(monkeypatch):
    database = install_database(monkeypatch, user_service, [None])

    result = user_service.verify_user("reader-1")

    assert result == {"message": "Пользователь верифицирован"}
    assert "is_verified=TRUE" in database.calls[0][0]
    database.assert_finished()


@pytest.mark.requirement("FR-14")
def test_admin_can_deactivate_user(monkeypatch):
    database = install_database(monkeypatch, user_service, [None])

    result = user_service.deactivate_user("reader-1")

    assert result == {"message": "Пользователь деактивирован"}
    assert "is_active=FALSE" in database.calls[0][0]
    database.assert_finished()


@pytest.mark.requirement("FR-14")
@pytest.mark.requirement("ERR-08")
def test_active_user_cannot_be_permanently_deleted(monkeypatch):
    database = install_database(
        monkeypatch,
        user_service,
        [{"user_id": "reader-1", "role": "STUDENT", "is_active": True}],
    )

    with pytest.raises(HTTPException) as error:
        user_service.delete_user_permanently("reader-1", "admin-1")

    assert error.value.status_code == 400
    assert error.value.detail == "Сначала деактивируйте пользователя"
    database.assert_finished()


@pytest.mark.requirement("FR-14")
@pytest.mark.requirement("ERR-09")
def test_user_with_library_history_cannot_be_permanently_deleted(monkeypatch):
    database = install_database(
        monkeypatch,
        user_service,
        [
            {"user_id": "reader-1", "role": "STUDENT", "is_active": False},
            {"has_references": True},
        ],
    )

    with pytest.raises(HTTPException) as error:
        user_service.delete_user_permanently("reader-1", "admin-1")

    assert error.value.status_code == 409
    assert "историей библиотеки" in error.value.detail
    database.assert_finished()


@pytest.mark.requirement("FR-14")
def test_unused_inactive_user_can_be_permanently_deleted(monkeypatch):
    database = install_database(
        monkeypatch,
        user_service,
        [
            {"user_id": "reader-1", "role": "STUDENT", "is_active": False},
            {"has_references": False},
            None,
        ],
    )

    result = user_service.delete_user_permanently("reader-1", "admin-1")

    assert result == {"message": "Пользователь удалён окончательно"}
    assert "DELETE FROM users" in database.calls[-1][0]
    database.assert_finished()


@pytest.mark.requirement("FR-01")
@pytest.mark.requirement("SEC-07")
def test_admin_can_create_librarian_with_hashed_password(monkeypatch):
    database = install_database(monkeypatch, user_service, [None, None])
    monkeypatch.setattr(
        user_service,
        "hash_password",
        lambda password: f"hashed:{password}",
    )
    data = SimpleNamespace(
        login="librarian",
        email="librarian@example.com",
        password="safe-password-123",
        first_name="Анна",
        last_name="Петрова",
    )

    result = user_service.create_librarian(data)

    assert result["user_id"]
    insert_params = database.calls[-1][1]
    assert insert_params[3] == "hashed:safe-password-123"
    database.assert_finished()
