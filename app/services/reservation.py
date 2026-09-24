import uuid

from fastapi import HTTPException

from app.core.database import get_db


def notify_staff(db, title, message):
    """Сообщить активным сотрудникам о новой заявке читателя."""
    staff = db.execute(
        """
        SELECT user_id FROM users
        WHERE role IN ('ADMIN', 'LIBRARIAN') AND is_active=TRUE
        """
    ).fetchall()

    for employee in staff:
        db.execute(
            """
            INSERT INTO notifications (
                notification_id, user_id, type, title,
                message, sent_date, link
            ) VALUES (?, ?, 'RESERVATION_REQUEST', ?, ?, CURRENT_TIMESTAMP, ?)
            """,
            (
                uuid.uuid4().hex,
                employee["user_id"],
                title,
                message,
                "/admin/loans",
            ),
        )


def reserve_book(book_id, user_id, publication_year=None, edition_number=None):
    with get_db() as db:
        book = db.execute(
            "SELECT title FROM books WHERE book_id=?",
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

        queued = db.execute(
            """
            SELECT 1 FROM book_queue
            WHERE user_id=? AND book_id=?
              AND status IN ('WAITING', 'NOTIFIED')
            """,
            (user_id, book_id),
        ).fetchone()

        if queued:
            raise HTTPException(400, "Вы уже находитесь в очереди на эту книгу")

        reader = db.execute(
            "SELECT login, first_name, last_name FROM users WHERE user_id=?",
            (user_id,),
        ).fetchone()

        copy_query = """
            SELECT * FROM book_copies
            WHERE book_id=? AND status='AVAILABLE'
        """
        copy_params = [book_id]
        if publication_year is not None:
            copy_query += " AND publication_year=?"
            copy_params.append(publication_year)
        if edition_number is not None:
            copy_query += " AND edition_number=?"
            copy_params.append(edition_number)
        copy_query += """
            ORDER BY copy_number
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """
        copy = db.execute(copy_query, copy_params).fetchone()

        if not copy:
            position = db.execute(
                """
                SELECT COALESCE(MAX(position), 0) + 1 AS next_position
                FROM book_queue
                WHERE book_id=? AND status IN ('WAITING', 'NOTIFIED')
                """,
                (book_id,),
            ).fetchone()["next_position"]

            queue_id = uuid.uuid4().hex
            db.execute(
                """
                INSERT INTO book_queue (
                    queue_id, book_id, user_id,
                    position, status, created_at,
                    preferred_publication_year, preferred_edition_number
                ) VALUES (?, ?, ?, ?, 'WAITING', CURRENT_TIMESTAMP, ?, ?)
                """,
                (
                    queue_id, book_id, user_id, position,
                    publication_year, edition_number,
                ),
            )

            notify_staff(
                db,
                "Новая заявка на книгу",
                f"{reader['first_name']} {reader['last_name']} ({reader['login']}) "
                f"ожидает книгу «{book['title']}».",
            )

            return {"queued": True, "queue_id": queue_id, "position": position}

        reservation_id = uuid.uuid4().hex

        db.execute(
            """
            INSERT INTO reservations (
                reservation_id, copy_id, user_id,
                reservation_date, status, expiry_date, priority,
                preferred_publication_year, preferred_edition_number
            ) VALUES (?, ?, ?, CURRENT_DATE, 'ACTIVE', CURRENT_DATE + 3, ?, ?, ?)
            """,
            (
                reservation_id, copy["copy_id"], user_id,
                copy["copy_number"] or 0, publication_year, edition_number,
            ),
        )

        db.execute(
            "UPDATE book_copies SET status='RESERVED' WHERE copy_id=?",
            (copy["copy_id"],),
        )

        notify_staff(
            db,
            "Новая бронь читателя",
            f"{reader['first_name']} {reader['last_name']} ({reader['login']}) "
            f"забронировал(а) «{book['title']}».",
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


def list_staff_requests():
    """Вернуть сотруднику активные брони и очередь читателей."""
    reservations_query = """
        SELECT r.reservation_id, r.reservation_date, r.expiry_date,
               r.preferred_publication_year, r.preferred_edition_number,
               u.user_id, u.login, u.first_name, u.last_name,
               b.book_id, b.title, b.author,
               c.copy_id, c.inventory_number, c.branch,
               c.publication_year, c.edition_number
        FROM reservations r
        JOIN users u ON u.user_id=r.user_id
        JOIN book_copies c ON c.copy_id=r.copy_id
        JOIN books b ON b.book_id=c.book_id
        WHERE r.status='ACTIVE'
        ORDER BY r.reservation_date, r.reservation_id
    """
    queue_query = """
        SELECT q.queue_id, q.position, q.status, q.created_at,
               q.preferred_publication_year, q.preferred_edition_number,
               u.user_id, u.login, u.first_name, u.last_name,
               b.book_id, b.title, b.author
        FROM book_queue q
        JOIN users u ON u.user_id=q.user_id
        JOIN books b ON b.book_id=q.book_id
        WHERE q.status IN ('WAITING', 'NOTIFIED')
        ORDER BY q.position, q.created_at
    """

    with get_db() as db:
        reservations = db.execute(reservations_query).fetchall()
        queue = db.execute(queue_query).fetchall()

    return {
        "reservations": [dict(row) for row in reservations],
        "queue": [dict(row) for row in queue],
    }


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


def fulfill_reservation(reservation_id, librarian):
    """Оформить зарезервированный экземпляр как реальную выдачу."""
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

    # borrow_book повторно блокирует и проверяет бронь уже в транзакции выдачи.
    from app.schemas.loan import BorrowRequest
    from app.services.loan import borrow_book

    request = BorrowRequest(
        copy_id=str(reservation["copy_id"]),
        user_id=str(reservation["user_id"]),
        reservation_id=reservation_id,
    )
    return borrow_book(request, librarian)
