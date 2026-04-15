from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relación uno-a-muchos con Order
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, nombre='{self.nombre}', email='{self.email}')>"


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    total = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relaciones
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def calcular_total(self):
        """Calcula el total sumando todos los items"""
        self.total = sum(item.subtotal for item in self.items)

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, total={self.total})>"


class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    producto = Column(String(200), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    # Relación con Order
    order = relationship("Order", back_populates="items")

    def __repr__(self):
        return f"<OrderItem(producto='{self.producto}', cantidad={self.cantidad}, subtotal={self.subtotal})>"