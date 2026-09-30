"""RESTAURANTE (roadmap_backend §4). Propiedad §2: id_restaurante = id_perfil del token.
fn_cambiar_estado = roadmap_bd §6 (UNICA via de estado); vw_facturas = §8b.
Horarios PUT = reemplazo completo (DELETE+INSERT en una transaccion).
Errores -> ErrorAPI (raiz {error,mensaje}, §0), NO HTTPException(detail=...) que anida
bajo 'detail' y rompe lo que lee el front (roadmap_frontend §0: 'mostrar siempre mensaje')."""
from fastapi import APIRouter, Depends          # sin HTTPException: ya no se usa
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores import ErrorAPI                 # fix 2: errores en raiz (§0)
from app.esquemas import (
    HorarioIn, HorarioItem, MotivoIn, OkRespuesta, PedidoCompleto, ProductoActualizarIn,
    ProductoCreadoOut, ProductoCrearIn, RestauranteProductoOut, VwFacturasRow,
)                                                # fix 5: HorarioItem en cabecera, no inline
from app.seguridad import requiere_rol
from app.services.pedido import armar_pedido_completo   # fix 1: sin prefijo 'backend.'

router = APIRouter(prefix="/api/restaurante", tags=["restaurante"])


def _check_pedido(db, id_pedido, id_restaurante):
    # Propiedad §2: el restaurante solo ve/cambia pedidos de SU restaurante -> 403 del MOSTRADOR.
    # Aqui .first() is None SI es caso de negocio (no es suyo) -> 403, no scalar_one.
    if db.execute(text("SELECT 1 FROM pedido WHERE id_pedido = :id AND id_restaurante = :r"),
                  {"id": id_pedido, "r": id_restaurante}).first() is None:
        raise ErrorAPI("SIN_PERMISO", "El pedido no es de este restaurante.", 403)   # fix 2


@router.get("/pedidos", response_model=list[PedidoCompleto])
def listar_pedidos(activos: bool = True, db: Session = Depends(get_db),
                   user: dict = Depends(requiere_rol("restaurante"))):
    estados = (1, 2, 3) if activos else (4, 5, 6)  # tablero vs historial (§4)
    ids = db.execute(text(
        "SELECT id_pedido FROM pedido WHERE id_restaurante = :r AND id_estado = ANY(:e) "
        "ORDER BY fecha_creacion DESC"
    ), {"r": user["id_perfil"], "e": list(estados)}).scalars().all()
    return [armar_pedido_completo(db, i) for i in ids]  # N+1 aceptable: pocos pedidos en {1,2,3} simultaneos por restaurante (ventana del tablero)


@router.post("/pedidos/{id}/aceptar", response_model=PedidoCompleto)
def aceptar(id: int, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("restaurante"))):
    _check_pedido(db, id, user["id_perfil"])
    db.execute(text("SELECT fn_cambiar_estado(:id, 2, :u)"), {"id": id, "u": int(user["sub"])})  # fix 4
    db.commit()
    return armar_pedido_completo(db, id)


@router.post("/pedidos/{id}/listo", response_model=PedidoCompleto)
def listo(id: int, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("restaurante"))):
    _check_pedido(db, id, user["id_perfil"])
    db.execute(text("SELECT fn_cambiar_estado(:id, 3, :u)"), {"id": id, "u": int(user["sub"])})  # fix 4
    db.commit()
    return armar_pedido_completo(db, id)


@router.post("/pedidos/{id}/cancelar", response_model=PedidoCompleto)
def cancelar(id: int, datos: MotivoIn, db: Session = Depends(get_db),
             user: dict = Depends(requiere_rol("restaurante"))):
    _check_pedido(db, id, user["id_perfil"])
    db.execute(text("SELECT fn_cambiar_estado(:id, 6, :u, :m)"),
               {"id": id, "u": int(user["sub"]), "m": datos.motivo})   # fix 4
    db.commit()
    return armar_pedido_completo(db, id)  # TRANSICION_INVALIDA propaga al handler global §0


