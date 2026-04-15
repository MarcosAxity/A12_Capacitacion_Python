from dataclasses import dataclass, field
from typing import List, Optional, Annotated
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
    field_serializer
)


# ============================================================================
# PARTE 1: DATACLASS ORDER CON CÁLCULOS DERIVADOS Y COMPARACIONES
# ============================================================================

class EstadoOrden(Enum):
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    ENVIADO = "enviado"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"


@dataclass
class ItemOrden:
    """Representa un item individual en la orden"""
    producto_id: int
    nombre: str
    precio_unitario: Decimal
    cantidad: int
    descuento: Decimal = Decimal('0.00')  # Descuento en porcentaje (0-100)

    def __post_init__(self):
        """Validaciones básicas"""
        if self.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        if self.precio_unitario < 0:
            raise ValueError("El precio no puede ser negativo")
        if not (0 <= self.descuento <= 100):
            raise ValueError("El descuento debe estar entre 0 y 100")

    @property
    def subtotal(self) -> Decimal:
        """Calcula el subtotal sin descuento"""
        return self.precio_unitario * self.cantidad

    @property
    def monto_descuento(self) -> Decimal:
        """Calcula el monto del descuento"""
        return self.subtotal * (self.descuento / Decimal('100'))

    @property
    def total(self) -> Decimal:
        """Calcula el total con descuento aplicado"""
        return self.subtotal - self.monto_descuento


@dataclass(order=True)
class Order:
    """
    Orden con cálculos derivados y comparaciones.
    Las órdenes se comparan por su total (order=True usa el primer campo para comparar)
    """
    # Campo para comparación (debe ser el primero cuando order=True)
    sort_index: Decimal = field(init=False, repr=False)

    # Campos principales
    orden_id: int
    cliente_id: int
    items: List[ItemOrden] = field(default_factory=list)
    estado: EstadoOrden = EstadoOrden.PENDIENTE
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_actualizacion: Optional[datetime] = None
    impuesto_porcentaje: Decimal = Decimal('16.00')  # IVA por defecto
    costo_envio: Decimal = Decimal('0.00')
    notas: Optional[str] = None

    def __post_init__(self):
        """Inicializa el sort_index después de la creación"""
        self.sort_index = self.total
        if not self.items:
            raise ValueError("La orden debe tener al menos un item")

    # ========================================================================
    # CÁLCULOS DERIVADOS
    # ========================================================================

    @property
    def subtotal(self) -> Decimal:
        """Suma de todos los subtotales de items (sin descuentos)"""
        return sum(item.subtotal for item in self.items)

    @property
    def total_descuentos(self) -> Decimal:
        """Suma de todos los descuentos aplicados"""
        return sum(item.monto_descuento for item in self.items)

    @property
    def subtotal_con_descuento(self) -> Decimal:
        """Subtotal después de aplicar descuentos"""
        return self.subtotal - self.total_descuentos

    @property
    def monto_impuesto(self) -> Decimal:
        """Calcula el impuesto sobre el subtotal con descuento"""
        return self.subtotal_con_descuento * (self.impuesto_porcentaje / Decimal('100'))

    @property
    def total(self) -> Decimal:
        """Total final: subtotal con descuento + impuesto + envío"""
        return self.subtotal_con_descuento + self.monto_impuesto + self.costo_envio

    @property
    def cantidad_items(self) -> int:
        """Cantidad total de productos (suma de cantidades)"""
        return sum(item.cantidad for item in self.items)

    @property
    def cantidad_productos_unicos(self) -> int:
        """Cantidad de productos diferentes"""
        return len(self.items)

    # ========================================================================
    # MÉTODOS DE NEGOCIO
    # ========================================================================

    def agregar_item(self, item: ItemOrden) -> None:
        """Agrega un item a la orden"""
        self.items.append(item)
        self.actualizar_fecha()
        self.sort_index = self.total  # Actualizar índice de ordenamiento

    def remover_item(self, producto_id: int) -> bool:
        """Remueve un item por producto_id. Retorna True si se removió."""
        for i, item in enumerate(self.items):
            if item.producto_id == producto_id:
                self.items.pop(i)
                self.actualizar_fecha()
                self.sort_index = self.total
                return True
        return False

    def actualizar_estado(self, nuevo_estado: EstadoOrden) -> None:
        """Actualiza el estado de la orden"""
        if self.estado == EstadoOrden.CANCELADO:
            raise ValueError("No se puede modificar una orden cancelada")
        self.estado = nuevo_estado
        self.actualizar_fecha()

    def aplicar_descuento_orden(self, porcentaje: Decimal) -> None:
        """Aplica un descuento adicional a todos los items"""
        if not (0 <= porcentaje <= 100):
            raise ValueError("El descuento debe estar entre 0 y 100")
        for item in self.items:
            # Aplicar descuento adicional
            descuento_actual = item.descuento
            item.descuento = min(descuento_actual + porcentaje, Decimal('100'))
        self.actualizar_fecha()
        self.sort_index = self.total

    def actualizar_fecha(self) -> None:
        """Actualiza la fecha de última modificación"""
        self.fecha_actualizacion = datetime.now()

    def puede_ser_cancelada(self) -> bool:
        """Verifica si la orden puede ser cancelada"""
        return self.estado in [EstadoOrden.PENDIENTE, EstadoOrden.PROCESANDO]

    def resumen(self) -> str:
        """Genera un resumen legible de la orden"""
        return f"""
        Orden #{self.orden_id}
        Cliente: {self.cliente_id}
        Estado: {self.estado.value}
        Items: {self.cantidad_productos_unicos} productos ({self.cantidad_items} unidades)
        Subtotal: ${self.subtotal:.2f}
        Descuentos: -${self.total_descuentos:.2f}
        Impuesto ({self.impuesto_porcentaje}%): ${self.monto_impuesto:.2f}
        Envío: ${self.costo_envio:.2f}
        ----------------------------------------
        TOTAL: ${self.total:.2f}
        """


