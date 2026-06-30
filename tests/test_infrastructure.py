from httpx import AsyncClient


async def test_health_check(client: AsyncClient):
    """Testuje, czy endpoint infrastrukturalny zwraca poprawny status i konfigurację."""
    # Wykonujemy asynchroniczny strzał do naszego API
    response = await client.get("/health")
    
    # Bezwzględne asercje – sprawdzamy stan faktyczny
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_url_configured"] is True
    assert data["jwt_algorithm"] == "HS256"