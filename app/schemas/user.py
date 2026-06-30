import uuid
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    role: str = Field(default="Employee", max_length=50)


# To przysyła klient podczas rejestracji
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100, description="Surowe hasło użytkownika")
    organization_id: uuid.UUID = Field(
        ...,
        description="Pole ignorowane przy rejestracji firmy — organizacja jest tworzona automatycznie.",
    )


# To zwraca API (Zauważ: BEZWZGLĘDNY BRAK HASŁA W OUTPUT-IE!)
class UserOut(UserBase):
    id: uuid.UUID
    organization_id: uuid.UUID

    model_config = {"from_attributes": True}