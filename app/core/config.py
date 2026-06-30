from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Pydantic automatycznie zmapuje nazwy z pliku .env (wielkość liter nie ma znaczenia)
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Dynamicznie budujemy asynchroniczny URL dla SQLAlchemy
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Wskazujemy Pydanticowi, skąd ma brać dane i żeby ignorował inne śmieci ze środowiska
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Tworzymy jedną globalną instancję ustawień (wzorzec projektowy: Singleton)
settings = Settings()