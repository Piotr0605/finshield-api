from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, expenses, budget, ai
import app.models.budget  # noqa: F401 — rejestracja modelu dla relacji SQLAlchemy

SWAGGER_DESCRIPTION = """
## FinShield API — instrukcja Swagger

1. **Rejestracja** — `POST /auth/register-company` (bez autoryzacji) lub użyj istniejącego konta.
2. **Logowanie** — `POST /auth/login` (username = email, password = hasło).
3. **Authorize** — kliknij kłódkę u góry, wklej token z pola `access_token` (lub użyj flow OAuth2).
4. **Budżety** — tylko rola **Admin** może wywołać `POST /budgets/`.
5. **Wydatki** — `PATCH`/`DELETE` wymagają UUID z `GET /expenses/` (nie używaj `1` jako ID).
6. **Employee** — może edytować/usuwać wyłącznie własne wydatki; Admin ma pełny dostęp w organizacji.
7. **Pracownicy** — Admin może dodać pracownika przez `POST /auth/register-employee`.
"""

app = FastAPI(
    title="FinShield API",
    description=SWAGGER_DESCRIPTION,
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True, "docExpansion": "list"},
)

# Konfiguracja CORS – pozwala frontendowi rozmawiać z backendem
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rejestracja wszystkich modułów w systemie
app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(budget.router)  
app.include_router(ai.router)


@app.get("/health", tags=["Infrastructure"])
async def health_check():
    return {
        "status": "healthy",
        "database_url_configured": bool(settings.DATABASE_URL),
        "jwt_algorithm": settings.JWT_ALGORITHM,
    }