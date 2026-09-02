"""Esquema Avro para OrderCreatedEvent (equivalente al mensaje .proto)."""

ORDER_CREATED_AVRO_SCHEMA = {
    "type": "record",
    "name": "OrderCreatedEvent",
    "namespace": "orders",
    "fields": [
        {"name": "event_id", "type": "string"},
        {"name": "order_id", "type": "string"},
        {"name": "customer_id", "type": "string"},
        {"name": "total_amount", "type": "double"},
        {"name": "occurred_at", "type": "string"},
    ],
}
