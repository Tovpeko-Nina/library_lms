from datetime import date

from fastapi import HTTPException

from app.core.database import get_db


def list_user_fines(user_id):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM fines WHERE user_id=? ORDER BY created_date DESC",
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def list_fines():
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM fines ORDER BY created_date DESC"
        ).fetchall()

    return [dict(row) for row in rows]


def list_unpaid_fines():
    with get_db() as db:
        rows = db.execute("SELECT * FROM fines WHERE is_paid=0").fetchall()

    return [dict(row) for row in rows]


def pay_fine(fine_id, user):
    with get_db() as db:
        fine = db.execute(
            "SELECT * FROM fines WHERE fine_id=?",
            (fine_id,),
        ).fetchone()

        if not fine:
            raise HTTPException(404, "Штраф не найден")

        if user["role"] in ("STUDENT", "EMPLOYEE"):
            if fine["user_id"] != user["user_id"]:
                raise HTTPException(404, "Штраф не найден")

        db.execute(
            "UPDATE fines SET is_paid=1, paid_date=? WHERE fine_id=?",
            (str(date.today()), fine_id),
        )

    return {"message": "Штраф оплачен"}


def calculate_fine(loan_id):
    with get_db() as db:
        loan = db.execute(
            "SELECT fine_amount FROM loans WHERE loan_id=?",
            (loan_id,),
        ).fetchone()

    if not loan:
        raise HTTPException(404, "Выдача не найдена")

    return {"fine": loan["fine_amount"]}
