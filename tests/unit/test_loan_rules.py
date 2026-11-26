from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services import loan
from tests.unit.fakes import install_database

pytestmark = pytest.mark.unit


def reader(**changes):
    result = {
        "user_id": "reader-1",
        "role": "STUDENT",
        "is_active": True,
        "is_verified": True,
    }
    result.update(changes)
    return result


def copy(**changes):
    result = {"copy_id": "copy-1", "status": "AVAILABLE"}
    result.update(changes)
    return result


def policy(**changes):
    result = {
        "max_books_per_user": 5,
        "max_loan_days": 14,
        "max_renewals": 2,
        "renewal_days": 7,
        "overdue_grace_period": 0,
        "daily_fine_rate": 10,
        "lost_book_fee": 1000,
        "damaged_book_fee": 500,
        "max_fine_amount": 0,
    }
    result.update(changes)
    return result


def borrow_request(**changes):
    result = {
        "copy_id": "copy-1",
        "user_id": "reader-1",
        "reservation_id": None,
    }
    result.update(changes)
    return SimpleNamespace(**result)


@pytest.mark.requirement("BR-02")
@pytest.mark.requirement("ERR-08")
def test_inactive_reader_cannot_borrow_copy(monkeypatch):
    database = install_database(
        monkeypatch,
        loan,
        [reader(is_active=False), copy(), policy()],
    )

    with pytest.raises(HTTPException) as error:
        loan.borrow_book(borrow_request(), {"user_id": "librarian-1"})

    assert error.value.status_code == 403
    assert "неактив" in error.value.detail.lower()
    database.assert_finished()


@pytest.mark.requirement("BR-03")
@pytest.mark.requirement("ERR-08")
def test_unverified_reader_cannot_borrow_copy(monkeypatch):
    database = install_database(
        monkeypatch,
        loan,
        [reader(is_verified=False), copy(), policy()],
    )

    with pytest.raises(HTTPException) as error:
        loan.borrow_book(borrow_request(), {"user_id": "librarian-1"})

    assert error.value.status_code == 403
    assert error.value.detail == "Пользователь не верифицирован"
    database.assert_finished()


@pytest.mark.requirement("BR-04")
@pytest.mark.requirement("ERR-08")
@pytest.mark.parametrize("status", ["ISSUED", "LOST", "DAMAGED"])
def test_non_available_copy_cannot_be_issued_without_reservation(monkeypatch, status):
    database = install_database(monkeypatch, loan, [reader(), copy(status=status), policy()])

    with pytest.raises(HTTPException) as error:
        loan.borrow_book(borrow_request(), {"user_id": "librarian-1"})

    assert error.value.status_code == 400
    assert error.value.detail == "Экземпляр недоступен"
    database.assert_finished()


@pytest.mark.requirement("BR-07")
@pytest.mark.requirement("ERR-08")
def test_reader_at_active_loan_limit_cannot_borrow(monkeypatch):
    database = install_database(
        monkeypatch,
        loan,
        [reader(), copy(), policy(max_books_per_user=5), {"count": 5}],
    )

    with pytest.raises(HTTPException) as error:
        loan.borrow_book(borrow_request(), {"user_id": "librarian-1"})

    assert error.value.status_code == 400
    assert error.value.detail == "Достигнут лимит книг"
    database.assert_finished()


@pytest.mark.requirement("FR-15")
@pytest.mark.requirement("BR-04")
@pytest.mark.requirement("BR-09")
def test_available_copy_can_be_issued_without_reservation(monkeypatch):
    database = install_database(
        monkeypatch,
        loan,
        [reader(), copy(), policy(), {"count": 4}, None, None, None],
    )

    result = loan.borrow_book(borrow_request(), {"user_id": "librarian-1"})

    assert result["reservation_fulfilled"] is False
    assert result["due_date"] == str(date.today() + timedelta(days=14))
    assert any("SET status='ISSUED'" in query for query, _ in database.calls)
    assert any("INSERT INTO loans" in query for query, _ in database.calls)
    database.assert_finished()


@pytest.mark.requirement("BR-05")
@pytest.mark.requirement("ERR-08")
def test_reserved_copy_cannot_be_issued_to_another_reader(monkeypatch):
    reservation = {
        "reservation_id": "reservation-1",
        "copy_id": "copy-1",
        "user_id": "another-reader",
    }
    database = install_database(
        monkeypatch,
        loan,
        [reader(), copy(status="RESERVED"), policy(), reservation],
    )

    with pytest.raises(HTTPException) as error:
        loan.borrow_book(borrow_request(), {"user_id": "librarian-1"})

    assert error.value.status_code == 400
    assert error.value.detail == "Экземпляр забронирован другим читателем"
    assert not any("INSERT INTO loans" in query for query, _ in database.calls)
    database.assert_finished()


@pytest.mark.requirement("FR-15")
@pytest.mark.requirement("BR-05")
@pytest.mark.requirement("BR-06")
@pytest.mark.requirement("BR-09")
def test_reserved_copy_can_be_issued_to_reservation_owner(monkeypatch):
    reservation = {
        "reservation_id": "reservation-1",
        "copy_id": "copy-1",
        "user_id": "reader-1",
    }
    database = install_database(
        monkeypatch,
        loan,
        [
            reader(),
            copy(status="RESERVED"),
            policy(),
            reservation,
            {"count": 0},
            None,
            None,
            None,
            None,
        ],
    )

    result = loan.borrow_book(
        borrow_request(reservation_id="reservation-1"),
        {"user_id": "librarian-1"},
    )

    assert result["reservation_fulfilled"] is True
    assert any("SET status='FULFILLED'" in query for query, _ in database.calls)
    assert any("SET status='ISSUED'" in query for query, _ in database.calls)
    database.assert_finished()


@pytest.mark.requirement("BR-08")
@pytest.mark.requirement("FR-17")
def test_loan_below_renewal_limit_can_be_renewed(monkeypatch):
    due_date = date.today() + timedelta(days=3)
    database = install_database(
        monkeypatch,
        loan,
        [
            {
                "loan_id": "loan-1",
                "user_id": "reader-1",
                "copy_id": "copy-1",
                "renewal_count": 1,
                "due_date": due_date,
            },
            policy(max_renewals=2, renewal_days=7),
            None,
            None,
        ],
    )

    result = loan.renew_loan(SimpleNamespace(loan_id="loan-1"), reader())

    assert result["due_date"] == str(due_date + timedelta(days=7))
    database.assert_finished()


@pytest.mark.requirement("BR-08")
@pytest.mark.requirement("ERR-08")
def test_loan_at_renewal_limit_cannot_be_renewed(monkeypatch):
    database = install_database(
        monkeypatch,
        loan,
        [
            {
                "loan_id": "loan-1",
                "user_id": "reader-1",
                "copy_id": "copy-1",
                "renewal_count": 2,
                "due_date": date.today(),
            },
            policy(max_renewals=2),
        ],
    )

    with pytest.raises(HTTPException) as error:
        loan.renew_loan(SimpleNamespace(loan_id="loan-1"), reader())

    assert error.value.status_code == 400
    assert error.value.detail == "Достигнут лимит продлений"
    database.assert_finished()
