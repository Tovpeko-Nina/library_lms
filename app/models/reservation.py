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
