from dataclasses import dataclass


@dataclass
class Book:
    """Описание издания книги."""

    book_id: str
    title: str
    author: str
    isbn: str | None = None
    genre: str | None = None
    publication_date: str | None = None
    publisher: str | None = None
    replacement_cost: float | None = None
    description: str | None = None
    pages: int | None = None
    language: str = "Русский"


@dataclass
class BookCopy:
    """Физический экземпляр книги."""

    copy_id: str
    book_id: str
    branch: str
    status: str
    copy_number: int | None = None
    inventory_number: str | None = None
    condition: str = "NEW"
