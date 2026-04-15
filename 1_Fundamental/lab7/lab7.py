import httpx
import asyncio
from pathlib import Path
from typing import Optional

class HTTPClientRobusto:
    """Cliente HTTP con reintentos, timeouts y streaming"""

    def __init__(self, timeout: float = 30.0, max_retries: int = 3):
        """
        Inicializa el cliente HTTP

        Args:
            timeout: Tiempo máximo de espera en segundos
            max_retries: Número máximo de reintentos
        """
        self.max_retries = max_retries
        self.client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            http2=True,
            follow_redirects=True
        )

    def get_con_reintentos(self, url: str) -> Optional[httpx.Response]:
        """
        Realiza GET con reintentos automáticos

        Args:
            url: URL a consultar

        Returns:
            Response si tiene éxito, None si falla
        """
        for intento in range(self.max_retries):
            try:
                print(f"🔄 Intento {intento + 1}/{self.max_retries}: {url}")

                response = self.client.get(url)
                response.raise_for_status()

                print(f"✅ Éxito: {response.status_code}")
                return response

            except httpx.TimeoutException:
                print(f"⏱️  Timeout en intento {intento + 1}")
                if intento == self.max_retries - 1:
                    print("❌ Timeout final, no hay más reintentos")
                    return None

            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                print(f"⚠️  Error HTTP {status}")

                # No reintentar errores del cliente (4xx)
                if 400 <= status < 500:
                    print("❌ Error del cliente, no se reintenta")
                    return None

                # Reintentar errores del servidor (5xx)
                if intento == self.max_retries - 1:
                    print("❌ Error del servidor, no hay más reintentos")
                    return None

            except httpx.RequestError as e:
                print(f"🌐 Error de red: {e}")
                if intento == self.max_retries - 1:
                    return None

            # Espera antes del siguiente intento (backoff exponencial)
            if intento < self.max_retries - 1:
                espera = 2 ** intento
                print(f"⏳ Esperando {espera} segundos antes de reintentar...")
                import time
                time.sleep(espera)

        return None

    def descargar_streaming(self, url: str, ruta_destino: str) -> bool:
        """
        Descarga un archivo usando streaming (eficiente en memoria)

        Args:
            url: URL del archivo a descargar
            ruta_destino: Ruta donde guardar el archivo

        Returns:
            True si la descarga fue exitosa, False en caso contrario
        """
        print(f"\n📥 Iniciando descarga: {url}")
        print(f"💾 Destino: {ruta_destino}")

        try:
            # Crear directorio si no existe
            Path(ruta_destino).parent.mkdir(parents=True, exist_ok=True)

            # Streaming: no carga todo en memoria
            with self.client.stream('GET', url) as response:
                response.raise_for_status()

                # Obtener tamaño total si está disponible
                total_size = int(response.headers.get('content-length', 0))
                descargado = 0

                # Guardar en disco por chunks
                with open(ruta_destino, 'wb') as archivo:
                    for chunk in response.iter_bytes(chunk_size=8192):  # 8KB por chunk
                        archivo.write(chunk)
                        descargado += len(chunk)

                        # Mostrar progreso
                        if total_size > 0:
                            porcentaje = (descargado / total_size) * 100
                            print(f"\r📊 Progreso: {porcentaje:.1f}% ({descargado}/{total_size} bytes)", end='')

                print(f"\n✅ Descarga completada: {descargado} bytes guardados")
                return True

        except httpx.HTTPStatusError as e:
            print(f"\n❌ Error HTTP {e.response.status_code}: {e}")
            return False

        except httpx.RequestError as e:
            print(f"\n❌ Error de red: {e}")
            return False

        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            return False

    def close(self):
        """Cierra el cliente y libera recursos"""
        self.client.close()
        print("🔒 Cliente cerrado")


# ============================================
# EJEMPLOS DE USO
# ============================================

def ejemplo_get_simple():
    """Ejemplo 1: GET simple con reintentos"""
    print("=" * 60)
    print("EJEMPLO 1: GET con reintentos")
    print("=" * 60)

    cliente = HTTPClientRobusto(timeout=10.0, max_retries=3)

    # Probar con una API pública
    response = cliente.get_con_reintentos('https://httpbin.org/json')

    if response:
        print(f"\n📄 Contenido recibido:")
        print(response.json())
    else:
        print("\n❌ No se pudo obtener respuesta")

    cliente.close()


def ejemplo_timeout():
    """Ejemplo 2: Probar timeout"""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Timeout (espera 10 segundos)")
    print("=" * 60)

    cliente = HTTPClientRobusto(timeout=5.0, max_retries=2)

    # Esta URL tarda 10 segundos en responder, causará timeout
    response = cliente.get_con_reintentos('https://httpbin.org/delay/10')

    if not response:
        print("\n✅ Timeout manejado correctamente")

    cliente.close()


def ejemplo_descarga_streaming():
    """Ejemplo 3: Descarga de archivo con streaming"""
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Descarga por streaming")
    print("=" * 60)

    cliente = HTTPClientRobusto(timeout=60.0)

    # Descargar una imagen de ejemplo
    url = 'https://httpbin.org/image/png'
    ruta = './descargas/imagen_ejemplo.png'

    exito = cliente.descargar_streaming(url, ruta)

    if exito:
        print(f"\n✅ Archivo disponible en: {ruta}")

    cliente.close()


def ejemplo_manejo_errores():
    """Ejemplo 4: Manejo de diferentes errores HTTP"""
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Manejo de errores HTTP")
    print("=" * 60)

    cliente = HTTPClientRobusto(timeout=10.0, max_retries=2)

    # Error 404 (no se reintenta)
    print("\n🧪 Probando error 404...")
    cliente.get_con_reintentos('https://httpbin.org/status/404')

    # Error 500 (se reintenta)
    print("\n🧪 Probando error 500...")
    cliente.get_con_reintentos('https://httpbin.org/status/500')

    cliente.close()


# ============================================
# PROGRAMA PRINCIPAL
# ============================================

if __name__ == '__main__':
    print("🚀 Laboratorio: Cliente HTTP Robusto con httpx\n")

    # Ejecutar ejemplos
    ejemplo_get_simple()
    ejemplo_timeout()
    ejemplo_descarga_streaming()
    ejemplo_manejo_errores()

    print("\n" + "=" * 60)
    print("✅ Laboratorio completado")
    print("=" * 60)