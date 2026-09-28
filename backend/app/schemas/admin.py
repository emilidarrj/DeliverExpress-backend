"""ADMIN de §4. Las RUTAS las fija §4; los CUERPOS/CAMPOS que §4 no repite se derivan de las
TABLAS de roadmap_bd §3 (que §0 backend declara "mismos nombres de columnas"). Email como str.
Las entradas espejan CHECK de FORMATO (precio>0, cedula/rif regex, ultimos4); la BD revalida
(doble barrera). NO calcula negocio (RNF-05)."""
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.compartidos import DisponibilidadFull, Prioridad, _Entrada, _Salida
from app.schemas.pedido import TipoVehiculo

_CEDULA = r"^[VE]-[0-9]{6,9}$"            # BD §3 repartidor.cedula CHECK
_RIF = r"^[VEJPG]-[0-9]{8}-[0-9]$"        # BD §3 restaurante.rif CHECK


# --- Zonas (BD §3 zona) ---
class ZonaAdminOut(_Salida):
    id_zona: int
    nombre: str
    descripcion: str | None      # (NULL) BD §3
    latitud_centro: float
    longitud_centro: float


class ZonaAdminIn(_Entrada):
    nombre: str = Field(max_length=80)
    descripcion: str | None = None
    latitud_centro: float
    longitud_centro: float


# --- Categorias (BD §3 categoria) ---
class CategoriaAdminOut(_Salida):
    id_categoria: int
    nombre: str


class CategoriaAdminIn(_Entrada):
    nombre: str = Field(max_length=60)


# --- Tarifas (BD §3 tarifa_envio; CHECK km_hasta>km_desde vive en BD, no se replica) ---
class TarifaAdminOut(_Salida):
    id_tarifa: int
    km_desde: float
    km_hasta: float
    precio: float


class TarifaAdminIn(_Entrada):
    km_desde: float
    km_hasta: float
    precio: float = Field(gt=0)  # BD §3 CHECK precio > 0


# --- Parametros (BD §3 parametro_sistema; PUT /parametros/{clave} {valor}) ---
class ParametroOut(_Salida):
    clave: str
    valor: str
    descripcion: str | None      # (NULL) BD §3


class ParametroIn(_Entrada):
    valor: str = Field(max_length=100)   # BD §3 valor VARCHAR(100)


# --- Tasas BCV (BD §3 tasa_bcv; §4 expone fecha, tasa_usd, fecha_registro) ---
class TasaBcvOut(_Salida):
    fecha: date                  # DATE UNIQUE (BD §3)
    tasa_usd: float              # NUMERIC(14,4)
    fecha_registro: datetime     # TIMESTAMPTZ


class TasaBcvIn(_Entrada):
    fecha: date
    tasa_usd: float = Field(gt=0)  # BD §3 CHECK tasa_usd > 0


# --- Restaurantes (BD §3 restaurante + restaurante_zona; §4 POST/PUT fijan campos) ---
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
    zonas: list[int]             # derivado: ids de restaurante_zona (BD §3); front marca casillas


class RestauranteAdminIn(_Entrada):
    # §4 POST: email, password, nombre, id_categoria, direccion, telefono, latitud,
    #          longitud, tiempo_prep_min, rif, razon_social, direccion_fiscal, zonas
    email: str
    password: str
    nombre: str = Field(max_length=100)
    id_categoria: int
    direccion: str = Field(max_length=200)
    telefono: str = Field(max_length=20)
    latitud: float
    longitud: float
    tiempo_prep_min: int = Field(gt=0)   # BD §3 CHECK > 0
    rif: str = Field(pattern=_RIF)       # BD §3 CHECK regex
    razon_social: str = Field(max_length=150)
    direccion_fiscal: str = Field(max_length=250)
    zonas: list[int]


class RestauranteAdminPutIn(_Entrada):
    # §4 PUT: mismos campos sin email/password + activo
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


# --- Repartidores (BD §3 repartidor; §4 POST/PUT fijan campos) ---
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
    latitud_actual: float | None   # (NULL) BD §3
    longitud_actual: float | None  # (NULL) BD §3
    calificacion_promedio: float
    total_calificaciones: int
    en_revision: bool
    activo: bool


class RepartidorAdminIn(_Entrada):
    # §4 POST: email, password, nombre, telefono, cedula, tipo_vehiculo, id_zona
    email: str
    password: str
    nombre: str = Field(max_length=100)
    telefono: str = Field(max_length=20)
    cedula: str = Field(pattern=_CEDULA)   # BD §3 CHECK regex
    tipo_vehiculo: TipoVehiculo
    id_zona: int


class RepartidorAdminPutIn(_Entrada):
    # §4 PUT: nombre, telefono, cedula, tipo_vehiculo, id_zona, activo
    nombre: str = Field(max_length=100)
    telefono: str = Field(max_length=20)
    cedula: str = Field(pattern=_CEDULA)
    tipo_vehiculo: TipoVehiculo
    id_zona: int
    activo: bool


# --- Coordinadores (BD §3 coordinador; §4 POST fijan campos) ---
class CoordinadorAdminOut(_Salida):
    id_coordinador: int
    id_usuario: int
    nombre: str
    telefono: str


class CoordinadorAdminIn(_Entrada):
    # §4 POST: email, password, nombre, telefono
    email: str
    password: str
    nombre: str = Field(max_length=100)
    telefono: str = Field(max_length=20)


# --- Usuarios: PUT /api/admin/usuarios/{id}/activo {activo} (§4) ---
class UsuarioActivoIn(_Entrada):
    activo: bool