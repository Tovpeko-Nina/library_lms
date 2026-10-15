import pytest
from pydantic import ValidationError

from app.schemas.book import CopyCreate
from app.schemas.user import RegisterRequest

pytestmark = pytest.mark.unit


def valid_registration(**changes):
    data = {
        "login": "reader",
        "email": "reader@example.com",
        "password": "safe-password-123",
        "first_name": "Иван",
        "last_name": "Иванов",
    }
    data.update(changes)
    return data


def test_registration_accepts_valid_password():
    request = RegisterRequest(**valid_registration())

    assert request.password == "safe-password-123"


def test_registration_rejects_password_shorter_than_twelve_characters():
    with pytest.raises(ValidationError):
        RegisterRequest(**valid_registration(password="short"))


def test_registration_rejects_password_longer_than_bcrypt_limit():
    with pytest.raises(ValidationError, match="72 байта"):
        RegisterRequest(**valid_registration(password="я" * 37))


def test_copy_requires_publication_year():
    with pytest.raises(ValidationError):
        CopyCreate.model_validate({"branch": "AVTOZAVODSKAYA"})


@pytest.mark.parametrize("year", [999, 10000])
def test_copy_rejects_publication_year_outside_supported_range(year):
    with pytest.raises(ValidationError):
        CopyCreate(branch="AVTOZAVODSKAYA", publication_year=year)


def test_copy_allows_missing_edition_number():
    copy = CopyCreate(branch="AVTOZAVODSKAYA", publication_year=2024)

    assert copy.edition_number is None
