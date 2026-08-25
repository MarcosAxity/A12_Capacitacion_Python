import aiohttp


async def _get_token(session: aiohttp.ClientSession, server_url: str) -> str:
    async with session.post(
        f"{server_url}/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
    ) as resp:
        body = await resp.json()
        return body["access_token"]


async def test_crear_y_listar_item(server_url):
    async with aiohttp.ClientSession() as session:
        token = await _get_token(session, server_url)
        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "name": "Teclado",
            "description": "Mecanico",
            "price": 999.999,
            "tax": 16,
        }
        async with session.post(
            f"{server_url}/api/v1/items/", json=payload, headers=headers
        ) as resp:
            assert resp.status == 201
            created = await resp.json()
            assert created["name"] == "Teclado"
            assert (
                created["price"] == 1000.0
            )  # normalizado por el validator (2 decimales)
            assert created["owner"] == "admin"

        async with session.get(f"{server_url}/api/v1/items/", headers=headers) as resp:
            assert resp.status == 200
            items = await resp.json()
            assert len(items) >= 1


async def test_crear_item_datos_invalidos(server_url):
    async with aiohttp.ClientSession() as session:
        token = await _get_token(session, server_url)
        headers = {"Authorization": f"Bearer {token}"}

        # name vacío y price negativo -> debe fallar la validación Pydantic (422)
        payload = {"name": "", "price": -5}
        async with session.post(
            f"{server_url}/api/v1/items/", json=payload, headers=headers
        ) as resp:
            assert resp.status == 422
            body = await resp.json()
            assert "detail" in body


async def test_obtener_item_inexistente(server_url):
    async with aiohttp.ClientSession() as session:
        token = await _get_token(session, server_url)
        headers = {"Authorization": f"Bearer {token}"}

        async with session.get(
            f"{server_url}/api/v1/items/99999", headers=headers
        ) as resp:
            assert resp.status == 404


async def test_actualizar_y_eliminar_item(server_url):
    async with aiohttp.ClientSession() as session:
        token = await _get_token(session, server_url)
        headers = {"Authorization": f"Bearer {token}"}

        payload = {"name": "Mouse", "price": 250}
        async with session.post(
            f"{server_url}/api/v1/items/", json=payload, headers=headers
        ) as resp:
            item = await resp.json()

        async with session.put(
            f"{server_url}/api/v1/items/{item['id']}",
            json={"price": 300},
            headers=headers,
        ) as resp:
            assert resp.status == 200
            updated = await resp.json()
            assert updated["price"] == 300.0
            assert updated["name"] == "Mouse"  # no se tocó

        async with session.delete(
            f"{server_url}/api/v1/items/{item['id']}", headers=headers
        ) as resp:
            assert resp.status == 204

        async with session.get(
            f"{server_url}/api/v1/items/{item['id']}", headers=headers
        ) as resp:
            assert resp.status == 404
