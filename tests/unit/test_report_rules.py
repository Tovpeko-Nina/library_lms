import pytest

from app.services import report
from tests.unit.fakes import install_database

pytestmark = pytest.mark.unit


@pytest.mark.requirement("FR-24")
def test_inventory_report_counts_statuses_and_branches(monkeypatch):
    database = install_database(
        monkeypatch,
        report,
        [
            [
                {"status": "AVAILABLE", "count": 4},
                {"status": "ISSUED", "count": 2},
                {"status": "LOST", "count": 1},
            ],
            [
                {"branch": "MAIN", "count": 5},
                {"branch": "SCIENCE", "count": 2},
            ],
        ],
    )

    result = report.inventory_report()

    assert result == {
        "total_books": 7,
        "available_books": 4,
        "issued_books": 2,
        "lost_books": 1,
        "damaged_books": 0,
        "reserved_books": 0,
        "books_by_branch": {"MAIN": 5, "SCIENCE": 2},
    }
    database.assert_finished()


@pytest.mark.requirement("FR-25")
def test_usage_report_aggregates_loans_readers_and_paid_fines(monkeypatch):
    database = install_database(
        monkeypatch,
        report,
        [{"count": 12}, {"count": 5}, {"total": 350}],
    )

    result = report.usage_report()

    assert result == {
        "total_loans": 12,
        "total_readers": 5,
        "total_fines_collected": 350,
    }
    database.assert_finished()
