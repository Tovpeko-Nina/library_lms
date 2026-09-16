from dataclasses import dataclass


@dataclass
class Notification:
    """Уведомление пользователя."""

    notification_id: str
    user_id: str
    type: str
    title: str
    message: str
    sent_date: str
    is_read: bool = False
