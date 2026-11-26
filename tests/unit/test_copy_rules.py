from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services import copy
from tests.unit.fakes import install_database

pytestmark = pytest.mark.unit


@pytest.mark.requirement("FR-12")
def test_copy_status_change_is_recorded_in_inventory_log(monkeypatch):
    database = install_database(monkeypatch, copy, [{"status": "AVAILABLE"}, None, None])

    result = copy.change_status(
        "copy-1",
        SimpleNamespace(status="DAMAGED", reason="Повреждена обложка"),
        "librarian-1",
    )

    assert result == {"message": "Статус изменён"}
    update_query, update_params = database.calls[1]
    log_query, log_params = database.calls[2]
    assert "UPDATE book_copies" in update_query
    assert update_params == ("DAMAGED", "DAMAGED", "Повреждена обложка", "copy-1")
    assert "INSERT INTO inventory_log" in log_query
    assert log_params[1:] == (
        "copy-1",
        "librarian-1",
        "AVAILABLE",
        "DAMAGED",
        "Повреждена обложка",
    )
    database.assert_finished()


@pytest.mark.requirement("ERR-08")
def test_unknown_copy_status_is_rejected_before_database_change(monkeypatch):
    database = install_database(monkeypatch, copy, [])

    with pytest.raises(HTTPException) as error:
        copy.change_status(
            "copy-1",
            SimpleNamespace(status="DESTROYED", reason=None),
            "librarian-1",
        )

    assert error.value.status_code == 400
    assert database.calls == []
