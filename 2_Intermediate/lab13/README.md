# Módulo 13 — Patrones de Diseño en Python

Proyecto didáctico que implementa y prueba (con `pytest`) los principales
patrones de diseño de la Banda de los Cuatro (GoF), organizados por
categoría, más el laboratorio práctico solicitado.

## 1. Objetivos del módulo

- **Implementar patrones relevantes con ejemplos reales**: cada patrón está
  resuelto sobre un caso de uso de negocio concreto (facturación, pagos,
  notificaciones, pedidos, UI, etc.), no sobre ejemplos abstractos tipo
  `Animal`/`Perro`/`Gato`.
- **Identificar antipatrones y señales de refactor**: ver la sección
  [Antipatrones y señales de refactor](#5-antipatrones-y-señales-de-refactor).

## 2. Estructura del proyecto

```
modulo13_patrones/
├── README.md                 <- este archivo
├── requirements.txt          <- dependencias (pytest, pytest-cov)
├── pytest.ini                <- configuración de pytest
├── src/
│   ├── creational/
│   │   └── patterns.py       <- Factory, Abstract Factory, Builder, Singleton
│   ├── structural/
│   │   └── patterns.py       <- Adapter, Facade, Composite, Decorator, Proxy
│   ├── behavioral/
│   │   └── patterns.py       <- Strategy, Observer, Command, Mediator,
│   │                             Template Method, State
│   ├── idiomatic/
│   │   └── patterns.py       <- decoradores, context managers, dataclasses
│   └── lab/                  <- LABORATORIO (los 3 entregables pedidos)
│       ├── pricing_strategy.py            <- Strategy para precios
│       ├── cache_decorator.py             <- Decorator de caché (TTL)
│       └── external_provider_adapter.py   <- Adapter para proveedor externo
└── tests/                    <- pruebas con pytest (1 archivo por módulo)
    ├── test_pricing_strategy.py
    ├── test_cache_decorator.py
    ├── test_external_provider_adapter.py
    ├── test_creational.py
    ├── test_structural.py
    ├── test_behavioral.py
    └── test_idiomatic.py
```

Cada archivo de `src/` está ampliamente comentado: explica **qué problema
resuelve el patrón**, **por qué se eligió** y, en el caso del Singleton,
**cuándo conviene evitarlo**.

## 3. Cómo ejecutar el proyecto

### 3.1. Requisitos previos

- Python 3.10 o superior (se usan `from __future__ import annotations`,
  `list[str]`, `dict[str, str]`, etc.)
- `pip`

### 3.2. Instalación

1. Entra a la carpeta del proyecto:

   ```bash
   cd lab13
   ```

2. (Recomendado) Crea y activa un entorno virtual:

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Linux / macOS
   .venv\Scripts\activate           # Windows
   ```

3. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

### 3.3. Ejecutar las pruebas (pytest)

Desde la raíz del proyecto (`modulo13_patrones/`):

```bash
python -m pytest
```

Salida esperada (resumen):

```
tests/test_behavioral.py ........                    [ 15%]
tests/test_cache_decorator.py .......                [ 28%]
tests/test_creational.py .....                       [ 37%]
tests/test_external_provider_adapter.py ........      [ 52%]
tests/test_idiomatic.py .........                    [ 69%]
tests/test_pricing_strategy.py ..........             [ 88%]
tests/test_structural.py ......                       [100%]

53 passed
```

Para ver el detalle de cada caso (verbose, ya activado por defecto vía
`pytest.ini`) o filtrar solo el laboratorio:

```bash
# Solo los 3 módulos del laboratorio
python -m pytest tests/test_pricing_strategy.py tests/test_cache_decorator.py tests/test_external_provider_adapter.py

# Un solo archivo
python -m pytest tests/test_pricing_strategy.py -v

# Un solo test puntual
python -m pytest tests/test_cache_decorator.py::test_expira_despues_del_ttl -v
```

### 3.4. Ver cobertura de pruebas (opcional)

```bash
python -m pytest --cov=src --cov-report=term-missing
```

### 3.5. Usar los módulos desde un script propio / REPL

Todo el código vive bajo el paquete `src`, así que se importa como
cualquier paquete de Python. Ejemplo rápido desde la raíz del proyecto:

```bash
python
```

```python
from src.lab.pricing_strategy import Carrito, ItemPrecio, PrecioClienteVIP

carrito = Carrito()
carrito.agregar_item(ItemPrecio("Camiseta", 200.0, 2))
carrito.establecer_estrategia(PrecioClienteVIP(0.10))
print(carrito.total())  # 360.0
```

## 4. Contenido clave y dónde se implementa cada patrón

| Categoría        | Patrón            | Archivo                                             |
|-------------------|--------------------|-----------------------------------------------------|
| Creacional        | Factory Method     | `src/creational/patterns.py` (`FabricaNotificaciones`) |
| Creacional        | Abstract Factory   | `src/creational/patterns.py` (`FabricaUI*`)          |
| Creacional        | Builder            | `src/creational/patterns.py` (`ConstructorConsultaSQL`) |
| Creacional        | Singleton          | `src/creational/patterns.py` (`ConfiguracionApp`)    |
| Estructural       | Adapter            | `src/structural/patterns.py` y **`src/lab/external_provider_adapter.py`** |
| Estructural       | Facade             | `src/structural/patterns.py` (`FachadaPedidos`)      |
| Estructural       | Composite          | `src/structural/patterns.py` (`Carpeta`/`Archivo`)   |
| Estructural       | Decorator          | `src/structural/patterns.py` y **`src/lab/cache_decorator.py`** |
| Estructural       | Proxy              | `src/structural/patterns.py` (`ProxyControlAcceso`)  |
| Comportamiento    | Strategy           | `src/behavioral/patterns.py` y **`src/lab/pricing_strategy.py`** |
| Comportamiento    | Observer           | `src/behavioral/patterns.py` (`Pedido`/`ObservadorPedido`) |
| Comportamiento    | Command            | `src/behavioral/patterns.py` (`HistorialComandos`)   |
| Comportamiento    | Mediator           | `src/behavioral/patterns.py` (`SalaChat`)            |
| Comportamiento    | Template Method    | `src/behavioral/patterns.py` (`ProcesadorArchivo`)   |
| Comportamiento    | State              | `src/behavioral/patterns.py` (`PedidoConEstado`)     |
| Idiomático        | Decoradores        | `src/idiomatic/patterns.py` (`medir_tiempo`, `reintentar`) |
| Idiomático        | Context managers   | `src/idiomatic/patterns.py` (`ConexionBD`, `temporizador`) |
| Idiomático        | Dataclasses        | `src/idiomatic/patterns.py` (`Dinero`, `ItemCarrito`) |

## 5. El laboratorio en detalle

### 5.1. Strategy para precios (`src/lab/pricing_strategy.py`)

Resuelve el problema de calcular el total de un carrito de compra bajo
distintas políticas comerciales (precio regular, cliente VIP, cupón de
descuento, oferta 3x2) **sin usar condicionales `if/elif` gigantes**.

- `EstrategiaPrecio`: interfaz común (clase abstracta).
- `PrecioRegular`, `PrecioClienteVIP`, `PrecioConCupon`, `PrecioOferta3x2`:
  estrategias concretas, cada una en su propia clase, testeable de forma
  aislada.
- `Carrito`: el *contexto* que delega el cálculo en la estrategia activa y
  permite cambiarla en caliente (`establecer_estrategia`).

### 5.2. Decorator de caché (`src/lab/cache_decorator.py`)

Un *decorator* de función (patrón Decorator en su forma idiomática de
Python) que:

- Cachea el resultado de una función según sus argumentos.
- Aplica un **TTL** (tiempo de vida) configurable, tras el cual el
  resultado se recalcula.
- Limita el tamaño máximo del caché con una política FIFO simple (evita el
  antipatrón de "caché sin límite").
- Expone métricas (`cache_info()` con `hits`/`misses`/`tasa_aciertos`) y
  utilidades (`invalidar(...)`, `limpiar_cache()`), replicando lo que
  ofrecería una librería real como `functools.lru_cache`, pero con soporte
  de expiración por tiempo.
- Acepta un `reloj` inyectable, lo que permite probar el TTL en los tests
  sin depender de `time.sleep` real (pruebas rápidas y deterministas).

### 5.3. Adapter para proveedor externo (`src/lab/external_provider_adapter.py`)

Modela un caso muy común en la industria: integrar un **proveedor de pagos
externo** cuyo SDK tiene una interfaz incompatible con la que usa nuestra
aplicación (nombres de métodos distintos, montos en formato *string* en
vez de centavos, errores como diccionarios en vez de excepciones).

- `PasarelaPago`: interfaz propia (la que consume el resto de la app).
- `ProveedorPagoExternoSDK`: simula el SDK de terceros (el *Adaptee*), con
  su propia forma de trabajar que **no controlamos ni modificamos**.
- `AdaptadorProveedorExterno`: traduce entre ambas interfaces (el
  *Adapter*), incluyendo la conversión de formatos (centavos ↔ decimal) y
  el mapeo de errores propios del proveedor a nuestro `ResultadoPago`.

### 5.4. Pruebas con pytest

Cada uno de los tres módulos del laboratorio tiene su archivo de pruebas
correspondiente en `tests/`, con casos que cubren tanto el camino feliz
como casos límite (montos inválidos, TTL vencido, reembolsos duplicados,
descuentos que llevarían el total a negativo, etc.). Además, se agregaron
pruebas para el resto de los patrones (`test_creational.py`,
`test_structural.py`, `test_behavioral.py`, `test_idiomatic.py`) para dar
cobertura completa a todo el contenido del módulo.

## 6. Antipatrones y señales de refactor

Identificados explícitamente a lo largo del código (ver comentarios
inline) y resumidos aquí:

1. **Singleton como "variable global disfrazada"** (`src/creational/patterns.py`)
   - *Antipatrón*: usar un Singleton para compartir estado mutable entre
     módulos.
   - *Por qué es un problema*: dificulta las pruebas (el estado persiste
     entre tests, como se ve en `ConfiguracionApp.reset_para_pruebas`),
     esconde dependencias (acoplamiento implícito) y falla en entornos
     con múltiples procesos/workers, donde cada proceso tiene su propia
     instancia.
   - *Señal de refactor*: si necesitas mockear el Singleton en tests o si
     el "singleton" empieza a tener múltiples responsabilidades → cámbialo
     por inyección de dependencias explícita, o usa directamente un módulo
     de Python (que ya es un singleton por diseño del intérprete).

2. **Cadena de `if/elif` para reglas de negocio que cambian seguido**
   - *Antipatrón*: un método `calcular_precio(tipo_cliente, ...)` con 10
     ramas `if`.
   - *Señal de refactor*: cada vez que agregas una promoción nueva tienes
     que tocar el mismo método gigante (viola Open/Closed) → extraer a
     **Strategy**, como se hizo en `src/lab/pricing_strategy.py`.

3. **Caché sin límite de tamaño ni expiración**
   - *Antipatrón*: un `dict` global que va creciendo indefinidamente y
     nunca invalida entradas viejas.
   - *Por qué es un problema*: fuga de memoria y datos obsoletos servidos
     indefinidamente.
   - *Señal de refactor*: si ves un caché "manual" con un `dict` sin TTL
     ni tope, migrar a un decorator como `cache_con_ttl` (o `lru_cache`)
     con política de expiración y desalojo explícitas.

4. **Adaptar un SDK externo "a mano" en cada punto de uso**
   - *Antipatrón*: llamar a `sdk.create_charge(...)` directamente desde
     distintos lugares del código de negocio, repitiendo la traducción de
     formatos (centavos → string, mapeo de errores) en cada sitio.
   - *Señal de refactor*: si el mismo bloque de "traducción" aparece en
     más de un lugar, o si cambiar de proveedor de pagos implicaría tocar
     múltiples archivos → centralizar en un **Adapter** único, como
     `AdaptadorProveedorExterno`.

5. **God Object / Facade mal usada como "cajón de sastre"**
   - *Antipatrón*: una clase `FachadaPedidos` que, en vez de *delegar* en
     subsistemas especializados, termina absorbiendo ella misma toda la
     lógica de inventario, pagos y envíos.
   - *Señal de refactor*: si una Facade empieza a tener lógica de negocio
     propia (no solo orquestación), es momento de mover esa lógica de
     vuelta a servicios especializados y dejar la Facade como una capa
     delgada de coordinación.

6. **Decorator/Proxy que rompe el contrato de la interfaz original**
   - *Antipatrón*: un Decorator o Proxy que cambia la forma de los datos
     de entrada/salida respecto al objeto que envuelve.
   - *Señal de refactor*: si el código cliente necesita saber si está
     hablando con el objeto real o con el decorador/proxy para funcionar
     correctamente, el patrón está mal implementado — el envoltorio debe
     ser transparente (ver `ProxyControlAcceso` y `ConDecoradorBebida`,
     que respetan exactamente la interfaz `Bebida`/`ServicioDatosSensibles`).

## 7. Notas de diseño adicionales

- Se usó **type hints** (`from __future__ import annotations`) en todo el
  proyecto para facilitar el mantenimiento y el uso de herramientas como
  `mypy` (no incluido en este entregable, pero el código es compatible).
- Los nombres de clases, variables y comentarios están en español para
  alinearse con el contexto del curso; los nombres de módulos y patrones
  técnicos se mantienen en su forma estándar en inglés (Factory, Builder,
  Strategy, etc.) por ser la nomenclatura universalmente reconocida.
- Cada módulo de `src/` puede leerse de forma independiente: no hay
  dependencias cruzadas entre `creational`, `structural`, `behavioral`,
  `idiomatic` y `lab`.
