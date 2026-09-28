"""RESTAURANTE de §4, fiel a roadmap_bd §3. Anida PedidoCompleto (ya congelado) para los
endpoints de pedidos. Producto de restaurante SÍ expone 'disponible' (§4 restaurante/products),
a diferencia del de cliente que lo usa solo como filtro. Las entradas espejan CHECK de formato
(precio>0); la BD revalida. NO calcula negocio (RNF-05). GET /facturas reusa VwFacturasRow
(de facturas.py) en el router, no se define schema extra aqui."""
from datetime import time
from pydantic import BaseModel, Field

from app.schemas.compartidos import HorarioItem, MotivoIn, _Entrada, _Salida
from app.schemas.pedido import PedidoCompleto


# GET /api/restaurante/pedidos?activos=true|false -> list[PedidoCompleto] (§4).
# POST aceptar / listo / cancelar -> PedidoCompleto actualizado (§4 restaurante).
# cancelar cuerpo {motivo} -> MotivoIn (compartidos).


# --- Productos (GET/POST/PUT /api/restaurante/productos) ---
class RestauranteProductoOut(_Salida):
    id_producto: int
    nombre: str
    descripcion: str | None    # (NULL) BD §3
    precio: float
    exento_iva: bool
    disponible: bool           # §4 restaurante/products SÍ lo expone (interruptor del front)


class ProductoCrearIn(_Entrada):
    nombre: str = Field(max_length=100)
    descripcion: str | None = None      # (NULL) BD §3; opcional en el formulario
    precio: float = Field(gt=0)         # espeja producto.precio CHECK > 0 (BD §3)
    exento_iva: bool = False            # default BD §3


class ProductoActualizarIn(_Entrada):
    nombre: str = Field(max_length=100)
    descripcion: str | None = None
    precio: float = Field(gt=0)
    exento_iva: bool
    disponible: bool


class ProductoCreadoOut(_Salida):
    id_producto: int


# --- Horarios (GET/PUT /api/restaurante/horarios) ---
# GET -> list[HorarioItem] (compartidos). PUT reemplaza el horario completo -> list[HorarioIn].
class HorarioIn(_Entrada):
    dia_semana: int = Field(ge=0, le=6)
    hora_apertura: time         # TIME (BD §3); Pydantic coeerce "08:00" -> time al validar
    hora_cierre: time
    # CHECK hora_cierre>hora_apertura (BD §3) NO se replica: lo valida la BD (RNF-05).