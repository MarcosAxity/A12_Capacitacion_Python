# Lab API — FastAPI + JWT + Pydantic + Testing

## 1. Estructura del proyecto

```
app/
  core/
    config.py          # settings centralizados
    security.py         # hashing + creación/validación de JWT
    dependencies.py     # get_current_user / get_current_active_user
  db/
    fake_db.py          # "base de datos" en memoria (para el lab)
  schemas/
    user.py, token.py, item.py   # modelos Pydantic (request/response)
  routers/
    auth.py              # POST /api/v1/auth/login
    items.py              # CRUD /api/v1/items
  middlewares.py         # middleware propio (logging + tiempo de respuesta)
  main.py                # arma la app, CORS, middlewares, routers
tests/
  conftest.py           # levanta la app real (uvicorn) para testear con aiohttp
  test_auth.py
  test_items.py
```

Separar `routers`, `schemas`, `core` y `db` permite escalar el proyecto sin
mezclar responsabilidades: los routers solo orquestan, la validación vive en
los schemas, y la seguridad/config vive en `core`.

## 2. Instalación

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Ejecutar la API

```bash
uvicorn app.main:app --reload
```

- Documentación interactiva (Swagger): http://127.0.0.1:8000/docs
- Documentación alternativa (ReDoc): http://127.0.0.1:8000/redoc
- Especificación OpenAPI cruda: http://127.0.0.1:8000/openapi.json

FastAPI genera el `openapi.json` automáticamente a partir de los schemas
Pydantic y los `summary`/`description` de cada endpoint — no hay que
mantener documentación aparte.

## 4. Probar la autenticación

Usuario de prueba: `admin` / `admin123`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Devuelve un token JWT. Se usa como header en los endpoints protegidos:

```bash
curl http://127.0.0.1:8000/api/v1/items/ \
  -H "Authorization: Bearer <TOKEN>"
```

## 5. Validación con Pydantic

`ItemCreate` valida, entre otras cosas:
- `name`: obligatorio, 1–100 caracteres.
- `price`: obligatorio, debe ser > 0, y un `field_validator` lo redondea a
  2 decimales.
- `tax`: opcional, debe ser ≥ 0.

Si el payload no cumple, FastAPI responde automáticamente `422 Unprocessable
Entity` con el detalle de qué campo falló, sin escribir código extra.

## 6. Seguridad implementada

- **JWT**: `python-jose` firma/verifica tokens HS256 con expiración.
- **Password hashing**: `passlib[bcrypt]`, nunca se guardan contraseñas en
  texto plano.
- **OAuth2PasswordBearer**: integra el flujo de login con Swagger UI (botón
  "Authorize").
- **Dependencias (`Depends`)**: `get_current_active_user` protege cada
  endpoint de `items` sin duplicar lógica.
- **CORS**: configurado vía `CORSMiddleware` con orígenes permitidos en
  `settings.BACKEND_CORS_ORIGINS`.
- **Middleware propio**: `LoggingMiddleware` mide el tiempo de respuesta de
  cada request y lo agrega como header `X-Process-Time-ms`.

## 7. Prueba manual paso a paso (curl)

Con el servidor corriendo (`uvicorn app.main:app --reload`), abre una
**segunda terminal** (no cierres la que tiene el servidor) y sigue estos
pasos en orden.

### 7.1 Login y guardar el token en una variable

No copies/pegues el token a mano — al pegarlo en la terminal suele
cortarse en varias líneas y rompe el comando. Mejor captúralo directo en
una variable:

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo $TOKEN   # debe imprimir una sola línea larga tipo eyJhbGciOi...
```

### 7.2 Endpoint protegido sin token → debe fallar (401)

```bash
curl -i http://127.0.0.1:8000/api/v1/items/
```

Respuesta esperada: `HTTP/1.1 401 Unauthorized`,
`{"detail":"Not authenticated"}`. Confirma que `get_current_active_user`
bloquea el acceso sin credenciales.

### 7.3 Mismo endpoint con token → debe funcionar (200)

```bash
curl -i http://127.0.0.1:8000/api/v1/items/ -H "Authorization: Bearer $TOKEN"
```

Respuesta esperada: `HTTP/1.1 200 OK` con `[]` (todavía no hay items).

### 7.4 Crear un item válido (201)

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/items/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Teclado", "price": 999.999, "tax": 16}'
```

Respuesta esperada: `201 Created` con el item creado.

### 7.5 Ver el redondeo del `field_validator` en acción

