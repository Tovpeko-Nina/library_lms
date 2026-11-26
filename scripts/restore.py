import argparse
import os
from pathlib import Path

from app.core.db_tools import restore_backup


def main() -> None:
    parser = argparse.ArgumentParser(description="Восстановить PostgreSQL из резервной копии")
    parser.add_argument("--backup-file", required=True, type=Path)
    parser.add_argument("--confirm", action="store_true")
    arguments = parser.parse_args()

    if not arguments.confirm:
        raise SystemExit("Восстановление изменит БД; требуется --confirm")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL обязателен")

    restore_backup(database_url, arguments.backup_file)
    print(f"База восстановлена из: {arguments.backup_file}")


if __name__ == "__main__":
    main()
