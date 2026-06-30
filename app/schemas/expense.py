import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ExpenseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Kwota wydatku, musi być większa od 0")
    category: str = Field(..., min_length=1, max_length=100)


# Klient podaje tylko podstawowe info, resztę system wyciągnie z tokenu JWT
class ExpenseCreate(ExpenseBase):
    pass


# To wypluwa API do tabelki na frontendzie
class ExpenseOut(ExpenseBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}