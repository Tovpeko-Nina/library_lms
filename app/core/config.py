import os


def env_flag(name: str, default: bool = False) -> bool:
    """Прочитать логическое значение из переменной окружения."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "SECRET_KEY обязателен и должен содержать не менее 32 символов."
    )

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "Переменная DATABASE_URL обязательна. "
        "Пример: postgresql://lms:lms@localhost:5432/lms"
    )

SEED_DEMO_DATA = env_flag("SEED_DEMO_DATA", default=True)
JWT_ISSUER = os.getenv("JWT_ISSUER", "library-lms")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "library-lms-web")
JWT_TTL_MINUTES = int(os.getenv("JWT_TTL_MINUTES", "30"))
