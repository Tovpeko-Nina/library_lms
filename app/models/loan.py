from dataclasses import dataclass


@dataclass
class Loan:
    """Выдача экземпляра книги читателю."""

    loan_id: str
    copy_id: str
    user_id: str
    librarian_id: str
    issue_date: str
    due_date: str
    return_date: str | None = None
    renewal_count: int = 0
    fine_amount: float = 0
