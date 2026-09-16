import uuid
from datetime import date, timedelta

from fastapi import HTTPException

from app.core.database import get_db


READER_ROLES = {"STUDENT", "EMPLOYEE"}


def get_policy(db):
    return db.execute("SELECT * FROM borrowing_policy LIMIT 1").fetchone()


def borrow_book(data, librarian):
    with get_db() as db:
        reader = db.execute(
            "SELECT * FROM users WHERE user_id=?",
            (data.user_id,),
        ).fetchone()
        copy = db.execute(
            "SELECT * FROM book_copies WHERE copy_id=?",
            (data.copy_id,),
        ).fetchone()
        policy = get_policy(db)

        if not reader or not copy:
            raise HTTPException(404, "Пользователь/экземпляр не найден")

        if reader["role"] not in READER_ROLES:
            raise HTTPException(400, "Выдача доступна только читателям")

        if not reader["is_verified"]:
            raise HTTPException(403, "Пользователь не верифицирован")

        if copy["status"] != "AVAILABLE":
            raise HTTPException(400, "Экземпляр недоступен")

        active_count = db.execute(
            "SELECT COUNT(*) FROM loans "
            "WHERE user_id=? AND return_date IS NULL",
            (data.user_id,),
        ).fetchone()[0]

        if active_count >= policy["max_books_per_user"]:
            raise HTTPException(400, "Достигнут лимит книг")

        loan_id = uuid.uuid4().hex
        issue_date = date.today()
        due_date = issue_date + timedelta(days=policy["max_loan_days"])

        db.execute(
            """
            INSERT INTO loans (
                loan_id, copy_id, user_id, librarian_id,
                issue_date, due_date
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                loan_id,
                data.copy_id,
                data.user_id,
                librarian["user_id"],
                str(issue_date),
                str(due_date),
            ),
        )

        db.execute(
            """
            UPDATE book_copies
            SET status='ISSUED', issue_date=?, due_date=?
            WHERE copy_id=?
            """,
            (str(issue_date), str(due_date), data.copy_id),
        )

        add_notification(
            db,
            data.user_id,
            "WELCOME",
            "Книга выдана",
            f"Книга выдана до {due_date}.",
            "/my-loans",
        )

    return {"loan_id": loan_id, "due_date": str(due_date)}


def add_notification(db, user_id, kind, title, message, link):
    db.execute(
        """
        INSERT INTO notifications (
            notification_id, user_id, type, title,
            message, sent_date, link
        ) VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
        """,
        (uuid.uuid4().hex, user_id, kind, title, message, link),
    )


def return_book(data):
    with get_db() as db:
        loan = db.execute(
            "SELECT * FROM loans WHERE loan_id=? AND return_date IS NULL",
            (data.loan_id,),
        ).fetchone()
        policy = get_policy(db)

        if not loan:
            raise HTTPException(404, "Активная выдача не найдена")

        today = date.today()
        due_date = date.fromisoformat(loan["due_date"])
        grace = policy["overdue_grace_period"] or 0
        overdue_days = max(0, (today - due_date).days - grace)
        fine = overdue_days * policy["daily_fine_rate"]

        status = "AVAILABLE"

        if data.lost:
            status = "LOST"
            fine = max(fine, policy["lost_book_fee"] or 0)
        elif data.damaged:
            status = "DAMAGED"
            fine = max(fine, policy["damaged_book_fee"] or 0)

        if policy["max_fine_amount"]:
            fine = min(fine, policy["max_fine_amount"])

        db.execute(
            """
            UPDATE loans SET
                return_date=?, is_lost=?, is_damaged=?, damage_note=?,
                fine_amount=?, status_changed_date=?
            WHERE loan_id=?
            """,
            (
                str(today),
                int(data.lost),
                int(data.damaged),
                data.damage_note,
                fine,
                str(today),
                data.loan_id,
            ),
        )

        db.execute(
            """
            UPDATE book_copies SET
                status=?, issue_date=NULL, due_date=NULL,
                damage_description=CASE WHEN ?=1 THEN ? ELSE damage_description END,
                damaged_date=CASE WHEN ?=1 THEN ? ELSE damaged_date END,
                lost_date=CASE WHEN ?=1 THEN ? ELSE lost_date END,
                lost_by_user_id=CASE WHEN ?=1 THEN ? ELSE lost_by_user_id END
            WHERE copy_id=?
            """,
            (
                status,
                int(data.damaged), data.damage_note,
                int(data.damaged), str(today),
                int(data.lost), str(today),
                int(data.lost), loan["user_id"],
                loan["copy_id"],
            ),
        )

        if fine > 0:
            fine_type = "OVERDUE"

            if data.lost:
                fine_type = "LOST_BOOK"
            elif data.damaged:
                fine_type = "DAMAGED_BOOK"

            db.execute(
                """
                INSERT INTO fines (
                    fine_id, loan_id, user_id, amount,
                    type, description, created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    uuid.uuid4().hex,
                    data.loan_id,
                    loan["user_id"],
                    fine,
                    fine_type,
                    "Автоматический штраф",
                    str(today),
                ),
            )

            add_notification(
                db,
                loan["user_id"],
                "FINE_NOTIFICATION",
                "Начислен штраф",
                f"Сумма штрафа: {fine:.2f} руб.",
                "/fines",
            )

    return {"message": "Возврат обработан", "fine": fine, "status": status}


