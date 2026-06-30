from datetime import datetime, timedelta, timezone
from typing import Optional  # 🔥 TA LINIJKA JEST NOWA
import bcrypt
import jwt
from app.core.config import settings

# ==================== 🔒 SEKCJA HASEŁ 🔒 ====================

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )


# ==================== 🎫 SEKCJA JWT 🔒 ====================

# 🔥 ZAMIAST "timedelta | None" DAJEMY "Optional[timedelta]"
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generuje bezpieczny, podpisany cyfrowo token JWT dla użytkownika."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt