import pytest
from fastapi import HTTPException

from app.services import reservation
from tests.unit.fakes import install_database

pytestmark = pytest.mark.unit


def book():
    return {"title": "Чистый код"}


def reader():
    return {"login": "reader", "first_name": "Иван", "last_name": "Иванов"}


@pytest.mark.requirement("BR-19")
@pytest.mark.requirement("ERR-09")
def test_duplicate_active_reservation_is_rejected(monkeypatch):
    database = install_database(monkeypatch, reservation, [book(), {"exists": 1}])

    with pytest.raises(HTTPException) as error:
        reservation.reserve_book("book-1", "reader-1")

    assert error.value.status_code == 400
    assert "активная бронь" in error.value.detail
    database.assert_finished()


@pytest.mark.requirement("BR-19")
@pytest.mark.requirement("ERR-09")
def test_duplicate_active_queue_entry_is_rejected(monkeypatch):
    database = install_database(monkeypatch, reservation, [book(), None, {"exists": 1}])

    with pytest.raises(HTTPException) as error:
        reservation.reserve_book("book-1", "reader-1")

    assert error.value.status_code == 400
    assert "очереди" in error.value.detail
    database.assert_finished()


@pytest.mark.requirement("FR-19")
@pytest.mark.requirement("BR-13")
@pytest.mark.requirement("BR-20")
def test_unavailable_book_places_reader_in_queue_and_notifies_staff(monkeypatch):
    database = install_database(
        monkeypatch,
        reservation,
        [
            book(),
            None,
            None,
            reader(),
            None,
            {"next_position": 3},
            None,
            [{"user_id": "librarian-1"}, {"user_id": "admin-1"}],
            None,
            None,
        ],
    )

    result = reservation.reserve_book("book-1", "reader-1", 2020, 2)

    assert result["queued"] is True
    assert result["position"] == 3
    assert any("INSERT INTO book_queue" in query for query, _ in database.calls)
    notifications = [
        params for query, params in database.calls if "INSERT INTO notifications" in query
    ]
    assert len(notifications) == 2
    assert {params[1] for params in notifications} == {"librarian-1", "admin-1"}
    database.assert_finished()


@pytest.mark.requirement("FR-18")
@pytest.mark.requirement("BR-13")
def test_available_copy_is_reserved_and_staff_is_notified(monkeypatch):
    database = install_database(
        monkeypatch,
        reservation,
        [
            book(),
            None,
            None,
            reader(),
            {"copy_id": "copy-1", "copy_number": 2},
            None,
            None,
            [{"user_id": "librarian-1"}],
            None,
        ],
    )

    result = reservation.reserve_book("book-1", "reader-1", 2020, 2)

    assert result["queued"] is False
    assert result["reservation_id"]
    assert any("INSERT INTO reservations" in query for query, _ in database.calls)
    assert any("SET status='RESERVED'" in query for query, _ in database.calls)
    assert any("INSERT INTO notifications" in query for query, _ in database.calls)
    database.assert_finished()


@pytest.mark.requirement("BR-11")
@pytest.mark.requirement("BR-12")
def test_active_reservations_and_queue_are_visible_to_staff(monkeypatch):
    reservations = [{"reservation_id": "reservation-1", "title": "Чистый код"}]
    queue = [{"queue_id": "queue-1", "position": 1, "title": "Архитектура"}]
    database = install_database(monkeypatch, reservation, [reservations, queue])

    result = reservation.list_staff_requests()

    assert result == {"reservations": reservations, "queue": queue}
    database.assert_finished()
