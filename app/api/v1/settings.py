from fastapi import APIRouter, Depends

from app.api.v1.deps import roles
from app.schemas.settings import BorrowingPolicyUpdate
from app.services import settings as settings_service


router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get():
    return settings_service.get_policy()


@router.put("")
def put(data: BorrowingPolicyUpdate, user=Depends(roles("ADMIN"))):
    return settings_service.update_policy(data, user["user_id"])
