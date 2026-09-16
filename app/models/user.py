from dataclasses import dataclass


@dataclass
class User:
    """Пользователь библиотеки."""

    user_id: str
    login: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_verified: bool
    is_active: bool



def user_from_row(row):
    """Преобразовать строку SQLite в объект User."""
    return User(
        user_id=row["user_id"],
        login=row["login"],
        email=row["email"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        role=row["role"],
        is_verified=bool(row["is_verified"]),
        is_active=bool(row["is_active"]),
    )
