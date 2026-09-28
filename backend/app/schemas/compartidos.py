"""Bases y catalogos TRANSVERSALES (no viven en pedido.py para no acoplar dominios).
Rol/Prioridad/DisponibilidadFull = CHECK de usuario/repartidor (roadmap_bd §3).
HorarioItem lo usan cliente y restaurante con la misma forma exacta de §4.
CalificarOut lo usan cliente y repartidor (fn_calificar RETURNS INT, BD §8)."""
from datetime import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# --- Bases técnicas (no son contrato; el guion bajo = privado, no se re-exporta) ---
class _Salida(BaseModel):
    # model_validate(fila de vista/Row). NO devolver ORM crudo (roadmap_backend §0).
    model_config = ConfigDict(from_attributes=True)


class _Entrada(BaseModel):
    # Base de cuerpos que el FRONT manda como JSON (nunca mapea fila).
    pass


# --- Catalogos de tablas que la §3 del pedido NO expone (regla del mapa) ---
Rol = Literal["cliente", "restaurante", "repartidor", "coordinador", "admin"]      # BD §3 usuario.rol
Prioridad = Literal["normal", "baja"]                                             # BD §3 repartidor.prioridad
DisponibilidadFull = Literal["libre", "ocupado", "desconectado"]                  # BD §3 repartidor.disponibilidad


# --- Salidas/entradas triviales compartidas por varios actores ---
class OkRespuesta(BaseModel):
    # {ok: true} para acciones sin entidad (responder oferta, ubicacion, datos-fiscales).
    ok: bool = True


class MotivoIn(_Entrada):
    # {motivo} para cancelar (restaurante/coordinador, §4). VARCHAR(200) BD §3.
    motivo: str = Field(min_length=1, max_length=200)


class HorarioItem(_Salida):
    # Espeja horario_restaurante (BD §3). dia_semana SMALLINT CHECK 0-6; hora_* TIME.
    dia_semana: int = Field(ge=0, le=6)   # 0 = domingo (EXTRACT(DOW), BD §3)
    hora_apertura: time                    # TIME (BD §3)
    hora_cierre: time                      # TIME (BD §3); CHECK cierre>apertura vive en BD


class CalificarOut(_Salida):
    # {id_calificacion} — fn_calificar RETURNS INT (BD §8); lo usan cliente y repartidor.
    id_calificacion: int