import pytest
from fastapi import HTTPException

from app.services import favorite
from tests.unit.fakes import install_database

pytestmark = pytest.mark.unit


@pytest.mark.requirement("FR-27")
def test_existing_book_can_be_added_to_favorites(monkeypatch):
    database = install_database(monkeypatch, favorite, [{"exists": 1}, None])

    result = favorite.add_favorite("reader-1", "book-1")

    assert result == {"message": "Книга добавлена в избранное"}
    query, params = database.calls[1]
    assert "ON CONFLICT" in query
    assert params == ("reader-1", "book-1")
    database.assert_finished()


@pytest.mark.requirement("ERR-07")
def test_missing_book_cannot_be_added_to_favorites(monkeypatch):
    database = install_database(monkeypatch, favorite, [None])

    with pytest.raises(HTTPException) as error:
        favorite.add_favorite("reader-1", "missing-book")

    assert error.value.status_code == 404
    assert error.value.detail == "Книга не найдена"
    database.assert_finished()


@pytest.mark.requirement("FR-27")
def test_user_sees_only_their_favorite_books(monkeypatch):
    rows = [{"book_id": "book-1", "title": "Чистый код"}]
    database = install_database(monkeypatch, favorite, [rows])

    result = favorite.list_favorites("reader-1")

    assert result == rows
    query, params = database.calls[0]
    assert "WHERE f.user_id=?" in query
    assert params == ("reader-1",)
    database.assert_finished()


@pytest.mark.requirement("FR-27")
def test_removing_favorite_is_idempotent(monkeypatch):
    database = install_database(monkeypatch, favorite, [None])

    result = favorite.remove_favorite("reader-1", "book-1")

    assert result == {"message": "Книга удалена из избранного"}
    assert database.calls[0][1] == ("reader-1", "book-1")
    database.assert_finished()
