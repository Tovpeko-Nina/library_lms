from getpass import getpass

from pydantic import ValidationError

from app.core.database import init_db
from app.schemas.user import AdminCreate
from app.services.user import create_admin


def main():
    """Интерактивно создать администратора без хранения пароля в окружении."""
    print("Создание администратора Library LMS")
    login = input("Логин: ").strip()
    email = input("Email: ").strip()
    first_name = input("Имя: ").strip()
    last_name = input("Фамилия: ").strip()
    password = getpass("Пароль (минимум 12 символов): ")
    confirmation = getpass("Повторите пароль: ")

    if password != confirmation:
        raise SystemExit("Пароли не совпадают")

    try:
        data = AdminCreate(
            login=login,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        init_db()
        result = create_admin(data)
    except ValidationError as error:
        raise SystemExit(f"Некорректные данные:\n{error}") from error
    except ValueError as error:
        raise SystemExit(str(error)) from error

    print(f"Администратор создан. ID: {result['user_id']}")


if __name__ == "__main__":
    main()