# ============================================================================
# PARTE 2: MODELOS PYDANTIC PARA ENTRADA/SALIDA
# ============================================================================

class ItemOrdenIn(BaseModel):
    """Modelo de entrada para crear un item de orden"""
    producto_id: Annotated[int, Field(gt=0, description="ID del producto")]
    nombre: Annotated[str, Field(min_length=1, max_length=200)]
    precio_unitario: Annotated[Decimal, Field(gt=0, decimal_places=2, description="Precio por unidad")]
    cantidad: Annotated[int, Field(gt=0, le=1000, description="Cantidad de productos")]
    descuento: Annotated[Decimal, Field(ge=0, le=100, decimal_places=2, description="Descuento en porcentaje")] = Decimal('0.00')

    # Pydantic: @field_validator en lugar de @validator
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        """Limpia y valida el nombre del producto"""
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacío")
        return v.title()

    # Pydantic: model_config en lugar de Config class
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "producto_id": 101,
                    "nombre": "Laptop Dell XPS",
                    "precio_unitario": 1299.99,
                    "cantidad": 2,
                    "descuento": 10.00
                }
            ]
        }
    )


class OrderIn(BaseModel):
    """Modelo de entrada para crear una orden"""
    cliente_id: Annotated[int, Field(gt=0)]
    items: Annotated[List[ItemOrdenIn], Field(min_length=1, description="Lista de items (mínimo 1)")]
    impuesto_porcentaje: Annotated[
        Decimal,
        Field(ge=0, le=100, decimal_places=2, description="Porcentaje de impuesto")
    ] = Decimal('16.00')
    costo_envio: Annotated[
        Decimal,
        Field(ge=0, decimal_places=2, description="Costo de envío")
    ] = Decimal('0.00')
    notas: Optional[str] = Field(None, max_length=500)

    # Pydantic: @model_validator en lugar de @root_validator
    @model_validator(mode='after')
    def validar_orden(self) -> 'OrderIn':
        """Validaciones a nivel de toda la orden"""
        # Verificar que no haya productos duplicados
        producto_ids = [item.producto_id for item in self.items]
        if len(producto_ids) != len(set(producto_ids)):
            raise ValueError("No puede haber productos duplicados en la orden")

        # Validar total mínimo (ejemplo)
        total_estimado = sum(
            item.precio_unitario * item.cantidad for item in self.items
        )
        if total_estimado < Decimal('10.00'):
            raise ValueError("El total de la orden debe ser al menos $10.00")

        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "cliente_id": 42,
                    "items": [
                        {
                            "producto_id": 101,
                            "nombre": "Laptop",
                            "precio_unitario": 1299.99,
                            "cantidad": 1,
                            "descuento": 5.00
                        },
                        {
                            "producto_id": 102,
                            "nombre": "Mouse",
                            "precio_unitario": 29.99,
                            "cantidad": 2,
                            "descuento": 0.00
                        }
                    ],
                    "impuesto_porcentaje": 16.00,
                    "costo_envio": 15.00,
                    "notas": "Entrega urgente"
                }
            ]
        }
    )


