from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from .web import templates


router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Показать страницу входа."""
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    """Показать страницу регистрации."""
    return templates.TemplateResponse("auth/register.html", {"request": request})
