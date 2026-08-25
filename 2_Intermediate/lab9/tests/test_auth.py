import aiohttp


async def test_login_success(server_url):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{server_url}/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"},
        ) as resp:
            assert resp.status == 200
            body = await resp.json()
            assert "access_token" in body
            assert body["token_type"] == "bearer"


async def test_login_wrong_password(server_url):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{server_url}/api/v1/auth/login",
            data={"username": "admin", "password": "incorrecta"},
        ) as resp:
            assert resp.status == 401


async def test_protected_endpoint_sin_token(server_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{server_url}/api/v1/items/") as resp:
            assert resp.status == 401


async def test_openapi_disponible(server_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{server_url}/openapi.json") as resp:
            assert resp.status == 200
            spec = await resp.json()
            assert spec["info"]["title"] == "Lab API"
            assert "/api/v1/auth/login" in spec["paths"]
