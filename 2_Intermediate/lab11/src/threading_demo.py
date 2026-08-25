"""
threading_demo.py
------------------
Muestra dos formas de trabajar con hilos en Python para tareas I/O-bound
(simuladas aquí con time.sleep, que libera el GIL mientras "espera"):

1) threading.Thread "a mano": crear, iniciar y unir (join) hilos.
2) concurrent.futures.ThreadPoolExecutor: una interfaz de más alto nivel
   (pool de hilos + futuros) recomendada para la mayoría de los casos.

Ambas formas mejoran mucho el tiempo total frente a hacerlo todo
secuencialmente, porque mientras un hilo "espera" (E/S), otro puede
avanzar.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def tarea_io(id_tarea: int, duracion: float = 0.5) -> str:
    """Simula una operación de E/S (ej. una llamada de red) que bloquea
    pero libera el GIL mientras espera."""
    time.sleep(duracion)
    return f"Tarea {id_tarea} completada en {duracion}s"


def con_threading_manual(n_tareas: int) -> float:
    resultados = []
    lock = threading.Lock()

    def worker(i):
        r = tarea_io(i)
        with lock:
            resultados.append(r)

    inicio = time.perf_counter()
    hilos = [threading.Thread(target=worker, args=(i,)) for i in range(n_tareas)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    return time.perf_counter() - inicio


def con_thread_pool_executor(n_tareas: int, max_workers: int = 8) -> float:
    inicio = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = [executor.submit(tarea_io, i) for i in range(n_tareas)]
        for f in as_completed(futuros):
            f.result()  # aquí se recogería/usaría el resultado
    return time.perf_counter() - inicio


def version_secuencial(n_tareas: int) -> float:
    inicio = time.perf_counter()
    for i in range(n_tareas):
        tarea_io(i)
    return time.perf_counter() - inicio


if __name__ == "__main__":
    N = 8

    t_seq = version_secuencial(N)
    t_thread_manual = con_threading_manual(N)
    t_pool = con_thread_pool_executor(N)

    print("=== threading vs concurrent.futures (I/O-bound simulado) ===")
    print(f"Tareas: {N}, cada una duerme 0.5s")
    print(f"Secuencial:              {t_seq:.3f} s (esperado ~{N * 0.5:.1f}s)")
    print(f"threading.Thread manual: {t_thread_manual:.3f} s (esperado ~0.5s)")
    print(f"ThreadPoolExecutor:      {t_pool:.3f} s (esperado ~0.5-1.0s)")
