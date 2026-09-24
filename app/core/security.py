import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from .config import JWT_AUDIENCE, JWT_ISSUER, JWT_TTL_MINUTES, SECRET_KEY

# bcrypt остаётся единым алгоритмом хэширования паролей проекта.
password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=True,
)


def hash_password(password: str) -> str:
    """Получить хэш пароля."""
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Проверить пароль по сохранённому хэшу."""
    try:
        return password_context.verify(password, password_hash)
    except (TypeError, ValueError):
        return False


def create_token(user) -> str:
    """Создать короткоживущий JWT-токен пользователя."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["user_id"]),
        "role": user["role"],
        "ver": user["token_version"],
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,
        "jti": uuid.uuid4().hex,
        "exp": now + timedelta(minutes=JWT_TTL_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token: str):
    """Расшифровать и проверить JWT-токен."""
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=["HS256"],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
        options={"require": ["sub", "iss", "aud", "iat", "exp", "jti", "ver"]},
    )
