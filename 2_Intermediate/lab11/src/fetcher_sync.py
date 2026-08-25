"""
fetcher_sync.py
----------------
Versión SÍNCRONA de un "fetcher": descarga una lista de URLs una por una,
usando httpx.Client (bloqueante). Sirve como línea base para comparar
contra la versión concurrente con asyncio (fetcher_async.py).
"""

import time
from typing import List, Tuple

import httpx

# Lista de URLs de ejemplo. Se usan endpoints de la API pública de GitHub
# porque el entorno de este laboratorio permite tráfico hacia api.github.com.
# Puedes reemplazar esta lista por cualquier conjunto de URLs propio.
URLS = [
    "https://api.github.com/repos/python/cpython",
    "https://api.github.com/repos/psf/requests",
    "https://api.github.com/repos/encode/httpx",
    "https://api.github.com/repos/pallets/flask",
    "https://api.github.com/repos/pandas-dev/pandas",
    "https://api.github.com/repos/numpy/numpy",
    "https://api.github.com/repos/django/django",
    "https://api.github.com/repos/fastapi/fastapi",
]


def fetch_una_url(client: httpx.Client, url: str) -> Tuple[str, int]:
    """Descarga una URL y devuelve (url, status_code)."""
    respuesta = client.get(url, timeout=10.0)
    return url, respuesta.status_code


def fetch_todas_sync(urls: List[str]) -> Tuple[List[Tuple[str, int]], float]:
    """Descarga todas las URLs de forma secuencial (una tras otra)."""
    resultados = []
    inicio = time.perf_counter()

    with httpx.Client() as client:
        for url in urls:
            resultados.append(fetch_una_url(client, url))

    duracion = time.perf_counter() - inicio
    return resultados, duracion


if __name__ == "__main__":
    resultados, duracion = fetch_todas_sync(URLS)

    print("=== Fetcher SÍNCRONO (httpx.Client) ===")
    for url, status in resultados:
        print(f"[{status}] {url}")
    print(f"\nTotal: {len(resultados)} URLs en {duracion:.3f} s")
