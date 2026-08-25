# Módulo 11 · Concurrencia y rendimiento en Python

Solución práctica que cubre los contenidos, objetivos y laboratorio del
módulo: GIL, `threading`, `concurrent.futures`, `asyncio`, `multiprocessing`
y medición de rendimiento con `timeit` / `cProfile`.

## 1. Estructura del proyecto

```
modulo11_concurrencia/
├── README.md
├── requirements.txt
└── src/
    ├── gil_demo.py                  # GIL: por qué threading no acelera CPU-bound
    ├── threading_demo.py            # threading.Thread vs ThreadPoolExecutor
    ├── asyncio_demo.py              # event loop, async/await, asyncio.gather
    ├── fetcher_sync.py              # Laboratorio: fetcher síncrono (httpx.Client)
    ├── fetcher_async.py             # Laboratorio: fetcher async + Semaphore
    ├── compare_fetchers.py          # Laboratorio: comparación sync vs async
    ├── cpu_bound_multiprocessing.py # Laboratorio: cálculo CPU-bound con ProcessPoolExecutor
    ├── profiling_demo.py            # timeit y cProfile
    └── main.py                      # Orquestador: ejecuta todo o una sección
```

## 2. Cómo se relaciona cada archivo con el temario

| Contenido clave                     | Archivo(s)                                            |
|--------------------------------------|--------------------------------------------------------|
| GIL y sus implicaciones              | `gil_demo.py`                                          |
| `threading` y `concurrent.futures`   | `threading_demo.py`                                    |
| `asyncio`: event loop, async/await   | `asyncio_demo.py`                                       |
| `multiprocessing` para CPU-bound     | `cpu_bound_multiprocessing.py`                          |
| Medición con `timeit` y `cProfile`   | `profiling_demo.py`                                     |
| **Objetivo:** elegir el modelo apropiado | Todos los demos, comparados entre sí (ver sección 5) |
| **Objetivo:** E/S concurrente y medir mejoras | `fetcher_sync.py`, `fetcher_async.py`, `compare_fetchers.py` |
| **Laboratorio:** fetcher con `httpx.AsyncClient` + semáforo | `fetcher_async.py`                        |
| **Laboratorio:** comparación con versión síncrona | `fetcher_sync.py` + `compare_fetchers.py`           |
| **Laboratorio:** CPU-bound con `ProcessPoolExecutor` | `cpu_bound_multiprocessing.py`                  |

## 3. Requisitos previos

- Python 3.10 o superior (se usan anotaciones tipo `tuple[int, float]`).
- Conexión a internet **solo** para `fetcher_sync.py`, `fetcher_async.py` y
  `compare_fetchers.py` (consultan la API pública de GitHub). El resto de
  scripts funcionan sin red.

## 4. Instalación

Desde la carpeta raíz del proyecto (`modulo11_concurrencia/`):

```bash
# 1. (Recomendado) crear un entorno virtual
python3 -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate

# 2. Instalar dependencias (solo httpx)
pip install -r requirements.txt
```

## 5. Cómo ejecutar cada parte

Todos los comandos se ejecutan desde la carpeta `src/`:

```bash
cd src
```

### 5.1 GIL (contenido clave)

```bash
python gil_demo.py
```
Compara contar hasta 20 millones en 1 hilo vs en 4 hilos. Verás que el
tiempo **no mejora** (incluso puede empeorar un poco), porque el GIL
impide que dos hilos ejecuten bytecode Python simultáneamente. Esta es
la razón por la que, para CPU-bound, se necesita `multiprocessing`
(sección 5.5) en lugar de `threading`.

**Salida**
```bash
=== Demostración del GIL (tarea CPU-bound) ===
Trabajo total: contar hasta 20,000,000
Tiempo 1 hilo (secuencial):        0.325 s
Tiempo 4 hilos (threading):        0.312 s

Conclusión: por el GIL, usar threads NO acelera el trabajo
CPU-bound; para eso se necesita multiprocessing (ver
cpu_bound_multiprocessing.py).
```

### 5.2 threading y concurrent.futures

```bash
python threading_demo.py
```
Simula 8 tareas de E/S (`time.sleep(0.5)`) y compara:
- Secuencial (~4 s)
- `threading.Thread` manual (~0.5 s)
- `ThreadPoolExecutor` (~0.5 s, con interfaz de más alto nivel)

Aquí el GIL **sí se libera** durante `time.sleep`, por lo que los hilos
sí aportan una mejora real para tareas I/O-bound.

