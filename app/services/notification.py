import uuid

from fastapi import HTTPException

from app.core.database import get_db


def list_notifications(user_id):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM notifications "
            "WHERE user_id=? ORDER BY sent_date DESC",
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def mark_read(notification_id, user_id):
    with get_db() as db:
        notification = db.execute(
            "SELECT 1 FROM notifications "
            "WHERE notification_id=? AND user_id=?",
            (notification_id, user_id),
        ).fetchone()

        if not notification:
            raise HTTPException(404, "Уведомление не найдено")

        db.execute(
            """
            UPDATE notifications
            SET is_read=1, read_date=datetime('now')
            WHERE notification_id=?
            """,
            (notification_id,),
        )

    return {"message": "Прочитано"}


def send_overdue_notifications():
    query = """
        SELECT DISTINCT user_id
        FROM loans
        WHERE return_date IS NULL
          AND date(due_date) < date('now')
    """

    with get_db() as db:
        readers = db.execute(query).fetchall()

        for reader in readers:
            db.execute(
                """
                INSERT INTO notifications (
                    notification_id, user_id, type, title,
                    message, sent_date, link
                ) VALUES (
                    ?, ?, 'OVERDUE_REMINDER', 'Просроченные книги',
                    'У вас есть просроченная книга.', datetime('now'), ?
                )
                """,
                (uuid.uuid4().hex, reader["user_id"], "/my-loans"),
            )

    return {"sent": len(readers)}


def users_with_overdue_books():
    query = """
        SELECT DISTINCT u.user_id, u.login, u.email,
               u.first_name, u.last_name
        FROM users u
        JOIN loans l ON l.user_id=u.user_id
        WHERE l.return_date IS NULL
          AND date(l.due_date) < date('now')
    """

    with get_db() as db:
        rows = db.execute(query).fetchall()

    return [dict(row) for row in rows]
