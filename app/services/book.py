import uuid

import psycopg
from fastapi import HTTPException

from app.core.database import get_db


BOOK_FIELDS = (
    "isbn",
    "title",
    "author",
    "genre",
    "publication_date",
    "publisher",
    "replacement_cost",
    "description",
    "pages",
    "language",
)


def list_books(genre=None, author=None, branch=None, available=None, search=None, page=1, limit=20):
    query = """
        SELECT b.*,
               COUNT(c.copy_id) AS total_copies,
               SUM(CASE WHEN c.status='AVAILABLE' THEN 1 ELSE 0 END)
                   AS available_copies
        FROM books b
        LEFT JOIN book_copies c ON c.book_id=b.book_id
        WHERE 1=1
    """
    params = []

    if genre:
        query += " AND b.genre=?"
        params.append(genre)

    if author:
        query += " AND b.author LIKE ?"
        query = query.replace("b.author LIKE ?", "b.author ILIKE ?")
        params.append(f"%{author}%")

    if branch:
        query += " AND c.branch=?"
        params.append(branch)

    if search:
        query += " AND (b.title ILIKE ? OR b.author ILIKE ? OR b.isbn ILIKE ?)"
        params.extend([f"%{search}%"] * 3)

    query += " GROUP BY b.book_id"

    if available is True:
        query += " HAVING SUM(CASE WHEN c.status='AVAILABLE' THEN 1 ELSE 0 END) > 0"

    query += " ORDER BY b.title LIMIT ? OFFSET ?"
    params.extend([limit, (page - 1) * limit])

    with get_db() as db:
        rows = db.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def get_branches():
    """Получить список филиалов, в которых есть экземпляры."""
    with get_db() as db:
        rows = db.execute(
            "SELECT DISTINCT branch FROM book_copies ORDER BY branch"
        ).fetchall()

    return [row["branch"] for row in rows]


def get_genres():
    with get_db() as db:
        rows = db.execute(
            "SELECT DISTINCT genre FROM books "
            "WHERE genre IS NOT NULL ORDER BY genre"
        ).fetchall()

    return [row["genre"] for row in rows]


def search_books(query):
    return list_books(search=query)


def popular_books():
    query = """
        SELECT b.*, COUNT(l.loan_id) AS loans
        FROM books b
        JOIN book_copies c ON c.book_id=b.book_id
        JOIN loans l ON l.copy_id=c.copy_id
        GROUP BY b.book_id
        ORDER BY loans DESC
        LIMIT 20
    """

    with get_db() as db:
        rows = db.execute(query).fetchall()

    return [dict(row) for row in rows]


def get_book(book_id):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM books WHERE book_id=?",
            (book_id,),
        ).fetchone()

    if not row:
        raise HTTPException(404, "Книга не найдена")

    return dict(row)


def create_book(data):
    book_id = uuid.uuid4().hex
    values = [getattr(data, field) for field in BOOK_FIELDS]

    try:
        with get_db() as db:
            db.execute(
                """
                INSERT INTO books (
                    book_id, isbn, title, author, genre,
                    publication_date, publisher, replacement_cost,
                    description, pages, language, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (book_id, *values),
            )
    except psycopg.IntegrityError:
        raise HTTPException(400, "Книга с таким ISBN уже существует")

    return {"book_id": book_id}


def update_book(book_id, data):
    values = [getattr(data, field) for field in BOOK_FIELDS]

    with get_db() as db:
        db.execute(
            """
            UPDATE books SET
                isbn=?, title=?, author=?, genre=?, publication_date=?,
                publisher=?, replacement_cost=?, description=?, pages=?,
                language=?, updated_at=CURRENT_TIMESTAMP
            WHERE book_id=?
            """,
            (*values, book_id),
        )

    return {"message": "Обновлено"}


def patch_book(book_id, data):
    values = {key: value for key, value in data.items() if key in BOOK_FIELDS}

    if values:
        fields = ", ".join(f"{key}=?" for key in values)
        query = (
            f"UPDATE books SET {fields}, updated_at=CURRENT_TIMESTAMP "
            "WHERE book_id=?"
        )

        with get_db() as db:
            db.execute(query, (*values.values(), book_id))

    return {"message": "Обновлено"}


def delete_book(book_id):
    with get_db() as db:
        has_copies = db.execute(
            "SELECT 1 FROM book_copies WHERE book_id=?",
            (book_id,),
        ).fetchone()

        if has_copies:
            raise HTTPException(400, "Нельзя удалить книгу с экземплярами")

        db.execute("DELETE FROM books WHERE book_id=?", (book_id,))

    return {"message": "Удалено"}


def add_copy(book_id, data):
    copy_id = uuid.uuid4().hex

    with get_db() as db:
        book_exists = db.execute(
            "SELECT 1 FROM books WHERE book_id=?",
            (book_id,),
        ).fetchone()

        if not book_exists:
            raise HTTPException(404, "Книга не найдена")

        number = db.execute(
            "SELECT COALESCE(MAX(copy_number), 0) + 1 AS next_number "
            "FROM book_copies WHERE book_id=?",
            (book_id,),
        ).fetchone()["next_number"]

        db.execute(
            """
            INSERT INTO book_copies (
                copy_id, book_id, branch, status, copy_number,
                inventory_number, publication_year, edition_number,
                acquisition_date, price, condition
            )
            VALUES (?, ?, ?, 'AVAILABLE', ?, ?, ?, ?, CURRENT_DATE, ?, ?)
            """,
            (
                copy_id,
                book_id,
                data.branch,
                number,
                f"INV-{copy_id[:8]}",
                data.publication_year,
                data.edition_number,
                data.price,
                data.condition,
            ),
        )

    return {"copy_id": copy_id}


def list_copies(book_id):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM book_copies WHERE book_id=?",
            (book_id,),
        ).fetchall()

    return [dict(row) for row in rows]
