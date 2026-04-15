from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Base, User, Order, OrderItem
import crud

def test_sistema_ordenes():
    """Pruebas completas del sistema con SQLite en memoria"""

    # Crear engine en memoria
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        print("\n=== 1. CREAR USUARIOS ===")
        user1 = crud.crear_user(session, "Ana García", "ana@email.com")
        user2 = crud.crear_user(session, "Carlos López", "carlos@email.com")
        print(f"Creados: {user1}, {user2}")

        print("\n=== 2. LISTAR USUARIOS ===")
        usuarios = crud.listar_users(session)
        for u in usuarios:
            print(u)

        print("\n=== 3. CREAR ÓRDENES ===")
        order1 = crud.crear_order(session, user1.id)
        order2 = crud.crear_order(session, user1.id)
        print(f"Órdenes creadas: {order1}, {order2}")

        print("\n=== 4. AGREGAR ITEMS A LA ORDEN ===")
        item1 = crud.agregar_item(session, order1.id, "Laptop", 1, 1200.00)
        item2 = crud.agregar_item(session, order1.id, "Mouse", 2, 25.50)
        item3 = crud.agregar_item(session, order2.id, "Teclado", 1, 75.00)
        print(f"Items agregados: {item1}, {item2}, {item3}")

        print("\n=== 5. VERIFICAR TOTAL DE ORDEN ===")
        session.refresh(order1)
        print(f"Orden {order1.id} - Total: ${order1.total}")
        print(f"Items en la orden:")
        for item in order1.items:
            print(f"  - {item}")

        print("\n=== 6. ACTUALIZAR ITEM ===")
        crud.actualizar_item(session, item2.id, cantidad=5)
        session.refresh(order1)
        print(f"Orden {order1.id} después de actualizar - Total: ${order1.total}")

        print("\n=== 7. OBTENER ÓRDENES DE UN USUARIO ===")
        ordenes_ana = crud.listar_orders_usuario(session, user1.id)
        print(f"{user1.nombre} tiene {len(ordenes_ana)} órdenes:")
        for orden in ordenes_ana:
            print(f"  - {orden}")

        print("\n=== 8. ACTUALIZAR USUARIO ===")
        crud.actualizar_user(session, user1.id, nombre="Ana María García")
        session.refresh(user1)
        print(f"Usuario actualizado: {user1}")

        print("\n=== 9. ELIMINAR ITEM ===")
        crud.eliminar_item(session, item1.id)
        session.refresh(order1)
        print(f"Orden {order1.id} después de eliminar item - Total: ${order1.total}")

        print("\n=== 10. ELIMINAR ORDEN ===")
        crud.eliminar_order(session, order2.id)
        ordenes_restantes = crud.listar_orders_usuario(session, user1.id)
        print(f"Órdenes restantes de {user1.nombre}: {len(ordenes_restantes)}")

        print("\n=== 11. ELIMINAR USUARIO (CASCADE) ===")
        print(f"Antes de eliminar - Total usuarios: {len(crud.listar_users(session))}")
        crud.eliminar_user(session, user1.id)
        print(f"Después de eliminar - Total usuarios: {len(crud.listar_users(session))}")

        print("\n=== 12. VERIFICAR CASCADE ===")
        ordenes_restantes = session.query(Order).all()
        items_restantes = session.query(OrderItem).all()
        print(f"Órdenes en DB: {len(ordenes_restantes)}")
        print(f"Items en DB: {len(items_restantes)}")

    print("\n✅ Todas las pruebas completadas exitosamente")


if __name__ == "__main__":
    test_sistema_ordenes()