class ItemOrdenOut(BaseModel):
    """Modelo de salida para un item de orden"""
    producto_id: int
    nombre: str
    precio_unitario: Decimal
    cantidad: int
    descuento: Decimal
    subtotal: Decimal
    monto_descuento: Decimal
    total: Decimal

    # Pydantic: @field_serializer para controlar la serialización
    @field_serializer('precio_unitario', 'descuento', 'subtotal', 'monto_descuento', 'total')
    def serialize_decimal(self, value: Decimal) -> float:
        """Convierte Decimal a float en la serialización"""
        return float(value)

    model_config = ConfigDict(
        # Pydantic V2: from_attributes reemplaza a orm_mode
        from_attributes=True
    )


class OrderOut(BaseModel):
    """Modelo de salida para una orden completa"""
    orden_id: int
    cliente_id: int
    estado: str
    items: List[ItemOrdenOut]
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]

    # Cálculos
    subtotal: Decimal
    total_descuentos: Decimal
    subtotal_con_descuento: Decimal
    impuesto_porcentaje: Decimal
    monto_impuesto: Decimal
    costo_envio: Decimal
    total: Decimal

    # Metadata
    cantidad_items: int
    cantidad_productos_unicos: int
    notas: Optional[str]

    # Pydantic: @field_serializer para múltiples campos
    @field_serializer(
        'subtotal', 'total_descuentos', 'subtotal_con_descuento',
        'impuesto_porcentaje', 'monto_impuesto', 'costo_envio', 'total'
    )
    def serialize_decimal(self, value: Decimal) -> float:
        """Convierte Decimal a float en la serialización"""
        return float(value)

    @field_serializer('fecha_creacion', 'fecha_actualizacion')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Convierte datetime a ISO format"""
        return value.isoformat() if value else None

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================================
# PARTE 3: CONVERSIÓN ENTRE MODELOS PYDANTIC Y DATACLASS
# ============================================================================

class OrderConverter:
    """Clase para convertir entre modelos Pydantic y dataclass Order"""

    @staticmethod
    def from_pydantic_to_entity(order_in: OrderIn, orden_id: int) -> Order:
        """
        Convierte un OrderIn (Pydantic) a una entidad Order (dataclass)

        Args:
            order_in: Modelo de entrada validado por Pydantic
            orden_id: ID único para la orden

        Returns:
            Instancia de Order (dataclass)
        """
        # Convertir items
        items_entity = [
            ItemOrden(
                producto_id=item.producto_id,
                nombre=item.nombre,
                precio_unitario=item.precio_unitario,
                cantidad=item.cantidad,
                descuento=item.descuento
            )
            for item in order_in.items
        ]

        # Crear orden
        order = Order(
            orden_id=orden_id,
            cliente_id=order_in.cliente_id,
            items=items_entity,
            impuesto_porcentaje=order_in.impuesto_porcentaje,
            costo_envio=order_in.costo_envio,
            notas=order_in.notas
        )

        return order

    @staticmethod
    def from_entity_to_pydantic(order: Order) -> OrderOut:
        """
        Convierte una entidad Order (dataclass) a OrderOut (Pydantic)

        Args:
            order: Instancia de Order (dataclass)

        Returns:
            OrderOut validado por Pydantic
        """
        # Convertir items
        items_out = [
            ItemOrdenOut(
                producto_id=item.producto_id,
                nombre=item.nombre,
                precio_unitario=item.precio_unitario,
                cantidad=item.cantidad,
                descuento=item.descuento,
                subtotal=item.subtotal,
                monto_descuento=item.monto_descuento,
                total=item.total
            )
            for item in order.items
        ]

        # Crear OrderOut
        order_out = OrderOut(
            orden_id=order.orden_id,
            cliente_id=order.cliente_id,
            estado=order.estado.value,
            items=items_out,
            fecha_creacion=order.fecha_creacion,
            fecha_actualizacion=order.fecha_actualizacion,
            subtotal=order.subtotal,
            total_descuentos=order.total_descuentos,
            subtotal_con_descuento=order.subtotal_con_descuento,
            impuesto_porcentaje=order.impuesto_porcentaje,
            monto_impuesto=order.monto_impuesto,
            costo_envio=order.costo_envio,
            total=order.total,
            cantidad_items=order.cantidad_items,
            cantidad_productos_unicos=order.cantidad_productos_unicos,
            notas=order.notas
        )

        return order_out


# ============================================================================
# PARTE 4: DEMOSTRACIÓN Y PRUEBAS
# ============================================================================

def demo_completa():
    """Demostración completa del sistema de órdenes"""

    print("=" * 70)
    print("DEMO: SISTEMA DE ÓRDENES CON DATACLASSES Y PYDANTIC")
    print("=" * 70)

    # ========================================================================
    # 1. VALIDACIÓN DE ENTRADA CON PYDANTIC
    # ========================================================================
    print("\n1️⃣  VALIDACIÓN DE ENTRADA CON PYDANTIC")
    print("-" * 70)

    # Datos de entrada (simulando una petición API)
    datos_json = {
        "cliente_id": 42,
        "items": [
            {
                "producto_id": 101,
                "nombre": "  laptop dell xps  ",
                "precio_unitario": "1299.99",
                "cantidad": 1,
                "descuento": "10.00"
            },
            {
                "producto_id": 102,
                "nombre": "mouse inalámbrico",
                "precio_unitario": "29.99",
                "cantidad": 2,
                "descuento": "5.00"
            },
            {
                "producto_id": 103,
                "nombre": "teclado mecánico",
                "precio_unitario": "89.99",
                "cantidad": 1,
                "descuento": "0.00"
            }
        ],
        "impuesto_porcentaje": "16.00",
        "costo_envio": "25.00",
        "notas": "Entrega express - antes de las 5 PM"
    }

    try:
        # Pydantic valida y normaliza automáticamente
        order_in = OrderIn(**datos_json)
        print("✅ Datos validados correctamente por Pydantic")
        print(f"   Cliente: {order_in.cliente_id}")
        print(f"   Items: {len(order_in.items)}")
        print(f"   Primer producto: {order_in.items[0].nombre}")  # Normalizado a Title Case
    except Exception as e:
        print(f"❌ Error de validación: {e}")
        return

    # ========================================================================
    # 2. CONVERSIÓN A ENTIDAD DATACLASS
    # ========================================================================
    print("\n2️⃣  CONVERSIÓN A ENTIDAD (DATACLASS)")
    print("-" * 70)

    orden_id = 12345
    order = OrderConverter.from_pydantic_to_entity(order_in, orden_id)

    print(f"✅ Orden #{order.orden_id} creada")
    print(order.resumen())

    # ========================================================================
    # 3. CÁLCULOS DERIVADOS
    # ========================================================================
    print("\n3️⃣  CÁLCULOS DERIVADOS (PROPIEDADES)")
    print("-" * 70)

    print(f"Subtotal original:        ${order.subtotal:.2f}")
    print(f"Descuentos aplicados:    -${order.total_descuentos:.2f}")
    print(f"Subtotal con descuento:   ${order.subtotal_con_descuento:.2f}")
    print(f"Impuesto (16%):          +${order.monto_impuesto:.2f}")
    print(f"Costo de envío:          +${order.costo_envio:.2f}")
    print(f"{'='*40}")
    print(f"TOTAL FINAL:              ${order.total:.2f}")
    print(f"\nCantidad total de items: {order.cantidad_items}")
    print(f"Productos únicos: {order.cantidad_productos_unicos}")

    # ========================================================================
    # 4. OPERACIONES DE NEGOCIO
    # ========================================================================
    print("\n4️⃣  OPERACIONES DE NEGOCIO")
    print("-" * 70)

    # Agregar un nuevo item
    print("\n📦 Agregando nuevo item...")
    nuevo_item = ItemOrden(
        producto_id=104,
        nombre="Monitor 4K",
        precio_unitario=Decimal('399.99'),
        cantidad=1,
        descuento=Decimal('15.00')
    )
    order.agregar_item(nuevo_item)
    print(f"✅ Item agregado. Nuevo total: ${order.total:.2f}")

    # Aplicar descuento adicional
    print("\n💰 Aplicando descuento del 5% a toda la orden...")
    order.aplicar_descuento_orden(Decimal('5.00'))
    print(f"✅ Descuento aplicado. Nuevo total: ${order.total:.2f}")

    # Cambiar estado
    print("\n📊 Actualizando estado de la orden...")
    order.actualizar_estado(EstadoOrden.PROCESANDO)
    print(f"✅ Estado actualizado a: {order.estado.value}")

    # ========================================================================
    # 5. COMPARACIONES ENTRE ÓRDENES
    # ========================================================================
    print("\n5️⃣  COMPARACIONES ENTRE ÓRDENES")
    print("-" * 70)

    # Crear segunda orden más pequeña
    order2_data = {
        "cliente_id": 43,
        "items": [
            {
                "producto_id": 201,
                "nombre": "Cable USB",
                "precio_unitario": "9.99",
                "cantidad": 3,
                "descuento": "0.00"
            }
        ]
    }

    order_in_2 = OrderIn(**order2_data)
    order2 = OrderConverter.from_pydantic_to_entity(order_in_2, 12346)

    print(f"Orden 1 total: ${order.total:.2f}")
    print(f"Orden 2 total: ${order2.total:.2f}")
    print(f"\nComparaciones:")
    print(f"  order > order2:  {order > order2}")
    print(f"  order < order2:  {order < order2}")
    print(f"  order == order2: {order == order2}")

    # Ordenar múltiples órdenes
    order3 = OrderConverter.from_pydantic_to_entity(
        OrderIn(**{
            "cliente_id": 44,
            "items": [{"producto_id": 301, "nombre": "Libro", "precio_unitario": "19.99", "cantidad": 1}]
        }),
        12347
    )

    ordenes = [order, order2, order3]
    ordenes_ordenadas = sorted(ordenes)

    print(f"\n📋 Órdenes ordenadas por total (menor a mayor):")
    for idx, o in enumerate(ordenes_ordenadas, 1):
        print(f"  {idx}. Orden #{o.orden_id}: ${o.total:.2f}")

    # ========================================================================
    # 6. SERIALIZACIÓN A JSON (PYDANTIC)
    # ========================================================================
    print("\n6️⃣  SERIALIZACIÓN A JSON CON PYDANTIC")
    print("-" * 70)

    order_out = OrderConverter.from_entity_to_pydantic(order)

    # Pydantic V2: model_dump() en lugar de dict()
    order_dict = order_out.model_dump()
    print(f"✅ Orden convertida a diccionario ({len(order_dict)} campos)")

    # Pydantic V2: model_dump_json() en lugar de json()
    order_json = order_out.model_dump_json(indent=2)
    print(f"\n📄 JSON generado (primeros 500 caracteres):")
    print(order_json[:500] + "...")

    # ========================================================================
    # 7. MANEJO DE ERRORES
    # ========================================================================
    print("\n7️⃣  MANEJO DE ERRORES Y VALIDACIONES")
    print("-" * 70)

    # Intentar crear orden inválida
    print("\n❌ Intentando crear orden con cantidad negativa...")
    try:
        orden_invalida = OrderIn(**{
            "cliente_id": 45,
            "items": [
                {
                    "producto_id": 401,
                    "nombre": "Producto",
                    "precio_unitario": "10.00",
                    "cantidad": -5  # INVÁLIDO
                }
            ]
        })
    except Exception as e:
        print(f"   Rechazado: {type(e).__name__}")
        print(f"   Mensaje: {str(e)[:150]}")

    # Intentar crear orden sin items
    print("\n❌ Intentando crear orden sin items...")
    try:
        orden_sin_items = OrderIn(**{
            "cliente_id": 46,
            "items": []  # INVÁLIDO
        })
    except Exception as e:
        print(f"   Rechazado: {type(e).__name__}")
        print(f"   Mensaje: Lista debe tener al menos 1 item")

    # Intentar crear orden con productos duplicados
    print("\n❌ Intentando crear orden con productos duplicados...")
    try:
        orden_duplicados = OrderIn(**{
            "cliente_id": 47,
            "items": [
                {"producto_id": 501, "nombre": "Producto A", "precio_unitario": "10.00", "cantidad": 1},
                {"producto_id": 501, "nombre": "Producto A", "precio_unitario": "10.00", "cantidad": 2}  # DUPLICADO
            ]
        })
    except Exception as e:
        print(f"   Rechazado: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")

    print("\n" + "=" * 70)
    print("✅ DEMOSTRACIÓN COMPLETADA - PYDANTIC")
    print("=" * 70)

    # ========================================================================
    # 8. CARACTERÍSTICAS ADICIONALES DE PYDANTIC
    # ========================================================================
    print("\n8️⃣  CARACTERÍSTICAS NUEVAS DE PYDANTIC")
    print("-" * 70)

    print("\n🆕 Diferencias principales con V1:")
    print("   • @field_validator en lugar de @validator")
    print("   • @model_validator en lugar de @root_validator")
    print("   • model_dump() en lugar de dict()")
    print("   • model_dump_json() en lugar de json()")
    print("   • ConfigDict en lugar de Config class")
    print("   • from_attributes en lugar de orm_mode")
    print("   • @field_serializer para control fino de serialización")
    print("   • Mejor performance (núcleo en Rust)")
    print("   • Validación más estricta por defecto")


# ============================================================================
# EJECUTAR DEMOSTRACIÓN
# ============================================================================

if __name__ == "__main__":
    demo_completa()

