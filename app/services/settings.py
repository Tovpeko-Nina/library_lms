from app.core.database import get_db


def policy_to_dict(policy):
    return {
        "maxBooksPerUser": policy["max_books_per_user"],
        "maxBorrowDays": policy["max_loan_days"],
        "maxRenewCount": policy["max_renewals"],
        "verificationRequired": True,
        "dailyFineRate": policy["daily_fine_rate"],
        "lostBookFee": policy["lost_book_fee"],
        "damagedBookFee": policy["damaged_book_fee"],
        "renewalDays": policy["renewal_days"],
        "maxFineAmount": policy["max_fine_amount"],
        "overdueGracePeriod": policy["overdue_grace_period"],
    }


def get_policy():
    with get_db() as db:
        policy = db.execute(
            "SELECT * FROM borrowing_policy LIMIT 1"
        ).fetchone()

    return policy_to_dict(policy)


def update_policy(data, user_id):
    with get_db() as db:
        db.execute(
            """
            UPDATE borrowing_policy SET
                max_books_per_user=?, max_loan_days=?, max_renewals=?,
                daily_fine_rate=?, lost_book_fee=?, damaged_book_fee=?,
                renewal_days=?, max_fine_amount=?, overdue_grace_period=?,
                updated_at=CURRENT_TIMESTAMP, updated_by=?
            """,
            (
                data.maxBooksPerUser,
                data.maxBorrowDays,
                data.maxRenewCount,
                data.dailyFineRate,
                data.lostBookFee,
                data.damagedBookFee,
                data.renewalDays,
                data.maxFineAmount,
                data.overdueGracePeriod,
                user_id,
            ),
        )

    return get_policy()
