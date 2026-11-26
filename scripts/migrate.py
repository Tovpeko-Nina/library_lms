"""Apply Alembic migrations and safely adopt the pre-Alembic schema."""

import os

import psycopg
from alembic import command
from alembic.config import Config

LEGACY_REQUIRED_COLUMNS = {
    ("users", "user_id"),
    ("users", "password_hash"),
    ("books", "book_id"),
    ("book_copies", "copy_id"),
    ("loans", "loan_id"),
    ("reservations", "reservation_id"),
    ("inventory_log", "log_id"),
    ("audit_log", "entry_id"),
    ("book_queue", "queue_id"),
}
LEGACY_REQUIRED_TABLES = {"audit_log", "book_queue", "inventory_log"}


def _database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is required")
    return value


def _existing_tables(connection) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
        )
    }


def _existing_columns(connection) -> set[tuple[str, str]]:
    return {
        (row[0], row[1])
        for row in connection.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            """
        )
    }


def adopt_legacy_schema_if_needed(config: Config, database_url: str) -> bool:
    """Mark a verified pre-Alembic schema as revision 002 without changing data."""
    with psycopg.connect(database_url) as connection:
        tables = _existing_tables(connection)
        if "alembic_version" in tables or "users" not in tables:
            return False

        missing_tables = LEGACY_REQUIRED_TABLES - tables
        missing_columns = LEGACY_REQUIRED_COLUMNS - _existing_columns(connection)
        if missing_tables or missing_columns:
            details = []
            if missing_tables:
                details.append(f"missing tables: {sorted(missing_tables)}")
            if missing_columns:
                details.append(f"missing columns: {sorted(missing_columns)}")
            raise RuntimeError(
                "Existing database has no Alembic version and does not match "
                f"the verified legacy schema ({'; '.join(details)})."
            )

    command.stamp(config, "002")
    return True


def main() -> None:
    config = Config("alembic.ini")
    database_url = _database_url()
    adopted = adopt_legacy_schema_if_needed(config, database_url)
    if adopted:
        print("Existing pre-Alembic schema marked as revision 002; data preserved.")
    command.upgrade(config, "head")


if __name__ == "__main__":
    main()
