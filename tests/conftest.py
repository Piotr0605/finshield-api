import uuid
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import engine
from app.main import app

TEST_PASSWORD = "SuperTajneHaslo123!"


@pytest.fixture(autouse=True)
async def dispose_db_engine() -> AsyncGenerator[None, None]:
    """Zwalnia połączenia SQLAlchemy po każdym teście – zapobiega konfliktom event loop."""
    yield
    await engine.dispose()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
async def async_client(client: AsyncClient) -> AsyncClient:
    return client


async def _register_company(client: AsyncClient, unique_id: str) -> tuple[str, str]:
    """Rejestruje firmę i zwraca (email, hasło)."""
    email = f"test_{unique_id}@example.com"
    response = await client.post(
        "/auth/register-company",
        json={
            "company_data": {"name": f"Test Firma {unique_id} Sp. z o.o."},
            "user_data": {"email": email, "password": TEST_PASSWORD},
        },
    )
    assert response.status_code == 201
    return email, TEST_PASSWORD


async def _login(client: AsyncClient, email: str, password: str) -> dict[str, str]:
    response = await client.post("/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Rejestruje unikalną firmę (Admin) i zwraca nagłówek Authorization."""
    unique_id = uuid.uuid4().hex[:6]
    email, password = await _register_company(client, unique_id)
    return await _login(client, email, password)


@pytest.fixture
async def employee_auth_headers(client: AsyncClient, auth_headers: dict[str, str]) -> dict[str, str]:
    """Tworzy pracownika w organizacji Admina i zwraca jego token."""
    unique_id = uuid.uuid4().hex[:6]
    employee_email = f"employee_{unique_id}@example.com"
    employee_password = "EmployeeHaslo123!"

    create_response = await client.post(
        "/auth/register-employee",
        json={"email": employee_email, "password": employee_password},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    assert create_response.json()["role"] == "Employee"

    return await _login(client, employee_email, employee_password)
