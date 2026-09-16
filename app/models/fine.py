from dataclasses import dataclass


@dataclass
class Fine:
    """Штраф читателя."""

    fine_id: str
    loan_id: str
    user_id: str
    amount: float
    type: str
    description: str | None
    created_date: str
    is_paid: bool
