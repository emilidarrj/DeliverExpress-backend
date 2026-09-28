"""COORDINADOR de §4 + columnas de roadmap_bd §9 (vistas) y §3 (tabla repartidor).
Contrato puro de LECTURA. NO calcula nada (RNF-05). Los endpoints que devuelven 'pedido
completo' reusan PedidoCompleto de pedido.py (no van aqui); aqui van las FILAS PLANAS de
las vistas, que §9 fija como contrato ("Las columnas listadas son contrato con el backend").
OJO: /api/coordinador/repartidores NO es vw_repartidores_disponibles (esa solo trae LIBRES);
es lectura de la TABLA repartidor (BD §3) WHERE activo, por eso trae disponibilidad/en_revision."""
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.compartidos import DisponibilidadFull, Prioridad, _Salida
from app.schemas.pedido import EstadoCodigo, TipoVehiculo


# --- GET /api/coordinador/pedidos-activos -> vw_pedidos_activos (BD §9) ---
class VwPedidosActivosRow(_Salida):
    id_pedido: int
    fecha_creacion: datetime
    id_estado: int
    estado_codigo: EstadoCodigo
    estado_nombre: str
    minutos_en_estado: int
    id_restaurante: int
    restaurante: str
    tiempo_prep_min: int
    restaurante_lat: float
    restaurante_lon: float
    id_cliente: int
    cliente: str
    direccion_entrega: str
    entrega_lat: float
    entrega_lon: float
    # el pedido puede estar SIN repartidor (pedido.id_repartidor (NULL), BD §3):
    id_repartidor: int | None
    repartidor: str | None
    repartidor_lat: float | None
    repartidor_lon: float | None
    tiempo_estimado_min: int | None      # pedido.tiempo_estimado_min (NULL), BD §3
    minutos_desde_creacion: int
    total: float


# --- GET /api/coordinador/repartidores (BD §3 tabla repartidor, NO la vista de libres) ---
class CoordinadorRepartidorRow(_Salida):
    id_repartidor: int
    nombre: str
    zona: str                  # derivado: JOIN zona.nombre
    tipo_vehiculo: TipoVehiculo
    disponibilidad: DisponibilidadFull
    prioridad: Prioridad
    calificacion_promedio: float
    latitud_actual: float | None   # (NULL) BD §3: repartidor sin posicion
    longitud_actual: float | None  # (NULL) BD §3
    en_revision: bool


# --- GET /api/coordinador/reportes/tiempos -> vw_tiempos_por_etapa (BD §9) ---
class VwTiemposRow(_Salida):
    id_pedido: int
    id_restaurante: int
    id_repartidor: int | None  # (NULL) si el pedido no llego a tener repartidor
    fecha_creacion: datetime
    min_espera_restaurante: int    # 1->2
    min_preparacion: int           # 2->3
    min_espera_retiro: int         # 3->4
    min_entrega: int               # 4->5
    min_total: int                 # 1->5


# --- GET /api/coordinador/reportes/restaurantes -> vw_desempeno_restaurantes (BD §9) ---
class VwDesempenoRestaurantesRow(_Salida):
    id_restaurante: int
    restaurante: str
    categoria: str
    total_pedidos: int
    pedidos_cancelados: int
    prom_min_preparacion: float
    calificacion_promedio: float
    ventas_productos: float


# --- GET /api/coordinador/reportes/repartidores -> vw_desempeno_repartidores (BD §9) ---
class VwDesempenoRepartidoresRow(_Salida):
    id_repartidor: int
    repartidor: str
    tipo_vehiculo: TipoVehiculo
    entregas: int
    prom_min_entrega: float
    ofertas_recibidas: int
    ofertas_rechazadas: int
    tasa_rechazo: float            # proporcion 0..1 (BD §8 trg_actualizar_prioridad)
    ganancias: float               # envio + propina
    calificacion_promedio: float
    prioridad: Prioridad
    en_revision: bool


# --- GET /api/coordinador/reportes/liquidacion -> vw_liquidacion (BD §9) ---
class VwLiquidacionRow(_Salida):
    fecha: date                    # BD §9: fecha (DATE)
    id_restaurante: int
    restaurante: str
    pedidos: int
    ventas_productos: float
    comision_plataforma: float
    monto_restaurante: float
    envios: float
    propinas: float


# --- GET /api/coordinador/revision (§4) ---
class RevisionClienteRow(_Salida):
    id_cliente: int
    nombre: str
    calificacion_promedio: float
    total_calificaciones: int


class RevisionRepartidorRow(_Salida):
    id_repartidor: int
    nombre: str
    calificacion_promedio: float
    total_calificaciones: int


class RevisionOut(_Salida):
    clientes: list[RevisionClienteRow]
    repartidores: list[RevisionRepartidorRow]


# --- Entradas de coordinador (§4) ---
class ReasignarIn(BaseModel):
    id_repartidor: int | None      # {id_repartidor: 5 | null} -> automatico si null (BD §6)
# cancelar reusa MotivoIn de compartidos.py: {motivo}.