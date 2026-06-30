from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks, Path, Query
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from decimal import Decimal
from datetime import date, timedelta
from uuid import UUID
from typing import Annotated, Optional
from app.schemas.expense import ExpenseUpdate
import logging

from app.core.database import get_db, engine  # 🔥 Importujemy engine do sesji w tle
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.expense import Expense
from app.models.budget import Budget
from app.schemas.expense import ExpenseCreate, ExpenseOut, ExpenseSummaryOut, CategorySummary

logger = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/expenses", tags=["Expenses"])

EXPENSE_ID_PATH = Path(
    ...,
    description="UUID wydatku — skopiuj wartość `id` z odpowiedzi GET /expenses/",
    examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
)


# ==================== 📡 ASYNCHRONICZNY RADAR BUDGETOWY (BACKGROUND TASK) ====================
async def check_budget_threshold_background(organization_id: str, category: str):
    """
    Zadanie wykonywane w tle po udanym zapisie wydatku.
    Sprawdza, czy organizacja nie zbliża się niebezpiecznie do limitu (próg 80%).
    """
    # Tworzymy osobną sesję dla zadania w tle, żeby nie kolidować z zamkniętą sesją żądania HTTP
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with AsyncSessionLocal() as db:
        # 1. Pobieramy budżet dla kategorii
        budget_query = await db.execute(
            select(Budget).where(Budget.organization_id == organization_id, Budget.category == category)
        )
        budget = budget_query.scalar_one_or_none()
        
        if not budget:
            return  # Brak limitu, brak zabawy

        # 2. Liczymy ile łącznie wydano
        spent_query = await db.execute(
            select(func.sum(Expense.amount)).where(
                Expense.organization_id == organization_id, 
                Expense.category == category
            )
        )
        total_spent = spent_query.scalar() or Decimal("0.00")

        # 3. Matematyka biznesowa – sprawdzamy czy przekroczono 80%
        percentage_used = (total_spent / budget.limit_amount) * 100

        if percentage_used >= 80.0:
            logger.warning(
                f"\n🚨 🔥 [ALERT FINANSOWY] Organizacja {organization_id} przepierdala budżet! "
                f"Kategoria: '{category}' | Zużycie: {percentage_used:.2f}% "
                f"({total_spent} zł / {budget.limit_amount} zł)!\n"
            )
            # TODO: Tutaj w przyszłości wjedzie usługa wysyłania maili / Slacka


# ==================== ENDPOINTY ====================

@router.get("/summary", response_model=ExpenseSummaryOut)
async def get_expenses_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_result = await db.execute(
        select(func.sum(Expense.amount)).where(Expense.organization_id == current_user.organization_id)
    )
    total_amount = total_result.scalar() or Decimal("0.00")

    category_result = await db.execute(
        select(Expense.category, func.sum(Expense.amount))
        .where(Expense.organization_id == current_user.organization_id)
        .group_by(Expense.category)
    )
    
    by_category_list = [
        CategorySummary(category=row[0], total_amount=row[1])
        for row in category_result.all()
    ]

    return ExpenseSummaryOut(total_firm_amount=total_amount, by_category=by_category_list)


@router.post("/", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: ExpenseCreate,
    background_tasks: BackgroundTasks,  # 🔥 WSTRZYKNIĘTE BACKGROUND TASKS
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Twardy strażnik (blokada 100%)
    budget_query = await db.execute(
        select(Budget).where(
            Budget.organization_id == current_user.organization_id,
            Budget.category == expense_data.category
        )
    )
    budget = budget_query.scalar_one_or_none()

    if budget:
        current_spent_query = await db.execute(
            select(func.sum(Expense.amount)).where(
                Expense.organization_id == current_user.organization_id,
                Expense.category == expense_data.category
            )
        )
        current_spent = current_spent_query.scalar() or Decimal("0.00")

        if current_spent + expense_data.amount > budget.limit_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Operacja zablokowana! Przekroczysz miesięczny budżet dla kategorii '{expense_data.category}'. Limit: {budget.limit_amount}, Wydano: {current_spent}, Nowy wydatek: {expense_data.amount}"
            )

    # 2. Zapis wydatku do bazy (Twój naprawiony punkt 4!)
    new_expense = Expense(
        **expense_data.model_dump(),
        organization_id=current_user.organization_id,
        user_id=current_user.id
    )
    db.add(new_expense)
    await db.commit()
    await db.refresh(new_expense)

    # 3. 🔥 ODPAŁKA RADARU W TLE
    # Przekazujemy funkcję i jej argumenty. FastAPI odpali to PO wysłaniu odpowiedzi do klienta.
    background_tasks.add_task(
        check_budget_threshold_background, 
        str(current_user.organization_id), 
        expense_data.category
    )

    return new_expense


