import uuid
from datetime import datetime
from pydantic import BaseModel, Field


# Wspólne pola dla tworzenia i odczytu
class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Nazwa firmy/organizacji")


# To, co klient przysyła w requescie, żeby założyć organizację
class OrganizationCreate(OrganizationBase):
    pass


# To, co API zwraca w responsu (Zabezpieczone wyjście)
class OrganizationOut(OrganizationBase):
    id: uuid.UUID
    created_at: datetime

    # Włączamy tryb kompatybilności z ORM (Pydantic v2)
    # Dzięki temu Pydantic potrafi automatycznie przepisać obiekt SQLAlchemy na JSON
    model_config = {"from_attributes": True}