from __future__ import annotations

from pathlib import Path

import yaml
from openapi_spec_validator import validate

from serialization.demo_serialization import (
    build_sample_event_dict,
    deserialize_avro,
    deserialize_json,
    deserialize_protobuf,
    serialize_avro,
    serialize_json,
    serialize_protobuf,
)


def test_json_round_trip():
    event = build_sample_event_dict()
    assert deserialize_json(serialize_json(event)) == event


def test_avro_round_trip():
    event = build_sample_event_dict()
    assert deserialize_avro(serialize_avro(event)) == event


def test_protobuf_round_trip():
    event = build_sample_event_dict()
    message = deserialize_protobuf(serialize_protobuf(event))
    assert message.order_id == event["order_id"]
    assert message.customer_id == event["customer_id"]
    assert message.total_amount == event["total_amount"]


def test_protobuf_es_mas_compacto_que_json():
    event = build_sample_event_dict()
    assert len(serialize_protobuf(event)) < len(serialize_json(event))


def test_openapi_contract_es_valido():
    contract_path = Path(__file__).resolve().parent.parent / "contracts" / "openapi.yaml"
    spec = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    validate(spec)  # lanza excepción si el contrato no es válido
