from pydantic import BaseModel


class BorrowRequest(BaseModel):
    copy_id: str
    user_id: str


class ReturnRequest(BaseModel):
    loan_id: str
    lost: bool = False
    damaged: bool = False
    damage_note: str | None = None


class RenewRequest(BaseModel):
    loan_id: str
