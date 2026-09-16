from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.services import book as book_service

from .web import templates


router = APIRouter()


@router.get("/books", response_class=HTMLResponse)
def book_list(
    request: Request,
    search: str = "",
    genre: str = "",
    branch: str = "",
):
    """Показать каталог с фильтрами."""
    books = book_service.list_books(
        genre=genre or None,
        branch=branch or None,
        search=search or None,
        limit=100,
    )

    return templates.TemplateResponse(
        "books/list.html",
        {
            "request": request,
            "books": books,
            "search": search,
            "genre": genre,
            "branch": branch,
            "genres": book_service.get_genres(),
            "branches": book_service.get_branches(),
        },
    )


@router.get("/books/{book_id}", response_class=HTMLResponse)
def book_detail(request: Request, book_id: str):
    """Показать подробную информацию о книге."""
    try:
        book = book_service.get_book(book_id)
    except HTTPException:
        book = None

    copies = []
    if book:
        copies = book_service.list_copies(book_id)

    return templates.TemplateResponse(
        "books/detail.html",
        {
            "request": request,
            "book": book,
            "copies": copies,
        },
    )
