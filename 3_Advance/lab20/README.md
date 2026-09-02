# Módulo 20 — Interoperabilidad y ecosistema mixto (opcional)

Solución completa, validada de punta a punta, para el módulo de
interoperabilidad: contratos neutrales (OpenAPI + Protobuf), un servicio
gRPC de Orders con su cliente, y publicación de eventos de dominio en un
bus de mensajería (RabbitMQ / Redis), incluyendo comparación de formatos
de serialización (JSON / Avro / Protobuf).

---

## 1. Contenidos clave — qué se está revisando y por qué

### 1.1 Contratos neutrales: OpenAPI y Protobuf

Un **contrato neutral** es una definición del "shape" de los datos y las
operaciones que **no depende de ningún lenguaje de programación**. Es lo
que permite que un servicio en Python, otro en Go y un frontend en
TypeScript se entiendan entre sí sin compartir código.

- **Protobuf** (`proto/orders.proto`): define los mensajes (`Order`,
  `OrderItem`, `OrderCreatedEvent`) y el servicio RPC (`OrdersService`)
  con tipado fuerte. A partir de este único archivo se **generan** los
  stubs de Python (clases, cliente y servidor) con `grpc_tools.protoc`.
  Si mañana se necesita un cliente en Java o Go, se genera desde el
  **mismo** `.proto`, garantizando que todos hablan el mismo idioma.
- **OpenAPI** (`contracts/openapi.yaml`): describe el **equivalente REST**
  del mismo dominio (`POST /orders`, `GET /orders/{id}`). Se incluye para
  cubrir el caso de clientes que no pueden hablar gRPC (por ejemplo, un
  frontend web simple o un partner externo que solo consume HTTP/JSON).

El punto pedagógico central es que **ambos contratos describen el mismo
dominio de negocio** (una orden con items, total y estado) pero con
formatos y protocolos de transporte distintos. El contrato no está
"amarrado" a una tecnología.

### 1.2 Servicios/clients gRPC en Python

**gRPC** es un framework RPC (Remote Procedure Call) sobre HTTP/2 que usa
Protobuf como formato de serialización binaria. En este módulo se
implementa:

- `server/orders_servicer.py`: la clase que implementa la lógica de
  negocio del servicio (`CreateOrder`, `GetOrder`, `ListOrders`).
- `server/grpc_server.py`: el *composition root* que levanta el servidor
  gRPC real en un puerto TCP.
- `client/grpc_client.py`: un cliente real que abre un canal gRPC y llama
  a las tres operaciones remotas.

### 1.3 Mensajería con RabbitMQ/Redis/Kafka

La mensajería asíncrona desacopla a los servicios: el servicio de Orders
no necesita saber **quién** consume el evento `OrderCreated`, solo que lo
publica. Se implementaron dos adaptadores reales y uno de prueba:

- `messaging/rabbitmq_publisher.py`: usa **pika** (cliente AMQP) y publica
  en un *exchange* tipo `topic` llamado `orders`, con *routing key*
  `order.created`. Es la opción recomendada cuando se necesita
  enrutamiento flexible, colas duraderas y garantías de entrega.
- `messaging/redis_publisher.py`: usa **redis-py** con Pub/Sub sobre el
  canal `order.created`. Es una alternativa más ligera para notificación
  "fire and forget" (sin persistencia si no hay un suscriptor activo).
- `messaging/in_memory_publisher.py`: adaptador en memoria usado en
  pruebas y demos sin broker externo.
- **Kafka** no se implementó con un cliente real (no hay acceso de red a
  un broker Kafka en este entorno), pero el mismo puerto `EventPublisher`
  se extendería con una clase `KafkaPublisher` (p. ej. con `confluent-kafka`
  o `aiokafka`) sin tocar el servicio gRPC, ya que este solo depende de la
  interfaz `EventPublisher`, no de una librería concreta.

Todos los publishers comparten el mismo puerto (`messaging/base.py`,
un `typing.Protocol`), y el `messaging/factory.py` decide cuál instanciar
según la variable de entorno `MESSAGING_BACKEND` — el mismo patrón
factory/provider usado en el Módulo 12 para inversión de dependencias.

### 1.4 Serialización: JSON/Avro/Protobuf

