from app.core.database import get_db


def inventory_report():
    with get_db() as db:
        rows = db.execute(
            "SELECT status, COUNT(*) AS count "
            "FROM book_copies GROUP BY status"
        ).fetchall()
        counts = {row["status"]: row["count"] for row in rows}

        rows = db.execute(
            "SELECT branch, COUNT(*) AS count "
            "FROM book_copies GROUP BY branch"
        ).fetchall()
        branches = {row["branch"]: row["count"] for row in rows}

    return {
        "total_books": sum(counts.values()),
        "available_books": counts.get("AVAILABLE", 0),
        "issued_books": counts.get("ISSUED", 0),
        "lost_books": counts.get("LOST", 0),
        "damaged_books": counts.get("DAMAGED", 0),
        "reserved_books": counts.get("RESERVED", 0),
        "books_by_branch": branches,
    }


def missing_books():
    return copies_by_status("LOST")


def damaged_books():
    return copies_by_status("DAMAGED")


def copies_by_status(status):
    query = """
        SELECT c.*, b.title
        FROM book_copies c
        JOIN books b ON b.book_id=c.book_id
        WHERE c.status=?
    """

    with get_db() as db:
        rows = db.execute(query, (status,)).fetchall()

    return [dict(row) for row in rows]


def usage_report():
    with get_db() as db:
        total_loans = db.execute("SELECT COUNT(*) AS count FROM loans").fetchone()["count"]
        total_readers = db.execute(
            "SELECT COUNT(*) AS count FROM users "
            "WHERE role IN ('STUDENT', 'EMPLOYEE')"
        ).fetchone()["count"]
        fines = db.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM fines WHERE is_paid=TRUE"
        ).fetchone()["total"]

    return {
        "total_loans": total_loans,
        "total_readers": total_readers,
        "total_fines_collected": fines,
    }


def popular_books():
    query = """
        SELECT b.title, b.author, COUNT(l.loan_id) AS loans
        FROM books b
        JOIN book_copies c ON c.book_id=b.book_id
        JOIN loans l ON l.copy_id=c.copy_id
        GROUP BY b.book_id
        ORDER BY loans DESC
        LIMIT 20
    """

    with get_db() as db:
        rows = db.execute(query).fetchall()

    return [dict(row) for row in rows]


def borrowing_trends():
    query = """
        SELECT to_char(date_trunc('month', issue_date), 'YYYY-MM') AS month,
               COUNT(*) AS loans
        FROM loans
        GROUP BY month
        ORDER BY month
    """

    with get_db() as db:
        rows = db.execute(query).fetchall()

    return [dict(row) for row in rows]


def overdue_report():
    query = """
        SELECT l.*, b.title
        FROM loans l
        JOIN book_copies c ON c.copy_id=l.copy_id
        JOIN books b ON b.book_id=c.book_id
        WHERE l.return_date IS NULL
          AND l.due_date < CURRENT_DATE
    """

    with get_db() as db:
        rows = db.execute(query).fetchall()

    return [dict(row) for row in rows]


def branch_report(branch):
    query = """
        SELECT b.title, c.status, c.inventory_number
        FROM book_copies c
        JOIN books b ON b.book_id=c.book_id
        WHERE c.branch=?
    """

    with get_db() as db:
        rows = db.execute(query, (branch,)).fetchall()

    return [dict(row) for row in rows]
