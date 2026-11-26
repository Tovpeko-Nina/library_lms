"""Интеграционные проверки настоящей схемы и транзакций PostgreSQL."""

import uuid

import psycopg
import pytest

from app.core.database import get_db
from app.services import favorite

pytestmark = pytest.mark.integration


def _insert_user(connection, *, login: str = "reader", email: str = "reader@example.test"):
    user_id = uuid.uuid4()
    connection.execute(
        """
        INSERT INTO users (
            user_id, login, email, password_hash, first_name, last_name,
            role, is_verified, registration_date
        ) VALUES (%s, %s, %s, %s, %s, %s, 'STUDENT', TRUE, CURRENT_DATE)
        """,
        (user_id, login, email, "bcrypt-hash", "Иван", "Иванов"),
    )
    return user_id


@pytest.mark.requirement("QA-04")
def test_schema_is_created_in_dedicated_postgresql(clean_database):
    with psycopg.connect(clean_database) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
        }
        policy_row = connection.execute("SELECT COUNT(*) FROM borrowing_policy").fetchone()

    assert {"users", "books", "book_copies", "loans", "reservations"} <= table_names
    assert policy_row is not None
    assert policy_row[0] == 1


@pytest.mark.requirement("ERR-09")
def test_database_rejects_duplicate_login(clean_database):
    with psycopg.connect(clean_database) as connection:
        _insert_user(connection)
        with pytest.raises(psycopg.errors.UniqueViolation):
            _insert_user(connection, email="another@example.test")


@pytest.mark.requirement("FR-11")
@pytest.mark.parametrize("publication_year", [999, 10000])
def test_database_rejects_invalid_copy_publication_year(clean_database, publication_year):
    with psycopg.connect(clean_database) as connection:
        book_id = uuid.uuid4()
        connection.execute(
            "INSERT INTO books(book_id, title, author) VALUES(%s, %s, %s)",
            (book_id, "Тестовая книга", "Автор"),
        )
        with pytest.raises(psycopg.errors.CheckViolation):
            connection.execute(
                """
                INSERT INTO book_copies(
                    copy_id, book_id, branch, status, publication_year,
                    acquisition_date
                ) VALUES(%s, %s, 'MAIN', 'AVAILABLE', %s, CURRENT_DATE)
                """,
                (uuid.uuid4(), book_id, publication_year),
            )


@pytest.mark.requirement("ERR-10")
def test_get_db_rolls_back_transaction_after_error(clean_database):
    login = "rollback-reader"

    with pytest.raises(RuntimeError, match="planned failure"):
        with get_db() as database:
            _insert_user(database.connection, login=login, email="rollback@example.test")
            raise RuntimeError("planned failure")

    with psycopg.connect(clean_database) as connection:
        user_count_row = connection.execute(
            "SELECT COUNT(*) FROM users WHERE login = %s", (login,)
        ).fetchone()

    assert user_count_row is not None
    assert user_count_row[0] == 0


@pytest.mark.requirement("FR-27")
def test_favorite_lifecycle_is_persisted_in_postgresql(clean_database):
    with psycopg.connect(clean_database) as connection:
        user_id = _insert_user(connection)
        book_id = uuid.uuid4()
        connection.execute(
            "INSERT INTO books(book_id, title, author) VALUES(%s, %s, %s)",
            (book_id, "Избранная книга", "Автор"),
        )

    favorite.add_favorite(user_id, book_id)
    favorite.add_favorite(user_id, book_id)
    saved = favorite.list_favorites(user_id)

    assert len(saved) == 1
    assert saved[0]["book_id"] == book_id

    favorite.remove_favorite(user_id, book_id)
    assert favorite.list_favorites(user_id) == []
