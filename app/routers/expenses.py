from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseOut

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post("/", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tworzy nowy wydatek w systemie.
    ID organizacji oraz ID użytkownika są AUTOMATYCZNIE wstrzykiwane z tokenu JWT.
    """
    # model_dump() wyciąga czysty słownik z Pydantica v2
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
    """
    Pobiera listę wszystkich wydatków firmy, do której należy zalogowany użytkownik.
    🔥 Dzięki indeksowi kompozytowemu baza radzi sobie z tym w ułamek sekundy.
    """
    # Bezwzględne odcięcie: filtrujemy PO organization_id zalogowanego usera!
    result = await db.execute(
        select(Expense)
        .where(Expense.organization_id == current_user.organization_id)
        .order_by(Expense.created_at.desc())
    )
    return result.scalars().all()