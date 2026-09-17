from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import (
    auth,
    books,
    copies,
    fines,
    loans,
    notifications,
    reports,
    reservations,
    settings,
    users,
)
from app.core.database import init_db
from app.routes import admin, auth as auth_pages, books as book_pages
from app.routes import loans as loan_pages
from app.routes.web import router as web_router


BASE_DIR = Path(__file__).resolve().parents[1]

app = FastAPI(
    title="Library Management System",
    version="2.0.0",
    description="LMS по ТЗ: FastAPI + SQLite + Jinja2 + JWT",
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


# REST API.
api_routers = (
    auth.router,
    users.router,
    books.router,
    copies.router,
    loans.router,
    fines.router,
    settings.router,
    notifications.router,
    reports.router,
    reservations.router,
)

for router in api_routers:
    app.include_router(router, prefix="/api/v1")


# Web-страницы.
app.include_router(web_router)
app.include_router(auth_pages.router)
app.include_router(book_pages.router)
app.include_router(loan_pages.router)
app.include_router(admin.router)


@app.on_event("startup")
def startup():
    """Создать БД и демонстрационные данные при запуске."""
    init_db()


@app.get("/health")
def health():
    """Служебная проверка доступности приложения."""
    return {"status": "ok", "service": "library-lms"}


@app.get("/api/v1/health")
def api_health():
    """Проверка доступности API."""
    return {"status": "ok"}


@app.get("/docs-link")
def docs_link():
    return RedirectResponse("/docs")
