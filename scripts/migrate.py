"""Apply Alembic migrations and safely adopt the pre-Alembic schema."""

import os

import psycopg
from alembic import command
from alembic.config import Config

LEGACY_REQUIRED_COLUMNS = {
    ("users", "token_version"),
    ("book_copies", "publication_year"),
    ("book_copies", "edition_number"),
    ("reservations", "preferred_publication_year"),
    ("reservations", "preferred_edition_number"),
    ("book_queue", "preferred_publication_year"),
    ("book_queue", "preferred_edition_number"),
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
    """Stamp a verified old init_db schema without changing its data."""
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

    command.stamp(config, "003")
    return True


def main() -> None:
    config = Config("alembic.ini")
    database_url = _database_url()
    adopted = adopt_legacy_schema_if_needed(config, database_url)
    if adopted:
        print("Existing pre-Alembic schema marked as revision 003; data preserved.")
    command.upgrade(config, "head")


if __name__ == "__main__":
    main()
