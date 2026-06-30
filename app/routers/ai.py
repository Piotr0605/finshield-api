from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai import AIAdviceOut
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["AI Advisor"])


@router.get("/advice", response_model=AIAdviceOut)
async def get_ai_financial_advice(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generuje inteligentny, personalizowany raport finansowy dla zalogowanego użytkownika
    na podstawie realnego stanu budżetów i wydatków jego firmy.
    """
    return await ai_service.generate_financial_advice(db, str(current_user.organization_id))