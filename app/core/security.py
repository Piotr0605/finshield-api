from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from app.core.config import settings

# ==================== 🔒 SEKCJA HASEŁ 🔒 ====================

def get_password_hash(password: str) -> str:
    """Zamienia surowe hasło użytkownika na bezpieczny hash bcrypt."""
    # Bcrypt wymaga bajtów, więc kodujemy string do utf-8
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Porównuje surowe hasło z hashem zapisanym w bazie danych."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )


# ==================== 🎫 SEKCJA JWT 🔒 ====================

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generuje bezpieczny, podpisany cyfrowo token JWT dla użytkownika."""
    to_encode = data.copy()
    
    # Obliczamy czas wygaśnięcia tokenu (standardowo UTC!)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Do ładunku (payload) tokenu dorzucamy datę wygaśnięcia ('exp')
    to_encode.update({"exp": expire})
    
    # Podpisujemy token naszym tajnym kluczem z pliku .env
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt