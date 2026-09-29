"""Ensamblo del PedidoCompleto anidado (roadmap_backend §3). SOLO LEE: hace JOINs a
estado/restaurante/cliente/direccion/repartidor/producto/factura/calificacion y arma el
objeto. NO calcula totales, IVA, comision ni distancias (RNF-05: eso vive en fn_*).
Hallazgo A: no existe fn_pedido_completo en roadmap_bd; si el Int.2 lo agrega, se
reemplaza el cuerpo por SELECT * FROM fn_pedido_completo(:id) y los routers no se tocan."""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.esquemas import (
    ClienteResumen, DetallePedido, DireccionResumen, HistorialEstado,
    PedidoCompleto, RepartidorResumen, RestauranteResumen,
)


def armar_pedido_completo(db: Session, id_pedido: int) -> PedidoCompleto | None:
    cab = db.execute(text("""
        SELECT p.id_pedido, p.id_estado, e.codigo AS estado_codigo, e.nombre AS estado_nombre,
               p.fecha_creacion, p.subtotal, p.costo_envio, p.propina, p.iva_total, p.igtf,
               p.total, p.moneda_pago, p.tasa_bcv_aplicada, p.total_ves, p.distancia_km,
               p.tiempo_estimado_min, p.motivo_cancelacion,
               p.id_restaurante, p.id_cliente, p.id_direccion, p.id_repartidor
        FROM pedido p
        JOIN estado_pedido e ON e.id_estado = p.id_estado
        WHERE p.id_pedido = :id
    """), {"id": id_pedido}).mappings().first()
    if cab is None:
        return None

    rest = db.execute(text(
        "SELECT id_restaurante, nombre, telefono, latitud, longitud FROM restaurante WHERE id_restaurante = :r"
    ), {"r": cab["id_restaurante"]}).mappings().one()
    cli = db.execute(text(
        "SELECT id_cliente, nombre, telefono FROM cliente WHERE id_cliente = :c"
    ), {"c": cab["id_cliente"]}).mappings().one()
    dir_ = db.execute(text(
        "SELECT id_direccion, direccion, referencia, latitud, longitud FROM direccion_cliente WHERE id_direccion = :d"
    ), {"d": cab["id_direccion"]}).mappings().one()

    rep = None
    if cab["id_repartidor"] is not None:
        rp = db.execute(text(
            "SELECT id_repartidor, nombre, telefono, tipo_vehiculo, calificacion_promedio, "
            "latitud_actual, longitud_actual FROM repartidor WHERE id_repartidor = :rp"
        ), {"rp": cab["id_repartidor"]}).mappings().first()
        rep = RepartidorResumen(**rp) if rp else None

    det = db.execute(text("""
        SELECT dp.id_producto, pr.nombre, dp.cantidad, dp.precio_unitario, dp.subtotal
        FROM detalle_pedido dp JOIN producto pr ON pr.id_producto = dp.id_producto
        WHERE dp.id_pedido = :id ORDER BY dp.id_producto
    """), {"id": id_pedido}).mappings().all()

    hist = db.execute(text("""
        SELECT h.id_estado, e.codigo AS estado_codigo, e.nombre AS estado_nombre, h.fecha_hora
        FROM historial_estado_pedido h JOIN estado_pedido e ON e.id_estado = h.id_estado
        WHERE h.id_pedido = :id ORDER BY h.fecha_hora
    """), {"id": id_pedido}).mappings().all()

    fac = db.execute(text(
        "SELECT id_factura FROM factura WHERE id_pedido = :id AND tipo = 'factura_cliente'"
    ), {"id": id_pedido}).scalar()  # uq_factura_pedido => 0 o 1 fila

    cals = [r["tipo"] for r in db.execute(text(
        "SELECT tipo FROM calificacion WHERE id_pedido = :id"
    ), {"id": id_pedido}).mappings().all()]

    return PedidoCompleto(
        id_pedido=cab["id_pedido"], id_estado=cab["id_estado"],
        estado_codigo=cab["estado_codigo"], estado_nombre=cab["estado_nombre"],
        fecha_creacion=cab["fecha_creacion"],
        subtotal=cab["subtotal"], costo_envio=cab["costo_envio"], propina=cab["propina"],
        iva_total=cab["iva_total"], igtf=cab["igtf"], total=cab["total"],
        moneda_pago=cab["moneda_pago"], tasa_bcv_aplicada=cab["tasa_bcv_aplicada"],
        total_ves=cab["total_ves"], id_factura=fac, distancia_km=cab["distancia_km"],
        tiempo_estimado_min=cab["tiempo_estimado_min"], motivo_cancelacion=cab["motivo_cancelacion"],
        restaurante=RestauranteResumen(**rest), cliente=ClienteResumen(**cli),
        direccion=DireccionResumen(**dir_), repartidor=rep,
        detalle=[DetallePedido(**r) for r in det],
        historial=[HistorialEstado(**r) for r in hist],
        calificaciones_hechas=cals,
    )