"""FACTURACION de §4 + columnas de roadmap_bd §8b/§9/§3. Contrato puro de LECTURA/entrada.
'numero_factura_afectada' e 'id_factura' (en pedido) son DERIVADOS por JOIN (no columnas de
la tabla que parece leer el endpoint), por eso van '| None' y el router los puebla con el
LEFT JOIN a factura (uq_factura_pedido, BD §8b). Los montos de vw_libro_ventas PUEDEN ser
negativos en nota_credito -> SIN ge=0. NO calcula negocio (RNF-05)."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.compartidos import _Salida
from app.schemas.pedido import Moneda  # catalogo pedido.moneda_pago (BD §3), no se redefine aqui

TipoFactura = Literal["factura_cliente", "factura_comision", "nota_credito"]   # BD §3 CHECK
EstadoFactura = Literal["emitida", "anulada"]                                  # BD §3 CHECK


# --- GET /api/facturas/{id}: 'todas las columnas de factura' + numero_afectada + detalle ---
class DetalleFacturaOut(_Salida):
    descripcion: str
    cantidad: float              # BD §8b: NUMERIC(10,2) (puede ser fraccion)
    precio_unitario: float
    alicuota_iva: float          # NUMERIC(5,2) CHECK IN (0,16)
    no_sujeto: bool              # TRUE solo propina (BD §8b)
    base_item: float
    iva_item: float
    subtotal_item: float


class FacturaOut(_Salida):
    # 30 columnas de factura (BD §3/§8b) + numero_factura_afectada (derivado) + detalle.
    id_factura: int
    tipo: TipoFactura
    numero_factura: str          # PPPP-NNNNNNNN
    numero_control: str          # PP-NNNNNN
    punto_venta: int
    estado: EstadoFactura
    id_cliente: int | None       # (NULL) BD §8b
    id_restaurante: int | None   # (NULL)
    id_pedido: int | None        # (NULL) solo factura_cliente
    id_factura_afectada: int | None   # (NULL) solo nota_credito
    numero_factura_afectada: str | None  # DERIVADO por JOIN (no es columna)
    rif_emisor: str
    razon_social_emisor: str
    direccion_fiscal_emisor: str
    rif_receptor: str | None     # (NULL) BD §8b
    razon_social_receptor: str
    direccion_fiscal_receptor: str | None  # (NULL)
    periodo_desde: date | None   # (NULL) solo factura_comision (DATE)
    periodo_hasta: date | None   # (NULL)
    moneda: Moneda
    tasa_bcv: float              # NUMERIC(14,4)
    base_imponible_16: float
    base_exenta: float
    monto_no_sujeto: float       # la propina
    iva_16: float
    igtf: float
    total: float
    total_ves: float             # NUMERIC(14,2)
    observaciones: str | None    # (NULL) motivo de la nota de credito
    id_usuario: int | None       # (NULL) quien la genero; NULL = sistema
    fecha_emision: datetime
    detalle: list[DetalleFacturaOut]


# --- GET /api/coordinador/facturas -> vw_facturas (BD §8b) ---
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


# --- GET /api/coordinador/libro-ventas -> vw_libro_ventas (notas en NEGATIVO, BD §8b) ---
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
    base_imponible_16: float     # pueden ser negativos en nota_credito: SIN ge=0
    base_exenta: float
    monto_no_sujeto: float
    iva_16: float
    igtf: float
    total: float
    total_ves: float


# --- GET /api/coordinador/resumen-iva -> vw_resumen_iva_mensual (BD §8b) ---
class VwResumenIvaRow(_Salida):
    periodo: str                 # texto 'YYYY-MM' (BD §8b)
    cantidad_documentos: int
    base_imponible_16: float
    base_exenta: float
    iva_debito: float
    igtf: float
    total: float
    total_ves: float


# --- liquidacion_repartidor (BD §3); usado por repartidor Y coordinador (§4) ---
class LiquidacionRow(_Salida):
    id_liquidacion: int
    numero: str                  # LIQ-NNNNNNNN
    periodo_desde: date          # DATE (BD §3)
    periodo_hasta: date          # DATE
    viajes: int
    total_envios: float
    total_propinas: float
    total: float
    fecha_emision: datetime


# --- Entradas de facturacion (§4) ---
class PeriodoIn(BaseModel):
    desde: date
    hasta: date


class AnularIn(BaseModel):
    motivo: str = Field(min_length=1, max_length=300)  # observaciones VARCHAR(300) (NULL) BD §8b


class CreadasOut(_Salida):
    creadas: int                 # {creadas: N} de fn_generar_facturas_comision / liquidaciones