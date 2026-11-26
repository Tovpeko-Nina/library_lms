"""Проверка отказа проверочного контура при ошибке миграции."""

import pytest

from scripts import migrate

pytestmark = pytest.mark.migration


@pytest.mark.requirement("MIG-07")
@pytest.mark.requirement("QA-12")
def test_broken_migration_error_is_not_swallowed(monkeypatch):
    expected_error = RuntimeError("synthetic broken migration")
    monkeypatch.setattr(migrate, "_database_url", lambda: "postgresql://test/lms_test")
    monkeypatch.setattr(
        migrate,
        "adopt_legacy_schema_if_needed",
        lambda config, database_url: False,
    )

    def broken_upgrade(config, revision):
        raise expected_error

    monkeypatch.setattr(migrate.command, "upgrade", broken_upgrade)

    with pytest.raises(RuntimeError) as error:
        migrate.main()

    assert error.value is expected_error
