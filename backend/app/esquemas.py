from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# =====================================================================
# 1. BASES TÉCNICAS Y CATÁLOGOS
# =====================================================================
class _Salida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class _Entrada(BaseModel):
    pass

Rol = Literal["cliente", "restaurante", "repartidor", "coordinador", "admin"]
Prioridad = Literal["normal", "baja"]
DisponibilidadFull = Literal["libre", "ocupado", "desconectado"]

EstadoCodigo = Literal[
    "recibido", "en_preparacion", "listo_para_retirar",
    "en_camino", "entregado", "cancelado",
]
TipoVehiculo = Literal["bicicleta", "moto", "auto"]
Moneda = Literal["USD", "VES"]
TipoCalificacion = Literal[
    "cliente_a_repartidor", "cliente_a_restaurante", "repartidor_a_cliente",
]

# Expresiones regulares compartidas
_CEDULA = r"^[VE]-[0-9]{6,9}$"
_RIF = r"^[VEJPG]-[0-9]{8}-[0-9]$"
_CEDULA_RIF = r"^(?:[VE]-[0-9]{6,9}|[VEJPG]-[0-9]{8}-[0-9])$"


# =====================================================================
# 2. ESQUEMAS COMPARTIDOS GENÉRICOS
# =====================================================================
class OkRespuesta(BaseModel):
    ok: bool = True

class MotivoIn(_Entrada):
    motivo: str = Field(min_length=1, max_length=200)

class HorarioItem(_Salida):
    dia_semana: int = Field(ge=0, le=6)
    hora_apertura: time
    hora_cierre: time

class CalificarOut(_Salida):
    id_calificacion: int


# =====================================================================
# 3. ENTIDADES BASE PARA PEDIDO COMPLETO
# =====================================================================
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
    referencia: str | None
    latitud: float
    longitud: float

class RepartidorResumen(_Salida):
    id_repartidor: int
    nombre: str
    telefono: str
    tipo_vehiculo: TipoVehiculo
    calificacion_promedio: float
    latitud_actual: float | None
    longitud_actual: float | None

class DetallePedido(_Salida):
    id_producto: int
    nombre: str
    cantidad: int
    precio_unitario: float
    subtotal: float

class HistorialEstado(_Salida):
    id_estado: int
    estado_codigo: EstadoCodigo
    estado_nombre: str
    fecha_hora: datetime

class PedidoCompleto(_Salida):
    id_pedido: int
    id_estado: int
    estado_codigo: EstadoCodigo
    estado_nombre: str
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

    id_factura: int | None
    distancia_km: float
    tiempo_estimado_min: int | None
    motivo_cancelacion: str | None

    restaurante: RestauranteResumen
    cliente: ClienteResumen
    direccion: DireccionResumen
    repartidor: RepartidorResumen | None
    detalle: list[DetallePedido]
    historial: list[HistorialEstado]
    calificaciones_hechas: list[TipoCalificacion]


# =====================================================================
# 4. AUTH
# =====================================================================
class LoginIn(BaseModel):
    email: str
    password: str

class LoginOut(BaseModel):
    token: str
    rol: Rol
    id_perfil: int | None
    nombre: str

class RegistroClienteIn(BaseModel):
    email: str
    password: str
    nombre: str = Field(max_length=100)
    telefono: str = Field(max_length=20)
    cedula_rif: str | None = None

class RegistroClienteOut(BaseModel):
    id_cliente: int

class YoOut(BaseModel):
    id_usuario: int
    rol: Rol
    id_perfil: int | None
    nombre: str


# =====================================================================
# 5. PÚBLICO
# =====================================================================
class CategoriaOut(_Salida):
    id_categoria: int
    nombre: str

class ZonaOut(_Salida):
    id_zona: int
    nombre: str
    latitud_centro: float
    longitud_centro: float


# =====================================================================
# 6. ADMIN
# =====================================================================
class ZonaAdminOut(_Salida):
    id_zona: int
    nombre: str
    descripcion: str | None
    latitud_centro: float
    longitud_centro: float

class ZonaAdminIn(_Entrada):
    nombre: str = Field(max_length=80)
    descripcion: str | None = None
    latitud_centro: float
    longitud_centro: float

class CategoriaAdminOut(_Salida):
    id_categoria: int
    nombre: str

class CategoriaAdminIn(_Entrada):
    nombre: str = Field(max_length=60)

class TarifaAdminOut(_Salida):
    id_tarifa: int
    km_desde: float
    km_hasta: float
    precio: float

