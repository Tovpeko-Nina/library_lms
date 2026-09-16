from fastapi import APIRouter, Depends

from app.api.v1.deps import roles
from app.services import fine as fine_service


router = APIRouter(prefix="/fines", tags=["fines"])


@router.get("/me")
def me(user=Depends(roles("STUDENT", "EMPLOYEE"))):
    return fine_service.list_user_fines(user["user_id"])


@router.get("")
def all(user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return fine_service.list_fines()


@router.get("/unpaid")
def unpaid(user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return fine_service.list_unpaid_fines()


@router.post("/pay/{fine_id}")
def pay(fine_id: str, user=Depends(roles("STUDENT", "EMPLOYEE", "LIBRARIAN"))):
    return fine_service.pay_fine(fine_id, user)


@router.get("/calculate/{loan_id}")
def calculate(loan_id: str, user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return fine_service.calculate_fine(loan_id)
