import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_and_health(client: AsyncClient):
    res = await client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

    health = await client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # Register
    reg_payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "strongpassword123",
        "role": "Frontend Engineer",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "jane@example.com"
    assert data["user"]["name"] == "Jane Doe"

    # Login
    login_payload = {
        "email": "jane@example.com",
        "password": "strongpassword123",
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Login wrong password
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "jane@example.com", "password": "wrongpassword"},
    )
    assert bad_login.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_me(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "testuser@example.com"
    assert data["name"] == "Test User"


@pytest.mark.asyncio
async def test_google_login_mock(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/google",
        json={"token": "test-google-token-999"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "user-999@gmail.com"
