from pydantic import BaseModel


class BorrowingPolicyUpdate(BaseModel):
    maxBooksPerUser: int
    maxBorrowDays: int
    maxRenewCount: int
    verificationRequired: bool = True
    dailyFineRate: float = 10
    lostBookFee: float = 0
    damagedBookFee: float = 0
    renewalDays: int = 7
    maxFineAmount: float = 0
    overdueGracePeriod: int = 0
