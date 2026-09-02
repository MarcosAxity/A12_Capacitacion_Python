"""Pruebas de los adaptadores de mensajería.

- InMemoryPublisher: sin dependencias externas.
- RedisPublisher: se inyecta un cliente fakeredis (Redis en memoria, misma
  API que redis-py) para no requerir un servidor Redis real.
- RabbitMQPublisher: se mockea pika.BlockingConnection porque levantar un
  broker AMQP real no es viable en este entorno de pruebas.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import fakeredis

from generated import orders_pb2
from messaging.factory import get_publisher
from messaging.in_memory_publisher import InMemoryPublisher
from messaging.rabbitmq_publisher import RabbitMQPublisher
from messaging.redis_publisher import RedisPublisher


def _sample_event() -> orders_pb2.OrderCreatedEvent:
    return orders_pb2.OrderCreatedEvent(
        event_id="evt-1",
        order_id="order-1",
        customer_id="cliente-1",
        total_amount=199.9,
        occurred_at="2026-01-01T00:00:00+00:00",
    )


def test_in_memory_publisher_captura_evento():
    publisher = InMemoryPublisher()
    event = _sample_event()

    publisher.publish_order_created(event)

    assert publisher.published_events == [event]


def test_redis_publisher_publica_bytes_protobuf():
    fake_client = fakeredis.FakeStrictRedis()
    publisher = RedisPublisher(client=fake_client)
    event = _sample_event()

    pubsub = fake_client.pubsub()
    pubsub.subscribe("order.created")
    pubsub.get_message()  # descarta el mensaje de confirmación de subscribe

    publisher.publish_order_created(event)

    message = pubsub.get_message(timeout=1)
    assert message is not None
    received_event = orders_pb2.OrderCreatedEvent()
    received_event.ParseFromString(message["data"])
    assert received_event.order_id == event.order_id


def test_rabbitmq_publisher_declara_exchange_y_publica():
    with patch("messaging.rabbitmq_publisher.pika.BlockingConnection") as mock_connection_cls:
        mock_channel = MagicMock()
        mock_connection = MagicMock()
        mock_connection.is_open = True
        mock_connection.channel.return_value = mock_channel
        mock_connection_cls.return_value = mock_connection

        publisher = RabbitMQPublisher(url="amqp://guest:guest@localhost:5672/%2F")
        event = _sample_event()
        publisher.publish_order_created(event)

        mock_channel.exchange_declare.assert_called_once()
        mock_channel.basic_publish.assert_called_once()
        _, kwargs = mock_channel.basic_publish.call_args
        assert kwargs["routing_key"] == "order.created"
        assert kwargs["body"] == event.SerializeToString()


def test_factory_devuelve_in_memory_por_defecto(monkeypatch):
    monkeypatch.delenv("MESSAGING_BACKEND", raising=False)
    publisher = get_publisher()
    assert isinstance(publisher, InMemoryPublisher)


def test_factory_devuelve_redis_cuando_se_indica():
    publisher = get_publisher(backend="redis")
    assert isinstance(publisher, RedisPublisher)


def test_factory_backend_invalido_lanza_error():
    import pytest

    with pytest.raises(ValueError):
        get_publisher(backend="kafka-inexistente")
