"""Autenticacion JWT y control de rol. roadmap_backend.txt §2."""
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, Header

from app.config import settings
from app.errores import ErrorAPI

_ALG = "HS256"


def crear_token(id_usuario: int, rol: str, id_perfil: int, nombre: str) -> str:
    """Arma el JWT con las claims pactadas. sub va como string (estandar JWT)."""
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(id_usuario),
        "rol": rol,
        "id_perfil": id_perfil,
        "nombre": nombre,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.jwt_expira_min),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALG)


def get_current_user(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Devuelve el payload del token o lanza 401. El front manda: Bearer <token>."""
    if not authorization or not authorization.startswith("Bearer "):
        raise ErrorAPI("NO_AUTENTICADO", "Credenciales ausentes o invalidas.", 401)
    token = authorization.split(" ", 1)[1].strip()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[_ALG])
    except jwt.ExpiredSignatureError:
        raise ErrorAPI("TOKEN_EXPIRADO", "Sesion expirada. Inicia sesion de nuevo.", 401)
    except jwt.InvalidTokenError:
        raise ErrorAPI("TOKEN_INVALIDO", "Token invalido.", 401)


def requiere_rol(*roles: str):
    """Dependencia fabrica: exige que el rol del token este en 'roles'.
    Uso:  user = Depends(requiere_rol("cliente"))
          user = Depends(requiere_rol("coordinador", "admin"))
    """
    def _dep(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user.get("rol") not in roles:
            raise ErrorAPI("SIN_PERMISO", "No tienes permiso para esta accion.", 403)
        return user
    return _dep