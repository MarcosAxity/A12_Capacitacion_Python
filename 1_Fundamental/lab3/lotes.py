import time
from contextlib import contextmanager
from typing import Iterable, Generator, Any, Optional
from datetime import datetime

# PARTE A: Generador por lotes
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


# PARTE B: Context Manager de temporización
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


# Context manager alternativo como clase (más completo)
class Timer:
    """
    Context manager de temporización con características avanzadas.
    """
    def __init__(
        self,
        nombre: str = "Operación",
        verbose: bool = True,
        acumular: bool = False
    ):
        self.nombre = nombre
        self.verbose = verbose
        self.acumular = acumular

        self.inicio = None
        self.fin = None
        self.segundos = 0
        self.ejecuciones = []
        self.total_acumulado = 0

    def __enter__(self):
        self.inicio = time.perf_counter()
        if self.verbose:
            print(f"⏱ [{datetime.now().strftime('%H:%M:%S')}] Iniciando: {self.nombre}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fin = time.perf_counter()
        self.segundos = self.fin - self.inicio

        if self.acumular:
            self.ejecuciones.append(self.segundos)
            self.total_acumulado = sum(self.ejecuciones)

        if self.verbose:
            mensaje = f"✓ [{datetime.now().strftime('%H:%M:%S')}] {self.nombre}: {self.segundos:.3f}s"
            if self.acumular:
                mensaje += f" (total acumulado: {self.total_acumulado:.3f}s)"
            print(mensaje)

        return False  # No suprimir excepciones

    def promedio(self) -> float:
        """Retorna el tiempo promedio de ejecución"""
        if not self.ejecuciones:
            return 0
        return self.total_acumulado / len(self.ejecuciones)


# EJEMPLO INTEGRADO: Procesamiento por lotes con temporización
def procesar_datos_ejemplo():
    """
    Ejemplo que combina el generador por lotes con el timer.
    """
    # Simulamos datos grandes
    datos = range(1000)

    print("\n" + "=" * 60)
    print("PROCESAMIENTO POR LOTES CON TEMPORIZACIÓN")
    print("=" * 60 + "\n")

    with timer("Procesamiento completo", umbral_warning=2.0) as tiempo_total:
        lotes_procesados = 0

        for lote in batch_generator(datos, batch_size=100):
            with timer(f"Lote {lotes_procesados + 1}", verbose=False) as tiempo_lote:
                # Simulamos procesamiento
                resultado = sum(lote)
                time.sleep(0.1)  # Simular trabajo

            lotes_procesados += 1

            # Logging cada cierto número de lotes
            if lotes_procesados % 3 == 0:
                print(f"  → Procesados {lotes_procesados} lotes "
                      f"({len(lote)} elementos en último lote)")

    print(f"\nResumen: {lotes_procesados} lotes en {tiempo_total['segundos']:.2f}s")


# Ejemplo con Timer como clase (acumulación)
def ejemplo_timer_acumulativo():
    """
    Demuestra el uso del Timer con acumulación.
    """
    print("\n" + "=" * 60)
    print("TIMER ACUMULATIVO")
    print("=" * 60 + "\n")

    timer_acumulativo = Timer("Operación repetida", acumular=True)

    for i in range(5):
        with timer_acumulativo:
            time.sleep(0.1 + i * 0.05)  # Tiempo variable

    print(f"\nPromedio de ejecución: {timer_acumulativo.promedio():.3f}s")
    print(f"Total de ejecuciones: {len(timer_acumulativo.ejecuciones)}")


# Ejemplo: Pipeline de procesamiento
def pipeline_completo():
    """
    Ejemplo real: procesamiento de datos en pipeline.
    """
    print("\n" + "=" * 60)
    print("PIPELINE DE PROCESAMIENTO COMPLETO")
    print("=" * 60 + "\n")

    # Generador de datos simulado
    def generar_registros(n):
        for i in range(n):
            yield {
                'id': i,
                'valor': i * 2,
                'categoria': 'A' if i % 2 == 0 else 'B'
            }

    with timer("Pipeline completo") as tiempo_total:
        # Fase 1: Carga
        with timer("Carga de datos"):
            datos = list(generar_registros(500))

        # Fase 2: Procesamiento por lotes
        resultados = []
        with timer("Procesamiento por lotes"):
            for lote in batch_generator(datos, batch_size=50):
                with timer(f"Procesando lote de {len(lote)} registros", verbose=False):
                    # Procesar lote
                    suma_lote = sum(r['valor'] for r in lote)
                    resultados.append(suma_lote)
                    time.sleep(0.05)  # Simular procesamiento

        # Fase 3: Agregación
        with timer("Agregación final"):
            total = sum(resultados)
            print(f"  Total calculado: {total}")


# Ejecutar todos los ejemplos
if __name__ == "__main__":
    procesar_datos_ejemplo()
    ejemplo_timer_acumulativo()
    pipeline_completo()