from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings


# 1. Tworzymy asynchroniczny silnik bazy danych (Engine)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Loguje każdy wygenerowany czysty SQL do terminala – pokochasz to przy debugowaniu
    future=True
)

# 2. Tworzymy fabrykę asynchronicznych sesji
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False  # Zapobiega błędom asynchronicznego leniwego ładowania relacji
)

# 3. Generator sesji (Wstrzykiwanie zależności - Dependency Injection)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session  # Przekazujemy aktywną sesję do endpointu API
        finally:
            await session.close()  # Gwarantujemy zamknięcie połączenia po obsłużeniu requestu!