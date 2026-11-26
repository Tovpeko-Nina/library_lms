import pytest
from fastapi import HTTPException

from app.services import notification
from tests.unit.fakes import install_database

pytestmark = pytest.mark.unit


@pytest.mark.requirement("FR-23")
def test_user_can_list_their_notifications(monkeypatch):
    rows = [{"notification_id": "notice-1", "user_id": "reader-1", "is_read": False}]
    database = install_database(monkeypatch, notification, [rows])

    result = notification.list_notifications("reader-1")

    assert result == rows
    assert database.calls[0][1] == ("reader-1",)
    database.assert_finished()


@pytest.mark.requirement("FR-23")
def test_notification_owner_can_mark_it_as_read(monkeypatch):
    database = install_database(monkeypatch, notification, [{"exists": 1}, None])

    result = notification.mark_read("notice-1", "reader-1")

    assert result == {"message": "Прочитано"}
    assert database.calls[0][1] == ("notice-1", "reader-1")
    assert "is_read=TRUE" in database.calls[1][0]
    database.assert_finished()


@pytest.mark.requirement("ERR-07")
def test_other_users_notification_is_not_exposed(monkeypatch):
    database = install_database(monkeypatch, notification, [None])

    with pytest.raises(HTTPException) as error:
        notification.mark_read("notice-1", "other-reader")

    assert error.value.status_code == 404
    database.assert_finished()