class TarifaAdminIn(_Entrada):
    km_desde: float
    km_hasta: float
    precio: float = Field(gt=0)

class ParametroOut(_Salida):
    clave: str
    valor: str
    descripcion: str | None

class ParametroIn(_Entrada):
    valor: str = Field(max_length=100)

class TasaBcvOut(_Salida):
    fecha: date
    tasa_usd: float
    fecha_registro: datetime

class TasaBcvIn(_Entrada):
    fecha: date
    tasa_usd: float = Field(gt=0)

class RestauranteAdminOut(_Salida):
    id_restaurante: int
    id_usuario: int
    id_categoria: int
    nombre: str
    direccion: str
    telefono: str
    latitud: float
    longitud: float
    tiempo_prep_min: int
    rif: str
    razon_social: str
    direccion_fiscal: str
    calificacion_promedio: float
    total_calificaciones: int
    activo: bool
    zonas: list[int]

class RestauranteAdminIn(_Entrada):
    email: str
    password: str
    nombre: str = Field(max_length=100)
    id_categoria: int
    direccion: str = Field(max_length=200)
    telefono: str = Field(max_length=20)
    latitud: float
    longitud: float
    tiempo_prep_min: int = Field(gt=0)
    rif: str = Field(pattern=_RIF)
    razon_social: str = Field(max_length=150)
    direccion_fiscal: str = Field(max_length=250)
    zonas: list[int]

class RestauranteAdminPutIn(_Entrada):
    nombre: str = Field(max_length=100)
    id_categoria: int
    direccion: str = Field(max_length=200)
    telefono: str = Field(max_length=20)
    latitud: float
    longitud: float
    tiempo_prep_min: int = Field(gt=0)
    rif: str = Field(pattern=_RIF)
    razon_social: str = Field(max_length=150)
    direccion_fiscal: str = Field(max_length=250)
    zonas: list[int]
    activo: bool

class RepartidorAdminOut(_Salida):
    id_repartidor: int
    id_usuario: int
    id_zona: int
    nombre: str
    telefono: str
    cedula: str
    tipo_vehiculo: TipoVehiculo
    disponibilidad: DisponibilidadFull
    prioridad: Prioridad
    latitud_actual: float | None
    longitud_actual: float | None
    calificacion_promedio: float
    total_calificaciones: int
    en_revision: bool
    activo: bool

class RepartidorAdminIn(_Entrada):
    email: str
    password: str
    nombre: str = Field(max_length=100)
    telefono: str = Field(max_length=20)
    cedula: str = Field(pattern=_CEDULA)
    tipo_vehiculo: TipoVehiculo
    id_zona: int

class RepartidorAdminPutIn(_Entrada):
    nombre: str = Field(max_length=100)
    telefono: str = Field(max_length=20)
    cedula: str = Field(pattern=_CEDULA)
    tipo_vehiculo: TipoVehiculo
    id_zona: int
    activo: bool

class CoordinadorAdminOut(_Salida):
    id_coordinador: int
    id_usuario: int
    nombre: str
    telefono: str

class CoordinadorAdminIn(_Entrada):
    email: str
    password: str
    nombre: str = Field(max_length=100)
    telefono: str = Field(max_length=20)

class UsuarioActivoIn(_Entrada):
    activo: bool


# =====================================================================
# 7. CLIENTE
# =====================================================================
TipoCalCliente = Literal["cliente_a_repartidor", "cliente_a_restaurante"]

class DireccionOut(_Salida):
    id_direccion: int
    id_zona: int
    zona: str
    direccion: str
    referencia: str | None
    latitud: float
    longitud: float
    principal: bool

class DireccionIn(_Entrada):
    id_zona: int
    direccion: str = Field(max_length=200)
    referencia: str | None = None
    latitud: float
    longitud: float
    principal: bool = False

class DireccionCreadaOut(_Salida):
    id_direccion: int

class RestauranteListaOut(_Salida):
    id_restaurante: int
    nombre: str
    categoria: str
    direccion: str
    calificacion_promedio: float
    tiempo_prep_min: int
    abierto_ahora: bool
    distancia_km: float
    costo_envio: float

class RestauranteDetalleOut(_Salida):
    id_restaurante: int
    nombre: str
    categoria: str
    direccion: str
    telefono: str
    calificacion_promedio: float
    tiempo_prep_min: int
    horario: list[HorarioItem]

class ProductoClienteOut(_Salida):
    id_producto: int
    nombre: str
    descripcion: str | None
    precio: float
    exento_iva: bool

