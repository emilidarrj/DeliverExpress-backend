"""COORDINADOR (roadmap_backend §4) [coordinador, admin]. Lee vw_* (§9) y tabla repartidor (§3)."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores import ErrorAPI
from app.esquemas import (
    CoordinadorRepartidorRow, MotivoIn, OkRespuesta, PedidoCompleto, ReasignarIn,
    RevisionClienteRow, RevisionOut, RevisionRepartidorRow, VwDesempenoRepartidoresRow,
    VwDesempenoRestaurantesRow, VwLiquidacionRow, VwPedidosActivosRow, VwTiemposRow,
)
from app.seguridad import requiere_rol
from app.services.pedido import armar_pedido_completo

router = APIRouter(prefix="/api/coordinador", tags=["coordinador"])
_ROL = ("coordinador", "admin")


def _existe_pedido(db, id_pedido):
    if db.execute(text("SELECT 1 FROM pedido WHERE id_pedido = :id"), {"id": id_pedido}).first() is None:
        raise ErrorAPI("NO_ENCONTRADO", "Pedido no existe.", 404)


@router.get("/pedidos-activos", response_model=list[VwPedidosActivosRow])
def pedidos_activos(db: Session = Depends(get_db), user: dict = Depends(requiere_rol(*_ROL))):
    rows = db.execute(text("SELECT * FROM vw_pedidos_activos ORDER BY fecha_creacion")).mappings().all()
    return [VwPedidosActivosRow(**r) for r in rows]


@router.get("/repartidores", response_model=list[CoordinadorRepartidorRow])
def repartidores(db: Session = Depends(get_db), user: dict = Depends(requiere_rol(*_ROL))):
    rows = db.execute(text("""
        SELECT rp.id_repartidor, rp.nombre, z.nombre AS zona, rp.tipo_vehiculo, rp.disponibilidad,
               rp.prioridad, rp.calificacion_promedio, rp.latitud_actual, rp.longitud_actual, rp.en_revision
        FROM repartidor rp JOIN zona z ON z.id_zona = rp.id_zona
        WHERE rp.activo = TRUE ORDER BY rp.nombre
    """)).mappings().all()
    return [CoordinadorRepartidorRow(**r) for r in rows]


@router.post("/pedidos/{id}/reasignar", response_model=OkRespuesta)
def reasignar(id: int, datos: ReasignarIn, db: Session = Depends(get_db),
              user: dict = Depends(requiere_rol(*_ROL))):
    _existe_pedido(db, id)
    db.execute(text("SELECT fn_reasignar_pedido(:id, :rep, :u)"),
               {"id": id, "rep": datos.id_repartidor, "u": int(user["sub"])})
    db.commit()
    return OkRespuesta()


@router.post("/pedidos/{id}/cancelar", response_model=OkRespuesta)
def cancelar(id: int, datos: MotivoIn, db: Session = Depends(get_db),
             user: dict = Depends(requiere_rol(*_ROL))):
    _existe_pedido(db, id)
    db.execute(text("SELECT fn_cambiar_estado(:id, 6, :u, :m)"),
               {"id": id, "u": int(user["sub"]), "m": datos.motivo})
    db.commit()
    return OkRespuesta()


@router.get("/pedidos/{id}", response_model=PedidoCompleto)
def detalle_pedido(id: int, db: Session = Depends(get_db), user: dict = Depends(requiere_rol(*_ROL))):
    pedido = armar_pedido_completo(db, id)
    if pedido is None:
        raise ErrorAPI("NO_ENCONTRADO", "Pedido no existe.", 404)
    return pedido


@router.get("/reportes/tiempos", response_model=list[VwTiemposRow])
def reportes_tiempos(desde: date | None = Query(None), hasta: date | None = Query(None),
                     db: Session = Depends(get_db), user: dict = Depends(requiere_rol(*_ROL))):
    rows = db.execute(text("""
        SELECT * FROM vw_tiempos_por_etapa
        WHERE (:desde IS NULL OR fecha_creacion >= :desde::date)
          AND (:hasta IS NULL OR fecha_creacion < (:hasta::date + interval '1 day'))
        ORDER BY fecha_creacion
    """), {"desde": desde, "hasta": hasta}).mappings().all()
    return [VwTiemposRow(**r) for r in rows]


@router.get("/reportes/restaurantes", response_model=list[VwDesempenoRestaurantesRow])
def reportes_restaurantes(db: Session = Depends(get_db), user: dict = Depends(requiere_rol(*_ROL))):
    rows = db.execute(text("SELECT * FROM vw_desempeno_restaurantes ORDER BY id_restaurante")).mappings().all()
    return [VwDesempenoRestaurantesRow(**r) for r in rows]


@router.get("/reportes/repartidores", response_model=list[VwDesempenoRepartidoresRow])
def reportes_repartidores(db: Session = Depends(get_db), user: dict = Depends(requiere_rol(*_ROL))):
    rows = db.execute(text("SELECT * FROM vw_desempeno_repartidores ORDER BY id_repartidor")).mappings().all()
    return [VwDesempenoRepartidoresRow(**r) for r in rows]


@router.get("/reportes/liquidacion", response_model=list[VwLiquidacionRow])
def reportes_liquidacion(desde: date | None = Query(None), hasta: date | None = Query(None),
                         db: Session = Depends(get_db), user: dict = Depends(requiere_rol(*_ROL))):
    rows = db.execute(text("""
        SELECT * FROM vw_liquidacion
        WHERE (:desde IS NULL OR fecha >= :desde) AND (:hasta IS NULL OR fecha <= :hasta)
        ORDER BY fecha
    """), {"desde": desde, "hasta": hasta}).mappings().all()
    return [VwLiquidacionRow(**r) for r in rows]


@router.get("/revision", response_model=RevisionOut)
def revision(db: Session = Depends(get_db), user: dict = Depends(requiere_rol(*_ROL))):
    cl = db.execute(text("SELECT id_cliente, nombre, calificacion_promedio, total_calificaciones FROM cliente WHERE en_revision = TRUE ORDER BY calificacion_promedio")).mappings().all()
    rp = db.execute(text("SELECT id_repartidor, nombre, calificacion_promedio, total_calificaciones FROM repartidor WHERE en_revision = TRUE ORDER BY calificacion_promedio")).mappings().all()
    return RevisionOut(clientes=[RevisionClienteRow(**x) for x in cl],
                       repartidores=[RevisionRepartidorRow(**x) for x in rp])