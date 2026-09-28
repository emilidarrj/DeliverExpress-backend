"""REPARTIDOR de §4, fiel a roadmap_bd §3/§6. Anida PedidoCompleto (oferta-pendiente y
pedido-actual). disponibilidad/prioridad/tipo_vehiculo = Literal (compartidos/pedido).
La respuesta de retirado/entregado se asume PedidoCompleto por simetria con restaurante
(§4 no la fija; fn_cambiar_estado RETURNS VOID, BD §6). fn_calificar RETURNS INT respalda
CalificarOut (compartidos) sin inventar. GET /liquidaciones reusa LiquidacionRow (facturas)."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.compartidos import (
    CalificarOut, DisponibilidadFull, OkRespuesta, Prioridad, _Entrada, _Salida,
)
from app.schemas.pedido import EstadoCodigo, PedidoCompleto, TipoVehiculo

# §4 PUT disponibilidad solo acepta libre|desconectado (no 'ocupado': no se permite si lo esta).
DisponibilidadSet = Literal["libre", "desconectado"]


# GET /api/repartidor/yo (§4)
class RepartidorYoOut(_Salida):
    id_repartidor: int
    nombre: str
    tipo_vehiculo: TipoVehiculo        # catalogo BD §3 (importado de pedido.py)
    disponibilidad: DisponibilidadFull
    prioridad: Prioridad
    calificacion_promedio: float
    en_revision: bool


class DisponibilidadIn(_Entrada):
    disponibilidad: DisponibilidadSet  # subconjunto que §4 permite enviar


# GET /api/repartidor/oferta-pendiente -> null o {...} (§4)
class OfertaPendienteOut(_Salida):
    id_oferta: int
    fecha_oferta: datetime
    segundos_restantes: int        # derivado: oferta_expira_seg (BD §4) - edad de la oferta
    distancia_km: float            # oferta_asignacion.distancia_km NOT NULL (BD §3)
    pedido: PedidoCompleto         # anida el pedido completo (§3 backend)
# El endpoint devuelve OfertaPendienteOut | None (null si no tiene oferta pendiente).


class ResponderOfertaIn(_Entrada):
    acepta: bool                   # §4 {acepta: true | false}


# POST retirado / entregado -> PedidoCompleto (ver nota). fn_cambiar_estado RETURNS VOID.


# POST /api/repartidor/ubicacion -> OkRespuesta (fn_registrar_ubicacion RETURNS VOID, BD §6)
class UbicacionIn(_Entrada):
    latitud: float
    longitud: float


# POST /api/repartidor/pedidos/{id}/calificar -> fn_calificar(id,'repartidor_a_cliente',...)
# §4 cuerpo {puntaje, comentario} (el tipo esta fijo en la ruta, no se manda).
class CalificarRepartidorIn(_Entrada):
    puntaje: int = Field(ge=1, le=5)            # CHECK 1-5 (BD §3)
    comentario: str | None = Field(default=None, max_length=300)  # VARCHAR(300) (NULL)
# Respuesta: CalificarOut (compartidos).


# GET /api/repartidor/historial (§4)
class RepartidorHistorialOut(_Salida):
    id_pedido: int
    fecha_creacion: datetime
    restaurante: str             # derivado: JOIN restaurante.nombre
    costo_envio: float
    propina: float
    estado_codigo: EstadoCodigo  # catalogo BD §4


# GET /api/repartidor/liquidaciones (§4) -> list[LiquidacionRow] (compartido con coordinador, BD §3)