"""
cpu_bound_multiprocessing.py
-----------------------------
Laboratorio: pequeño cálculo CPU-bound usando ProcessPoolExecutor.

A diferencia de threading (limitado por el GIL para código Python puro),
multiprocessing crea PROCESOS del sistema operativo independientes, cada
uno con su propio intérprete de Python y su propio GIL. Esto permite
aprovechar varios núcleos de CPU en paralelo real para tareas de cómputo
intensivo.

Tarea de ejemplo: contar cuántos números primos hay en varios rangos de
números (operación puramente CPU-bound, sin E/S).
"""

import time
from concurrent.futures import ProcessPoolExecutor
from typing import List


def es_primo(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def contar_primos_en_rango(rango: range) -> int:
    """Cuenta cuántos primos hay dentro de un rango. Es la función que
    se ejecutará en cada proceso worker."""
    return sum(1 for n in rango if es_primo(n))


def dividir_en_rangos(inicio: int, fin: int, n_partes: int) -> List[range]:
    """Divide [inicio, fin) en n_partes rangos aproximadamente iguales."""
    total = fin - inicio
    paso = total // n_partes
    rangos = []
    for i in range(n_partes):
        r_inicio = inicio + i * paso
        r_fin = fin if i == n_partes - 1 else inicio + (i + 1) * paso
        rangos.append(range(r_inicio, r_fin))
    return rangos


def version_secuencial(inicio: int, fin: int) -> tuple[int, float]:
    t0 = time.perf_counter()
    total = contar_primos_en_rango(range(inicio, fin))
    return total, time.perf_counter() - t0


def version_multiproceso(
    inicio: int, fin: int, n_procesos: int = 4
) -> tuple[int, float]:
    rangos = dividir_en_rangos(inicio, fin, n_procesos)

    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=n_procesos) as executor:
        resultados = list(executor.map(contar_primos_en_rango, rangos))
    total = sum(resultados)
    return total, time.perf_counter() - t0


if __name__ == "__main__":
    INICIO, FIN = 0, 300_000
    N_PROCESOS = 4

    print("=== CPU-bound: conteo de primos con ProcessPoolExecutor ===")
    print(f"Rango: [{INICIO:,}, {FIN:,})\n")

    total_seq, t_seq = version_secuencial(INICIO, FIN)
    print(f"Secuencial:            {total_seq:,} primos en {t_seq:.3f} s")

    total_mp, t_mp = version_multiproceso(INICIO, FIN, N_PROCESOS)
    print(f"Multiproceso ({N_PROCESOS} procesos): {total_mp:,} primos en {t_mp:.3f} s")

    if t_mp > 0:
        print(f"\nSpeedup aproximado: {t_seq / t_mp:.2f}x")
