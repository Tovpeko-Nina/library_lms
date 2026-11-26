from fastapi import HTTPException

from app.core.database import get_db


def add_favorite(user_id, book_id):
    """Добавить книгу в избранное; повторный запрос не создаёт дубль."""
    with get_db() as db:
        exists = db.execute("SELECT 1 FROM books WHERE book_id=?", (book_id,)).fetchone()
        if not exists:
            raise HTTPException(404, "Книга не найдена")

        db.execute(
            """
            INSERT INTO favorite_books(user_id, book_id)
            VALUES(?, ?)
            ON CONFLICT (user_id, book_id) DO NOTHING
            """,
            (user_id, book_id),
        )

    return {"message": "Книга добавлена в избранное"}


def list_favorites(user_id):
    """Вернуть избранные книги пользователя, начиная с недавно добавленных."""
    with get_db() as db:
        rows = db.execute(
            """
            SELECT b.*, f.added_at
            FROM favorite_books f
            JOIN books b ON b.book_id=f.book_id
            WHERE f.user_id=?
            ORDER BY f.added_at DESC
            """,
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def remove_favorite(user_id, book_id):
    """Удалить книгу из избранного; отсутствие записи также считается успехом."""
    with get_db() as db:
        db.execute(
            "DELETE FROM favorite_books WHERE user_id=? AND book_id=?",
            (user_id, book_id),
        )

    return {"message": "Книга удалена из избранного"}
