"""RESTAURANTE (roadmap_backend §4).

Propiedad §2: id_restaurante = id_perfil del token.

fn_cambiar_estado = roadmap_bd §6 (UNICA via de estado).
vw_facturas = §8b.

Horarios PUT = reemplazo completo (DELETE + INSERT en una transaccion).

Errores -> ErrorAPI (raiz {error,mensaje}, §0), NO HTTPException(detail=...)
que anida bajo 'detail' y rompe lo que lee el front.
"""

from fastapi import APIRouter, Depends

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores import ErrorAPI
from app.esquemas import (
    HorarioIn,
    HorarioItem,
    MotivoIn,
    OkRespuesta,
    PedidoCompleto,
    PerfilRestauranteIn,
    PerfilRestauranteOut,
    ProductoActualizarIn,
    ProductoCreadoOut,
    ProductoCrearIn,
    RestauranteProductoOut,
    VwFacturasRow,
)
from app.seguridad import requiere_rol
from app.services.pedido import armar_pedido_completo


router = APIRouter(
    prefix="/api/restaurante",
    tags=["restaurante"],
)


# =====================================================================
# VALIDACIONES INTERNAS
# =====================================================================

def _check_pedido(db, id_pedido, id_restaurante):
    """
    El restaurante solo puede ver o cambiar pedidos
    pertenecientes a su propio restaurante.
    """
    if db.execute(
        text("""
            SELECT 1
            FROM pedido
            WHERE id_pedido = :id
              AND id_restaurante = :r
        """),
        {
            "id": id_pedido,
            "r": id_restaurante,
        },
    ).first() is None:
        raise ErrorAPI(
            "SIN_PERMISO",
            "El pedido no es de este restaurante.",
            403,
        )


# =====================================================================
# PERFIL
# =====================================================================

@router.get(
    "/perfil",
    response_model=PerfilRestauranteOut,
)
def obtener_perfil(
    db: Session = Depends(get_db),
    user: dict = Depends(requiere_rol("restaurante")),
):
    """
    Obtiene los datos del restaurante autenticado.

    Propiedad §2:
    user["id_perfil"] = id_restaurante.

    El email pertenece a usuario, mientras que telefono, rif,
    nombre y razon_social pertenecen a restaurante.
    """

    row = db.execute(
        text("""
            SELECT
                r.id_restaurante,
                r.nombre,
                u.email,
                r.telefono,
                r.rif,
                r.razon_social
            FROM restaurante r
            JOIN usuario u
                ON u.id_usuario = r.id_usuario
            WHERE r.id_restaurante = :r
        """),
        {
            "r": user["id_perfil"],
        },
    ).mappings().first()

    if row is None:
        raise ErrorAPI(
            "NO_ENCONTRADO",
            "Perfil de restaurante no existe.",
            404,
        )

    return PerfilRestauranteOut(**row)


@router.put(
    "/perfil",
    response_model=PerfilRestauranteOut,
)
def actualizar_perfil(
    datos: PerfilRestauranteIn,
    db: Session = Depends(get_db),
    user: dict = Depends(requiere_rol("restaurante")),
):
    """
    Actualiza los datos editables del perfil del restaurante.

    Editables:
    - telefono
    - rif

    No se modifica:
    - nombre
    - email
    - razon_social

    Esto evita que la pantalla Mi Perfil cambie datos estructurales
    que actualmente administra el módulo de administración.
    """

    with db.begin():
        row = db.execute(
            text("""
                UPDATE restaurante
                SET telefono = :telefono,
                    rif = :rif
                WHERE id_restaurante = :r
                RETURNING
                    id_restaurante,
                    id_usuario,
                    nombre,
                    telefono,
                    rif,
                    razon_social
            """),
            {
                "telefono": datos.telefono,
                "rif": datos.rif,
                "r": user["id_perfil"],
            },
        ).mappings().first()

        if row is None:
            raise ErrorAPI(
                "NO_ENCONTRADO",
                "Perfil de restaurante no existe.",
                404,
            )

        usuario = db.execute(
            text("""
                SELECT email
                FROM usuario
                WHERE id_usuario = :u
            """),
            {
                "u": row["id_usuario"],
            },
        ).mappings().first()

        if usuario is None:
            raise ErrorAPI(
                "NO_ENCONTRADO",
                "Usuario del restaurante no existe.",
                404,
            )

    return PerfilRestauranteOut(
        id_restaurante=row["id_restaurante"],
        nombre=row["nombre"],
        email=usuario["email"],
        telefono=row["telefono"],
        rif=row["rif"],
        razon_social=row["razon_social"],
    )