`serialization/demo_serialization.py` toma **el mismo evento lógico**
(`OrderCreatedEvent`) y lo serializa con tres formatos distintos para
comparar:

| Formato  | Tipo    | Requiere esquema | Tamaño típico | Legible por humanos |
|----------|---------|-------------------|----------------|----------------------|
| JSON     | Texto   | No (opcional)      | Mayor          | Sí                   |
| Avro     | Binario | Sí (schema Avro)   | Compacto       | No                   |
| Protobuf | Binario | Sí (`.proto`)      | Compacto       | No                   |

JSON es ideal para depuración y APIs públicas; Avro es muy usado en
pipelines de datos (Kafka + Schema Registry) porque el esquema viaja
separado del payload y permite evolución controlada; Protobuf combina
tipado fuerte, generación de código multi-lenguaje y tamaño reducido,
por lo que es la elección natural para gRPC.

---

## 2. Objetivos — por qué deben cumplirse

**Objetivo 1: Definir contratos y comunicarse entre servicios
heterogéneos.**
En un ecosistema real, los servicios rara vez están escritos en un solo
lenguaje ni se despliegan todos al mismo tiempo. Si la comunicación
depende de "acordarse" de la forma de los datos, cualquier cambio no
coordinado rompe a los consumidores en producción. Un contrato explícito
(`.proto` u OpenAPI) actúa como **fuente única de verdad**, es
verificable (se puede validar automáticamente, como hace
`test_openapi_contract_es_valido`), y permite generar código y
documentación de forma determinista. Sin esto, la interoperabilidad se
vuelve frágil y dependiente de comunicación informal entre equipos.

**Objetivo 2: Integrar mensajería para eventos.**
No todas las comunicaciones deben ser síncronas (petición/respuesta). Un
evento como `OrderCreated` normalmente interesa a **varios** consumidores
(facturación, inventario, notificaciones) que no deberían bloquear la
creación de la orden ni acoplarse directamente al servicio de Orders. La
mensajería asíncrona logra:

- **Desacoplamiento temporal**: el consumidor no necesita estar
  disponible en el momento exacto en que ocurre el evento.
- **Escalabilidad independiente**: cada consumidor procesa a su propio
  ritmo.
- **Resiliencia**: si un consumidor falla, el productor (Orders) no se ve
  afectado.

Cumplir este objetivo implica diseñar el evento como un contrato propio
(`OrderCreatedEvent`) y elegir un backend de mensajería apropiado según
las garantías necesarias (RabbitMQ para enrutamiento/durabilidad, Redis
para simplicidad y baja latencia).

---

## 3. Descripción de la solución y cómo ejecutarla

### 3.1 Estructura del proyecto

```
modulo20/
├── proto/orders.proto              # Contrato Protobuf/gRPC (fuente)
├── generated/                      # Stubs generados (NO editar a mano)
│   ├── orders_pb2.py               # Clases de mensajes
│   ├── orders_pb2_grpc.py          # Cliente/servidor gRPC
│   └── orders_pb2.pyi
├── contracts/openapi.yaml          # Contrato REST equivalente
├── server/
│   ├── orders_servicer.py          # Lógica de negocio del servicio
│   └── grpc_server.py              # Composition root / arranque
├── client/grpc_client.py           # Cliente gRPC de demostración
├── messaging/
│   ├── base.py                     # Puerto EventPublisher (Protocol)
│   ├── rabbitmq_publisher.py       # Adaptador RabbitMQ (pika)
│   ├── redis_publisher.py          # Adaptador Redis (redis-py)
│   ├── in_memory_publisher.py      # Adaptador en memoria (tests/demo)
│   └── factory.py                  # Selección de backend por entorno
├── serialization/
│   ├── avro_schema.py              # Esquema Avro del evento
│   └── demo_serialization.py       # Comparación JSON/Avro/Protobuf
├── tests/                          # Suite pytest (18 pruebas, todas verdes)
├── requirements.txt
└── README.md
```

### 3.2 Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3.3 (Opcional) Regenerar los stubs de gRPC desde el .proto

Los stubs ya están generados en `generated/`, pero si modificas
`proto/orders.proto` debes regenerarlos:

```bash
python -m grpc_tools.protoc \
  -I proto \
  --python_out=generated \
  --grpc_python_out=generated \
  --pyi_out=generated \
  proto/orders.proto
```

