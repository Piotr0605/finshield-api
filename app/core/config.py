from pathlib import Path  # TA LINIJKA JEST KRYTYCZNA! Duża litera 'P'
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Obliczamy absolutną ścieżkę do katalogu głównego projektu
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str
    AI_MODEL: str = "gemini-2.5-flash"

    SQL_ECHO: bool = False
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Wskazujemy bezwzględną ścieżkę do pliku .env na dysku
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")


# Globalna instancja ustawień
settings = Settings()