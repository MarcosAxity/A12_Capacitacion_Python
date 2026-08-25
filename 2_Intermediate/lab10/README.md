# Módulo 10 · Pruebas y TDD

## Descripción del módulo

Este laboratorio aborda cuatro conceptos clave para construir software confiable en Python:

- **pytest (fixtures, parametrización, markers):** pytest es el framework estándar de pruebas en Python. Las **fixtures** permiten preparar y limpiar el estado necesario para un test (datos, conexiones, objetos) de forma reutilizable y desacoplada. La **parametrización** evita duplicar código al ejecutar el mismo test con múltiples combinaciones de entradas/salidas esperadas. Los **markers** permiten etiquetar pruebas (por ejemplo `slow`, `unit`, `integration`) para organizarlas y ejecutar solo el subconjunto relevante en cada contexto (desarrollo local vs. CI).

- **Mocking con `unittest.mock`:** permite aislar la unidad de código que se está probando de sus dependencias externas (APIs, bases de datos, servicios de terceros, reloj del sistema, etc.), sustituyéndolas por objetos simulados (`Mock`, `patch`). Esto hace que las pruebas sean rápidas, deterministas y no dependan de infraestructura externa.

- **Property-based testing con Hypothesis:** en lugar de escribir casos de prueba fijos, se definen **propiedades** que el código debe cumplir siempre (invariantes), y la librería genera automáticamente cientos de entradas —incluyendo casos límite que un humano difícilmente pensaría— para intentar romper esa propiedad. Esto complementa a las pruebas tradicionales encontrando errores de diseño no anticipados.

- **Cobertura e integración en CI:** la cobertura (`pytest-cov`) mide qué porcentaje del código está siendo ejercitado por las pruebas, ayudando a identificar rutas sin probar. Integrar las pruebas y el umbral de cobertura en un pipeline de CI (GitHub Actions) garantiza que ningún cambio rompa la suite ni degrade la calidad antes de llegar a producción.

## Importancia de los objetivos del laboratorio

El laboratorio tiene dos objetivos centrales:

1. **Practicar TDD y diseñar pruebas confiables:** desarrollar siguiendo el ciclo *Red → Green → Refactor* obliga a pensar primero en el comportamiento esperado (el "contrato") antes que en la implementación. Esto reduce errores de diseño, documenta el comportamiento del sistema mediante los propios tests, y da la confianza necesaria para refactorizar sin miedo a romper funcionalidad existente.

2. **Asegurar cobertura suficiente y una suite estable:** una suite con buena cobertura y sin pruebas "frágiles" (flaky) es lo que permite integrar cambios con frecuencia (integración continua) sin introducir regresiones. La cobertura por sí sola no garantiza calidad, pero combinada con property-based testing y mocking bien aplicado, da una red de seguridad mucho más sólida para el crecimiento del proyecto a largo plazo.

Historia de usuario implementada con TDD:

> Como cliente, quiero aplicar un cupón de descuento a mi carrito, para
> pagar menos, sin que el total sea nunca negativo ni el descuento supere
> el 100%.

## Contenido

- `carrito.py` — implementación (`Carrito`, `CuponInvalido`)
- `test_carrito.py` — suite de pruebas:
  - fixtures (`carrito`)
  - parametrización (`@pytest.mark.parametrize`)
  - markers (`unit`, `slow`)
  - mocking (`unittest.mock.Mock` para un validador externo de cupones)
  - property-based testing con **Hypothesis**
- `pytest.ini` — configuración de markers
- `requirements.txt` — dependencias
- `.github/workflows/tests.yml` — CI con reporte y umbral de cobertura

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecutar pruebas

```bash
# todas las pruebas
pytest

# excluyendo las lentas
pytest -m "not slow"

# solo un tipo de marker
pytest -m unit
```

## Reporte de cobertura

```bash
pytest --cov=carrito --cov-report=term-missing --cov-report=html
```

Esto genera un reporte en terminal (líneas no cubiertas) y una carpeta
`htmlcov/` navegable en el navegador. En CI se usa `--cov-fail-under=85`
para romper el pipeline si la cobertura baja del umbral.