# =====================================================================
# PEDIDOS
# =====================================================================

@router.get(
    "/pedidos",
    response_model=list[PedidoCompleto],
)
def listar_pedidos(
    activos: bool = True,
    db: Session = Depends(get_db),
    user: dict = Depends(requiere_rol("restaurante")),
):
    estados = (1, 2, 3) if activos else (4, 5, 6)

    ids = db.execute(
        text("""
            SELECT id_pedido
            FROM pedido
            WHERE id_restaurante = :r
              AND id_estado = ANY(:e)
            ORDER BY fecha_creacion DESC
        """),
        {
            "r": user["id_perfil"],
            "e": list(estados),
        },
    ).scalars().all()

    return [
        armar_pedido_completo(db, i)
        for i in ids
    ]


@router.post(
    "/pedidos/{id}/aceptar",
    response_model=PedidoCompleto,
)
def aceptar(
    id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(requiere_rol("restaurante")),
):
    _check_pedido(
        db,
        id,
        user["id_perfil"],
    )

    db.execute(
        text("""
            SELECT fn_cambiar_estado(:id, 2, :u)
        """),
        {
            "id": id,
            "u": int(user["sub"]),
        },
    )

    db.commit()

    return armar_pedido_completo(
        db,
        id,
    )


@router.post(
    "/pedidos/{id}/listo",
    response_model=PedidoCompleto,
)
def listo(
    id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(requiere_rol("restaurante")),
):
    _check_pedido(
        db,
        id,
        user["id_perfil"],
    )

    db.execute(
        text("""
            SELECT fn_cambiar_estado(:id, 3, :u)
        """),
        {
            "id": id,
            "u": int(user["sub"]),
        },
    )

    db.commit()

    return armar_pedido_completo(
        db,
        id,
    )


@router.post(
    "/pedidos/{id}/cancelar",
    response_model=PedidoCompleto,
)
def cancelar(
    id: int,
    datos: MotivoIn,
    db: Session = Depends(get_db),
    user: dict = Depends(requiere_rol("restaurante")),
):
    _check_pedido(
        db,
        id,
        user["id_perfil"],
    )

    db.execute(
        text("""
            SELECT fn_cambiar_estado(:id, 6, :u, :m)
        """),
        {
            "id": id,
            "u": int(user["sub"]),
            "m": datos.motivo,
        },
    )

    db.commit()

    return armar_pedido_completo(
        db,
        id,
    )


# =====================================================================
# PRODUCTOS
# =====================================================================

@router.get(
    "/productos",
    response_model=list[RestauranteProductoOut],
)
def listar_productos(
    db: Session = Depends(get_db),
    user: dict = Depends(requiere_rol("restaurante")),
):
    rows = db.execute(
        text("""
            SELECT
                id_producto,
                nombre,
                descripcion,
                precio,
                exento_iva,
                disponible
            FROM producto
            WHERE id_restaurante = :r
            ORDER BY id_producto
        """),
        {
            "r": user["id_perfil"],
        },
    ).mappings().all()

    return [
        RestauranteProductoOut(**x)
        for x in rows
    ]


