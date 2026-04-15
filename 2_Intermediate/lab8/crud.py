from sqlalchemy.orm import Session
from models import User, Order, OrderItem

# ========== CRUD USER ==========

def crear_user(session: Session, nombre: str, email: str) -> User:
    """Crea un nuevo usuario"""
    user = User(nombre=nombre, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def obtener_user(session: Session, user_id: int) -> User:
    """Obtiene un usuario por ID"""
    return session.query(User).filter(User.id == user_id).first()

def listar_users(session: Session):
    """Lista todos los usuarios"""
    return session.query(User).all()

def actualizar_user(session: Session, user_id: int, nombre: str = None, email: str = None):
    """Actualiza datos de un usuario"""
    user = obtener_user(session, user_id)
    if user:
        if nombre:
            user.nombre = nombre
        if email:
            user.email = email
        session.commit()
        session.refresh(user)
    return user

def eliminar_user(session: Session, user_id: int):
    """Elimina un usuario"""
    user = obtener_user(session, user_id)
    if user:
        session.delete(user)
        session.commit()
        return True
    return False


# ========== CRUD ORDER ==========

def crear_order(session: Session, user_id: int) -> Order:
    """Crea una nueva orden para un usuario"""
    order = Order(user_id=user_id)
    session.add(order)
    session.commit()
    session.refresh(order)
    return order

def obtener_order(session: Session, order_id: int) -> Order:
    """Obtiene una orden por ID"""
    return session.query(Order).filter(Order.id == order_id).first()

def listar_orders_usuario(session: Session, user_id: int):
    """Lista todas las órdenes de un usuario"""
    return session.query(Order).filter(Order.user_id == user_id).all()

def eliminar_order(session: Session, order_id: int):
    """Elimina una orden"""
    order = obtener_order(session, order_id)
    if order:
        session.delete(order)
        session.commit()
        return True
    return False


# ========== CRUD ORDER ITEM ==========

def agregar_item(session: Session, order_id: int, producto: str, cantidad: int, precio: float) -> OrderItem:
    """Agrega un item a una orden"""
    subtotal = cantidad * precio
    item = OrderItem(
        order_id=order_id,
        producto=producto,
        cantidad=cantidad,
        precio=precio,
        subtotal=subtotal
    )
    session.add(item)

    # Actualizar total de la orden
    order = obtener_order(session, order_id)
    order.calcular_total()

    session.commit()
    session.refresh(item)
    return item

def obtener_item(session: Session, item_id: int) -> OrderItem:
    """Obtiene un item por ID"""
    return session.query(OrderItem).filter(OrderItem.id == item_id).first()

def actualizar_item(session: Session, item_id: int, cantidad: int = None, precio: float = None):
    """Actualiza un item y recalcula subtotal"""
    item = obtener_item(session, item_id)
    if item:
        if cantidad is not None:
            item.cantidad = cantidad
        if precio is not None:
            item.precio = precio

        item.subtotal = item.cantidad * item.precio

        # Recalcular total de la orden
        item.order.calcular_total()

        session.commit()
        session.refresh(item)
    return item

def eliminar_item(session: Session, item_id: int):
    """Elimina un item de una orden"""
    item = obtener_item(session, item_id)
    if item:
        order = item.order
        session.delete(item)
        order.calcular_total()
        session.commit()
        return True
    return False