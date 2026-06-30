import uuid
from httpx import AsyncClient


async def test_full_auth_flow(client: AsyncClient):
    unique_id = uuid.uuid4().hex[:6]
    company_name = f"Serwis Rowerowy {unique_id} Sp. z o.o."
    email = f"mechanik_{unique_id}@skoczek.pl"
    password = "SuperTajneHaslo123!"

    payload = {
        "company_data": {"name": company_name},
        "user_data": {"email": email, "password": password},
    }

    register_response = await client.post("/auth/register-company", json=payload)
    assert register_response.status_code == 201

    reg_data = register_response.json()
    assert reg_data["email"] == email
    assert reg_data["role"] == "Admin"
    assert "id" in reg_data
    assert "organization_id" in reg_data

    duplicate_response = await client.post("/auth/register-company", json=payload)
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Organizacja o podanej nazwie już istnieje."

    login_response = await client.post("/auth/login", data={"username": email, "password": password})
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


async def test_register_duplicate_email_blocked(client: AsyncClient):
    unique_id = uuid.uuid4().hex[:6]
    email = f"dup_{unique_id}@example.com"
    password = "SuperTajneHaslo123!"

    first = await client.post(
        "/auth/register-company",
        json={
            "company_data": {"name": f"Firma A {unique_id}"},
            "user_data": {"email": email, "password": password},
        },
    )
    assert first.status_code == 201

    second = await client.post(
        "/auth/register-company",
        json={
            "company_data": {"name": f"Firma B {unique_id}"},
            "user_data": {"email": email, "password": password},
        },
    )
    assert second.status_code == 400
    assert second.json()["detail"] == "Użytkownik o podanym adresie email już istnieje."


async def test_register_employee_by_admin(client: AsyncClient, auth_headers: dict):
    unique_id = uuid.uuid4().hex[:6]
    response = await client.post(
        "/auth/register-employee",
        json={"email": f"worker_{unique_id}@example.com", "password": "EmployeeHaslo123!"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["role"] == "Employee"


async def test_register_employee_forbidden_for_employee(client: AsyncClient, employee_auth_headers: dict):
    response = await client.post(
        "/auth/register-employee",
        json={"email": "hacker@example.com", "password": "EmployeeHaslo123!"},
        headers=employee_auth_headers,
    )
    assert response.status_code == 403
