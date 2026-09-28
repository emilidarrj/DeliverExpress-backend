"""AUTH de §4. id_perfil es NULL para admin (roadmap_bd §10 fn_login) -> int | None.
rol = catalogo usuario.rol (BD §3). Email como str para no tocar el requirements pinneado."""
from pydantic import BaseModel, Field

from app.schemas.compartidos import Rol


class LoginIn(BaseModel):
    email: str            # §4 no fija formato; BD solo VARCHAR(120) UNIQUE
    password: str


class LoginOut(BaseModel):
    token: str
    rol: Rol
    id_perfil: int | None  # NULL para admin (roadmap_bd §10)
    nombre: str


class RegistroClienteIn(BaseModel):
    email: str
    password: str
    nombre: str = Field(max_length=100)     # cliente.nombre VARCHAR(100) BD §3
    telefono: str = Field(max_length=20)    # cliente.telefono VARCHAR(20) BD §3
    cedula_rif: str | None = None           # §4 "(opcional)"; regex lo valida DatosFiscalesIn/BD


class RegistroClienteOut(BaseModel):
    id_cliente: int


class YoOut(BaseModel):
    id_usuario: int
    rol: Rol
    id_perfil: int | None  # NULL para admin (roadmap_bd §10)
    nombre: str