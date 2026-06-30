from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.expense import Expense
from app.models.budget import Budget
from app.schemas.expense import ExpenseCreate, ExpenseOut, ExpenseSummaryOut, CategorySummary

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.get("/summary", response_model=ExpenseSummaryOut)
async def get_expenses_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Wyciąga potężne podsumowanie finansowe organizacji z bazy danych.
    Liczy łączną sumę wszystkich kosztów oraz grupuje je po kategoriach.
    """
    # 1. Wyliczamy łączną sumę wszystkich wydatków firmy
    total_result = await db.execute(
        select(func.sum(Expense.amount))
        .where(Expense.organization_id == current_user.organization_id)
    )
    total_amount = total_result.scalar() or 0.00

    # 2. Wyliczamy sumy pogrupowane po kategoriach (GROUP BY)
    category_result = await db.execute(
        select(Expense.category, func.sum(Expense.amount))
        .where(Expense.organization_id == current_user.organization_id)
        .group_by(Expense.category)
    )
    
    # Mapujemy surowe wiersze z bazy na obiekty Pydantica (BEZ ZBĘDNYCH KROPEK!)
    by_category_list = [
        CategorySummary(category=row[0], total_amount=row[1])
        for row in category_result.all()
    ]

    return ExpenseSummaryOut(
        total_firm_amount=total_amount,
        by_category=by_category_list
    )


@router.post("/", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tworzy nowy wydatek, ale najpierw sprawdza asynchronicznie,
    czy nie przekroczymy sufitu zdefiniowanego w budżecie firmy.
    """
    # ==================== 🛡️ STRAŻNIK BUDŻETU 🛡️ ====================
    # 1. Sprawdzamy, czy istnieje limit dla tej kategorii w organizacji
    budget_query = await db.execute(
        select(Budget).where(
            Budget.organization_id == current_user.organization_id,
            Budget.category == expense_data.category
        )
    )
    budget = budget_query.scalar_one_or_none()

    if budget:
        # 2. Sumujemy dotychczasowe wydatki z tej kategorii
        current_spent_query = await db.execute(
            select(func.sum(Expense.amount)).where(
                Expense.organization_id == current_user.organization_id,
                Expense.category == expense_data.category
            )
        )
        current_spent = current_spent_query.scalar() or Decimal("0.00")

        # 3. Sprawdzamy, czy nowy wydatek wepchnie nas pod lód
        if current_spent + expense_data.amount > budget.limit_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Operacja zablokowana! Przekroczysz miesięczny budżet dla kategorii '{expense_data.category}'. "
                       f"Limit: {budget.limit_amount}"
            )