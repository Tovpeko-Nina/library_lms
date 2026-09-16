from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    login: str
    email: EmailStr
    password: str = Field(min_length=6)
    first_name: str
    last_name: str
    role: str = "STUDENT"


class LoginRequest(BaseModel):
    login: str
    password: str


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
    password: str = Field(min_length=6)
    first_name: str
    last_name: str
