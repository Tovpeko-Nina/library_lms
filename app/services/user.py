import uuid

from fastapi import HTTPException

from app.core.database import get_db
from app.core.security import hash_password


def get_current_user(user_id):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE user_id=? AND is_active=TRUE",
            (user_id,),
        ).fetchone()

    if not row:
        raise HTTPException(401, "Пользователь не найден")

    return row


def get_profile(user):
    return dict(user)


def update_profile(user, data):
    with get_db() as db:
        db.execute(
            """
            UPDATE users SET
                first_name=?, last_name=?, phone=?, address=?,
                faculty=?, department=?, group_name=?, graduation_date=?
            WHERE user_id=?
            """,
            (
                data.first_name,
                data.last_name,
                data.phone,
                data.address,
                data.faculty,
                data.department,
                data.group_name,
                data.graduation_date,
                user["user_id"],
            ),
        )

    return {"message": "Профиль обновлён"}


def list_users(role=None, verified=None):
    query = "SELECT * FROM users WHERE 1=1"
    params = []

    if role:
        query += " AND role=?"
        params.append(role)

    if verified is not None:
        query += " AND is_verified=?"
        params.append(verified)

    with get_db() as db:
        rows = db.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def get_user(user_id):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE user_id=?",
            (user_id,),
        ).fetchone()

    if not row:
        raise HTTPException(404, "Пользователь не найден")

    return dict(row)


def create_librarian(data):
    with get_db() as db:
        exists = db.execute(
            "SELECT 1 FROM users WHERE login=? OR email=?",
            (data.login, data.email),
        ).fetchone()

        if exists:
            raise HTTPException(400, "Логин/email занят")

        user_id = uuid.uuid4().hex

        db.execute(
            """
            INSERT INTO users (
                user_id, login, email, password_hash,
                first_name, last_name, role, is_verified,
                registration_date
            ) VALUES (?, ?, ?, ?, ?, ?, 'LIBRARIAN', TRUE, CURRENT_DATE)
            """,
            (
                user_id,
                data.login,
                data.email,
                hash_password(data.password),
                data.first_name,
                data.last_name,
            ),
        )

    return {"user_id": user_id}


def deactivate_user(user_id):
    with get_db() as db:
        db.execute(
            "UPDATE users SET is_active=FALSE WHERE user_id=?",
            (user_id,),
        )

    return {"message": "Пользователь деактивирован"}


def delete_user_permanently(user_id, current_user_id):
    """Удалить неиспользуемую деактивированную учётную запись."""
    with get_db() as db:
        user = db.execute(
            "SELECT user_id, role, is_active FROM users WHERE user_id=? FOR UPDATE",
            (user_id,),
        ).fetchone()

        if not user:
            raise HTTPException(404, "Пользователь не найден")

        if str(user["user_id"]) == str(current_user_id):
            raise HTTPException(400, "Нельзя удалить собственную учётную запись")

        if user["role"] == "ADMIN":
            raise HTTPException(400, "Учётную запись администратора удалять нельзя")

        if user["is_active"]:
            raise HTTPException(400, "Сначала деактивируйте пользователя")

        references = db.execute(
            """
            SELECT
                EXISTS(SELECT 1 FROM loans WHERE user_id=? OR librarian_id=?)
                OR EXISTS(SELECT 1 FROM fines WHERE user_id=?)
                OR EXISTS(SELECT 1 FROM reservations WHERE user_id=?)
                OR EXISTS(SELECT 1 FROM notifications WHERE user_id=?)
                OR EXISTS(SELECT 1 FROM book_queue WHERE user_id=?)
                OR EXISTS(SELECT 1 FROM inventory_log WHERE librarian_id=? OR changed_by_user=?)
                OR EXISTS(SELECT 1 FROM audit_log WHERE user_id=?)
                OR EXISTS(SELECT 1 FROM book_copies WHERE lost_by_user_id=?)
                OR EXISTS(SELECT 1 FROM inventory_reports WHERE librarian_id=?)
                OR EXISTS(SELECT 1 FROM usage_reports WHERE librarian_id=?)
                OR EXISTS(SELECT 1 FROM borrowing_policy WHERE updated_by=?)
                AS has_references
            """,
            (
                user_id, user_id, user_id, user_id, user_id,
                user_id, user_id, user_id, user_id, user_id,
                user_id, user_id, user_id,
            ),
        ).fetchone()

        if references["has_references"]:
            raise HTTPException(
                409,
                "Пользователь связан с историей библиотеки и может быть только деактивирован",
            )

        db.execute("DELETE FROM users WHERE user_id=?", (user_id,))

    return {"message": "Пользователь удалён окончательно"}


def verify_user(user_id):
    with get_db() as db:
        db.execute(
            """
            UPDATE users
            SET is_verified=TRUE, verification_token=NULL
            WHERE user_id=?
            """,
            (user_id,),
        )

    return {"message": "Пользователь верифицирован"}
