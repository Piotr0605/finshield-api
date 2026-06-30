import pytest
from httpx import AsyncClient
from decimal import Decimal


@pytest.mark.asyncio
async def test_create_expense_within_budget(async_client: AsyncClient, auth_headers: dict):
    """
    Testuje sytuację, gdzie wydatek mieści się w limicie budżetowym.
    Oczekujemy kodu 201 i poprawnego zapisu.
    """
    kategoria = "Narzedzia"

    # 1. Najpierw ustawiamy budżet dla kategorii na 500 zł
    budget_response = await async_client.post(
        "/budgets/",
        json={"category": kategoria, "limit_amount": 500.00},
        headers=auth_headers
    )
    assert budget_response.status_code == 201

    # 2. Dodajemy wydatek na 200 zł (zostaje jeszcze 300 zł luzu)
    expense_response = await async_client.post(
        "/expenses/",
        json={"title": "Klucz do kasety Park Tool", "amount": 200.00, "category": kategoria},
        headers=auth_headers
    )
    
    assert expense_response.status_code == 201
    data = expense_response.json()
    assert data["title"] == "Klucz do kasety Park Tool"
    assert data["category"] == kategoria


@pytest.mark.asyncio
async def test_create_expense_exceeding_budget_blocked(async_client: AsyncClient, auth_headers: dict):
    """
    Testuje bezwzględność naszego Strażnika Budżetu.
    Próba dodania wydatku przekraczającego limit musi skończyć się kodem 400.
    """
    kategoria = "Części eksploatacyjne"

    # 1. Ustawiamy ciasny budżet na 100 zł
    budget_response = await async_client.post(
        "/budgets/",
        json={"category": kategoria, "limit_amount": 100.00},
        headers=auth_headers
    )
    assert budget_response.status_code == 201

    # 2. Próbujemy bezczelnie kupić oponę za 250 zł
    expense_response = await async_client.post(
        "/expenses/",
        json={"title": "Opona Maxxis Assegai 3C", "amount": 250.00, "category": kategoria},
        headers=auth_headers
    )
    
    # 3. Sprawdzamy, czy strażnik dał mu po łapach
    assert expense_response.status_code == 400
    error_data = expense_response.json()
    assert "Operacja zablokowana!" in error_data["detail"]
    assert "Limit: 100.00" in error_data["detail"]