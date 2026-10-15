import stat
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from scripts.bootstrap_env import (
    PASSWORD_PLACEHOLDER,
    SECRET_PLACEHOLDER,
    create_environment,
)

pytestmark = pytest.mark.unit


def parse_environment(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            name, value = line.split("=", 1)
            result[name] = value
    return result


def test_create_environment_generates_private_secrets(tmp_path):
    template = tmp_path / ".env.example"
    target = tmp_path / ".env"
    template.write_text(
        "\n".join(
            (
                f"SECRET_KEY={SECRET_PLACEHOLDER}",
                f"DATABASE_URL=postgresql://lms:{PASSWORD_PLACEHOLDER}@127.0.0.1:5432/lms",
                f"POSTGRES_PASSWORD={PASSWORD_PLACEHOLDER}",
            )
        ),
        encoding="utf-8",
    )

    assert create_environment(template, target) is True

    environment = parse_environment(target)
    database_url = urlsplit(environment["DATABASE_URL"])

    assert len(environment["SECRET_KEY"]) == 64
    assert len(environment["POSTGRES_PASSWORD"]) == 48
    assert database_url.password == environment["POSTGRES_PASSWORD"]
    assert SECRET_PLACEHOLDER not in target.read_text(encoding="utf-8")
    assert PASSWORD_PLACEHOLDER not in target.read_text(encoding="utf-8")
    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_create_environment_preserves_existing_file(tmp_path):
    template = tmp_path / ".env.example"
    target = tmp_path / ".env"
    template.write_text(
        f"SECRET_KEY={SECRET_PLACEHOLDER}\nPOSTGRES_PASSWORD={PASSWORD_PLACEHOLDER}\n",
        encoding="utf-8",
    )
    target.write_text("SECRET_KEY=existing-secret\n", encoding="utf-8")

    assert create_environment(template, target) is False
    assert target.read_text(encoding="utf-8") == "SECRET_KEY=existing-secret\n"
    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_create_environment_requires_known_placeholders(tmp_path):
    template = tmp_path / ".env.example"
    target = tmp_path / ".env"
    template.write_text("SECRET_KEY=already-replaced\n", encoding="utf-8")

    try:
        create_environment(template, target)
    except ValueError as error:
        assert "SECRET_KEY" in str(error)
    else:
        raise AssertionError("Ожидалась ошибка для шаблона без безопасных заглушек")
