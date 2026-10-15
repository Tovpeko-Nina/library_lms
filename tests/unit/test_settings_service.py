from types import SimpleNamespace

import pytest

from app.services import settings
from tests.unit.fakes import install_database

pytestmark = pytest.mark.unit


@pytest.mark.requirement("FR-26")
def test_updated_policy_is_written_and_returned(monkeypatch):
    stored_policy = {
        "max_books_per_user": 7,
        "max_loan_days": 21,
        "max_renewals": 3,
        "daily_fine_rate": 12,
        "lost_book_fee": 1500,
        "damaged_book_fee": 500,
        "renewal_days": 5,
        "max_fine_amount": 5000,
        "overdue_grace_period": 2,
    }
    database = install_database(monkeypatch, settings, [None, stored_policy])
    data = SimpleNamespace(
        maxBooksPerUser=7,
        maxBorrowDays=21,
        maxRenewCount=3,
        dailyFineRate=12,
        lostBookFee=1500,
        damagedBookFee=500,
        renewalDays=5,
        maxFineAmount=5000,
        overdueGracePeriod=2,
    )

    result = settings.update_policy(data, "admin-1")

    assert result["maxBooksPerUser"] == 7
    assert result["maxBorrowDays"] == 21
    assert database.calls[0][1][-1] == "admin-1"
    assert "UPDATE borrowing_policy" in database.calls[0][0]
    database.assert_finished()
