import asyncio
from typing import Generator
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Tworzy globalną pętlę zdarzeń (event loop) na czas trwania całej sesji testowej."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> Generator[AsyncClient, None, None]:
    """Tworzy asynchronicznego klienta HTTP połączonego z aplikacją FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac