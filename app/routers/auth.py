from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.organization import Organization
from app.models.user import User
from app.schemas.user import UserOut
from app.schemas.auth import RegisterCompanyRequest, TokenOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register-company", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_company(payload: RegisterCompanyRequest, db: AsyncSession = Depends(get_db)):
    """
    Tworzy nową organizację (firmę) oraz przypisuje do niej pierwszego użytkownika (Admina).
    Wszystko w jednej, asynchronicznej transakcji.
    """
    company_data = payload.company_data
    user_data = payload.user_data

    # 1. Sprawdzamy, czy firma o takiej nazwie już nie istnieje
    existing_org = await db.execute(select(Organization).where(Organization.name == company_data.name))
    if existing_org.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Organizacja o podanej nazwie już istnieje.")

    # 2. Sprawdzamy, czy użytkownik z takim mailem już nie siedzi w bazie
    existing_user = await db.execute(select(User).where(User.email == user_data.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Użytkownik o podanym adresie email już istnieje.")

    # 3. Tworzymy i dodajemy organizację
    new_org = Organization(name=company_data.name)
    db.add(new_org)
    await db.flush()  # Wymuszamy wygenerowanie ID dla organizacji, ale jeszcze nie robimy commit

    # 4. Tworzymy użytkownika i parujemy go z nowo stworzoną organizacją
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pwd,
        role="Admin",  # Pierwszy użytkownik firmy staje się jej bossem
        organization_id=new_org.id
    )
    db.add(new_user)
    
    # 5. Zamykamy transakcję – zapisujemy wszystko na stałe w bazie
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=TokenOut)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Endpoint logowania kompatybilny ze Swagger UI OAuth2.
    Weryfikuje hasło i zwraca token dostępu JWT.
    """
    # 1. Szukamy gościa po adresie email (Swagger przekazuje email w polu 'username')
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    # 2. Jeśli nie ma maila albo hasło się nie zgadza – rzucamy generyczny błąd 401
    # Nigdy nie mów, co dokładnie się nie zgadzało, żeby nie ułatwiać życia hakerom!
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Niepoprawny email lub hasło.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Generujemy token JWT, zaszywając w nim ID użytkownika i jego rolę
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "org_id": str(user.organization_id)}
    )

    # 4. Zwracamy token w formacie wymaganym przez specyfikację OAuth2
    return {"access_token": access_token, "token_type": "bearer"}