**Salida**

```bash
=== threading vs concurrent.futures (I/O-bound simulado) ===
Tareas: 8, cada una duerme 0.5s
Secuencial:              4.033 s (esperado ~4.0s)
threading.Thread manual: 0.506 s (esperado ~0.5s)
ThreadPoolExecutor:      0.506 s (esperado ~0.5-1.0s)
```

### 5.3 asyncio: event loop y async/await

```bash
python asyncio_demo.py
```
Mismo experimento que el anterior pero con corrutinas (`async def`) y
`asyncio.sleep`. Muestra la diferencia entre:
- Hacer `await` uno por uno (sigue siendo secuencial, ~4 s).
- Lanzar todas las corrutinas con `asyncio.gather` (concurrente, ~0.5 s).

**Salida**

```bash
=== asyncio: event loop y async/await ===
Tareas: 8, cada una 'duerme' 0.5s (asyncio.sleep)
await secuencial (una a una): 4.010 s (esperado ~4.0s)
asyncio.gather (concurrente): 0.501 s (esperado ~0.5s)
```


### 5.4 Laboratorio — Fetcher concurrente (I/O-bound)

**Versión síncrona** (una petición HTTP tras otra):
```bash
python fetcher_sync.py
```

**Salida**

```bash
=== Fetcher SÍNCRONO (httpx.Client) ===
[200] https://api.github.com/repos/python/cpython
[200] https://api.github.com/repos/psf/requests
[200] https://api.github.com/repos/encode/httpx
[200] https://api.github.com/repos/pallets/flask
[200] https://api.github.com/repos/pandas-dev/pandas
[200] https://api.github.com/repos/numpy/numpy
[200] https://api.github.com/repos/django/django
[200] https://api.github.com/repos/fastapi/fastapi
```


**Versión asíncrona** (con `httpx.AsyncClient` + `asyncio.Semaphore`):
```bash
python fetcher_async.py
```
El semáforo (`asyncio.Semaphore(max_concurrencia)`) limita cuántas
peticiones están "en vuelo" al mismo tiempo (por defecto 4), para no
saturar el servidor remoto ni disparar demasiadas conexiones a la vez.

**Salida**

```bash
=== Fetcher ASÍNCRONO (httpx.AsyncClient + Semaphore) ===
[200] https://api.github.com/repos/python/cpython
[200] https://api.github.com/repos/psf/requests
[200] https://api.github.com/repos/encode/httpx
[200] https://api.github.com/repos/pallets/flask
[200] https://api.github.com/repos/pandas-dev/pandas
[200] https://api.github.com/repos/numpy/numpy
[200] https://api.github.com/repos/django/django
[200] https://api.github.com/repos/fastapi/fastapi

Total: 8 URLs en 0.420 s (max_concurrencia=4)
```


**Comparación directa (ejecuta ambas y calcula el speedup):**
```bash
python compare_fetchers.py
```
Salida esperada (aproximada, depende de tu conexión):
```
Síncrono (httpx.Client, secuencial):        1.3 s
Asíncrono (httpx.AsyncClient + Semaphore):  0.3 s
Speedup aproximado: ~4x más rápido con asyncio
```

**Salida**

```bash
Descargando 8 URLs con ambos enfoques...

=== Comparación Síncrono vs Asíncrono ===
Síncrono (httpx.Client, secuencial):        1.024 s
Asíncrono (httpx.AsyncClient + Semaphore):  0.438 s

Speedup aproximado: 2.34x más rápido con asyncio

Nota: la mejora depende de la latencia de red y del número de
URLs. Con más URLs y mayor latencia, la ventaja de la versión
asíncrona suele ser todavía más grande, porque las esperas de
red se solapan en lugar de sumarse.
```


> **Nota:** las URLs de ejemplo usan la API pública de GitHub
> (`api.github.com`), que tiene un límite de ~60 peticiones/hora para
> clientes anónimos. Si ves algún código `403` es por ese límite de
> tasa, no un error del código. Puedes reemplazar la lista `URLS` en
> `fetcher_sync.py` por cualquier otro conjunto de endpoints propios.

### 5.5 Laboratorio — Cálculo CPU-bound con ProcessPoolExecutor

```bash
python cpu_bound_multiprocessing.py
```
Cuenta números primos en el rango `[0, 300_000)`, primero de forma
secuencial y luego repartiendo el trabajo entre 4 procesos con
`ProcessPoolExecutor`. Al usar procesos (no hilos), cada uno tiene su
propio GIL, por lo que **sí** se logra paralelismo real de CPU.

