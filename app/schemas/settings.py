from pydantic import BaseModel, Field


class BorrowingPolicyUpdate(BaseModel):
    maxBooksPerUser: int = Field(ge=1)
    maxBorrowDays: int = Field(ge=1)
    maxRenewCount: int = Field(ge=0)
    verificationRequired: bool = True
    dailyFineRate: float = Field(default=10, ge=0)
    lostBookFee: float = Field(default=0, ge=0)
    damagedBookFee: float = Field(default=0, ge=0)
    renewalDays: int = Field(default=7, ge=1)
    maxFineAmount: float = Field(default=0, ge=0)
    overdueGracePeriod: int = Field(default=0, ge=0)
