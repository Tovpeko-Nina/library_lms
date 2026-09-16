from fastapi import APIRouter, Depends

from app.api.v1.deps import roles
from app.schemas.loan import BorrowRequest, RenewRequest, ReturnRequest
from app.services import loan as loan_service


router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("/borrow")
def borrow(data: BorrowRequest, user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return loan_service.borrow_book(data, user)


@router.post("/return")
def return_book(data: ReturnRequest, user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return loan_service.return_book(data)


@router.post("/renew")
def renew(
    data: RenewRequest,
    user=Depends(roles("STUDENT", "EMPLOYEE", "LIBRARIAN", "ADMIN")),
):
    return loan_service.renew_loan(data, user)


@router.get("")
def all_loans(user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return loan_service.list_loans()


@router.get("/me")
def my_loans(user=Depends(roles("STUDENT", "EMPLOYEE"))):
    return loan_service.list_user_loans(user["user_id"])


@router.get("/overdue")
def overdue(user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return loan_service.list_overdue_loans()


@router.get("/active")
def active(user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return loan_service.list_active_loans()
