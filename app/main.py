from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, expenses, budget, ai
import app.models.budget  # noqa: F401 — rejestracja modelu dla relacji SQLAlchemy

app = FastAPI(
    title="FinShield API",
    description="System kontroli wydatków i Multi-tenant security",
    version="1.0.0"
)

# Konfiguracja CORS – pozwala frontendowi rozmawiać z backendem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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