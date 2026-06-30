import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_expense_within_budget(async_client: AsyncClient, auth_headers: dict):
    kategoria = "Narzedzia"

    budget_response = await async_client.post(
        "/budgets/",
        json={"category": kategoria, "limit_amount": 500.00},
        headers=auth_headers,
    )
    assert budget_response.status_code == 201

    expense_response = await async_client.post(
        "/expenses/",
        json={"title": "Klucz do kasety Park Tool", "amount": 200.00, "category": kategoria},
        headers=auth_headers,
    )

    assert expense_response.status_code == 201
    data = expense_response.json()
    assert data["title"] == "Klucz do kasety Park Tool"
    assert data["category"] == kategoria


@pytest.mark.asyncio
async def test_create_expense_exceeding_budget_blocked(async_client: AsyncClient, auth_headers: dict):
    kategoria = "Czesci eksploatacyjne"

    await async_client.post(
        "/budgets/",
        json={"category": kategoria, "limit_amount": 100.00},
        headers=auth_headers,
    )

    expense_response = await async_client.post(
        "/expenses/",
        json={"title": "Opona Maxxis Assegai 3C", "amount": 250.00, "category": kategoria},
        headers=auth_headers,
    )

    assert expense_response.status_code == 400
    assert "Operacja zablokowana!" in expense_response.json()["detail"]


@pytest.mark.asyncio
async def test_patch_and_delete_expense(async_client: AsyncClient, auth_headers: dict):
    create_response = await async_client.post(
        "/expenses/",
        json={"title": "Smar do lancucha", "amount": 50.00, "category": "Chemia"},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    expense_id = create_response.json()["id"]

    patch_response = await async_client.patch(
        f"/expenses/{expense_id}",
        json={"title": "Smar premium", "amount": 75.00},
        headers=auth_headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["title"] == "Smar premium"

    delete_response = await async_client.delete(f"/expenses/{expense_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    list_response = await async_client.get("/expenses/", headers=auth_headers)
    assert all(item["id"] != expense_id for item in list_response.json())


@pytest.mark.asyncio
async def test_patch_expense_invalid_amount_rejected(async_client: AsyncClient, auth_headers: dict):
    create_response = await async_client.post(
        "/expenses/",
        json={"title": "Pedaly", "amount": 100.00, "category": "Akcesoria"},
        headers=auth_headers,
    )
    expense_id = create_response.json()["id"]

    patch_response = await async_client.patch(
        f"/expenses/{expense_id}",
        json={"amount": 0},
        headers=auth_headers,
    )
    assert patch_response.status_code == 422


@pytest.mark.asyncio
async def test_expenses_summary(async_client: AsyncClient, auth_headers: dict):
    await async_client.post(
        "/expenses/",
        json={"title": "Koszyk", "amount": 100.00, "category": "Akcesoria"},
        headers=auth_headers,
    )
    await async_client.post(
        "/expenses/",
        json={"title": "Lampka", "amount": 50.00, "category": "Akcesoria"},
        headers=auth_headers,
    )

    summary_response = await async_client.get("/expenses/summary", headers=auth_headers)
    assert summary_response.status_code == 200
    data = summary_response.json()
    assert float(data["total_firm_amount"]) == 150.00
    assert any(c["category"] == "Akcesoria" and float(c["total_amount"]) == 150.00 for c in data["by_category"])


@pytest.mark.asyncio
async def test_expenses_pagination_and_category_filter(async_client: AsyncClient, auth_headers: dict):
    for i in range(3):
        await async_client.post(
            "/expenses/",
            json={"title": f"Wydatek {i}", "amount": 10.00 + i, "category": "IT"},
            headers=auth_headers,
        )
    await async_client.post(
        "/expenses/",
        json={"title": "Inny", "amount": 99.00, "category": "Biuro"},
        headers=auth_headers,
    )

    filtered = await async_client.get("/expenses/?category=IT&limit=2&offset=0", headers=auth_headers)
    assert filtered.status_code == 200
    items = filtered.json()
    assert len(items) == 2
    assert all(item["category"] == "IT" for item in items)
