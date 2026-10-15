import pytest

from app.core import db_tools

pytestmark = pytest.mark.unit


@pytest.mark.requirement("SEC-02")
def test_database_url_is_parsed_without_losing_escaped_credentials():
    connection = db_tools.parse_database_url(
        "postgresql://lms%20user:p%40ss@db.internal:5433/lms_test"
    )

    assert connection.host == "db.internal"
    assert connection.port == 5433
    assert connection.user == "lms user"
    assert connection.password == "p@ss"
    assert connection.database == "lms_test"


@pytest.mark.parametrize(
    "database_url",
    ["sqlite:///file.db", "postgresql:///lms", "postgresql://user@localhost"],
)
def test_invalid_database_url_is_rejected(database_url):
    with pytest.raises(ValueError):
        db_tools.parse_database_url(database_url)


@pytest.mark.requirement("REC-01")
@pytest.mark.requirement("SEC-09")
def test_backup_does_not_put_password_in_process_arguments(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(db_tools, "require_tool", lambda name: "/usr/bin/pg_dump")
    monkeypatch.setattr(
        db_tools.subprocess, "run", lambda command, **options: calls.append((command, options))
    )

    output = tmp_path / "backup.dump"
    db_tools.create_backup("postgresql://lms:top-secret@db:5432/lms", output)

    command, options = calls[0]
    assert "top-secret" not in " ".join(command)
    assert options["env"]["PGPASSWORD"] == "top-secret"
    assert options["check"] is True


@pytest.mark.requirement("REC-03")
@pytest.mark.requirement("REC-04")
def test_restore_rejects_missing_backup_before_starting_tool(monkeypatch, tmp_path):
    monkeypatch.setattr(
        db_tools,
        "require_tool",
        lambda name: pytest.fail("pg_restore не должен запускаться"),
    )

    with pytest.raises(FileNotFoundError):
        db_tools.restore_backup(
            "postgresql://lms:password@db:5432/lms",
            tmp_path / "missing.dump",
        )


@pytest.mark.requirement("REC-03")
def test_restore_uses_clean_mode_and_does_not_expose_password(monkeypatch, tmp_path):
    backup = tmp_path / "backup.dump"
    backup.touch()
    calls = []
    monkeypatch.setattr(db_tools, "require_tool", lambda name: "/usr/bin/pg_restore")
    monkeypatch.setattr(
        db_tools.subprocess, "run", lambda command, **options: calls.append((command, options))
    )

    db_tools.restore_backup("postgresql://lms:top-secret@db:5432/lms", backup)

    command, options = calls[0]
    assert "--clean" in command
    assert "--if-exists" in command
    assert "--no-owner" in command
    assert "top-secret" not in " ".join(command)
    assert options["env"]["PGPASSWORD"] == "top-secret"
