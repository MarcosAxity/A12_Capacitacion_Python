import time
import functools
from typing import Callable, Type, Tuple

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


# Ejemplos de uso
import random

# Ejemplo 1: Simulación de API inestable
@retry_with_backoff(max_intentos=4, backoff_base=1, backoff_factor=2)
def llamar_api_inestable():
    """Simula una API que falla aleatoriamente"""
    if random.random() < 0.7:  # 70% de probabilidad de fallar
        raise ConnectionError("Error de conexión con la API")
    return {"status": "success", "data": [1, 2, 3]}


# Ejemplo 2: Específico para errores de red
@retry_with_backoff(
    max_intentos=3,
    backoff_base=0.5,
    excepciones=(ConnectionError, TimeoutError)
)
def descargar_archivo(url: str):
    """Simula descarga de archivo con posibles errores de red"""
    if random.random() < 0.5:
        raise ConnectionError(f"No se pudo conectar a {url}")
    return f"Contenido descargado de {url}"


# Ejemplo 3: Sin reintentos (para comparación)
@retry_with_backoff(max_intentos=5, backoff_base=0.5, backoff_factor=1.5)
def operacion_base_datos():
    """Simula operación en base de datos"""
    if random.random() < 0.6:
        raise TimeoutError("Timeout en la base de datos")
    return "Datos guardados exitosamente"


# Pruebas
if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBA 1: API inestable")
    print("=" * 60)
    try:
        resultado = llamar_api_inestable()
        print(f"Resultado: {resultado}\n")
    except Exception as e:
        print(f"Error final: {e}\n")

    print("=" * 60)
    print("PRUEBA 2: Descarga de archivo")
    print("=" * 60)
    try:
        contenido = descargar_archivo("https://example.com/archivo.zip")
        print(f"Resultado: {contenido}\n")
    except Exception as e:
        print(f"Error final: {e}\n")

    print("=" * 60)
    print("PRUEBA 3: Operación de base de datos")
    print("=" * 60)
    try:
        resultado = operacion_base_datos()
        print(f"Resultado: {resultado}\n")
    except Exception as e:
        print(f"Error final: {e}\n")