> **Importante:** el speedup real depende del número de núcleos físicos
> disponibles en tu máquina. En una máquina con 1 solo núcleo (como
> algunos entornos de contenedor) no habrá mejora; en una máquina con 4
> u 8 núcleos deberías ver un speedup cercano a 2-4x.


**Salida**

```bash
=== CPU-bound: conteo de primos con ProcessPoolExecutor ===
Rango: [0, 300,000)

Secuencial:            25,997 primos en 0.127 s
Multiproceso (4 procesos): 25,997 primos en 0.143 s

Speedup aproximado: 0.89x
```


### 5.6 Medición con timeit y cProfile

```bash
python profiling_demo.py
```
- **timeit**: compara microscópicamente dos formas de sumar los primeros
  1,000,000 de números (bucle `for` vs `sum(range(n))` nativo).
- **cProfile**: perfila una función completa y muestra qué sub-función
  consume más tiempo (`ncalls`, `tottime`, `cumtime`), útil para
  encontrar cuellos de botella reales antes de optimizar.

**Salida**

```bash
=== timeit: comparar dos formas de sumar 0..999999 ===
Bucle for manual (5 ejecuciones): 0.0902 s totales (0.0180 s por ejecución)
sum(range(n)) built-in (5 ejec.): 0.0298 s totales (0.0060 s por ejecución)
La versión built-in es ~3.0x más rápida.

=== cProfile: perfilando funcion_lenta() ===
         200004 function calls in 0.021 seconds

   Ordered by: cumulative time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.012    0.012    0.021    0.021 ./A12_Capacitacion_Python/2_Intermediate/lab11/src/profiling_demo.py:53(funcion_lenta)
   200000    0.008    0.000    0.008    0.000 {method 'append' of 'list' objects}
        1    0.000    0.000    0.001    0.001 ./A12_Capacitacion_Python/2_Intermediate/lab11/src/profiling_demo.py:62(operacion_costosa)
        1    0.001    0.001    0.001    0.001 {built-in method builtins.sorted}
        1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}



Lectura rápida de las columnas:
  ncalls   -> número de veces que se llamó a la función
  tottime  -> tiempo propio de la función (sin contar subllamadas)
  cumtime  -> tiempo acumulado incluyendo subllamadas
```


### 5.7 Ejecutar todo de una vez

```bash
python main.py            # ejecuta las 6 secciones en orden
python main.py gil        # ejecuta solo una sección: gil | threading | asyncio | fetch | cpu | profiling
```

## 6. Guía rápida para elegir el modelo de concurrencia (Objetivo 1)

| Situación                                            | Modelo recomendado                        |
|-------------------------------------------------------|--------------------------------------------|
| Muchas esperas de E/S (HTTP, DB, archivos), pocas conexiones | `threading` / `concurrent.futures.ThreadPoolExecutor` |
| Muchas esperas de E/S, miles de conexiones concurrentes | `asyncio` (más eficiente en memoria que miles de hilos) |
| Cómputo puro en Python que satura la CPU               | `multiprocessing` / `ProcessPoolExecutor`  |
| Cómputo puro pero con librerías en C que liberan el GIL (NumPy, pandas) | A veces `threading` basta, porque la parte pesada corre fuera del GIL |
| No sé dónde está el cuello de botella                   | Medir primero con `cProfile` / `timeit`, luego decidir |

## 7. Resultados de ejemplo obtenidos al validar esta solución

*(Medidos en el entorno de desarrollo de esta solución; tus tiempos
variarán según CPU, red y carga de la máquina.)*

```
GIL demo:            1 hilo 0.66s   vs  4 hilos 0.65s   (sin mejora, como se espera)
threading demo:      secuencial 4.0s  vs  ThreadPoolExecutor 0.50s
asyncio demo:        secuencial 4.0s  vs  gather concurrente 0.50s
fetchers (8 URLs):   síncrono 0.28s   vs  asíncrono 0.22s (~1.25x, limitado por pocas URLs/latencia baja)
cProfile:             identifica que 'funcion_lenta' concentra el tiempo, con 200,000 llamadas a list.append
```

## 8. Notas finales

- Todos los scripts son independientes y se pueden ejecutar por separado.
- El código está comentado en español explicando el "por qué", no solo
  el "qué", conforme a los objetivos pedagógicos del módulo.
- No se requieren credenciales ni API keys para ningún script.
