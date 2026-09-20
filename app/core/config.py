import os


def env_flag(name: str, default: bool = False) -> bool:
    """Прочитать логическое значение из переменной окружения."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "Переменная SECRET_KEY обязательна. "
        "Скопируйте .env.example в .env и задайте собственное значение."
    )

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "Переменная DATABASE_URL обязательна. "
        "Пример: postgresql://lms:lms@localhost:5432/lms"
    )

INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD")
SEED_DEMO_DATA = env_flag("SEED_DEMO_DATA", default=True)
