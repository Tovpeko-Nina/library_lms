from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.services.user import get_current_user


bearer = HTTPBearer(auto_error=False)


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    """Получить пользователя из JWT."""
    if not credentials:
        raise HTTPException(401, "Требуется Bearer JWT")

    try:
        token_data = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(401, "Недействительный токен")

    user = get_current_user(token_data["sub"])
    if token_data["ver"] != user["token_version"]:
        raise HTTPException(401, "Токен отозван")
    return user


def roles(*allowed_roles):
    """Разрешить доступ только указанным ролям."""
    def check_role(user=Depends(current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(403, "Недостаточно прав")

        return user

    return check_role
