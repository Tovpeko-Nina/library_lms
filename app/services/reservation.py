import uuid

from fastapi import HTTPException

from app.core.database import get_db


def reserve_book(book_id, user_id):
    with get_db() as db:
        book = db.execute(
            "SELECT 1 FROM books WHERE book_id=?",
            (book_id,),
        ).fetchone()

        if not book:
            raise HTTPException(404, "Книга не найдена")

        active = db.execute(
            """
            SELECT 1
            FROM reservations r
            JOIN book_copies c ON c.copy_id=r.copy_id
            WHERE r.user_id=? AND c.book_id=? AND r.status='ACTIVE'
            """,
            (user_id, book_id),
        ).fetchone()

        if active:
            raise HTTPException(400, "У вас уже есть активная бронь этой книги")

        copy = db.execute(
            """
            SELECT * FROM book_copies
            WHERE book_id=? AND status='AVAILABLE'
            LIMIT 1
            """,
            (book_id,),
        ).fetchone()

        if not copy:
            position = db.execute(
                """
                SELECT COALESCE(MAX(position), 0) + 1
                FROM book_queue
                WHERE book_id=? AND status IN ('WAITING', 'NOTIFIED')
                """,
                (book_id,),
            ).fetchone()[0]

            queue_id = uuid.uuid4().hex
            db.execute(
                """
                INSERT INTO book_queue (
                    queue_id, book_id, user_id,
                    position, status, created_at
                ) VALUES (?, ?, ?, ?, 'WAITING', datetime('now'))
                """,
                (queue_id, book_id, user_id, position),
            )

            return {"queued": True, "queue_id": queue_id, "position": position}

        reservation_id = uuid.uuid4().hex

        db.execute(
            """
            INSERT INTO reservations (
                reservation_id, copy_id, user_id,
                reservation_date, status, expiry_date, priority
            ) VALUES (?, ?, ?, date('now'), 'ACTIVE', date('now', '+3 day'), ?)
            """,
            (reservation_id, copy["copy_id"], user_id, copy["copy_number"] or 0),
        )

        db.execute(
            "UPDATE book_copies SET status='RESERVED' WHERE copy_id=?",
            (copy["copy_id"],),
        )

    return {"reservation_id": reservation_id, "queued": False}


def list_user_reservations(user_id):
    query = """
        SELECT r.*, b.title, c.inventory_number, c.branch
        FROM reservations r
        JOIN book_copies c ON c.copy_id=r.copy_id
        JOIN books b ON b.book_id=c.book_id
        WHERE r.user_id=?
        ORDER BY r.reservation_date DESC
    """

    with get_db() as db:
        rows = db.execute(query, (user_id,)).fetchall()

    return [dict(row) for row in rows]


def cancel_reservation(reservation_id, user):
    with get_db() as db:
        reservation = db.execute(
            "SELECT * FROM reservations WHERE reservation_id=?",
            (reservation_id,),
        ).fetchone()

        is_reader = user["role"] in ("STUDENT", "EMPLOYEE")
        is_owner = reservation and reservation["user_id"] == user["user_id"]

        if not reservation or (is_reader and not is_owner):
            raise HTTPException(404, "Бронь не найдена")

        db.execute(
            "UPDATE reservations SET status='CANCELLED' WHERE reservation_id=?",
            (reservation_id,),
        )

        if reservation["status"] == "ACTIVE":
            db.execute(
                """
                UPDATE book_copies
                SET status='AVAILABLE'
                WHERE copy_id=? AND status='RESERVED'
                """,
                (reservation["copy_id"],),
            )

    return {"message": "Бронь отменена"}


def fulfill_reservation(reservation_id):
    with get_db() as db:
        reservation = db.execute(
            """
            SELECT * FROM reservations
            WHERE reservation_id=? AND status='ACTIVE'
            """,
            (reservation_id,),
        ).fetchone()

        if not reservation:
            raise HTTPException(404, "Активная бронь не найдена")

        db.execute(
            "UPDATE reservations SET status='FULFILLED' WHERE reservation_id=?",
            (reservation_id,),
        )

        db.execute(
            """
            UPDATE book_copies
            SET status='AVAILABLE'
            WHERE copy_id=? AND status='RESERVED'
            """,
            (reservation["copy_id"],),
        )

    return {"message": "Бронирование выполнено; экземпляр снова доступен для выдачи"}
