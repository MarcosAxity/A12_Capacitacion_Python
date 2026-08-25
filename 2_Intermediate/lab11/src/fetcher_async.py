"""
fetcher_async.py
-----------------
Versión ASÍNCRONA y CONCURRENTE del "fetcher" usando httpx.AsyncClient.

Puntos clave del laboratorio:
- Se usa un único httpx.AsyncClient compartido (reutiliza conexiones).
- Se limita la concurrencia con un asyncio.Semaphore, para no lanzar
  cientos de peticiones simultáneas y saturar el servidor remoto o
  nuestra propia máquina. El semáforo actúa como un "torniquete":
  solo N corrutinas pueden estar dentro del bloque `async with sem`
  al mismo tiempo; el resto espera su turno.
- asyncio.gather lanza todas las descargas "a la vez" y el event loop
  las va alternando cada vez que una hace `await` (esperando la red).
"""

import asyncio
import time
from typing import List, Tuple

import httpx
from fetcher_sync import URLS


async def fetch_una_url(
    client: httpx.AsyncClient,
    url: str,
    semaforo: asyncio.Semaphore,
) -> Tuple[str, int]:
    """Descarga una URL respetando el límite de concurrencia del semáforo."""
    async with semaforo:  # Solo entran aquí como máximo `semaforo._value` corrutinas
        respuesta = await client.get(url, timeout=10.0)
        return url, respuesta.status_code


async def fetch_todas_async(
    urls: List[str],
    max_concurrencia: int = 4,
) -> Tuple[List[Tuple[str, int]], float]:
    """Descarga todas las URLs de forma concurrente, limitando a
    `max_concurrencia` peticiones simultáneas mediante un semáforo."""
    semaforo = asyncio.Semaphore(max_concurrencia)

    inicio = time.perf_counter()

    async with httpx.AsyncClient() as client:
        tareas = [fetch_una_url(client, url, semaforo) for url in urls]
        resultados = await asyncio.gather(*tareas)

    duracion = time.perf_counter() - inicio
    return list(resultados), duracion


if __name__ == "__main__":
    resultados, duracion = asyncio.run(fetch_todas_async(URLS, max_concurrencia=4))

    print("=== Fetcher ASÍNCRONO (httpx.AsyncClient + Semaphore) ===")
    for url, status in resultados:
        print(f"[{status}] {url}")
    print(f"\nTotal: {len(resultados)} URLs en {duracion:.3f} s (max_concurrencia=4)")
