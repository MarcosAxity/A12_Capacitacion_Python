"""
main.py
-------
Orquesta la ejecución de todos los demos del Módulo 11 en orden.

Uso:
    python src/main.py            # ejecuta todo
    python src/main.py gil        # ejecuta solo la demo del GIL
    python src/main.py threading  # ejecuta solo threading_demo
    python src/main.py asyncio    # ejecuta solo asyncio_demo
    python src/main.py fetch      # ejecuta la comparación de fetchers (requiere red)
    python src/main.py cpu        # ejecuta el demo de multiprocessing
    python src/main.py profiling  # ejecuta timeit + cProfile
"""

import sys


def main():
    opcion = sys.argv[1] if len(sys.argv) > 1 else "all"

    secciones = {
        "gil": "gil_demo.py",
        "threading": "threading_demo.py",
        "asyncio": "asyncio_demo.py",
        "fetch": "compare_fetchers.py",
        "cpu": "cpu_bound_multiprocessing.py",
        "profiling": "profiling_demo.py",
    }

    if opcion == "all":
        for nombre, archivo in secciones.items():
            print(f"\n{'#' * 70}\n# Ejecutando: {archivo}\n{'#' * 70}\n")
            with open(archivo) as f:
                codigo = f.read()
            exec(compile(codigo, archivo, "exec"), {"__name__": "__main__"})
    elif opcion in secciones:
        archivo = secciones[opcion]
        with open(archivo) as f:
            codigo = f.read()
        exec(compile(codigo, archivo, "exec"), {"__name__": "__main__"})
    else:
        print(f"Opción no reconocida: {opcion}")
        print(f"Opciones válidas: all, {', '.join(secciones.keys())}")
        sys.exit(1)


if __name__ == "__main__":
    main()
