import time
import functools
from contextlib import contextmanager
from typing import Callable, Type, Tuple, Optional, Generator, Iterable
from datetime import datetime


def retry_with_backoff(
    max_intentos: int = 3,
    backoff_base: float = 1.0,
    backoff_factor: float = 2.0,
    excepciones: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorador que reintenta una función con backoff exponencial.

    Args:
        max_intentos: Número máximo de intentos
        backoff_base: Tiempo de espera inicial en segundos
        backoff_factor: Factor multiplicador para cada reintento
        excepciones: Tupla de excepciones a capturar

    Example:
        @retry_with_backoff(max_intentos=3, backoff_base=2)
        def llamada_api():
            return requests.get('https://api.example.com')
    """
    def decorador(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ultima_excepcion = None

            for intento in range(max_intentos):
                try:
                    resultado = func(*args, **kwargs)
                    if intento > 0:
                        print(f"✓ {func.__name__} exitoso en intento {intento + 1}")
                    return resultado

                except excepciones as e:
                    ultima_excepcion = e

                    if intento < max_intentos - 1:
                        # Calcular tiempo de espera con backoff exponencial
                        espera = backoff_base * (backoff_factor ** intento)
                        print(f"⚠ {func.__name__} falló (intento {intento + 1}/{max_intentos}): {e}")
                        print(f"  Reintentando en {espera:.1f}s...")
                        time.sleep(espera)
                    else:
                        print(f"✗ {func.__name__} falló después de {max_intentos} intentos")

            # Si llegamos aquí, todos los intentos fallaron
            raise ultima_excepcion

        return wrapper
    return decorador


@contextmanager
def timer(
    nombre_operacion: str = "Operación",
    verbose: bool = True,
    umbral_warning: Optional[float] = None
):
    """
    Context manager para medir tiempo de ejecución.

    Args:
        nombre_operacion: Nombre descriptivo de la operación
        verbose: Si imprimir el resultado automáticamente
        umbral_warning: Tiempo en segundos para mostrar advertencia

    Yields:
        Diccionario con estadísticas de tiempo (se actualiza al salir)

    Example:
        with timer("Procesamiento de datos") as t:
            procesar_datos()
        print(f"Duró {t['segundos']:.2f}s")
    """
    stats = {
        'nombre': nombre_operacion,
        'inicio': None,
        'fin': None,
        'segundos': 0,
        'timestamp_inicio': None,
        'timestamp_fin': None
    }

    stats['inicio'] = time.perf_counter()
    stats['timestamp_inicio'] = datetime.now()

    if verbose:
        print(f"⏱ Iniciando: {nombre_operacion}")

    try:
        yield stats
    finally:
        stats['fin'] = time.perf_counter()
        stats['timestamp_fin'] = datetime.now()
        stats['segundos'] = stats['fin'] - stats['inicio']

        if verbose:
            emoji = "✓"
            mensaje = f"{emoji} {nombre_operacion}: {stats['segundos']:.3f}s"

            # Advertencia si supera el umbral
            if umbral_warning and stats['segundos'] > umbral_warning:
                mensaje += f" ⚠ (superó umbral de {umbral_warning}s)"

            print(mensaje)


# Caso real: Procesamiento de archivo grande con reintentos
@retry_with_backoff(max_intentos=3, backoff_base=1)
def procesar_archivo_grande(ruta_archivo: str):
    """
    Procesa un archivo grande por lotes con manejo de errores.
    """
    with timer(f"Procesamiento de {ruta_archivo}"):
        with open(ruta_archivo, 'r') as f:
            for lote_lineas in batch_generator(f, batch_size=1000):
                # Procesar cada lote
                for linea in lote_lineas:
                    # Tu lógica aquí
                    pass


# Caso real: ETL con reintentos y métricas
@retry_with_backoff(max_intentos=3, excepciones=(ConnectionError,))
def extraer_datos_api(endpoint: str, limite: int = 10000):
    """
    Extrae datos de una API en lotes con reintentos.
    """
    datos_extraidos = []

    with timer("Extracción completa de API") as t:
        for offset in range(0, limite, 100):
            with timer(f"Extrayendo offset {offset}", verbose=False):
                # Simular llamada API
                lote = list(range(offset, min(offset + 100, limite)))
                datos_extraidos.extend(lote)
                time.sleep(0.05)

    print(f"Extraídos {len(datos_extraidos)} registros")
    return datos_extraidos


def batch_generator(
    iterable: Iterable,
    batch_size: int
) -> Generator[list, None, None]:
    """
    Genera lotes de elementos de un iterable.

    Args:
        iterable: Cualquier iterable (lista, generador, etc.)
        batch_size: Tamaño de cada lote

    Yields:
        Listas con batch_size elementos (el último puede ser menor)

    Example:
        for lote in batch_generator(range(100), 10):
            procesar_lote(lote)
    """
    batch = []

    for item in iterable:
        batch.append(item)

        if len(batch) == batch_size:
            yield batch
            batch = []

    # Yield del último lote si tiene elementos
    if batch:
        yield batch


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CASO DE USO: ETL CON REINTENTOS")
    print("=" * 60 + "\n")

    try:
        datos = extraer_datos_api("https://api.example.com/datos")

        with timer("Transformación por lotes"):
            for lote in batch_generator(datos, batch_size=500):
                # Transformar cada lote
                transformados = [x * 2 for x in lote]
                time.sleep(0.1)

        print("\n✓ Pipeline ETL completado exitosamente")
    except Exception as e:
        print(f"\n✗ Pipeline falló: {e}")