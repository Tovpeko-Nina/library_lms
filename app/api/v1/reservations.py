from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.deps import roles
from app.services import reservation as reservation_service


router = APIRouter(prefix="/reservations", tags=["reservations"])


class ReservationRequest(BaseModel):
    book_id: str


@router.post("")
def reserve(
    data: ReservationRequest,
    user=Depends(roles("STUDENT", "EMPLOYEE")),
):
    return reservation_service.reserve_book(data.book_id, user["user_id"])


@router.get("/me")
def my_reservations(user=Depends(roles("STUDENT", "EMPLOYEE"))):
    return reservation_service.list_user_reservations(user["user_id"])


@router.delete("/{reservation_id}")
def cancel(
    reservation_id: str,
    user=Depends(roles("STUDENT", "EMPLOYEE", "LIBRARIAN", "ADMIN")),
):
    return reservation_service.cancel_reservation(reservation_id, user)


@router.post("/{reservation_id}/fulfill")
def fulfill(
    reservation_id: str,
    user=Depends(roles("LIBRARIAN", "ADMIN")),
):
    return reservation_service.fulfill_reservation(reservation_id)
