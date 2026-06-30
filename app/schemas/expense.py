import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional 



class ExpenseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Kwota wydatku, musi być większa od 0")
    category: str = Field(..., min_length=1, max_length=100)


# Klient podaje tylko podstawowe info przy tworzeniu
class ExpenseCreate(ExpenseBase):
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Klucz do kasety Park Tool",
                "amount": 199.99,
                "category": "Narzedzia",
            }
        }
    }


# To wypluwa API do pojedynczego wydatku
class ExpenseOut(ExpenseBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== 📊 SCHEMATY AGREGACJI 📊 ====================

class CategorySummary(BaseModel):
    category: str
    total_amount: Decimal


class ExpenseSummaryOut(BaseModel):
    total_firm_amount: Decimal
    by_category: list[CategorySummary]

    model_config = {"from_attributes": True}

class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[Decimal] = None
    category: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Zaktualizowany tytuł wydatku",
                "amount": 149.99,
            }
        }
    }