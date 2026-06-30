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

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Wskazujemy bezwzględną ścieżkę do pliku .env na dysku
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")


# Globalna instancja ustawień
settings = Settings()