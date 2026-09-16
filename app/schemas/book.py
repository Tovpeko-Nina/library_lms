from pydantic import BaseModel


class BookCreate(BaseModel):
    isbn: str | None = None
    title: str
    author: str
    genre: str | None = None
    publication_date: str | None = None
    publisher: str | None = None
    replacement_cost: float | None = None
    description: str | None = None
    pages: int | None = None
    language: str = "Русский"


class CopyCreate(BaseModel):
    branch: str
    price: float | None = None
    condition: str = "NEW"


class CopyStatusUpdate(BaseModel):
    status: str
    reason: str | None = None
