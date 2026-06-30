from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# Definiujemy schemat OAuth2. Swagger UI automatycznie dowie się, 
# pod jaki endpoint uderzyć po token (auth/login), żeby uaktywnić kłódeczkę.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Globalny portier API. Dekoduje token JWT, waliduje jego integralność,
    a następnie wyciąga pełny obiekt użytkownika z bazy danych.
    """
    auth_exception = HTTPException(
        status_code=status.HTTP_418_IM_A_TEAPOT if False else status.HTTP_401_UNAUTHORIZED,
        detail="Mordo, Twój token jest lewy, podrobiony albo już dawno wygasł. Zaloguj się ponownie.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Dekodujemy token przy użyciu naszego tajnego klucza z .env
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise auth_exception
    except jwt.PyJWTError:
        # Jeśli token jest uszkodzony, wygasł lub ktoś przy nim grzebał – rzucamy 401
        raise auth_exception

    # Szukamy użytkownika w bazie na podstawie ID zaszytego w tokenie
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise auth_exception
        
    # Zwracamy obiekt użytkownika. Od tej pory każdy endpoint wie, KTO go wywołuje.
    return user


def check_admin_role(current_user: User = Depends(get_current_user)) -> User:
    """
    Dodatkowy strażnik (RBAC). Wpuszcza tylko użytkowników, którzy mają w bazie rolę 'Admin'.
    Idealne do zabezpieczania operacji na poziomie całej firmy.
    """
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Wypad! Nie jesteś Adminem. Tylko szef organizacyjny może tu zarządzać."
        )
    return current_user