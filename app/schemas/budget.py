import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class BudgetBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    limit_amount: Decimal = Field(..., gt=0, decimal_places=2, description="Miesięczny limit dla kategorii")


class BudgetCreate(BudgetBase):
    pass


class BudgetOut(BudgetBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}