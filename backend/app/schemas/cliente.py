"""CLIENTE de §4, fiel a roadmap_bd §3/§9. Importa catalogos de pedido.py (no los redefine)
y bases/HorarioItem/CalificarOut de compartidos. referencia/descripcion son (NULL) -> | None.
Las validaciones de entrada (gt/ge/pattern/max_length) espejan CHECK de FORMATO; la BD las
revalida (doble barrera) y NINGUNA calcula negocio (RNF-05)."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.compartidos import CalificarOut, HorarioItem, _Entrada, _Salida
from app.schemas.pedido import EstadoCodigo, Moneda  # catalogos ya en pedido.py

# Subconjunto de calificacion.tipo (BD §3) que el CLIENTE puede emitir (§4 lista 2 de 3).
TipoCalCliente = Literal["cliente_a_repartidor", "cliente_a_restaurante"]
# CHECK de cliente.cedula_rif (BD §3), combinado en un regex anclado.
_CEDULA_RIF = r"^(?:[VE]-[0-9]{6,9}|[VEJPG]-[0-9]{8}-[0-9])$"


# --- Direcciones (GET/POST /api/cliente/direcciones) ---
class DireccionOut(_Salida):
    id_direccion: int
    id_zona: int
    zona: str                  # derivado: JOIN zona.nombre
    direccion: str
    referencia: str | None     # (NULL) BD §3
    latitud: float
    longitud: float
    principal: bool


class DireccionIn(_Entrada):
    id_zona: int
    direccion: str = Field(max_length=200)
    referencia: str | None = None   # (NULL) en BD; el front puede mandar null u omitir
    latitud: float
    longitud: float
    principal: bool = False


class DireccionCreadaOut(_Salida):
    id_direccion: int


# --- Restaurantes (lista y detalle) ---
class RestauranteListaOut(_Salida):
    id_restaurante: int
    nombre: str
    categoria: str             # derivado: JOIN categoria.nombre
    direccion: str
    calificacion_promedio: float   # NUMERIC(3,2)
    tiempo_prep_min: int
    abierto_ahora: bool        # derivado: fn_restaurante_disponible (BD §5)
    distancia_km: float        # derivado: fn_distancia_km (BD §5)
    costo_envio: float         # derivado: fn_costo_envio (BD §5)


class RestauranteDetalleOut(_Salida):
    id_restaurante: int
    nombre: str
    categoria: str             # derivado: JOIN categoria.nombre
    direccion: str
    telefono: str
    calificacion_promedio: float
    tiempo_prep_min: int
    horario: list[HorarioItem]


# --- Menu / productos disponibles (solo disponibles, §4) ---
class ProductoClienteOut(_Salida):
    id_producto: int
    nombre: str
    descripcion: str | None    # (NULL) BD §3
    precio: float
    exento_iva: bool
    # disponible NO se expone aqui (§4 cliente/products lo usa como FILTRO, no campo).


# --- Recomendaciones (vw_recomendaciones_cliente; §4 NO expone id_cliente/ranking de §9) ---
class RecomendacionOut(_Salida):
    id_producto: int
    producto: str              # derivado: JOIN producto.nombre
    id_restaurante: int
    restaurante: str           # derivado: JOIN restaurante.nombre
    categoria: str             # derivado: JOIN categoria.nombre
    veces_pedido: int


# --- Cotizar / crear pedido ---
class ItemProductoIn(_Entrada):
    id_producto: int
    cantidad: int = Field(gt=0)    # espeja detalle_pedido.cantidad CHECK > 0 (BD §3)


class CotizarIn(_Entrada):
    id_restaurante: int
    id_direccion: int
    productos: list[ItemProductoIn]   # lista vacia la rechaza la BD (PRODUCTO_INVALIDO)
    propina: float = Field(ge=0)      # espeja pedido.propina CHECK >= 0 (BD §3)
    moneda_pago: Moneda               # catalogo pedido.moneda_pago (BD §3)


class CotizarOut(_Salida):
    # OJO: la cotizacion usa 'tasa_bcv' (nombre de fn_cotizar_pedido, BD §6),
    # NO 'tasa_bcv_aplicada' (columna de pedido, §3 backend).
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
    ultimos4: str = Field(pattern=r"^\d{4}$")   # espeja pago.ultimos4 CHECK (BD §3, RNF-09)


# --- Historial del cliente (GET /api/cliente/pedidos) ---
class PedidoResumenOut(_Salida):
    id_pedido: int
    fecha_creacion: datetime
    restaurante: str           # derivado: JOIN restaurante.nombre
    estado_codigo: EstadoCodigo  # catalogo pedido/estado (BD §4)
    estado_nombre: str
    total: float


# --- Calificar (POST /api/cliente/pedidos/{id}/calificar -> fn_calificar) ---
class CalificarIn(_Entrada):
    tipo: TipoCalCliente
    puntaje: int = Field(ge=1, le=5)            # espeja calificacion.puntaje CHECK 1-5 (BD §3)
    comentario: str | None = Field(default=None, max_length=300)  # VARCHAR(300) (NULL)
# Respuesta: CalificarOut (importado de compartidos, no definido aqui).


# --- Datos fiscales (PUT /api/cliente/datos-fiscales; §4 no fija respuesta -> OkRespuesta) ---
class DatosFiscalesIn(_Entrada):
    cedula_rif: str = Field(pattern=_CEDULA_RIF)   # espeja CHECK de cliente.cedula_rif (BD §3)