"""
gil_demo.py
-----------
Demuestra el impacto del GIL (Global Interpreter Lock) de CPython.

El GIL es un candado global que permite que, en un proceso CPython, solo
UN hilo ejecute bytecode Python a la vez. Esto significa que:

- Para tareas CPU-bound (cálculo puro en Python), usar varios *threads*
  NO acelera el trabajo, porque solo uno corre bytecode en cada instante.
  De hecho puede ser incluso más lento por el overhead de cambio de contexto.
- Para tareas I/O-bound (esperar red, disco, DB), el GIL SÍ se libera
  mientras se espera la operación de E/S, por lo que threading/asyncio
  sí ayudan a solapar esperas.
- Para aprovechar varios núcleos de CPU en tareas de cómputo puro, hace
  falta multiprocessing (procesos separados, cada uno con su propio GIL).

Este script mide el tiempo de una tarea CPU-bound (contar hasta N)
ejecutada:
    1) de forma secuencial (1 hilo)
    2) con 4 threads (cada uno haciendo 1/4 del trabajo)

y muestra que el tiempo con threads NO mejora (incluso empeora un poco).
"""

import threading
import time


def cpu_bound_count(n: int) -> int:
    """Tarea puramente CPU-bound: cuenta hasta n sumando en Python puro."""
    total = 0
    for i in range(n):
        total += i
    return total


def version_secuencial(n_total: int) -> float:
    inicio = time.perf_counter()
    cpu_bound_count(n_total)
    return time.perf_counter() - inicio


def version_con_threads(n_total: int, n_hilos: int = 4) -> float:
    porcion = n_total // n_hilos
    hilos = [
        threading.Thread(target=cpu_bound_count, args=(porcion,))
        for _ in range(n_hilos)
    ]

    inicio = time.perf_counter()
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    return time.perf_counter() - inicio


if __name__ == "__main__":
    N = 20_000_000

    t_secuencial = version_secuencial(N)
    t_threads = version_con_threads(N, n_hilos=4)

    print("=== Demostración del GIL (tarea CPU-bound) ===")
    print(f"Trabajo total: contar hasta {N:,}")
    print(f"Tiempo 1 hilo (secuencial):        {t_secuencial:.3f} s")
    print(f"Tiempo 4 hilos (threading):         {t_threads:.3f} s")
    print()
    print("Conclusión: por el GIL, usar threads NO acelera el trabajo")
    print("CPU-bound; para eso se necesita multiprocessing (ver")
    print("cpu_bound_multiprocessing.py).")
