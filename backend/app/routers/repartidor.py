"""REPARTIDOR (roadmap_backend §4). Propiedad §2: id_repartidor = id_perfil del token."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores import ErrorAPI
from app.esquemas import (
    CalificarOut, CalificarRepartidorIn, DisponibilidadIn, LiquidacionRow, OkRespuesta,
    OfertaPendienteOut, PedidoCompleto, RepartidorHistorialOut, RepartidorYoOut,
    ResponderOfertaIn, UbicacionIn,
)
from app.seguridad import requiere_rol
from app.services.pedido import armar_pedido_completo

router = APIRouter(prefix="/api/repartidor", tags=["repartidor"])


def _check_pedido(db, id_pedido, id_repartidor):
    if db.execute(text("SELECT 1 FROM pedido WHERE id_pedido = :id AND id_repartidor = :r"),
                  {"id": id_pedido, "r": id_repartidor}).first() is None:
        raise ErrorAPI("SIN_PERMISO", "El pedido no esta asignado a este repartidor.", 403)


@router.get("/yo", response_model=RepartidorYoOut)
def yo(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("repartidor"))):
    row = db.execute(text("SELECT id_repartidor, nombre, tipo_vehiculo, disponibilidad, prioridad, calificacion_promedio, en_revision FROM repartidor WHERE id_repartidor = :r"),
                     {"r": user["id_perfil"]}).mappings().first()
    if row is None:
        raise ErrorAPI("NO_ENCONTRADO", "Repartidor no existe.", 404)
    return RepartidorYoOut(**row)


@router.put("/disponibilidad", response_model=OkRespuesta)
def disponibilidad(datos: DisponibilidadIn, db: Session = Depends(get_db),
                   user: dict = Depends(requiere_rol("repartidor"))):
    row = db.execute(text("UPDATE repartidor SET disponibilidad = :d WHERE id_repartidor = :r AND disponibilidad <> 'ocupado' RETURNING id_repartidor"),
                     {"d": datos.disponibilidad, "r": user["id_perfil"]}).mappings().first()
    db.commit()
    if row is None:
        raise ErrorAPI("SIN_PERMISO", "No puede cambiar disponibilidad estando ocupado.", 403)
    return OkRespuesta()


@router.get("/oferta-pendiente", response_model=OfertaPendienteOut | None)
def oferta_pendiente(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("repartidor"))):
    o = db.execute(text("""
        SELECT id_oferta, fecha_oferta, distancia_km, id_pedido,
               (fn_param_num('oferta_expira_seg') - EXTRACT(EPOCH FROM (now() - fecha_oferta)))::INT AS segundos_restantes
        FROM oferta_asignacion
        WHERE id_repartidor = :r AND respuesta = 'pendiente'
        ORDER BY fecha_oferta DESC LIMIT 1
    """), {"r": user["id_perfil"]}).mappings().first()
    if o is None:
        return None
    pedido = armar_pedido_completo(db, o["id_pedido"])
    if pedido is None:
        raise ErrorAPI("ERROR_INTERNO", "Invariante rota: oferta con pedido inexistente (FK §3).", 500)
    return OfertaPendienteOut(id_oferta=o["id_oferta"], fecha_oferta=o["fecha_oferta"],
                              segundos_restantes=max(o["segundos_restantes"], 0),
                              distancia_km=o["distancia_km"], pedido=pedido)


@router.post("/ofertas/{id}/responder", response_model=OkRespuesta)
def responder(id: int, datos: ResponderOfertaIn, db: Session = Depends(get_db),
              user: dict = Depends(requiere_rol("repartidor"))):
    if db.execute(text("SELECT 1 FROM oferta_asignacion WHERE id_oferta = :id AND id_repartidor = :r"),
                  {"id": id, "r": user["id_perfil"]}).first() is None:
        raise ErrorAPI("SIN_PERMISO", "La oferta no es del repartidor.", 403)
    db.execute(text("SELECT fn_responder_oferta(:id, :a)"), {"id": id, "a": datos.acepta})
    db.commit()
    return OkRespuesta()


@router.get("/pedido-actual", response_model=PedidoCompleto | None)
def pedido_actual(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("repartidor"))):
    id_pedido = db.execute(text("SELECT id_pedido FROM pedido WHERE id_repartidor = :r AND id_estado IN (2,3,4) ORDER BY fecha_creacion DESC LIMIT 1"),
                           {"r": user["id_perfil"]}).scalar()
    return armar_pedido_completo(db, id_pedido) if id_pedido else None


@router.post("/pedidos/{id}/retirado", response_model=PedidoCompleto)
def retirado(id: int, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("repartidor"))):
    _check_pedido(db, id, user["id_perfil"])
    db.execute(text("SELECT fn_cambiar_estado(:id, 4, :u)"), {"id": id, "u": int(user["sub"])})
    db.commit()
    return armar_pedido_completo(db, id)


@router.post("/pedidos/{id}/entregado", response_model=PedidoCompleto)
def entregado(id: int, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("repartidor"))):
    _check_pedido(db, id, user["id_perfil"])
    db.execute(text("SELECT fn_cambiar_estado(:id, 5, :u)"), {"id": id, "u": int(user["sub"])})
    db.commit()
    return armar_pedido_completo(db, id)


@router.post("/ubicacion", response_model=OkRespuesta)
def ubicacion(datos: UbicacionIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("repartidor"))):
    db.execute(text("SELECT fn_registrar_ubicacion(:r, :la, :lo)"),
               {"r": user["id_perfil"], "la": datos.latitud, "lo": datos.longitud})
    db.commit()
    return OkRespuesta()


@router.post("/pedidos/{id}/calificar", response_model=CalificarOut)
def calificar(id: int, datos: CalificarRepartidorIn, db: Session = Depends(get_db),
              user: dict = Depends(requiere_rol("repartidor"))):
    _check_pedido(db, id, user["id_perfil"])
    id_cal = db.execute(text("SELECT fn_calificar(:id, 'repartidor_a_cliente', :p, :co)"),
                        {"id": id, "p": datos.puntaje, "co": datos.comentario}).scalar_one()
    db.commit()
    return CalificarOut(id_calificacion=id_cal)


@router.get("/historial", response_model=list[RepartidorHistorialOut])
def historial(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("repartidor"))):
    rows = db.execute(text("""
        SELECT p.id_pedido, p.fecha_creacion, r.nombre AS restaurante, p.costo_envio, p.propina, e.codigo AS estado_codigo
        FROM pedido p JOIN restaurante r ON r.id_restaurante = p.id_restaurante
        JOIN estado_pedido e ON e.id_estado = p.id_estado
        WHERE p.id_repartidor = :r AND p.id_estado IN (5,6) ORDER BY p.fecha_creacion DESC
    """), {"r": user["id_perfil"]}).mappings().all()
    return [RepartidorHistorialOut(**x) for x in rows]


@router.get("/liquidaciones", response_model=list[LiquidacionRow])
def liquidaciones(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("repartidor"))):
    rows = db.execute(text("SELECT id_liquidacion, numero, periodo_desde, periodo_hasta, viajes, total_envios, total_propinas, total, fecha_emision FROM liquidacion_repartidor WHERE id_repartidor = :r ORDER BY periodo_desde DESC"),
                      {"r": user["id_perfil"]}).mappings().all()
    return [LiquidacionRow(**x) for x in rows]