@router.post(
    "/productos",
    response_model=ProductoCreadoOut,
    status_code=201,
)
def crear_producto(
    datos: ProductoCrearIn,
    db: Session = Depends(get_db),
    user: dict = Depends(requiere_rol("restaurante")),
):
    id_prod = db.execute(
        text("""
            INSERT INTO producto (
                id_restaurante,
                nombre,
                descripcion,
                precio,
                exento_iva
            )
            VALUES (
                :r,
                :n,
                :d,
                :p,
                :e
            )
            RETURNING id_producto
        """),
        {
            "r": user["id_perfil"],
            "n": datos.nombre,
            "d": datos.descripcion,
            "p": datos.precio,
            "e": datos.exento_iva,
        },
    ).scalar_one()

    db.commit()

    return ProductoCreadoOut(
        id_producto=id_prod,
    )


@router.put(
    "/productos/{id}",
    response_model=OkRespuesta,
)
def actualizar_producto(
    id: int,
    datos: ProductoActualizarIn,
    db: Session = Depends(get_db),
    user: dict = Depends(requiere_rol("restaurante")),
):
    row = db.execute(
        text("""
            UPDATE producto
            SET
                nombre = :n,
                descripcion = :d,
                precio = :p,
                exento_iva = :e,
                disponible = :disp
            WHERE id_producto = :id
              AND id_restaurante = :r
            RETURNING id_producto
        """),
        {
            "n": datos.nombre,
            "d": datos.descripcion,
            "p": datos.precio,
            "e": datos.exento_iva,
            "disp": datos.disponible,
            "id": id,
            "r": user["id_perfil"],
        },
    ).mappings().first()

    db.commit()

    if row is None:
        raise ErrorAPI(
            "SIN_PERMISO",
            "El producto no es de este restaurante.",
            403,
        )

    return OkRespuesta()


# =====================================================================
# HORARIOS
# =====================================================================

@router.get(
    "/horarios",
    response_model=list[HorarioItem],
)
def listar_horarios(
    db: Session = Depends(get_db),
    user: dict = Depends(requiere_rol("restaurante")),
):
    rows = db.execute(
        text("""
            SELECT
                dia_semana,
                hora_apertura,
                hora_cierre
            FROM horario_restaurante
            WHERE id_restaurante = :r
            ORDER BY dia_semana
        """),
        {
            "r": user["id_perfil"],
        },
    ).mappings().all()

    return [
        HorarioItem(**x)
        for x in rows
    ]


@router.put(
    "/horarios",
    response_model=OkRespuesta,
)
def reemplazar_horarios(
    datos: list[HorarioIn],
    db: Session = Depends(get_db),
    user: dict = Depends(requiere_rol("restaurante")),
):
    r = user["id_perfil"]

    with db.begin():
        db.execute(
            text("""
                DELETE FROM horario_restaurante
                WHERE id_restaurante = :r
            """),
            {
                "r": r,
            },
        )

        for h in datos:
            db.execute(
                text("""
                    INSERT INTO horario_restaurante (
                        id_restaurante,
                        dia_semana,
                        hora_apertura,
                        hora_cierre
                    )
                    VALUES (
                        :r,
                        :d,
                        :a,
                        :c
                    )
                """),
                {
                    "r": r,
                    "d": h.dia_semana,
                    "a": h.hora_apertura,
                    "c": h.hora_cierre,
                },
            )

    return OkRespuesta()


# =====================================================================
# FACTURAS
# =====================================================================

@router.get(
    "/facturas",
    response_model=list[VwFacturasRow],
)
def mis_facturas(
    db: Session = Depends(get_db),
    user: dict = Depends(requiere_rol("restaurante")),
):
    rows = db.execute(
        text("""
            SELECT *
            FROM vw_facturas
            WHERE id_restaurante = :r
            ORDER BY fecha_emision DESC
        """),
        {
            "r": user["id_perfil"],
        },
    ).mappings().all()

    return [
        VwFacturasRow(**x)
        for x in rows
    ]