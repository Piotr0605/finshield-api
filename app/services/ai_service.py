import httpx
import json
from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.budget import Budget
from app.models.expense import Expense
from app.schemas.ai import AIAdviceOut


async def generate_financial_advice(db: AsyncSession, organization_id: str) -> AIAdviceOut:
    """
    Agreguje budżety oraz wydatki i przesyła raport do Gemini przez warstwę kompatybilności OpenAI.
    """
    # 1. Pobieramy limity budżetowe organizacji
    budget_query = await db.execute(select(Budget).where(Budget.organization_id == organization_id))
    budgets = budget_query.scalars().all()

    if not budgets:
        return AIAdviceOut(
            status="STABLE",
            summary="Brak zdefiniowanych budżetów w systemie.",
            analysis="Wprowadź najpierw limity miesięczne w sekcji 'Budgets', aby AI miało punkt odniesienia do analizy."
        )

    # 2. Pobieramy sumy wydatków pogrupowane według kategorii
    expense_query = await db.execute(
        select(Expense.category, func.sum(Expense.amount))
        .where(Expense.organization_id == organization_id)
        .group_by(Expense.category)
    )
    expenses_data = {row[0]: row[1] for row in expense_query.all()}

    # 3. Formatujemy raport finansowy, który przekażemy modelowi LLM jako kontekst
    financial_report = []
    for b in budgets:
        spent = expenses_data.get(b.category, Decimal("0.00"))
        left = b.limit_amount - spent
        pct = (spent / b.limit_amount) * 100 if b.limit_amount > 0 else 0
        financial_report.append(
            f"- Kategoria: '{b.category}' | Limit: {b.limit_amount} zł | Wydano: {spent} zł | Zostało: {left} zł ({pct:.1f}% zużycia)"
        )

    report_context = "\n".join(financial_report)

    # 4. Prompt systemowy wymuszający surowy ton i konkretną strukturę JSON
    system_prompt = (
        "Jesteś genialnym, ale niezwykle surowym i pragmatycznym Dyrektorem Finansowym (CFO). "
        "Analizujesz budżety organizacji i ich aktualne wydatki. Twoim zadaniem jest wypluć raport "
        "w formacie JSON zawierający klucze: 'status' (wartości: STABLE, WARNING lub CRITICAL), "
        "'summary' (jedno celne, dosadne zdanie podsumowania) oraz 'analysis' (głęboka, profesjonalna analiza "
        "w formacie Markdown, zawierająca konkretne rekomendacje oszczędnościowe, pisana zwięźle i konkretnie). "
        "Bądź formalny, jeśli firma niepotrzebnie wydaje pieniądze, powiedz to wprost."
    )

    user_prompt = f"Oto aktualny stan finansów mojej organizacji:\n\n{report_context}\n\nPrzeanalizuj te dane i zwróć wymagany format JSON."

    # 5. Konfiguracja nagłówków i payloadu dla kompatybilnego API Google AI Studio
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},  # Wymuszenie czystego JSON-a na wyjściu z Gemini
        "temperature": 0.3
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            result_json = response.json()
            raw_content = result_json["choices"][0]["message"]["content"]
            ai_data = json.loads(raw_content)
            
            return AIAdviceOut(
                status=ai_data.get("status", "STABLE"),
                summary=ai_data.get("summary", "Analiza ukończona pomyślnie."),
                analysis=ai_data.get("analysis", "Brak szczegółowych danych w analizie.")
            )
            
    except Exception as e:
        # Bezpiecznik: jeśli padnie sieć, skończą się limity lub klucz będzie zły, aplikacja nie rzuci błędem 500
        return AIAdviceOut(
            status="WARNING",
            summary="System doradczy AI jest chwilowo niedostępny.",
            analysis=f"Błąd komunikacji z zewnętrznym modelem LLM: {str(e)}. Sprawdź poprawność klucza API w pliku .env."
        )