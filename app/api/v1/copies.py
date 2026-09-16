from fastapi import APIRouter, Depends

from app.api.v1.deps import roles
from app.schemas.book import CopyStatusUpdate
from app.services import copy as copy_service


router = APIRouter(prefix="/copies", tags=["copies"])


@router.delete("/{copy_id}")
def delete(copy_id: str, user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return copy_service.delete_copy(copy_id)


@router.patch("/{copy_id}/status")
def status(
    copy_id: str,
    data: CopyStatusUpdate,
    user=Depends(roles("ADMIN", "LIBRARIAN")),
):
    return copy_service.change_status(copy_id, data, user["user_id"])
