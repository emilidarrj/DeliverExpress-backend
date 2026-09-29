"""AUTH (roadmap_backend §4). fn_login/fn_registrar_cliente = roadmap_bd §10.
id_perfil NULL para admin (§10) -> crear_token acepta int | None (ver seguridad.py).
Errores de auth: raise HTTPException con detail dict; el handler de errores.py los
pone en raiz como {error,mensaje} (§0). /yo usa get_current_user (cualquiera logueado,
§4), NO requiere_rol (eso es para endpoints de actor con rol especifico)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas import (
    LoginIn, LoginOut, RegistroClienteIn, RegistroClienteOut, YoOut,
)
from app.seguridad import crear_token, get_current_user   # nombre REAL de seguridad.py

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/registro-cliente", response_model=RegistroClienteOut, status_code=201)
def registrar_cliente(datos: RegistroClienteIn, db: Session = Depends(get_db)):
    id_cliente = db.execute(text(
        "SELECT fn_registrar_cliente(:e, :p, :n, :t, :c)"
    ), {"e": datos.email, "p": datos.password, "n": datos.nombre,
        "t": datos.telefono, "c": datos.cedula_rif}).scalar_one()
    db.commit()
    return RegistroClienteOut(id_cliente=id_cliente)  # EMAIL_REPETIDO propaga -> handler global 400


@router.post("/login", response_model=LoginOut)
def login(datos: LoginIn, db: Session = Depends(get_db)):
    row = db.execute(text(
        "SELECT id_usuario, rol, id_perfil, nombre FROM fn_login(:e, :p)"
    ), {"e": datos.email, "p": datos.password}).mappings().first()
    if row is None:  # §2: si no devuelve filas -> 401
        raise HTTPException(status_code=401, detail={
            "error": "NO_AUTENTICADO", "mensaje": "Email o clave incorrectos"})
    # crear_token toma POSICIONALES (id_usuario, rol, id_perfil, nombre); NO existe 'sub=':
    # el claim sub lo arma crear_token por dentro con str(id_usuario).
    token = crear_token(row["id_usuario"], row["rol"], row["id_perfil"], row["nombre"])
    return LoginOut(token=token, rol=row["rol"], id_perfil=row["id_perfil"], nombre=row["nombre"])


@router.get("/yo", response_model=YoOut)
def yo(user: dict = Depends(get_current_user)):
    # sub viene como str (crear_token hace str(id_usuario)); int() explicito por robustez.
    return YoOut(id_usuario=int(user["sub"]), rol=user["rol"],
                 id_perfil=user["id_perfil"], nombre=user["nombre"])