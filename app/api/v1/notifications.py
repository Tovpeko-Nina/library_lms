from fastapi import APIRouter, Depends

from app.api.v1.deps import current_user, roles
from app.services import notification as notification_service


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def get(user=Depends(current_user)):
    return notification_service.list_notifications(user["user_id"])


@router.patch("/{notification_id}/read")
def mark_read(notification_id: str, user=Depends(current_user)):
    return notification_service.mark_read(notification_id, user["user_id"])


@router.post("/send-overdue")
def send_overdue(user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return notification_service.send_overdue_notifications()


@router.get("/overdue")
def overdue(user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return notification_service.users_with_overdue_books()
