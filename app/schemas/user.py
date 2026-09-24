from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field


def validate_password(value: str) -> str:
    """Проверить пароль с учётом ограничения bcrypt в 72 байта."""
    if not value.strip():
        raise ValueError("Пароль не может состоять только из пробелов")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Пароль не должен превышать 72 байта в UTF-8")
    return value


Password = Annotated[
    str,
    Field(min_length=12, max_length=72),
    AfterValidator(validate_password),
]


class RegisterRequest(BaseModel):
    login: str
    email: EmailStr
    password: Password
    first_name: str
    last_name: str
    role: str = "STUDENT"


class LoginRequest(BaseModel):
    login: str
    password: str = Field(min_length=1, max_length=128)


class ProfileUpdate(BaseModel):
    first_name: str
    last_name: str
    phone: str | None = None
    address: str | None = None
    faculty: str | None = None
    department: str | None = None
    group_name: str | None = None
    graduation_date: str | None = None


class LibrarianCreate(BaseModel):
    login: str
    email: EmailStr
    password: Password
    first_name: str
    last_name: str


class AdminCreate(LibrarianCreate):
    """Данные одноразового bootstrap-создания администратора."""


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: Password
