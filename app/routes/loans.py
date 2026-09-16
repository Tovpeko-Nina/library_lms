from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from .web import templates


router = APIRouter()


@router.get("/my-loans", response_class=HTMLResponse)
def my_loans_page(request: Request):
    """Страница текущих и прошлых выдач пользователя."""
    return templates.TemplateResponse("loans/my_loans.html", {"request": request})
