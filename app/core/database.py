import uuid
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from .config import DATABASE_URL, SEED_DEMO_DATA


class Database:
    """Небольшая обёртка над psycopg с единым интерфейсом для сервисов."""

    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, params=None):
        # Сервисы используют DB-API placeholders; psycopg ожидает %s.
        query = query.replace("?", "%s")
        return self.connection.execute(query, params or ())


@contextmanager
def get_db():
    """Открыть PostgreSQL-транзакцию и выполнить commit либо rollback."""
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as connection:
        try:
            yield Database(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def seed_demo_data() -> None:
    """Однократно добавить демонстрационный каталог после применения миграций."""
    if not SEED_DEMO_DATA:
        return

    with get_db() as db:
        if db.execute("SELECT 1 FROM books LIMIT 1").fetchone():
            return

        demo_books = [
            ("9785170878561", "Мастер и Маргарита", "Михаил Булгаков", "Роман", 1967, "АСТ"),
            (
                "9780140449136",
                "Преступление и наказание",
                "Фёдор Достоевский",
                "Классика",
                1866,
                "Penguin",
            ),
            (
                "9780132350884",
                "Чистый код",
                "Роберт Мартин",
                "Программирование",
                2008,
                "Prentice Hall",
            ),
        ]
        branches = ["AVTOZAVODSKAYA", "KORCHAGINA", "PRYANISHNIKOVA"]

        for book_index, (isbn, title, author, genre, year, publisher) in enumerate(demo_books):
            book_id = uuid.uuid4()
            db.execute(
                """
                INSERT INTO books (
                    book_id, isbn, title, author, genre, publication_date,
                    publisher, description, pages, language
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    book_id,
                    isbn,
                    title,
                    author,
                    genre,
                    str(year),
                    publisher,
                    "Демонстрационная запись каталога.",
                    300,
                    "Русский",
                ),
            )
            for number in range(1, 4):
                copy_id = uuid.uuid4()
                db.execute(
                    """
                    INSERT INTO book_copies (
                        copy_id, book_id, branch, status, copy_number,
                        inventory_number, publication_year, edition_number,
                        acquisition_date, price, condition
                    ) VALUES (?, ?, ?, 'AVAILABLE', ?, ?, ?, 1, CURRENT_DATE, ?, 'GOOD')
                    """,
                    (
                        copy_id,
                        book_id,
                        branches[(book_index + number - 1) % 3],
                        number,
                        f"INV-{book_index + 1:02d}-{number:03d}",
                        year,
                        1200 + 100 * book_index,
                    ),
                )