def renew_loan(data, user):
    with get_db() as db:
        loan = db.execute(
            "SELECT * FROM loans WHERE loan_id=? AND return_date IS NULL",
            (data.loan_id,),
        ).fetchone()
        policy = get_policy(db)

        if not loan:
            raise HTTPException(404, "Выдача не найдена")

        if user["role"] in READER_ROLES and loan["user_id"] != user["user_id"]:
            raise HTTPException(404, "Выдача не найдена")

        if loan["renewal_count"] >= policy["max_renewals"]:
            raise HTTPException(400, "Достигнут лимит продлений")

        new_due_date = date.fromisoformat(loan["due_date"])
        new_due_date += timedelta(days=policy["renewal_days"])

        db.execute(
            "UPDATE loans SET due_date=?, is_renewed=1, "
            "renewal_count=renewal_count+1 WHERE loan_id=?",
            (str(new_due_date), data.loan_id),
        )

        db.execute(
            "UPDATE book_copies SET due_date=? WHERE copy_id=?",
            (str(new_due_date), loan["copy_id"]),
        )

    return {"due_date": str(new_due_date)}


def list_loans():
    query = """
        SELECT l.*, b.title, u.login,
               c.inventory_number, c.branch
        FROM loans l
        JOIN book_copies c ON c.copy_id=l.copy_id
        JOIN books b ON b.book_id=c.book_id
        JOIN users u ON u.user_id=l.user_id
        ORDER BY l.issue_date DESC
    """

    with get_db() as db:
        rows = db.execute(query).fetchall()

    return [dict(row) for row in rows]


def list_user_loans(user_id):
    query = """
        SELECT l.*, b.title, c.inventory_number, c.branch
        FROM loans l
        JOIN book_copies c ON c.copy_id=l.copy_id
        JOIN books b ON b.book_id=c.book_id
        WHERE l.user_id=?
        ORDER BY l.issue_date DESC
    """

    with get_db() as db:
        rows = db.execute(query, (user_id,)).fetchall()

    return [dict(row) for row in rows]


def list_active_loans():
    query = """
        SELECT l.*, b.title, u.login,
               c.inventory_number, c.branch
        FROM loans l
        JOIN book_copies c ON c.copy_id=l.copy_id
        JOIN books b ON b.book_id=c.book_id
        JOIN users u ON u.user_id=l.user_id
        WHERE l.return_date IS NULL
        ORDER BY l.due_date
    """

    with get_db() as db:
        rows = db.execute(query).fetchall()

    return [dict(row) for row in rows]


def list_overdue_loans():
    query = """
        SELECT l.*, b.title, u.login,
               c.inventory_number, c.branch
        FROM loans l
        JOIN book_copies c ON c.copy_id=l.copy_id
        JOIN books b ON b.book_id=c.book_id
        JOIN users u ON u.user_id=l.user_id
        WHERE l.return_date IS NULL
          AND date(l.due_date) < date('now')
        ORDER BY l.due_date
    """

    with get_db() as db:
        rows = db.execute(query).fetchall()

    return [dict(row) for row in rows]
