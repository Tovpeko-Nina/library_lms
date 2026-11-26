"""Безопасный запуск штатных инструментов резервного копирования PostgreSQL."""

import os
import shutil

# pg_dump/pg_restore are PostgreSQL's supported backup interface. They are
# invoked below without a shell and with an argument list, never as command text.
import subprocess  # nosec B404
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit


@dataclass(frozen=True)
class PostgreSQLConnection:
    host: str
    port: int
    user: str
    password: str
    database: str


def parse_database_url(database_url: str) -> PostgreSQLConnection:
    """Разобрать URL и не допустить неоднозначного подключения."""
    parsed = urlsplit(database_url)
    database = parsed.path.removeprefix("/")
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("Поддерживается только PostgreSQL DATABASE_URL")
    if not parsed.hostname or not parsed.username or not database:
        raise ValueError("DATABASE_URL должен содержать host, user и имя базы")

    return PostgreSQLConnection(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=unquote(parsed.username),
        password=unquote(parsed.password or ""),
        database=unquote(database),
    )


def _tool_environment(connection: PostgreSQLConnection) -> dict[str, str]:
    environment = os.environ.copy()
    environment["PGPASSWORD"] = connection.password
    return environment


def require_tool(name: str) -> str:
    executable = shutil.which(name)
    if not executable:
        raise RuntimeError(
            f"Не найден {name}. Установите PostgreSQL client tools "
            "(Ubuntu: sudo apt install postgresql-client)."
        )
    return executable


def create_backup(database_url: str, output_file: Path) -> None:
    connection = parse_database_url(database_url)
    executable = require_tool("pg_dump")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    # Executable is resolved locally and arguments are passed without a shell.
    subprocess.run(  # nosec B603
        [
            executable,
            "--host",
            connection.host,
            "--port",
            str(connection.port),
            "--username",
            connection.user,
            "--dbname",
            connection.database,
            "--format=custom",
            "--file",
            str(output_file),
        ],
        env=_tool_environment(connection),
        check=True,
    )


def restore_backup(database_url: str, backup_file: Path) -> None:
    if not backup_file.is_file():
        raise FileNotFoundError(f"Файл резервной копии не найден: {backup_file}")

    connection = parse_database_url(database_url)
    executable = require_tool("pg_restore")
    # Executable is resolved locally and arguments are passed without a shell.
    subprocess.run(  # nosec B603
        [
            executable,
            "--host",
            connection.host,
            "--port",
            str(connection.port),
            "--username",
            connection.user,
            "--dbname",
            connection.database,
            "--clean",
            "--if-exists",
            "--no-owner",
            str(backup_file),
        ],
        env=_tool_environment(connection),
        check=True,
    )
