"""
asyncio_demo.py
----------------
Introduce el modelo de concurrencia de asyncio:

- Un único hilo con un "event loop" (bucle de eventos) que va
  alternando entre corrutinas cada vez que una hace `await` sobre
  una operación de E/S.
- `async def` define una corrutina; `await` cede el control al event
  loop mientras se espera un resultado (I/O, timers, etc.).
- asyncio.gather permite lanzar varias corrutinas "concurrentemente"
  (concurrencia cooperativa, no paralelismo real de CPU).

Este script simula 5 tareas de E/S con asyncio.sleep y compara el
tiempo total con y sin concurrencia.
"""

import asyncio
import time


async def tarea_async(id_tarea: int, duracion: float = 0.5) -> str:
    """Corrutina que simula una espera de E/S (p. ej. una petición HTTP)."""
    await asyncio.sleep(duracion)
    return f"Tarea async {id_tarea} completada en {duracion}s"


async def secuencial_async(n_tareas: int) -> float:
    """Aunque usemos async/await, si hacemos await uno por uno,
    seguimos siendo secuenciales (no aprovechamos la concurrencia)."""
    inicio = time.perf_counter()
    for i in range(n_tareas):
        await tarea_async(i)
    return time.perf_counter() - inicio


async def concurrente_async(n_tareas: int) -> float:
    """asyncio.gather lanza todas las corrutinas y el event loop
    las va alternando mientras cada una espera su E/S."""
    inicio = time.perf_counter()
    await asyncio.gather(*(tarea_async(i) for i in range(n_tareas)))
    return time.perf_counter() - inicio


async def main():
    N = 8

    t_seq = await secuencial_async(N)
    t_conc = await concurrente_async(N)

    print("=== asyncio: event loop y async/await ===")
    print(f"Tareas: {N}, cada una 'duerme' 0.5s (asyncio.sleep)")
    print(f"await secuencial (una a una): {t_seq:.3f} s (esperado ~{N * 0.5:.1f}s)")
    print(f"asyncio.gather (concurrente): {t_conc:.3f} s (esperado ~0.5s)")


if __name__ == "__main__":
    asyncio.run(main())
