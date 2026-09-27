"""Forma del pedido completo (roadmap_backend.txt §3), con la nullabilidad y
los catalogos de roadmap_bd.txt §3/§4. ESPEJO CONGELADO: se modifica SOLO si
el Int.1/2 notifica un cambio en 01_esquema_tablas.sql o 02_catalogos.sql, y
entonces se actualiza aqui Y en roadmap_backend.txt avisando al grupo (§0).
NO calcula nada (RNF-05). Dinero/coordenadas salen float por §3 (transporte
JSON); en la BD se guardan NUMERIC (RNF-06 = almacenamiento). NO cambiar a
Decimal: Pydantic v2 lo serializaria como string y rompe formato.js del front."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

# Catalogos cerrados de roadmap_bd §3/§4 (CHECK / estado_pedido / calificacion.tipo).
EstadoCodigo = Literal[
    "recibido", "en_preparacion", "listo_para_retirar",
    "en_camino", "entregado", "cancelado",
]
TipoVehiculo = Literal["bicicleta", "moto", "auto"]
Moneda = Literal["USD", "VES"]
TipoCalificacion = Literal[
    "cliente_a_repartidor", "cliente_a_restaurante", "repartidor_a_cliente",
]


class _Salida(BaseModel):
    # Permite model_validate(fila de vista/Row). NO significa devolver ORM crudo (§0).
    model_config = ConfigDict(from_attributes=True)


class RestauranteResumen(_Salida):
    id_restaurante: int
    nombre: str
    telefono: str
    latitud: float
    longitud: float


class ClienteResumen(_Salida):
    id_cliente: int
    nombre: str
    telefono: str


class DireccionResumen(_Salida):
    id_direccion: int
    direccion: str
    referencia: str | None          # (NULL) roadmap_bd §3
    latitud: float
    longitud: float


class RepartidorResumen(_Salida):
    id_repartidor: int
    nombre: str
    telefono: str
    tipo_vehiculo: TipoVehiculo
    calificacion_promedio: float
    latitud_actual: float | None    # (NULL) roadmap_bd §3: repartidor sin posicion
    longitud_actual: float | None   # (NULL) roadmap_bd §3


class DetallePedido(_Salida):
    id_producto: int
    nombre: str                     # derivado: JOIN producto.nombre
    cantidad: int
    precio_unitario: float
    subtotal: float


class HistorialEstado(_Salida):
    id_estado: int
    estado_codigo: EstadoCodigo     # derivado: JOIN estado_pedido.codigo
    estado_nombre: str              # derivado: JOIN estado_pedido.nombre
    fecha_hora: datetime


class PedidoCompleto(_Salida):
    id_pedido: int
    id_estado: int
    estado_codigo: EstadoCodigo     # derivado: JOIN estado_pedido.codigo
    estado_nombre: str              # derivado: JOIN estado_pedido.nombre
    fecha_creacion: datetime

    subtotal: float
    costo_envio: float
    propina: float
    iva_total: float
    igtf: float
    total: float

    moneda_pago: Moneda
    tasa_bcv_aplicada: float
    total_ves: float

    id_factura: int | None          # derivado: LEFT JOIN factura (no es columna de pedido)
    distancia_km: float
    tiempo_estimado_min: int | None  # (NULL) roadmap_bd §3
    motivo_cancelacion: str | None   # (NULL) roadmap_bd §3

    restaurante: RestauranteResumen
    cliente: ClienteResumen
    direccion: DireccionResumen
    repartidor: RepartidorResumen | None   # pedido.id_repartidor (NULL)
    detalle: list[DetallePedido]
    historial: list[HistorialEstado]
    calificaciones_hechas: list[TipoCalificacion]

# Columnas de BD que a PROPOSITO NO se exponen (no estan en §3 backend; agregarlas
# violaria "no inventar" de roadmap_backend §0 / roadmap_bd §0): comision_plataforma,
# monto_restaurante (el restaurante los ve via vw_desempeno_restaurantes/vw_liquidacion),
# id_zona/principal (direccion), id_categoria/tiempo_prep_min/rif (restaurante),
# cedula/disponibilidad/prioridad (repartidor), id_historial/id_usuario (historial).