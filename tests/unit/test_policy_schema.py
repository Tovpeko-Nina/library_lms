import pytest
from pydantic import ValidationError

from app.schemas.settings import BorrowingPolicyUpdate

pytestmark = pytest.mark.unit


def valid_policy(**changes):
    values = {
        "maxBooksPerUser": 5,
        "maxBorrowDays": 14,
        "maxRenewCount": 2,
        "dailyFineRate": 10,
        "lostBookFee": 1000,
        "damagedBookFee": 500,
        "renewalDays": 7,
        "maxFineAmount": 5000,
        "overdueGracePeriod": 1,
    }
    values.update(changes)
    return values


@pytest.mark.requirement("FR-26")
def test_valid_borrowing_policy_is_accepted():
    policy = BorrowingPolicyUpdate(**valid_policy())

    assert policy.maxBooksPerUser == 5
    assert policy.maxBorrowDays == 14


@pytest.mark.requirement("FR-26")
@pytest.mark.requirement("ERR-02")
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("maxBooksPerUser", 0),
        ("maxBorrowDays", 0),
        ("maxRenewCount", -1),
        ("dailyFineRate", -0.01),
        ("lostBookFee", -0.01),
        ("damagedBookFee", -0.01),
        ("renewalDays", 0),
        ("maxFineAmount", -0.01),
        ("overdueGracePeriod", -1),
    ],
)
def test_invalid_borrowing_policy_boundary_is_rejected(field, value):
    with pytest.raises(ValidationError):
        BorrowingPolicyUpdate(**valid_policy(**{field: value}))
