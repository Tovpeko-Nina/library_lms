import argparse
import os
from pathlib import Path

from app.core.db_tools import create_backup


def main() -> None:
    parser = argparse.ArgumentParser(description="Создать резервную копию PostgreSQL")
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL обязателен")

    create_backup(database_url, arguments.output)
    print(f"Резервная копия: {arguments.output}")


if __name__ == "__main__":
    main()
