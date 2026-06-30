import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_employee_cannot_create_budget(async_client: AsyncClient, employee_auth_headers: dict):
    response = await async_client.post(
        "/budgets/",
        json={"category": "Marketing", "limit_amount": 1000.00},
        headers=employee_auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_employee_cannot_delete_admin_expense(
    async_client: AsyncClient,
    auth_headers: dict,
    employee_auth_headers: dict,
):
    admin_expense = await async_client.post(
        "/expenses/",
        json={"title": "Wydatek admina", "amount": 30.00, "category": "Biuro"},
        headers=auth_headers,
    )
    expense_id = admin_expense.json()["id"]

    delete_response = await async_client.delete(
        f"/expenses/{expense_id}",
        headers=employee_auth_headers,
    )
    assert delete_response.status_code == 403


@pytest.mark.asyncio
async def test_employee_can_manage_own_expense(
    async_client: AsyncClient,
    employee_auth_headers: dict,
):
    create_response = await async_client.post(
        "/expenses/",
        json={"title": "Moj wydatek", "amount": 25.00, "category": "Podroze"},
        headers=employee_auth_headers,
    )
    assert create_response.status_code == 201
    expense_id = create_response.json()["id"]

    patch_response = await async_client.patch(
        f"/expenses/{expense_id}",
        json={"title": "Moj wydatek zaktualizowany"},
        headers=employee_auth_headers,
    )
    assert patch_response.status_code == 200

    delete_response = await async_client.delete(
        f"/expenses/{expense_id}",
        headers=employee_auth_headers,
    )
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_admin_can_delete_employee_expense(
    async_client: AsyncClient,
    auth_headers: dict,
    employee_auth_headers: dict,
):
    employee_expense = await async_client.post(
        "/expenses/",
        json={"title": "Wydatek pracownika", "amount": 40.00, "category": "Szkolenia"},
        headers=employee_auth_headers,
    )
    expense_id = employee_expense.json()["id"]

    delete_response = await async_client.delete(
        f"/expenses/{expense_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204
