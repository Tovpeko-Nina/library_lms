import uuid

from fastapi import HTTPException

from app.core.database import get_db
from app.core.security import hash_password


def get_current_user(user_id):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE user_id=? AND is_active=1",
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
        params.append(int(verified))

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
            ) VALUES (?, ?, ?, ?, ?, ?, 'LIBRARIAN', 1, date('now'))
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
            "UPDATE users SET is_active=0 WHERE user_id=?",
            (user_id,),
        )

    return {"message": "Пользователь деактивирован"}


def verify_user(user_id):
    with get_db() as db:
        db.execute(
            """
            UPDATE users
            SET is_verified=1, verification_token=NULL
            WHERE user_id=?
            """,
            (user_id,),
        )

    return {"message": "Пользователь верифицирован"}
