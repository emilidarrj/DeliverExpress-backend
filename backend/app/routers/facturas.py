"""FACTURACION (roadmap_backend §4). Propiedad multi-rol ramificada por rol (no OR). Errores -> ErrorAPI."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores import ErrorAPI
from app.esquemas import (
    AnularIn, AnularOut, CreadasOut, DetalleFacturaOut, FacturaOut, LiquidacionAdminRow,
    PeriodoIn, VwFacturasRow, VwLibroVentasRow, VwResumenIvaRow,
)
from app.seguridad import get_current_user, requiere_rol

router = APIRouter(tags=["facturacion"])
_ROL = ("coordinador", "admin")


@router.get("/api/facturas/{id_factura}", response_model=FacturaOut)
def ver_factura(id_factura: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    f = db.execute(text("""
        SELECT f.*, af.numero_factura AS numero_factura_afectada
        FROM factura f LEFT JOIN factura af ON af.id_factura = f.id_factura_afectada
        WHERE f.id_factura = :id
    """), {"id": id_factura}).mappings().first()
    if f is None:
        raise ErrorAPI("NO_ENCONTRADO", "Factura no existe.", 404)
    rol = user["rol"]
    if rol == "cliente" and f["id_cliente"] != user["id_perfil"]:
        raise ErrorAPI("SIN_PERMISO", "La factura no es del cliente.", 403)
    if rol == "restaurante" and f["id_restaurante"] != user["id_perfil"]:
        raise ErrorAPI("SIN_PERMISO", "La factura no es del restaurante.", 403)
    if rol not in ("cliente", "restaurante", "coordinador", "admin"):
        raise ErrorAPI("SIN_PERMISO", "Rol sin acceso a facturas.", 403)
    det = db.execute(text("SELECT descripcion, cantidad, precio_unitario, alicuota_iva, no_sujeto, base_item, iva_item, subtotal_item FROM detalle_factura WHERE id_factura = :id ORDER BY id_detalle"),
                     {"id": id_factura}).mappings().all()
    return FacturaOut(**f, detalle=[DetalleFacturaOut(**d) for d in det])


@router.get("/api/coordinador/facturas", response_model=list[VwFacturasRow])
def listar_facturas(tipo: str | None = Query(None), desde: date | None = Query(None),
                    hasta: date | None = Query(None), db: Session = Depends(get_db),
                    user: dict = Depends(requiere_rol(*_ROL))):
    rows = db.execute(text("""
        SELECT * FROM vw_facturas
        WHERE (:tipo IS NULL OR tipo = :tipo)
          AND (:desde IS NULL OR fecha_emision >= :desde::date)
          AND (:hasta IS NULL OR fecha_emision < (:hasta::date + interval '1 day'))
        ORDER BY fecha_emision DESC
    """), {"tipo": tipo, "desde": desde, "hasta": hasta}).mappings().all()
    return [VwFacturasRow(**r) for r in rows]


@router.post("/api/coordinador/facturas/{id_factura}/anular", response_model=AnularOut)
def anular(id_factura: int, datos: AnularIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol(*_ROL))):
    id_nota = db.execute(text("SELECT fn_anular_factura(:id, :m, :u)"), {"id": id_factura, "m": datos.motivo, "u": int(user["sub"])}).scalar_one()
    db.commit()
    return AnularOut(id_factura=id_nota)


@router.get("/api/coordinador/libro-ventas", response_model=list[VwLibroVentasRow])
def libro_ventas(desde: date | None = Query(None), hasta: date | None = Query(None),
                 db: Session = Depends(get_db), user: dict = Depends(requiere_rol(*_ROL))):
    rows = db.execute(text("""
        SELECT * FROM vw_libro_ventas
        WHERE (:desde IS NULL OR fecha_emision >= :desde::date)
          AND (:hasta IS NULL OR fecha_emision < (:hasta::date + interval '1 day'))
        ORDER BY fecha_emision
    """), {"desde": desde, "hasta": hasta}).mappings().all()
    return [VwLibroVentasRow(**r) for r in rows]


@router.get("/api/coordinador/resumen-iva", response_model=list[VwResumenIvaRow])
def resumen_iva(db: Session = Depends(get_db), user: dict = Depends(requiere_rol(*_ROL))):
    rows = db.execute(text("SELECT * FROM vw_resumen_iva_mensual ORDER BY periodo")).mappings().all()
    return [VwResumenIvaRow(**r) for r in rows]


@router.get("/api/coordinador/liquidaciones", response_model=list[LiquidacionAdminRow])
def liquidaciones(desde: date | None = Query(None), hasta: date | None = Query(None),
                  db: Session = Depends(get_db), user: dict = Depends(requiere_rol(*_ROL))):
    rows = db.execute(text("""
        SELECT l.id_liquidacion, l.numero, l.id_repartidor, rp.nombre AS repartidor, l.periodo_desde, l.periodo_hasta,
               l.viajes, l.total_envios, l.total_propinas, l.total, l.fecha_emision
        FROM liquidacion_repartidor l JOIN repartidor rp ON rp.id_repartidor = l.id_repartidor
        WHERE (:desde IS NULL OR l.fecha_emision >= :desde::date)
          AND (:hasta IS NULL OR l.fecha_emision < (:hasta::date + interval '1 day'))
        ORDER BY l.fecha_emision DESC
    """), {"desde": desde, "hasta": hasta}).mappings().all()
    return [LiquidacionAdminRow(**r) for r in rows]


@router.post("/api/admin/facturacion/comisiones", response_model=CreadasOut)
def generar_comisiones(datos: PeriodoIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    n = db.execute(text("SELECT fn_generar_facturas_comision(:d, :h, :u)"), {"d": datos.desde, "h": datos.hasta, "u": int(user["sub"])}).scalar_one()
    db.commit()
    return CreadasOut(creadas=n)


@router.post("/api/admin/facturacion/liquidaciones", response_model=CreadasOut)
def generar_liquidaciones(datos: PeriodoIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    n = db.execute(text("SELECT fn_generar_liquidaciones(:d, :h)"), {"d": datos.desde, "h": datos.hasta}).scalar_one()
    db.commit()
    return CreadasOut(creadas=n)