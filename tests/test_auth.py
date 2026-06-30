import uuid
from httpx import AsyncClient


async def test_full_auth_flow(client: AsyncClient):
    """
    Dojebany test integracyjny przechodzący przez cały proces:
    Rejestracja -> Blokada duplikatu -> Logowanie.
    """
    # 1. Generujemy unikalne dane testowe, żeby baza nie pluła się o duplikaty
    unique_id = uuid.uuid4().hex[:6]
    company_name = f"Serwis Rowerowy {unique_id} Sp. z o.o."
    email = f"mechanik_{unique_id}@skoczek.pl"
    password = "SuperTajneHaslo123!"

    payload = {
        "company_data": {
            "name": company_name
        },
        "user_data": {
            "email": email,
            "password": password,
            "role": "Admin",
            "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"  # Losowy UUID, backend go nadpisze
        }
    }

    # ---- ETAP A: Rejestracja nowej firmy ----
    register_response = await client.post("/auth/register-company", json=payload)
    assert register_response.status_code == 201
    
    reg_data = register_response.json()
    assert reg_data["email"] == email
    assert reg_data["role"] == "Admin"
    assert "id" in reg_data
    assert "organization_id" in reg_data

    # ---- ETAP B: Próba rejestracji duplikatu (Edge Case) ----
    duplicate_response = await client.post("/auth/register-company", json=payload)
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Organizacja o podanej nazwie już istnieje."

    # ---- ETAP C: Logowanie na nowo stworzone konto ----
    # Specyfikacja OAuth2PasswordRequestForm wymaga wysłania danych jako form-data, nie JSON!
    login_payload = {
        "username": email,
        "password": password
    }
    
    login_response = await client.post("/auth/login", data=login_payload)
    assert login_response.status_code == 200
    
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"