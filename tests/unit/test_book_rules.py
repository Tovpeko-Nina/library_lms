from types import SimpleNamespace

import psycopg
import pytest
from fastapi import HTTPException

from app.services import book
from tests.unit.fakes import install_database

pytestmark = pytest.mark.unit


def book_data(**changes):
    result = {
        "isbn": "9780132350884",
        "title": "Чистый код",
        "author": "Роберт Мартин",
        "genre": "Программирование",
        "publication_date": "2008",
        "publisher": "Prentice Hall",
        "replacement_cost": 1500,
        "description": "О качестве кода",
        "pages": 464,
        "language": "Русский",
    }
    result.update(changes)
    return SimpleNamespace(**result)


@pytest.mark.requirement("FR-06")
@pytest.mark.requirement("FR-07")
@pytest.mark.requirement("FR-08")
def test_catalog_applies_search_and_availability_filters(monkeypatch):
    rows = [{"book_id": "book-1", "title": "Чистый код", "available_copies": 1}]
    database = install_database(monkeypatch, book, [rows])

    result = book.list_books(
        genre="Программирование",
        author="Мартин",
        branch="KORCHAGINA",
        available=True,
        search="код",
        page=2,
        limit=10,
    )

    assert result == rows
    query, params = database.calls[0]
    assert "b.genre=?" in query
    assert "b.author ILIKE ?" in query
    assert "c.branch=?" in query
    assert "b.title ILIKE ?" in query
    assert "HAVING" in query
    assert params[-2:] == [10, 10]
    database.assert_finished()


@pytest.mark.requirement("FR-09")
def test_librarian_can_create_book(monkeypatch):
    database = install_database(monkeypatch, book, [None])

    result = book.create_book(book_data())

    assert result["book_id"]
    query, params = database.calls[0]
    assert "INSERT INTO books" in query
    assert params[1] == "9780132350884"
    assert params[2] == "Чистый код"
    database.assert_finished()


@pytest.mark.requirement("FR-09")
@pytest.mark.requirement("ERR-09")
def test_duplicate_isbn_is_rejected(monkeypatch):
    database = install_database(monkeypatch, book, [psycopg.IntegrityError("duplicate")])

    with pytest.raises(HTTPException) as error:
        book.create_book(book_data())

    assert error.value.status_code == 400
    assert error.value.detail == "Книга с таким ISBN уже существует"
    database.assert_finished()


@pytest.mark.requirement("FR-10")
def test_book_update_writes_all_editable_fields(monkeypatch):
    database = install_database(monkeypatch, book, [None])

    result = book.update_book("book-1", book_data(title="Новый заголовок"))

    assert result == {"message": "Обновлено"}
    query, params = database.calls[0]
    assert "updated_at=CURRENT_TIMESTAMP" in query
    assert params[1] == "Новый заголовок"
    assert params[-1] == "book-1"
    database.assert_finished()


@pytest.mark.requirement("FR-10")
@pytest.mark.requirement("SEC-01")
def test_book_patch_ignores_fields_outside_allowlist(monkeypatch):
    database = install_database(monkeypatch, book, [None])

    result = book.patch_book(
        "book-1",
        {"title": "Безопасный заголовок", "created_at": "attacker-value"},
    )

    assert result == {"message": "Обновлено"}
    query, params = database.calls[0]
    assert "title=?" in query
    assert "created_at=?" not in query
    assert params == ("Безопасный заголовок", "book-1")
    database.assert_finished()


@pytest.mark.requirement("FR-11")
def test_librarian_can_add_copy_with_required_year(monkeypatch):
    database = install_database(
        monkeypatch,
        book,
        [{"exists": 1}, {"next_number": 3}, None],
    )
    data = SimpleNamespace(
        branch="KORCHAGINA",
        publication_year=2020,
        edition_number=None,
        price=1000,
        condition="GOOD",
    )

    result = book.add_copy("book-1", data)

    assert result["copy_id"]
    query, params = database.calls[-1]
    assert "INSERT INTO book_copies" in query
    assert params[3] == 3
    assert params[5] == 2020
    assert params[6] is None
    database.assert_finished()


@pytest.mark.requirement("FR-11")
@pytest.mark.requirement("ERR-07")
def test_copy_cannot_be_added_to_missing_book(monkeypatch):
    database = install_database(monkeypatch, book, [None])
    data = SimpleNamespace(
        branch="KORCHAGINA",
        publication_year=2020,
        edition_number=None,
        price=None,
        condition="GOOD",
    )

    with pytest.raises(HTTPException) as error:
        book.add_copy("missing-book", data)

    assert error.value.status_code == 404
    assert error.value.detail == "Книга не найдена"
    database.assert_finished()


@pytest.mark.requirement("FR-09")
@pytest.mark.requirement("ERR-08")
def test_book_with_copies_cannot_be_deleted(monkeypatch):
    database = install_database(monkeypatch, book, [{"exists": 1}])

    with pytest.raises(HTTPException) as error:
        book.delete_book("book-1")

    assert error.value.status_code == 400
    assert error.value.detail == "Нельзя удалить книгу с экземплярами"
    database.assert_finished()
