from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from .config import SECRET_KEY

# bcrypt используется для хранения паролей в виде хэша.
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Получить хэш пароля."""
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Проверить пароль по сохранённому хэшу."""
    return password_context.verify(password, password_hash)


def create_token(user) -> str:
    """Создать JWT-токен пользователя на 8 часов."""
    payload = {
        "sub": str(user["user_id"]),
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=8),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token: str):
    """Расшифровать и проверить JWT-токен."""
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
