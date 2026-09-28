"""PUBLICO de §4 (catalogos sin login). Espeja zona y categoria (BD §3). 
La respuesta de /zonas NO incluye descripcion (no esta en §4, aunque zona.descripcion
es (NULL) en BD §3 -> no se expone)."""

from app.schemas.compartidos import _Salida


class CategoriaOut(_Salida):
    id_categoria: int
    nombre: str


class ZonaOut(_Salida):
    id_zona: int
    nombre: str
    latitud_centro: float     # NUMERIC(9,6) -> float (transporte §3 backend)
    longitud_centro: float