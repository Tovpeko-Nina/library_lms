from fastapi import APIRouter, Depends

from app.api.v1.deps import roles
from app.schemas.book import BookCreate, CopyCreate
from app.services import book as book_service


router = APIRouter(prefix="/books", tags=["books"])


@router.get("")
def books(
    genre: str | None = None,
    author: str | None = None,
    branch: str | None = None,
    available: bool | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 20,
):
    return book_service.list_books(
        genre, author, branch, available, search, page, limit
    )


@router.get("/genres")
def genres():
    return book_service.get_genres()


@router.get("/search")
def search(q: str):
    return book_service.search_books(q)


@router.get("/popular")
def popular():
    return book_service.popular_books()


@router.post("")
def add_book(data: BookCreate, user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return book_service.create_book(data)


@router.get("/{book_id}")
def get_book(book_id: str):
    return book_service.get_book(book_id)


@router.put("/{book_id}")
def put_book(
    book_id: str,
    data: BookCreate,
    user=Depends(roles("ADMIN", "LIBRARIAN")),
):
    return book_service.update_book(book_id, data)


@router.patch("/{book_id}")
def patch_book(
    book_id: str,
    data: dict,
    user=Depends(roles("ADMIN", "LIBRARIAN")),
):
    return book_service.patch_book(book_id, data)


@router.delete("/{book_id}")
def delete_book(book_id: str, user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return book_service.delete_book(book_id)


@router.post("/{book_id}/copies")
def add_copy(
    book_id: str,
    data: CopyCreate,
    user=Depends(roles("ADMIN", "LIBRARIAN")),
):
    return book_service.add_copy(book_id, data)


@router.get("/{book_id}/copies")
def copies(book_id: str):
    return book_service.list_copies(book_id)
