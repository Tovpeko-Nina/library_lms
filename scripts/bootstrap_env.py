"""Create a private local .env from the committed safe template."""

import os
import secrets
from pathlib import Path

# These public template markers are deliberately not credentials. The script
# replaces both before creating .env; local secrets are generated below.
SECRET_PLACEHOLDER = "generate-a-random-value-with-at-least-32-characters"  # nosec B105
PASSWORD_PLACEHOLDER = "lms-local-password"  # nosec B105


def render_environment(template: str) -> str:
    """Replace public placeholders with newly generated local secrets."""
    if SECRET_PLACEHOLDER not in template:
        raise ValueError("В .env.example не найден шаблон SECRET_KEY")
    if PASSWORD_PLACEHOLDER not in template:
        raise ValueError("В .env.example не найден шаблон пароля PostgreSQL")

    secret_key = secrets.token_hex(32)
    database_password = secrets.token_hex(24)

    return template.replace(SECRET_PLACEHOLDER, secret_key).replace(
        PASSWORD_PLACEHOLDER,
        database_password,
    )


def create_environment(template_path: Path, target_path: Path) -> bool:
    """Create target atomically enough for local setup; preserve existing files."""
    if target_path.is_symlink():
        raise ValueError("Отказ от работы: .env не должен быть символической ссылкой")

    if target_path.exists():
        if not target_path.is_file():
            raise ValueError("Отказ от работы: путь .env не является обычным файлом")
        target_path.chmod(0o600)
        return False

    content = render_environment(template_path.read_text(encoding="utf-8"))

    # O_EXCL prevents overwriting a file created between the existence check and
    # opening it. Mode 0600 grants read/write access only to the current user.
    descriptor = os.open(target_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as environment_file:
        environment_file.write(content)

    return True


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    template_path = project_root / ".env.example"
    target_path = project_root / ".env"

    if create_environment(template_path, target_path):
        print("Создан приватный .env со случайными локальными секретами (права 0600).")
    else:
        print(".env уже существует — файл и его секреты оставлены без изменений.")


if __name__ == "__main__":
    main()
