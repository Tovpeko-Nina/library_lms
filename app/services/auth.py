import secrets
import uuid
from datetime import date

from fastapi import HTTPException

from app.core.database import get_db
from app.core.security import create_token, hash_password, verify_password


ALLOWED_READER_ROLES = {"STUDENT", "EMPLOYEE"}


def register_user(data):
    """Создать аккаунт читателя."""
    if data.role not in ALLOWED_READER_ROLES:
        raise HTTPException(400, "Регистрация доступна только читателям")

    with get_db() as db:
        exists = db.execute(
            "SELECT 1 FROM users WHERE login=? OR email=?",
            (data.login, data.email),
        ).fetchone()

        if exists:
            raise HTTPException(400, "Логин или email уже занят")

        user_id = uuid.uuid4().hex
        verification_token = secrets.token_urlsafe(24)
        password_hash = hash_password(data.password)

        db.execute(
            """
            INSERT INTO users (
                user_id, login, email, password_hash,
                first_name, last_name, role, is_verified,
                verification_token, registration_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                user_id,
                data.login,
                data.email,
                password_hash,
                data.first_name,
                data.last_name,
                data.role,
                verification_token,
                str(date.today()),
            ),
        )

    return {
        "message": "Регистрация выполнена",
        "user_id": user_id,
        "verification_token": verification_token,
    }


def login_user(data):
    """Проверить логин и пароль и создать JWT."""
    with get_db() as db:
        user = db.execute(
            "SELECT * FROM users WHERE login=? AND is_active=1",
            (data.login,),
        ).fetchone()

    if not user:
        raise HTTPException(401, "Неверный логин или пароль")

    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "Неверный логин или пароль")

    with get_db() as db:
        db.execute(
            "UPDATE users SET last_login=datetime('now') WHERE user_id=?",
            (user["user_id"],),
        )

    return {
        "access_token": create_token(user),
        "token_type": "bearer",
        "role": user["role"],
    }
