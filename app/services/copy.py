import uuid

from fastapi import HTTPException

from app.core.database import get_db


ALLOWED_STATUSES = {"AVAILABLE", "ISSUED", "RESERVED", "LOST", "DAMAGED"}


def delete_copy(copy_id):
    with get_db() as db:
        copy = db.execute(
            "SELECT status FROM book_copies WHERE copy_id=?",
            (copy_id,),
        ).fetchone()

        if not copy:
            raise HTTPException(404, "Экземпляр не найден")

        if copy["status"] == "ISSUED":
            raise HTTPException(400, "Выданный экземпляр списать нельзя")

        db.execute("DELETE FROM book_copies WHERE copy_id=?", (copy_id,))

    return {"message": "Экземпляр списан"}


def change_status(copy_id, data, librarian_id):
    if data.status not in ALLOWED_STATUSES:
        raise HTTPException(400, "Неверный статус")

    with get_db() as db:
        old = db.execute(
            "SELECT status FROM book_copies WHERE copy_id=?",
            (copy_id,),
        ).fetchone()

        if not old:
            raise HTTPException(404, "Экземпляр не найден")

        db.execute(
            """
            UPDATE book_copies
            SET status=?,
                damage_description=CASE
                    WHEN ?='DAMAGED' THEN ?
                    ELSE damage_description
                END
            WHERE copy_id=?
            """,
            (data.status, data.status, data.reason, copy_id),
        )

        db.execute(
            """
            INSERT INTO inventory_log (
                log_id, copy_id, librarian_id, old_status,
                new_status, reason, changed_date
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
            )
            """,
            (
                uuid.uuid4(), copy_id,
                librarian_id,
                old["status"],
                data.status,
                data.reason,
            ),
        )

    return {"message": "Статус изменён"}
