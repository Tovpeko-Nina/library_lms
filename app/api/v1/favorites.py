from fastapi import APIRouter, Depends

from app.api.v1.deps import roles
from app.services import favorite as favorite_service

router = APIRouter(prefix="/favorites", tags=["favorites"])
reader = roles("STUDENT", "EMPLOYEE")


@router.get("")
def favorites(user=Depends(reader)):
    return favorite_service.list_favorites(user["user_id"])


@router.put("/{book_id}")
def add_favorite(book_id: str, user=Depends(reader)):
    return favorite_service.add_favorite(user["user_id"], book_id)


@router.delete("/{book_id}")
def remove_favorite(book_id: str, user=Depends(reader)):
    return favorite_service.remove_favorite(user["user_id"], book_id)
