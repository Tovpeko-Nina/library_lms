from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from .web import templates


router = APIRouter()


@router.get("/admin", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})


@router.get("/admin/users", response_class=HTMLResponse)
def users(request: Request):
    return templates.TemplateResponse("admin/users.html", {"request": request})


@router.get("/admin/books", response_class=HTMLResponse)
def books(request: Request):
    return templates.TemplateResponse("admin/books.html", {"request": request})


@router.get("/admin/loans", response_class=HTMLResponse)
def loans(request: Request):
    return templates.TemplateResponse("admin/loans.html", {"request": request})
