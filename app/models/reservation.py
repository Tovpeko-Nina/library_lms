from dataclasses import dataclass


@dataclass
class Reservation:
    """Бронирование книги."""

    reservation_id: str
    copy_id: str
    user_id: str
    reservation_date: str
    status: str
    expiry_date: str
    priority: int = 0
    preferred_publication_year: int | None = None
    preferred_edition_number: int | None = None
