"""
compare_fetchers.py
--------------------
Ejecuta el fetcher síncrono (fetcher_sync.py) y el fetcher asíncrono
(fetcher_async.py) sobre el mismo conjunto de URLs y compara los
tiempos totales, mostrando el "speedup" (factor de mejora).

Uso:
    python src/compare_fetchers.py
"""

import asyncio

from fetcher_async import fetch_todas_async
from fetcher_sync import URLS, fetch_todas_sync


def main():
    print("Descargando", len(URLS), "URLs con ambos enfoques...\n")

    _, t_sync = fetch_todas_sync(URLS)
    _, t_async = asyncio.run(fetch_todas_async(URLS, max_concurrencia=4))

    print("=== Comparación Síncrono vs Asíncrono ===")
    print(f"Síncrono (httpx.Client, secuencial):        {t_sync:.3f} s")
    print(f"Asíncrono (httpx.AsyncClient + Semaphore):  {t_async:.3f} s")

    if t_async > 0:
        speedup = t_sync / t_async
        print(f"\nSpeedup aproximado: {speedup:.2f}x más rápido con asyncio")

    print(
        "\nNota: la mejora depende de la latencia de red y del número de\n"
        "URLs. Con más URLs y mayor latencia, la ventaja de la versión\n"
        "asíncrona suele ser todavía más grande, porque las esperas de\n"
        "red se solapan en lugar de sumarse."
    )


if __name__ == "__main__":
    main()
