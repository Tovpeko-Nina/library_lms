from fastapi import APIRouter, Depends

from app.api.v1.deps import current_user
from app.schemas.user import LoginRequest, RegisterRequest
from app.services import auth as auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(data: RegisterRequest):
    return auth_service.register_user(data)


@router.post("/login")
def login(data: LoginRequest):
    return auth_service.login_user(data)


@router.post("/logout")
def logout(user=Depends(current_user)):
    return auth_service.logout_user(user["user_id"])
