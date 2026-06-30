import uuid
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import engine
from app.main import app


@pytest.fixture(autouse=True)
async def dispose_db_engine() -> AsyncGenerator[None, None]:
    """Zwalnia połączenia SQLAlchemy po każdym teście – zapobiega konfliktom event loop."""
    yield
    await engine.dispose()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Tworzy asynchronicznego klienta HTTP połączonego z aplikacją FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def async_client(client: AsyncClient) -> AsyncClient:
    """Alias dla testów wydatków – ten sam klient HTTP co fixture `client`."""
    return client


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Rejestruje unikalną firmę i zwraca nagłówek Authorization z tokenem JWT."""
    unique_id = uuid.uuid4().hex[:6]
    password = "SuperTajneHaslo123!"

    register_response = await client.post(
        "/auth/register-company",
        json={
            "company_data": {"name": f"Test Firma {unique_id} Sp. z o.o."},
            "user_data": {
                "email": f"test_{unique_id}@example.com",
                "password": password,
                "role": "Admin",
                "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            },
        },
    )
    assert register_response.status_code == 201

    login_response = await client.post(
        "/auth/login",
        data={"username": f"test_{unique_id}@example.com", "password": password},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
