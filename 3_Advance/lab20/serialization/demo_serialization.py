"""Compara JSON, Avro y Protobuf serializando el MISMO evento de dominio.

Objetivo pedagógico: mostrar que un mismo contrato lógico (OrderCreatedEvent)
puede representarse en distintos formatos de serialización según la
necesidad (legibilidad humana vs. tamaño en bytes vs. compatibilidad de
esquemas), y que la elección de formato es independiente del contrato en sí.

Ejecución:
    python -m serialization.demo_serialization
"""
from __future__ import annotations

import io
import json
from datetime import datetime, timezone

import fastavro

from generated import orders_pb2
from serialization.avro_schema import ORDER_CREATED_AVRO_SCHEMA


def build_sample_event_dict() -> dict:
    return {
        "event_id": "evt-0001",
        "order_id": "order-1234",
        "customer_id": "cliente-001",
        "total_amount": 399.9,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }


def serialize_json(event: dict) -> bytes:
    return json.dumps(event).encode("utf-8")


def deserialize_json(raw: bytes) -> dict:
    return json.loads(raw.decode("utf-8"))


def serialize_avro(event: dict) -> bytes:
    buffer = io.BytesIO()
    fastavro.schemaless_writer(buffer, ORDER_CREATED_AVRO_SCHEMA, event)
    return buffer.getvalue()


def deserialize_avro(raw: bytes) -> dict:
    buffer = io.BytesIO(raw)
    return fastavro.schemaless_reader(buffer, ORDER_CREATED_AVRO_SCHEMA)


def serialize_protobuf(event: dict) -> bytes:
    message = orders_pb2.OrderCreatedEvent(**event)
    return message.SerializeToString()


def deserialize_protobuf(raw: bytes) -> orders_pb2.OrderCreatedEvent:
    message = orders_pb2.OrderCreatedEvent()
    message.ParseFromString(raw)
    return message


def main() -> None:
    event = build_sample_event_dict()

    json_bytes = serialize_json(event)
    avro_bytes = serialize_avro(event)
    proto_bytes = serialize_protobuf(event)

    print("Evento original:", event)
    print("-" * 60)
    print(f"JSON      -> {len(json_bytes):3d} bytes | {json_bytes}")
    print(f"Avro      -> {len(avro_bytes):3d} bytes | (binario, requiere esquema)")
    print(f"Protobuf  -> {len(proto_bytes):3d} bytes | (binario, requiere .proto)")
    print("-" * 60)

    assert deserialize_json(json_bytes) == event
    assert deserialize_avro(avro_bytes) == event
    proto_msg = deserialize_protobuf(proto_bytes)
    assert proto_msg.order_id == event["order_id"]

    print("Round-trip verificado correctamente en los tres formatos.")


if __name__ == "__main__":
    main()
