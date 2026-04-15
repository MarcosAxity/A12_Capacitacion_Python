# laboratorio_csv_metricas.py
import csv
import json
import logging
from pathlib import Path
from datetime import datetime

# ============================================
# 1. CONFIGURAR LOGGING CON DISTINTOS NIVELES
# ============================================

# Crear carpeta de logs
Path("logs").mkdir(exist_ok=True)

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG,  # Captura todos los niveles
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        # Handler para archivo (todos los logs)
        logging.FileHandler("logs/metricas.log", encoding="utf-8"),
        # Handler para consola (solo INFO y superiores)
        logging.StreamHandler()
    ]
)

# Configurar nivel de consola aparte
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
        handler.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


# ============================================
# 2. FUNCIÓN PARA INGESTAR CSV
# ============================================

def leer_csv(ruta_archivo):
    """Lee un archivo CSV y retorna los datos como lista de diccionarios"""
    ruta = Path(ruta_archivo)

    logger.info(f"Iniciando lectura de CSV: {ruta.name}")

    if not ruta.exists():
        logger.error(f"Archivo no encontrado: {ruta}")
        raise FileNotFoundError(f"No existe: {ruta}")

    logger.debug(f"Ruta absoluta: {ruta.resolve()}")

    try:
        with ruta.open("r", encoding="utf-8") as f:
            lector = csv.DictReader(f)
            datos = list(lector)

        logger.info(f"✓ CSV leído correctamente: {len(datos)} filas")
        logger.debug(f"Columnas encontradas: {list(datos[0].keys()) if datos else 'Sin datos'}")

        return datos

    except Exception as e:
        logger.error(f"Error al leer CSV: {e}", exc_info=True)
        raise


# ============================================
# 3. FUNCIÓN PARA CALCULAR MÉTRICAS
# ============================================

def calcular_metricas(datos, columna_numerica="edad"):
    """Calcula métricas estadísticas básicas de una columna numérica"""
    logger.info(f"Calculando métricas para columna: {columna_numerica}")

    if not datos:
        logger.warning("No hay datos para calcular métricas")
        return {}

    try:
        # Extraer valores numéricos y filtrar vacíos
        valores = []
        for fila in datos:
            try:
                valor = float(fila.get(columna_numerica, 0))
                valores.append(valor)
            except (ValueError, TypeError):
                logger.debug(f"Valor no numérico ignorado: {fila.get(columna_numerica)}")

        if not valores:
            logger.warning(f"No hay valores numéricos válidos en columna '{columna_numerica}'")
            return {}

        # Calcular métricas
        metricas = {
            "total_registros": len(datos),
            "valores_validos": len(valores),
            "suma": sum(valores),
            "promedio": sum(valores) / len(valores),
            "minimo": min(valores),
            "maximo": max(valores),
            "columna_analizada": columna_numerica
        }

        logger.info(f"✓ Métricas calculadas: promedio={metricas['promedio']:.2f}, min={metricas['minimo']}, max={metricas['maximo']}")
        logger.debug(f"Métricas completas: {metricas}")

        return metricas

    except Exception as e:
        logger.error(f"Error calculando métricas: {e}", exc_info=True)
        return {}


# ============================================
# 4. FUNCIÓN PARA EXPORTAR A JSON
# ============================================

def exportar_json(metricas, datos, ruta_salida="resultados.json"):
    """Exporta las métricas y datos a un archivo JSON"""
    ruta = Path(ruta_salida)

    logger.info(f"Exportando resultados a: {ruta.name}")

    # Crear directorio si no existe
    ruta.parent.mkdir(parents=True, exist_ok=True)

    # Preparar estructura de salida
    salida = {
        "timestamp": datetime.now().isoformat(),
        "metricas": metricas,
        "total_datos": len(datos),
        "muestra_datos": datos[:5] if len(datos) > 5 else datos  # Primeros 5 registros
    }

    try:
        with ruta.open("w", encoding="utf-8") as f:
            json.dump(salida, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ JSON exportado correctamente: {ruta.resolve()}")
        logger.debug(f"Tamaño del archivo: {ruta.stat().st_size} bytes")

        return ruta

    except Exception as e:
        logger.error(f"Error al exportar JSON: {e}", exc_info=True)
        raise


# ============================================
# 5. FUNCIÓN PRINCIPAL QUE INTEGRA TODO
# ============================================

def procesar_csv_completo(archivo_csv, columna_metrica="edad", archivo_salida="resultados.json"):
    """Pipeline completo: CSV → Métricas → JSON"""
    logger.info("=" * 50)
    logger.info("INICIO DEL PROCESAMIENTO")
    logger.info("=" * 50)

    try:
        # Paso 1: Ingestar CSV
        datos = leer_csv(archivo_csv)

        # Paso 2: Calcular métricas
        metricas = calcular_metricas(datos, columna_metrica)

        # Paso 3: Exportar a JSON
        ruta_json = exportar_json(metricas, datos, archivo_salida)

        logger.info("=" * 50)
        logger.info("PROCESAMIENTO COMPLETADO EXITOSAMENTE")
        logger.info("=" * 50)

        return ruta_json

    except Exception as e:
        logger.critical(f"FALLO CRÍTICO EN EL PROCESAMIENTO: {e}", exc_info=True)
        raise


# ============================================
# 6. CREAR CSV DE EJEMPLO Y EJECUTAR
# ============================================

def crear_csv_ejemplo():
    """Crea un CSV de ejemplo para probar"""
    datos_ejemplo = [
        {"nombre": "Ana", "edad": "28", "ciudad": "Madrid"},
        {"nombre": "Carlos", "edad": "35", "ciudad": "Barcelona"},
        {"nombre": "María", "edad": "22", "ciudad": "Valencia"},
        {"nombre": "Juan", "edad": "41", "ciudad": "Sevilla"},
        {"nombre": "Laura", "edad": "30", "ciudad": "Bilbao"},
    ]

    Path("datos").mkdir(exist_ok=True)
    archivo = Path("datos/personas.csv")

    with archivo.open("w", encoding="utf-8", newline="") as f:
        campos = ["nombre", "edad", "ciudad"]
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(datos_ejemplo)

    logger.info(f"CSV de ejemplo creado: {archivo}")
    return archivo


# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == "__main__":
    print("🚀 Iniciando laboratorio de CSV → Métricas → JSON\n")

    # Crear CSV de ejemplo
    archivo_csv = crear_csv_ejemplo()

    # Procesar
    try:
        resultado = procesar_csv_completo(
            archivo_csv="datos/personas.csv",
            columna_metrica="edad",
            archivo_salida="output/metricas_personas.json"
        )

        print(f"\n✅ Proceso completado")
        print(f"📊 Resultados en: {resultado}")
        print(f"📝 Logs en: logs/metricas.log")

    except Exception as e:
        print(f"\n❌ Error en el proceso: {e}")
        print("Revisa logs/metricas.log para más detalles")