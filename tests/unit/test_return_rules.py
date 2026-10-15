from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.services import loan
from tests.unit.fakes import install_database
from tests.unit.test_loan_rules import policy

pytestmark = pytest.mark.unit


def active_loan(**changes):
    result = {
        "loan_id": "loan-1",
        "copy_id": "copy-1",
        "user_id": "reader-1",
        "due_date": date.today(),
    }
    result.update(changes)
    return result


def return_request(**changes):
    result = {
        "loan_id": "loan-1",
        "lost": False,
        "damaged": False,
        "damage_note": None,
    }
    result.update(changes)
    return SimpleNamespace(**result)


@pytest.mark.requirement("FR-16")
@pytest.mark.requirement("BR-10")
def test_normal_return_sets_copy_status_to_available(monkeypatch):
    database = install_database(
        monkeypatch,
        loan,
        [active_loan(), policy(), None, None],
    )

    result = loan.return_book(return_request())

    assert result == {"message": "Возврат обработан", "fine": 0, "status": "AVAILABLE"}
    copy_update = next(params for query, params in database.calls if "UPDATE book_copies" in query)
    assert copy_update[0] == "AVAILABLE"
    assert not any("INSERT INTO fines" in query for query, _ in database.calls)
    database.assert_finished()


@pytest.mark.requirement("FR-21")
@pytest.mark.requirement("BR-14")
@pytest.mark.requirement("BR-17")
def test_lost_return_sets_copy_status_and_creates_fine(monkeypatch):
    database = install_database(
        monkeypatch,
        loan,
        [active_loan(), policy(lost_book_fee=1200), None, None, None, None],
    )

    result = loan.return_book(return_request(lost=True))

    assert result["status"] == "LOST"
    assert result["fine"] == 1200
    fine_params = next(params for query, params in database.calls if "INSERT INTO fines" in query)
    assert fine_params[3] == 1200
    assert fine_params[4] == "LOST_BOOK"
    database.assert_finished()


@pytest.mark.requirement("FR-22")
@pytest.mark.requirement("BR-15")
@pytest.mark.requirement("BR-18")
def test_damaged_return_sets_copy_status_and_creates_fine(monkeypatch):
    database = install_database(
        monkeypatch,
        loan,
        [active_loan(), policy(damaged_book_fee=650), None, None, None, None],
    )

    result = loan.return_book(return_request(damaged=True, damage_note="Повреждена обложка"))

    assert result["status"] == "DAMAGED"
    assert result["fine"] == 650
    fine_params = next(params for query, params in database.calls if "INSERT INTO fines" in query)
    assert fine_params[4] == "DAMAGED_BOOK"
    copy_update = next(params for query, params in database.calls if "UPDATE book_copies" in query)
    assert "Повреждена обложка" in copy_update
    database.assert_finished()


@pytest.mark.requirement("FR-20")
@pytest.mark.requirement("BR-16")
def test_overdue_return_creates_overdue_fine(monkeypatch):
    database = install_database(
        monkeypatch,
        loan,
        [
            active_loan(due_date=date.today() - timedelta(days=4)),
            policy(overdue_grace_period=1, daily_fine_rate=10),
            None,
            None,
            None,
            None,
        ],
    )

    result = loan.return_book(return_request())

    assert result["fine"] == 30
    fine_params = next(params for query, params in database.calls if "INSERT INTO fines" in query)
    assert fine_params[4] == "OVERDUE"
    database.assert_finished()


@pytest.mark.requirement("FR-20")
@pytest.mark.requirement("BR-16")
def test_return_within_grace_period_does_not_create_fine(monkeypatch):
    database = install_database(
        monkeypatch,
        loan,
        [
            active_loan(due_date=date.today() - timedelta(days=2)),
            policy(overdue_grace_period=2, daily_fine_rate=10),
            None,
            None,
        ],
    )

    result = loan.return_book(return_request())

    assert result["fine"] == 0
    assert not any("INSERT INTO fines" in query for query, _ in database.calls)
    database.assert_finished()


@pytest.mark.requirement("FR-20")
def test_fine_is_capped_by_policy_maximum(monkeypatch):
    database = install_database(
        monkeypatch,
        loan,
        [
            active_loan(due_date=date.today() - timedelta(days=100)),
            policy(daily_fine_rate=10, max_fine_amount=300),
            None,
            None,
            None,
            None,
        ],
    )

    result = loan.return_book(return_request())

    assert result["fine"] == 300
    database.assert_finished()