El validador de `price` en `app/schemas/item.py` hace `round(v, 2)`. Para
verlo tienes que enviar un `price` con **3 o más decimales** — si envías
algo que ya tiene 2 decimales (ej. `999.99`), la respuesta se ve igual
porque no había nada que redondear.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/items/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Mouse", "price": 12.3456}'
```

Enviaste `"price": 12.3456` → la respuesta debe traer `"price": 12.35`.
Compara el request y el response uno debajo del otro para confirmar el
cambio.

### 7.6 Validación con datos inválidos (422)

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/items/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "", "price": -5}'
```

Respuesta esperada: `422 Unprocessable Entity` con el detalle de qué
campo(s) fallaron (`name` vacío, `price` negativo). Pydantic valida antes
de que el código de negocio se ejecute.

### 7.7 Repetir todo en Swagger UI (más visual)

Abre http://127.0.0.1:8000/docs, clic en **Authorize** (arriba a la
derecha), ingresa `admin` / `admin123`, clic en **Authorize**. Desde ahí
puedes expandir cualquier endpoint, dar clic en **Try it out**, editar el
JSON del body y ejecutar — verás en vivo las mismas respuestas
200/201/401/422 sin escribir curl, y con el request/response uno debajo
del otro.

### 7.8 Obtener un item por id (200)

Usa el `id` que te devolvió el POST del paso 7.4 (por ejemplo `id=2`):

```bash
curl -i http://127.0.0.1:8000/api/v1/items/2 -H "Authorization: Bearer $TOKEN"
```

Respuesta esperada: `200 OK` con ese item exacto.

### 7.9 Item que no existe (404)

```bash
curl -i http://127.0.0.1:8000/api/v1/items/99999 -H "Authorization: Bearer $TOKEN"
```

Respuesta esperada: `404 Not Found`, `{"detail":"Item no encontrado"}`.
Confirma que el router valida existencia antes de devolver datos.

### 7.10 Actualizar un item (PUT, 200)

```bash
curl -i -X PUT http://127.0.0.1:8000/api/v1/items/2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"price": 850.5}'
```

Como `ItemUpdate` tiene todos los campos opcionales, solo mandas lo que
quieres cambiar. Respuesta esperada: `200` con `price` actualizado y el
resto de campos (`name`, `description`) intactos.

### 7.11 Eliminar un item (DELETE, 204)

```bash
curl -i -X DELETE http://127.0.0.1:8000/api/v1/items/2 -H "Authorization: Bearer $TOKEN"
```

Respuesta esperada: `204 No Content` (sin body). Es el código correcto
para un delete exitoso.

### 7.12 Confirmar que ya no existe (404)

```bash
curl -i http://127.0.0.1:8000/api/v1/items/2 -H "Authorization: Bearer $TOKEN"
```

Debe volver a dar `404`. Esto cierra el ciclo completo del CRUD: crear,
leer, actualizar, borrar y confirmar el borrado.

### 7.13 Login con usuario que no existe (401)

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=nadie&password=loquesea"
```

Debe dar `401`, igual que con password incorrecto. Confirma que el flujo
no distingue entre "usuario no existe" y "password mal" (por seguridad,
no revela cuál de los dos falló).

### 7.14 Verificar el header del middleware propio

```bash
curl -i http://127.0.0.1:8000/health
```

En los headers de respuesta busca `x-process-time-ms`. Ese header lo
agrega tu `LoggingMiddleware` en cada request, no viene de FastAPI por
defecto — confirma que el middleware personalizado está corriendo.

### 7.15 Verificar CORS con un origen permitido

```bash
curl -i -X OPTIONS http://127.0.0.1:8000/api/v1/items/ \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET"
```

Es un preflight CORS simulado. Debe responder con el header
`access-control-allow-origin: http://localhost:3000`, confirmando que
`CORSMiddleware` está configurado con los orígenes de
`settings.BACKEND_CORS_ORIGINS`.

## 8. Testing (pytest + aiohttp)

`tests/conftest.py` levanta la aplicación real con `uvicorn` en un hilo de
fondo (puerto libre aleatorio) y expone `server_url`. Los tests usan
`aiohttp.ClientSession` para hacer peticiones HTTP reales end-to-end
(login, endpoints protegidos, validación, CRUD completo).

```bash
pytest -v
```

Casos cubiertos:
- Login correcto / incorrecto.
- Acceso a endpoint protegido sin token → `401`.
- `openapi.json` disponible y coherente.
- Crear/listar/actualizar/eliminar items.
- Payload inválido → `422`.
- Item inexistente → `404`.
