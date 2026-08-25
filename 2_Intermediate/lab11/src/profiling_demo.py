"""
profiling_demo.py
-------------------
Muestra dos herramientas estándar para medir rendimiento en Python:

1) timeit: para medir el tiempo de ejecución de fragmentos de código
   pequeños de forma precisa (ejecuta el código varias veces y promedia,
   evitando ruido de una sola medición).

2) cProfile: para perfilar un programa completo y ver en qué funciones
   se gasta más tiempo (número de llamadas, tiempo acumulado, tiempo
   propio, etc.). Es la herramienta a usar cuando "algo es lento" y no
   sabemos qué parte del código es la responsable.

Uso:
    python src/profiling_demo.py
"""

import cProfile
import pstats
import timeit
from io import StringIO

# --- 1) timeit ---------------------------------------------------------


def suma_con_bucle(n: int) -> int:
    total = 0
    for i in range(n):
        total += i
    return total


def suma_con_sum_builtin(n: int) -> int:
    return sum(range(n))


def demo_timeit():
    print("=== timeit: comparar dos formas de sumar 0..999999 ===")

    tiempo_bucle = timeit.timeit(lambda: suma_con_bucle(1_000_000), number=5)
    tiempo_sum = timeit.timeit(lambda: suma_con_sum_builtin(1_000_000), number=5)

    print(
        f"Bucle for manual (5 ejecuciones): {tiempo_bucle:.4f} s totales "
        f"({tiempo_bucle / 5:.4f} s por ejecución)"
    )
    print(
        f"sum(range(n)) built-in (5 ejec.): {tiempo_sum:.4f} s totales "
        f"({tiempo_sum / 5:.4f} s por ejecución)"
    )
    print(f"La versión built-in es ~{tiempo_bucle / tiempo_sum:.1f}x más rápida.\n")


# --- 2) cProfile ---------------------------------------------------------


def funcion_lenta():
    """Función de ejemplo con una parte claramente más costosa que otra,
    para que se note en el perfil."""
    resultado = []
    for i in range(200_000):
        resultado.append(i * i)
    return operacion_costosa(resultado)


def operacion_costosa(datos):
    return sorted(datos, reverse=True)[:10]


def demo_cprofile():
    print("=== cProfile: perfilando funcion_lenta() ===")

    profiler = cProfile.Profile()
    profiler.enable()
    funcion_lenta()
    profiler.disable()

    salida = StringIO()
    stats = pstats.Stats(profiler, stream=salida).sort_stats("cumulative")
    stats.print_stats(8)  # mostrar solo las 8 funciones más relevantes

    print(salida.getvalue())
    print(
        "Lectura rápida de las columnas:\n"
        "  ncalls   -> número de veces que se llamó a la función\n"
        "  tottime  -> tiempo propio de la función (sin contar subllamadas)\n"
        "  cumtime  -> tiempo acumulado incluyendo subllamadas\n"
    )


if __name__ == "__main__":
    demo_timeit()
    demo_cprofile()
