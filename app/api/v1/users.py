from fastapi import APIRouter, Depends

from app.api.v1.deps import current_user, roles
from app.schemas.user import LibrarianCreate, PasswordChange, ProfileUpdate
from app.services import user as user_service


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def me(user=Depends(current_user)):
    return user_service.get_profile(user)


@router.put("/me")
def update_me(data: ProfileUpdate, user=Depends(current_user)):
    return user_service.update_profile(user, data)


@router.put("/me/password")
def change_password(data: PasswordChange, user=Depends(current_user)):
    return user_service.change_password(user, data)


@router.get("")
def users(
    role: str | None = None,
    verified: bool | None = None,
    user=Depends(roles("ADMIN", "LIBRARIAN")),
):
    return user_service.list_users(role, verified)


@router.post("/librarian")
def librarian(data: LibrarianCreate, user=Depends(roles("ADMIN"))):
    return user_service.create_librarian(data)


@router.put("/{user_id}/verify")
def verify(user_id: str, user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return user_service.verify_user(user_id)


@router.delete("/{user_id}")
def delete_user(user_id: str, user=Depends(roles("ADMIN"))):
    return user_service.deactivate_user(user_id)


@router.delete("/{user_id}/permanent")
def delete_user_permanently(user_id: str, user=Depends(roles("ADMIN"))):
    return user_service.delete_user_permanently(user_id, user["user_id"])


@router.get("/{user_id}")
def get_user(user_id: str, user=Depends(roles("ADMIN", "LIBRARIAN"))):
    return user_service.get_user(user_id)