class RecomendacionOut(_Salida):
    id_producto: int
    producto: str
    id_restaurante: int
    restaurante: str
    categoria: str
    veces_pedido: int

class ItemProductoIn(_Entrada):
    id_producto: int
    cantidad: int = Field(gt=0)

class CotizarIn(_Entrada):
    id_restaurante: int
    id_direccion: int
    productos: list[ItemProductoIn]
    propina: float = Field(ge=0)
    moneda_pago: Moneda

class CotizarOut(_Salida):
    distancia_km: float
    subtotal: float
    costo_envio: float
    propina: float
    iva_total: float
    igtf: float
    total: float
    tasa_bcv: float
    total_ves: float

class CrearPedidoIn(_Entrada):
    id_restaurante: int
    id_direccion: int
    productos: list[ItemProductoIn]
    propina: float = Field(ge=0)
    moneda_pago: Moneda
    ultimos4: str = Field(pattern=r"^\d{4}$")

class PedidoResumenOut(_Salida):
    id_pedido: int
    fecha_creacion: datetime
    restaurante: str
    estado_codigo: EstadoCodigo
    estado_nombre: str
    total: float

class CalificarIn(_Entrada):
    tipo: TipoCalCliente
    puntaje: int = Field(ge=1, le=5)
    comentario: str | None = Field(default=None, max_length=300)


# ← CAMBIO 1: ahora acepta telefono además de cedula_rif
class DatosFiscalesIn(_Entrada):
    cedula_rif: str = Field(pattern=_CEDULA_RIF)
    telefono: str | None = Field(default=None, max_length=20)


# =====================================================================
# 8. COORDINADOR
# =====================================================================
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
    id_repartidor: int | None
    repartidor: str | None
    repartidor_lat: float | None
    repartidor_lon: float | None
    tiempo_estimado_min: int | None
    minutos_desde_creacion: int
    total: float

class CoordinadorRepartidorRow(_Salida):
    id_repartidor: int
    nombre: str
    zona: str
    tipo_vehiculo: TipoVehiculo
    disponibilidad: DisponibilidadFull
    prioridad: Prioridad
    calificacion_promedio: float
    latitud_actual: float | None
    longitud_actual: float | None
    en_revision: bool

class VwTiemposRow(_Salida):
    id_pedido: int
    id_restaurante: int
    id_repartidor: int | None
    fecha_creacion: datetime
    min_espera_restaurante: int
    min_preparacion: int
    min_espera_retiro: int
    min_entrega: int
    min_total: int

class VwDesempenoRestaurantesRow(_Salida):
    id_restaurante: int
    restaurante: str
    categoria: str
    total_pedidos: int
    pedidos_cancelados: int
    prom_min_preparacion: float
    calificacion_promedio: float
    ventas_productos: float

class VwDesempenoRepartidoresRow(_Salida):
    id_repartidor: int
    repartidor: str
    tipo_vehiculo: TipoVehiculo
    entregas: int
    prom_min_entrega: float
    ofertas_recibidas: int
    ofertas_rechazadas: int
    tasa_rechazo: float
    ganancias: float
    calificacion_promedio: float
    prioridad: Prioridad
    en_revision: bool

class VwLiquidacionRow(_Salida):
    fecha: date
    id_restaurante: int
    restaurante: str
    pedidos: int
    ventas_productos: float
    comision_plataforma: float
    monto_restaurante: float
    envios: float
    propinas: float

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

class ReasignarIn(BaseModel):
    id_repartidor: int | None


# =====================================================================
# 9. FACTURACIÓN
# =====================================================================
TipoFactura = Literal["factura_cliente", "factura_comision", "nota_credito"]
EstadoFactura = Literal["emitida", "anulada"]

class DetalleFacturaOut(_Salida):
    descripcion: str
    cantidad: float
    precio_unitario: float
    alicuota_iva: float
    no_sujeto: bool
    base_item: float
    iva_item: float
    subtotal_item: float

class FacturaOut(_Salida):
    id_factura: int
    tipo: TipoFactura
    numero_factura: str
    numero_control: str
    punto_venta: int
    estado: EstadoFactura
    id_cliente: int | None
    id_restaurante: int | None
    id_pedido: int | None
    id_factura_afectada: int | None
    numero_factura_afectada: str | None
    rif_emisor: str
    razon_social_emisor: str
    direccion_fiscal_emisor: str
    rif_receptor: str | None
    razon_social_receptor: str
    direccion_fiscal_receptor: str | None
    periodo_desde: date | None
    periodo_hasta: date | None
    moneda: Moneda
    tasa_bcv: float
    base_imponible_16: float
    base_exenta: float
    monto_no_sujeto: float
    iva_16: float
    igtf: float
    total: float
    total_ves: float
    observaciones: str | None
    id_usuario: int | None
    fecha_emision: datetime
    detalle: list[DetalleFacturaOut]