@router.get("/productos", response_model=list[RestauranteProductoOut])
def listar_productos(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("restaurante"))):
    rows = db.execute(text("""
        SELECT id_producto, nombre, descripcion, precio, exento_iva, disponible
        FROM producto WHERE id_restaurante = :r ORDER BY id_producto
    """), {"r": user["id_perfil"]}).mappings().all()
    return [RestauranteProductoOut(**x) for x in rows]


@router.post("/productos", response_model=ProductoCreadoOut, status_code=201)
def crear_producto(datos: ProductoCrearIn, db: Session = Depends(get_db),
                   user: dict = Depends(requiere_rol("restaurante"))):
    # exento_iva FALSE y disponible TRUE son DEFAULT de la BD (§3); no los hardcodeo.
    id_prod = db.execute(text("""
        INSERT INTO producto (id_restaurante, nombre, descripcion, precio, exento_iva)
        VALUES (:r, :n, :d, :p, :e) RETURNING id_producto
    """), {"r": user["id_perfil"], "n": datos.nombre, "d": datos.descripcion,
           "p": datos.precio, "e": datos.exento_iva}).scalar_one()  # §3 PK SERIAL -> 1 valor
    db.commit()
    return ProductoCreadoOut(id_producto=id_prod)  # §4 responde {id_producto}


@router.put("/productos/{id}", response_model=OkRespuesta)
def actualizar_producto(id: int, datos: ProductoActualizarIn, db: Session = Depends(get_db),
                        user: dict = Depends(requiere_rol("restaurante"))):
    # fix 3: RETURNING id_producto evita Result.rowcount (no resuelve en SA 2.x) y es atomico.
    row = db.execute(text("""
        UPDATE producto SET nombre = :n, descripcion = :d, precio = :p, exento_iva = :e, disponible = :disp
        WHERE id_producto = :id AND id_restaurante = :r RETURNING id_producto
    """), {"n": datos.nombre, "d": datos.descripcion, "p": datos.precio,
           "e": datos.exento_iva, "disp": datos.disponible, "id": id, "r": user["id_perfil"]}).mappings().first()
    db.commit()
    if row is None:
        raise ErrorAPI("SIN_PERMISO", "El producto no es de este restaurante.", 403)   # B: 404->403, consistente con _check_pedido (mismo predicado id AND id_restaurante)
    return OkRespuesta()  # §4 no fija respuesta del PUT -> OkRespuesta (anotado al grupo)


@router.get("/horarios", response_model=list[HorarioItem])   # fix 5: tipo estricto (§4 forma)
def listar_horarios(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("restaurante"))):
    rows = db.execute(text(
        "SELECT dia_semana, hora_apertura, hora_cierre FROM horario_restaurante "
        "WHERE id_restaurante = :r ORDER BY dia_semana"
    ), {"r": user["id_perfil"]}).mappings().all()
    return [HorarioItem(**x) for x in rows]


@router.put("/horarios", response_model=OkRespuesta)
def reemplazar_horarios(datos: list[HorarioIn], db: Session = Depends(get_db),
                        user: dict = Depends(requiere_rol("restaurante"))):
    r = user["id_perfil"]
    with db.begin():  # transaccion atomica: DELETE + INSERT juntos (§4 "reemplaza el completo")
        db.execute(text("DELETE FROM horario_restaurante WHERE id_restaurante = :r"), {"r": r})
        for h in datos:
            db.execute(text("""
                INSERT INTO horario_restaurante (id_restaurante, dia_semana, hora_apertura, hora_cierre)
                VALUES (:r, :d, :a, :c)
            """), {"r": r, "d": h.dia_semana, "a": h.hora_apertura, "c": h.hora_cierre})
    return OkRespuesta()  # CHECK hora_cierre>hora_apertura y UNIQUE(prop,dia) propagan al handler §0


@router.get("/facturas", response_model=list[VwFacturasRow])
def mis_facturas(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("restaurante"))):
    # vw_facturas (§8b) es PLANA: una fila por factura -> no necesita armar_pedido_completo.
    rows = db.execute(text(
        "SELECT * FROM vw_facturas WHERE id_restaurante = :r ORDER BY fecha_emision DESC"
    ), {"r": user["id_perfil"]}).mappings().all()
    return [VwFacturasRow(**x) for x in rows]