from fastapi import APIRouter, Depends, status
from sqlalchemy import func  # 🔥 POTRZEBNE DO func.sum()
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseOut, ExpenseSummaryOut, CategorySummary  # 🔥 NOWE IMPORTY

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
    # scalar() wyciągnie pojedynczą wartość. Jeśli firma nie ma wydatków, zwróci None, więc dajemy 0
    total_amount = total_result.scalar() or 0.00

    # 2. Wyliczamy sumy pogrupowane po kategoriach (GROUP BY)
    category_result = await db.execute(
        select(Expense.category, func.sum(Expense.amount))
        .where(Expense.organization_id == current_user.organization_id)
        .group_by(Expense.category)
    )
    
    # Mapujemy surowe wiersze z bazy na obiekty Pydantica
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
    new_expense = Expense(
        **expense_data.model_dump(),
        organization_id=current_user.organization_id,
        user_id=current_user.id
    )
    db.add(new_expense)
    await db.commit()
    await db.refresh(new_expense)
    return new_expense


@router.get("/", response_model=list[ExpenseOut])
async def list_expenses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Expense)
        .where(Expense.organization_id == current_user.organization_id)
        .order_by(Expense.created_at.desc())
    )
    return result.scalars().all()