class VwFacturasRow(_Salida):
    id_factura: int
    tipo: TipoFactura
    numero_factura: str
    numero_control: str
    estado: EstadoFactura
    fecha_emision: datetime
    id_cliente: int | None
    id_restaurante: int | None
    id_pedido: int | None
    razon_social_receptor: str
    moneda: Moneda
    total: float
    total_ves: float

class VwLibroVentasRow(_Salida):
    fecha_emision: datetime
    tipo: TipoFactura
    numero_factura: str
    numero_control: str
    estado: EstadoFactura
    numero_factura_afectada: str | None
    rif_receptor: str | None
    razon_social_receptor: str
    moneda: Moneda
    tasa_bcv: float
    base_imponible_16: float
    base_exenta: float
    monto_no_sujeto: float
    iva_16: float
    igtf: float
    total: float
    total_ves: float

class VwResumenIvaRow(_Salida):
    periodo: str
    cantidad_documentos: int
    base_imponible_16: float
    base_exenta: float
    iva_debito: float
    igtf: float
    total: float
    total_ves: float

class LiquidacionRow(_Salida):
    id_liquidacion: int
    numero: str
    periodo_desde: date
    periodo_hasta: date
    viajes: int
    total_envios: float
    total_propinas: float
    total: float
    fecha_emision: datetime

class LiquidacionAdminRow(_Salida):
    id_liquidacion: int
    numero: str
    id_repartidor: int
    repartidor: str
    periodo_desde: date
    periodo_hasta: date
    viajes: int
    total_envios: float
    total_propinas: float
    total: float
    fecha_emision: datetime

class PeriodoIn(BaseModel):
    desde: date
    hasta: date

class AnularIn(BaseModel):
    motivo: str = Field(min_length=1, max_length=300)

class AnularOut(_Salida):
    id_factura: int

class CreadasOut(_Salida):
    creadas: int


# =====================================================================
# 10. REPARTIDOR
# =====================================================================
DisponibilidadSet = Literal["libre", "desconectado"]

class RepartidorYoOut(_Salida):
    id_repartidor: int
    nombre: str
    tipo_vehiculo: TipoVehiculo
    disponibilidad: DisponibilidadFull
    prioridad: Prioridad
    calificacion_promedio: float
    en_revision: bool

class DisponibilidadIn(_Entrada):
    disponibilidad: DisponibilidadSet

class OfertaPendienteOut(_Salida):
    id_oferta: int
    fecha_oferta: datetime
    segundos_restantes: int
    distancia_km: float
    pedido: PedidoCompleto

class ResponderOfertaIn(_Entrada):
    acepta: bool

class UbicacionIn(_Entrada):
    latitud: float
    longitud: float

class CalificarRepartidorIn(_Entrada):
    puntaje: int = Field(ge=1, le=5)
    comentario: str | None = Field(default=None, max_length=300)

class RepartidorHistorialOut(_Salida):
    id_pedido: int
    fecha_creacion: datetime
    restaurante: str
    costo_envio: float
    propina: float
    estado_codigo: EstadoCodigo


# =====================================================================
# 11. RESTAURANTE
# =====================================================================
class RestauranteProductoOut(_Salida):
    id_producto: int
    nombre: str
    descripcion: str | None
    precio: float
    exento_iva: bool
    disponible: bool

class ProductoCrearIn(_Entrada):
    nombre: str = Field(max_length=100)
    descripcion: str | None = None
    precio: float = Field(gt=0)
    exento_iva: bool = False

class ProductoActualizarIn(_Entrada):
    nombre: str = Field(max_length=100)
    descripcion: str | None = None
    precio: float = Field(gt=0)
    exento_iva: bool
    disponible: bool

class ProductoCreadoOut(_Salida):
    id_producto: int

class HorarioIn(_Entrada):
    dia_semana: int = Field(ge=0, le=6)
    hora_apertura: time
    hora_cierre: time


# ← CAMBIO 2: se agregó cedula_rif
class PerfilClienteOut(BaseModel):
    id_cliente: int
    nombre: str
    email: str
    telefono: str
    cedula_rif: str | None = None