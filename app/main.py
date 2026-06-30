from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, expenses, budget 

app = FastAPI(
    title="FinShield API",
    description="Dojebany system kontroli wydatków i Multi-tenant security",
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


@app.get("/health", tags=["Infrastructure"])
async def health_check():
    return {"status": "healthy", "database": "connected"}