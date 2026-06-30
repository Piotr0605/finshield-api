from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetOut

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.post("/", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget_data: BudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ustawia miesięczny limit wydatków dla konkretnej kategorii.
    Jeśli limit dla tej kategorii już istnieje – wyrzuci błąd 400.
    """
    # Sprawdzamy biznesowy unikalny warunek: jedna kategoria = jeden budżet w organizacji
    existing_query = await db.execute(
        select(Budget).where(
            Budget.organization_id == current_user.organization_id,
            Budget.category == budget_data.category
        )
    )
    if existing_query.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Budżet dla kategorii '{budget_data.category}' został już wcześniej zdefiniowany."
        )

    new_budget = Budget(
        **budget_data.model_dump(),
        organization_id=current_user.organization_id
    )
    db.add(new_budget)
    await db.commit()
    await db.refresh(new_budget)
    return new_budget


@router.get("/", response_model=list[BudgetOut])
async def list_budgets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Zwraca listę wszystkich zdefiniowanych limitów budżetowych dla firmy."""
    result = await db.execute(
        select(Budget).where(Budget.organization_id == current_user.organization_id)
    )
    return result.scalars().all()