@router.get("/", response_model=list[ExpenseOut])
async def list_expenses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100, description="Liczba rekordów do pobrania"),
    offset: int = Query(default=0, ge=0, description="Liczba rekordów do pominięcia"),
    category: Optional[str] = Query(default=None, description="Filtruj po kategorii wydatku"),
    start_date: Optional[date] = Query(default=None, description="Filtruj wydatki od tej daty (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, description="Filtruj wydatki do tej daty (YYYY-MM-DD)"),
):
    query = select(Expense).where(Expense.organization_id == current_user.organization_id)

    if category is not None:
        query = query.where(Expense.category == category)
    if start_date is not None:
        query = query.where(Expense.created_at >= start_date)
    if end_date is not None:
        # Uwzględnij cały dzień końcowy (created_at to datetime z godziną)
        query = query.where(Expense.created_at < end_date + timedelta(days=1))

    query = query.order_by(Expense.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()

# ==================== MIGRACJA / EDYCJA / USYWANIE ====================

@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={403: {"description": "Brak uprawnień — Employee nie może usuwać cudzych wydatków"}},
)
async def delete_expense(
    expense_id: Annotated[UUID, EXPENSE_ID_PATH],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Usuwa wydatek organizacji. Automatycznie uwalnia budżet."""
    result = await db.execute(
        select(Expense).where(
            Expense.id == expense_id, 
            Expense.organization_id == current_user.organization_id
        )
    )
    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono wydatku o podanym ID w Twojej organizacji."
        )

    if current_user.role != "Admin" and expense.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nie masz prawa usuwać cudzych wydatków.",
        )

    await db.delete(expense)
    await db.commit()
    return None


@router.patch(
    "/{expense_id}",
    response_model=ExpenseOut,
    responses={403: {"description": "Brak uprawnień — Employee może edytować tylko własne wpisy"}},
)
async def update_expense(
    expense_id: Annotated[UUID, EXPENSE_ID_PATH],
    expense_data: ExpenseUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aktualizuje wydatek. Jeśli kwota rośnie, Strażnik Budżetu 
    ponownie weryfikuje limity.
    """
    # 1. Szukamy gnoja w bazie
    result = await db.execute(
        select(Expense).where(
            Expense.id == expense_id, 
            Expense.organization_id == current_user.organization_id
        )
    )
    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono wydatku o podanym ID."
        )

    if current_user.role != "Admin" and expense.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Modyfikacja zabroniona. Możesz edytować wyłącznie własne wpisy.",
        )

    # 2. Logika zabezpieczeń, jeśli użytkownik zmienia kwotę lub kategorię
    target_category = expense_data.category or expense.category
    target_amount = expense_data.amount if expense_data.amount is not None else expense.amount

    # Sprawdzamy budżet tylko, jeśli cokolwiek z tych rzeczy się zmienia
    if expense_data.amount is not None or expense_data.category is not None:
        budget_query = await db.execute(
            select(Budget).where(Budget.organization_id == current_user.organization_id, Budget.category == target_category)
        )
        budget = budget_query.scalar_one_or_none()

        if budget:
            # Sumujemy wydatki z tej kategorii, OMIJAJĄC aktualnie edytowany wydatek
            spent_query = await db.execute(
                select(func.sum(Expense.amount)).where(
                    Expense.organization_id == current_user.organization_id,
                    Expense.category == target_category,
                    Expense.id != expense.id  # 🔥 Pomijamy samych siebie
                )
            )
            current_spent = spent_query.scalar() or Decimal("0.00")

            if current_spent + target_amount > budget.limit_amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Modyfikacja zablokowana! Przekroczysz budżet dla kategorii '{target_category}'."
                )

    # 3. Jeśli wszystko gra – aplikujemy zmiany przez model_dump(exclude_unset=True)
    update_dict = expense_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(expense, key, value)

    await db.commit()
    await db.refresh(expense)

    # 4. Odpalamy radar 80% w tle na nowo przeliczonych danych
    background_tasks.add_task(
        check_budget_threshold_background, 
        str(current_user.organization_id), 
        target_category
    )

    return expense