> **Nota**: tras regenerar, `generated/orders_pb2_grpc.py` importa
> `orders_pb2` con `import orders_pb2 as orders__pb2`. Debe ajustarse a
> `from . import orders_pb2 as orders__pb2` para que funcione como
> paquete Python (`generated.orders_pb2_grpc`). Este ajuste ya está
> aplicado en el código entregado.

### 3.4 Ejecutar el servidor y el cliente gRPC

En una terminal, levanta el servidor (por defecto usa el publisher en
memoria, sin necesidad de broker):

```bash
export PYTHONPATH=.
python -m server.grpc_server
# -> Servidor gRPC OrdersService escuchando en el puerto 50051
```

En otra terminal, ejecuta el cliente:

```bash
export PYTHONPATH=.
python -m client.grpc_client
```

Salida esperada (aproximada):

```
Orden creada -> id=<uuid> total=399.90 status=CONFIRMED
Orden consultada -> order_id: "<uuid>" ...
Total de órdenes en el servidor: 1
```

### 3.5 Publicar eventos en RabbitMQ o Redis reales

Por defecto (`MESSAGING_BACKEND=memory`) no se requiere ningún broker.
Para usar un broker real (por ejemplo, levantado con Docker):

```bash
# RabbitMQ
docker run -d --name rabbitmq -p 5672:5672 rabbitmq:3-management
export MESSAGING_BACKEND=rabbitmq
export RABBITMQ_URL=amqp://guest:guest@localhost:5672/%2F
python -m server.grpc_server

# Redis
docker run -d --name redis -p 6379:6379 redis:7
export MESSAGING_BACKEND=redis
export REDIS_URL=redis://localhost:6379/0
python -m server.grpc_server
```

Cada vez que el cliente llame a `CreateOrder`, el servidor publicará
automáticamente un evento `OrderCreatedEvent` (serializado en Protobuf
binario) en el broker configurado.

### 3.6 Ejecutar el demo de serialización

```bash
export PYTHONPATH=.
python -m serialization.demo_serialization
```

Imprime el mismo evento serializado en JSON, Avro y Protobuf, con su
tamaño en bytes, y verifica que el *round-trip* (serializar →
deserializar) reproduce el dato original en los tres formatos.

### 3.7 Ejecutar la suite de pruebas

```bash
pytest -v
```

La suite (18 pruebas) cubre:

- **`test_grpc_service.py`**: lógica del servicer de forma aislada
  (creación, validación, consulta, listado, publicación del evento),
  usando un `EventPublisher` en memoria y un `context` de gRPC simulado.
- **`test_grpc_end_to_end.py`**: levanta un servidor gRPC real en un
  puerto efímero y lo consume con un stub real — valida el contrato
  `.proto` "de punta a punta", no solo en memoria.
- **`test_messaging.py`**: valida `InMemoryPublisher`, `RedisPublisher`
  (con `fakeredis`, que emula la API de Redis sin servidor real) y
  `RabbitMQPublisher` (con `pika.BlockingConnection` mockeado, dado que
  no hay acceso de red a un broker AMQP en este entorno), además de la
  factory de selección de backend.
- **`test_serialization.py`**: *round-trip* de JSON/Avro/Protobuf y
  validación formal del contrato `contracts/openapi.yaml` con
  `openapi-spec-validator`.

Todas las pruebas fueron ejecutadas y verificadas en el sandbox antes de
esta entrega (18/18 en verde), y el flujo servidor↔cliente gRPC real
(fuera de pytest) fue probado manualmente contra un puerto TCP real.

### 3.8 Notas de diseño

- El servicer (`OrdersServicer`) depende únicamente del puerto
  `EventPublisher` (un `Protocol`), nunca de `pika` o `redis` de forma
  directa — mismo principio de Inversión de Dependencias aplicado en los
  módulos 12 y 16. Esto permite cambiar de broker (o añadir Kafka) sin
  tocar la lógica de negocio.
- El repositorio de órdenes es en memoria (`dict`) por simplicidad; en un
  escenario productivo se sustituiría por un adaptador de persistencia
  real, siguiendo el mismo patrón de puertos/adaptadores del Módulo 16.
