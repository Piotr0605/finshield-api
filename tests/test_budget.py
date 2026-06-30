import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_budget_unique_per_category(async_client: AsyncClient, auth_headers: dict):
    first = await async_client.post(
        "/budgets/",
        json={"category": "IT", "limit_amount": 500.00},
        headers=auth_headers,
    )
    assert first.status_code == 201

    duplicate = await async_client.post(
        "/budgets/",
        json={"category": "IT", "limit_amount": 1000.00},
        headers=auth_headers,
    )
    assert duplicate.status_code == 400
    assert "został już wcześniej zdefiniowany" in duplicate.json()["detail"]


@pytest.mark.asyncio
async def test_list_budgets(async_client: AsyncClient, auth_headers: dict):
    await async_client.post(
        "/budgets/",
        json={"category": "Marketing", "limit_amount": 300.00},
        headers=auth_headers,
    )

    response = await async_client.get("/budgets/", headers=auth_headers)
    assert response.status_code == 200
    categories = [b["category"] for b in response.json()]
    assert "Marketing" in categories
