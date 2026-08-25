from app.core.security import get_password_hash

# Usuario de prueba: admin / admin123
fake_users_db: dict[str, dict] = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": get_password_hash("admin123"),
        "disabled": False,
    }
}

# "Tabla" de items en memoria
fake_items_db: dict[int, "ItemOut"] = {}  # type: ignore[name-defined]

_item_id_seq = 0


def next_item_id() -> int:
    global _item_id_seq
    _item_id_seq += 1
    return _item_id_seq
