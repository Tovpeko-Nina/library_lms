"""HTTP-проверки маршрутизации, валидации и контроля доступа FastAPI."""

import uuid

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_token, hash_password
from app.main import app

pytestmark = [pytest.mark.api, pytest.mark.integration]


@pytest.fixture
def client(clean_database):
    with TestClient(app) as test_client:
        yield test_client


def _create_user(database_url, *, role="STUDENT", verified=True, password="valid-password-123"):
    user = {
        "user_id": uuid.uuid4(),
        "login": f"user-{uuid.uuid4().hex[:8]}",
        "email": f"{uuid.uuid4().hex[:8]}@example.test",
        "password_hash": hash_password(password),
        "first_name": "Иван",
        "last_name": "Иванов",
        "role": role,
        "is_verified": verified,
        "token_version": 0,
    }
    with psycopg.connect(database_url) as connection:
        connection.execute(
            """
            INSERT INTO users(
                user_id, login, email, password_hash, first_name, last_name,
                role, is_verified, registration_date, token_version
            ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, %s)
            """,
            tuple(user.values()),
        )
    return user, password


def _authorization(user):
    return {"Authorization": f"Bearer {create_token(user)}"}


@pytest.mark.requirement("ERR-04")
@pytest.mark.requirement("SEC-12")
def test_protected_api_without_token_returns_401(client):
    response = client.get("/api/v1/favorites")

    assert response.status_code == 401
    assert response.json() == {"detail": "Требуется Bearer JWT"}


@pytest.mark.requirement("ERR-06")
@pytest.mark.requirement("SEC-13")
def test_librarian_cannot_use_reader_favorites_api(client, clean_database):
    librarian, _ = _create_user(clean_database, role="LIBRARIAN")

    response = client.get("/api/v1/favorites", headers=_authorization(librarian))

    assert response.status_code == 403
    assert response.json() == {"detail": "Недостаточно прав"}


@pytest.mark.requirement("ERR-01")
@pytest.mark.requirement("SEC-05")
def test_registration_with_short_password_returns_422(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "login": "short-password",
            "email": "short@example.com",
            "password": "too-short",
            "first_name": "Иван",
            "last_name": "Иванов",
            "role": "STUDENT",
        },
    )

    assert response.status_code == 422


@pytest.mark.requirement("BR-01")
@pytest.mark.requirement("ERR-08")
def test_admin_cannot_self_register_through_api(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "login": "self-admin",
            "email": "admin@example.com",
            "password": "valid-password-123",
            "first_name": "Анна",
            "last_name": "Администратор",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Регистрация доступна только читателям"}


@pytest.mark.requirement("FR-01")
@pytest.mark.requirement("SEC-07")
def test_student_registration_persists_bcrypt_hash(client, clean_database):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "login": "new-reader",
            "email": "new-reader@example.com",
            "password": "valid-password-123",
            "first_name": "Иван",
            "last_name": "Иванов",
            "role": "STUDENT",
        },
    )

    assert response.status_code == 200
    with psycopg.connect(clean_database) as connection:
        saved = connection.execute(
            "SELECT role, is_verified, password_hash FROM users WHERE login='new-reader'"
        ).fetchone()

    assert saved is not None
    assert saved[0:2] == ("STUDENT", False)
    assert saved[2].startswith("$2")
    assert "valid-password-123" not in saved[2]


@pytest.mark.requirement("FR-02")
@pytest.mark.requirement("FR-04")
def test_valid_login_returns_bearer_token(client, clean_database):
    user, password = _create_user(clean_database)

    response = client.post(
        "/api/v1/auth/login",
        json={"login": user["login"], "password": password},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["role"] == "STUDENT"
    assert payload["access_token"]


@pytest.mark.requirement("FR-27")
def test_reader_can_add_list_and_remove_favorite(client, clean_database):
    reader, _ = _create_user(clean_database)
    book_id = uuid.uuid4()
    with psycopg.connect(clean_database) as connection:
        connection.execute(
            "INSERT INTO books(book_id, title, author) VALUES(%s, %s, %s)",
            (book_id, "Избранная книга", "Автор"),
        )
    headers = _authorization(reader)

    added = client.put(f"/api/v1/favorites/{book_id}", headers=headers)
    listed = client.get("/api/v1/favorites", headers=headers)
    removed = client.delete(f"/api/v1/favorites/{book_id}", headers=headers)
    empty = client.get("/api/v1/favorites", headers=headers)

    assert added.status_code == 200
    assert listed.status_code == 200
    assert [book["book_id"] for book in listed.json()] == [str(book_id)]
    assert removed.status_code == 200
    assert empty.json() == []
