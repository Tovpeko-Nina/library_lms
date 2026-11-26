"""Проверки создания и последовательного обновления схемы Alembic."""

import uuid

import psycopg
import pytest
from alembic import command
from alembic.config import Config

pytestmark = pytest.mark.migration


def _alembic_config() -> Config:
    return Config("alembic.ini")


@pytest.mark.requirement("MIG-02")
def test_clean_database_upgrades_to_head(initialized_database):
    command.downgrade(_alembic_config(), "base")
    command.upgrade(_alembic_config(), "head")

    with psycopg.connect(initialized_database) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        queue_exists = connection.execute("SELECT to_regclass('public.book_queue')").fetchone()
        favorites_exist = connection.execute(
            "SELECT to_regclass('public.favorite_books')"
        ).fetchone()

    assert revision == ("004",)
    assert queue_exists == ("book_queue",)
    assert favorites_exist == ("favorite_books",)


@pytest.mark.requirement("MIG-01")
def test_revisions_are_applied_in_order(initialized_database):
    command.downgrade(_alembic_config(), "base")

    for revision in ("001", "002", "003", "004"):
        command.upgrade(_alembic_config(), revision)
        with psycopg.connect(initialized_database) as connection:
            current = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        assert current == (revision,)


@pytest.mark.requirement("MIG-03")
def test_populated_database_upgrades_without_data_loss(initialized_database):
    command.downgrade(_alembic_config(), "base")
    command.upgrade(_alembic_config(), "001")
    user_id = uuid.uuid4()

    with psycopg.connect(initialized_database) as connection:
        connection.execute(
            """
            INSERT INTO users(
                user_id, login, email, password_hash, first_name, last_name,
                role, is_verified, registration_date
            ) VALUES(%s, 'saved-reader', 'saved@example.test', 'hash',
                     'Иван', 'Иванов', 'STUDENT', TRUE, CURRENT_DATE)
            """,
            (user_id,),
        )

    command.upgrade(_alembic_config(), "head")

    with psycopg.connect(initialized_database) as connection:
        saved_user = connection.execute(
            "SELECT login, token_version FROM users WHERE user_id = %s", (user_id,)
        ).fetchone()
        current = connection.execute("SELECT version_num FROM alembic_version").fetchone()

    assert saved_user == ("saved-reader", 0)
    assert current == ("004",)


@pytest.mark.requirement("MIG-04")
def test_upgrade_head_is_idempotent(initialized_database):
    command.upgrade(_alembic_config(), "head")
    marker_id = uuid.uuid4()

    with psycopg.connect(initialized_database) as connection:
        connection.execute(
            """
            INSERT INTO books(book_id, isbn, title, author)
            VALUES(%s, 'MIG-IDEMPOTENT', 'Сохранённая книга', 'Migration Test')
            ON CONFLICT (isbn) DO UPDATE SET title=EXCLUDED.title
            """,
            (marker_id,),
        )
        tables_before = {
            row[0]
            for row in connection.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
        }

    command.upgrade(_alembic_config(), "head")

    with psycopg.connect(initialized_database) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        tables_after = {
            row[0]
            for row in connection.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )
        }
        marker = connection.execute(
            "SELECT title FROM books WHERE isbn='MIG-IDEMPOTENT'"
        ).fetchone()

    assert revision == ("004",)
    assert tables_after == tables_before
    assert marker == ("Сохранённая книга",)
