from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.database import get_db


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Главная страница со статистикой библиотеки."""
    with get_db() as db:
        stats = {
            "books": db.execute("SELECT COUNT(*) AS count FROM books").fetchone()["count"],
            "copies": db.execute("SELECT COUNT(*) AS count FROM book_copies").fetchone()["count"],
            "active_loans": db.execute(
                "SELECT COUNT(*) AS count FROM loans WHERE return_date IS NULL"
            ).fetchone()["count"],
            "readers": db.execute(
                "SELECT COUNT(*) AS count FROM users "
                "WHERE role IN ('STUDENT','EMPLOYEE') AND is_active=TRUE"
            ).fetchone()["count"],
        }

        popular = db.execute(
            """
            SELECT b.title, b.author, COUNT(l.loan_id) AS loans
            FROM books b
            JOIN book_copies c ON c.book_id=b.book_id
            JOIN loans l ON l.copy_id=c.copy_id
            GROUP BY b.book_id
            ORDER BY loans DESC, b.title
            LIMIT 5
            """
        ).fetchall()

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "stats": stats,
            "popular": popular,
        },
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/profile", response_class=HTMLResponse)
def profile(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


@router.get("/notifications", response_class=HTMLResponse)
def notifications(request: Request):
    return templates.TemplateResponse("notifications.html", {"request": request})


@router.get("/fines", response_class=HTMLResponse)
def fines(request: Request):
    return templates.TemplateResponse("fines.html", {"request": request})


@router.get("/reports", response_class=HTMLResponse)
def reports(request: Request):
    return templates.TemplateResponse("reports/index.html", {"request": request})


@router.get("/settings", response_class=HTMLResponse)
def settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})
