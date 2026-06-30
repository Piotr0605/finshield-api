from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# 1. Inicjalizacja aplikacji FastAPI
app = FastAPI(
    title="FinShield API",
    description="Automated financial management system backend",
    version="1.0.0",
)

# 2. Konfiguracja CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 3. Endpoint typu Health Check
@app.get("/health", tags=["Infrastructure"])
async def health_check():
    return {
        "status": "healthy",
        "database_url_configured": bool(settings.DATABASE_URL),
        "jwt_algorithm": settings.JWT_ALGORITHM
    }


# 4. Prosty endpoint powitalny
@app.get("/", tags=["General"])
async def root():
    return {"message": "Welcome to FinShield API. Go to /docs for Swagger UI."}
    