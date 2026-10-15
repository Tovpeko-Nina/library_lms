"""Безопасная конфигурация, общая для всех автоматических тестов."""

import os
from urllib.parse import urlsplit

import pytest

os.environ.setdefault(
    "SECRET_KEY",
    "test-only-secret-key-with-at-least-32-characters",
)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://lms_test:lms-test-password@127.0.0.1:5433/lms_test",
)


def _validate_test_database_url(database_url: str) -> None:
    """Не позволить тестам работать с БД без явного тестового имени."""
    parsed = urlsplit(database_url)
    database_name = parsed.path.removeprefix("/")
    if parsed.scheme not in {"postgresql", "postgres"} or not database_name.endswith("_test"):
        raise RuntimeError(
            "TEST_DATABASE_URL должна указывать на PostgreSQL-БД с именем, "
            "оканчивающимся на '_test'."
        )


_validate_test_database_url(TEST_DATABASE_URL)
# Приложение во время pytest всегда использует проверенный тестовый адрес, даже
# если в терминале разработчика экспортирован рабочий DATABASE_URL.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("SEED_DEMO_DATA", "false")
os.environ.setdefault("JWT_ISSUER", "library-lms-test")
os.environ.setdefault("JWT_AUDIENCE", "library-lms-test-suite")


@pytest.fixture(scope="session")
def initialized_database():
    """Создать схему в отдельной PostgreSQL для integration-тестов."""
    import psycopg
    from alembic import command
    from alembic.config import Config

    try:
        with psycopg.connect(TEST_DATABASE_URL):
            pass
    except psycopg.OperationalError as error:
        pytest.fail(
            "Тестовая PostgreSQL недоступна. Запустите make test-db-up "
            "или полный make test.\n"
            f"Причина: {error}",
            pytrace=False,
        )

    command.upgrade(Config("alembic.ini"), "head")
    return TEST_DATABASE_URL


@pytest.fixture
def clean_database(initialized_database):
    """Удалить данные между integration-тестами, сохранив таблицы."""
    import psycopg

    tables = (
        "favorite_books",
        "audit_log",
        "inventory_log",
        "usage_reports",
        "inventory_reports",
        "notifications",
        "fines",
        "loans",
        "reservations",
        "book_queue",
        "book_copies",
        "books",
        "borrowing_policy",
        "users",
    )
    with psycopg.connect(initialized_database) as connection:
        connection.execute(f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE")
        connection.execute("INSERT INTO borrowing_policy(policy_id) VALUES(gen_random_uuid())")
    return initialized_database
