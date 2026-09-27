"""Forma del pedido completo. Espejo EXACTO de roadmap_backend.txt §3.
NO calcula nada: todos los importes/fechas/coordenadas vienen de la BD (RNF-05).
Si el grupo cambia la §3, se cambia aqui Y en roadmap_backend.txt, avisando al grupo."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class _Salida(BaseModel):
    # Base comun: permite model_validate(fila_de_vista_o_Row) sin cambiar el contrato.
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
    referencia: str
    latitud: float
    longitud: float


class RepartidorResumen(_Salida):
    id_repartidor: int
    nombre: str
    telefono: str
    tipo_vehiculo: str
    calificacion_promedio: float
    latitud_actual: float
    longitud_actual: float


class DetallePedido(_Salida):
    id_producto: int
    nombre: str
    cantidad: int
    precio_unitario: float
    subtotal: float


class HistorialEstado(_Salida):
    id_estado: int
    estado_codigo: str
    estado_nombre: str
    fecha_hora: datetime


class PedidoCompleto(_Salida):
    id_pedido: int
    id_estado: int
    estado_codigo: str
    estado_nombre: str
    fecha_creacion: datetime

    subtotal: float
    costo_envio: float
    propina: float
    iva_total: float
    igtf: float
    total: float

    moneda_pago: str
    tasa_bcv_aplicada: float
    total_ves: float

    id_factura: int | None          # se llena al entregar (BD)
    distancia_km: float
    tiempo_estimado_min: int
    motivo_cancelacion: str | None

    restaurante: RestauranteResumen
    cliente: ClienteResumen
    direccion: DireccionResumen
    repartidor: RepartidorResumen | None
    detalle: list[DetallePedido]
    historial: list[HistorialEstado]
    calificaciones_hechas: list[str]