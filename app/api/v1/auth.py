from fastapi import APIRouter

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
def logout():
    return {"message": "JWT stateless: токен перестанет действовать по истечении срока"}
