"""CLIENTE (roadmap_backend §4). Propiedad §2 por id_perfil del token."""
import json

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores import ErrorAPI
from app.esquemas import (
    CalificarIn, CalificarOut, CotizarIn, CotizarOut, CrearPedidoIn,
    DatosFiscalesIn, DireccionCreadaOut, DireccionIn, DireccionOut, HorarioItem,
    PedidoCompleto, PedidoResumenOut, ProductoClienteOut, RecomendacionOut,
    RestauranteDetalleOut, RestauranteListaOut, OkRespuesta,
)
from app.seguridad import requiere_rol
from app.services.pedido import armar_pedido_completo

router = APIRouter(prefix="/api/cliente", tags=["cliente"])


@router.get("/direcciones", response_model=list[DireccionOut])
def listar_direcciones(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("cliente"))):
    rows = db.execute(text("""
        SELECT d.id_direccion, d.id_zona, z.nombre AS zona, d.direccion, d.referencia, d.latitud, d.longitud, d.principal
        FROM direccion_cliente d JOIN zona z ON z.id_zona = d.id_zona
        WHERE d.id_cliente = :c ORDER BY d.principal DESC, d.id_direccion
    """), {"c": user["id_perfil"]}).mappings().all()
    return [DireccionOut(**r) for r in rows]


@router.post("/direcciones", response_model=DireccionCreadaOut, status_code=201)
def crear_direccion(datos: DireccionIn, db: Session = Depends(get_db),
                    user: dict = Depends(requiere_rol("cliente"))):
    id_dir = db.execute(text("""
        INSERT INTO direccion_cliente (id_cliente, id_zona, direccion, referencia, latitud, longitud, principal)
        VALUES (:c, :z, :d, :r, :la, :lo, :p) RETURNING id_direccion
    """), {"c": user["id_perfil"], "z": datos.id_zona, "d": datos.direccion,
           "r": datos.referencia, "la": datos.latitud, "lo": datos.longitud,
           "p": datos.principal}).scalar_one()
    db.commit()
    return DireccionCreadaOut(id_direccion=id_dir)


@router.get("/restaurantes", response_model=list[RestauranteListaOut])
def listar_restaurantes(id_direccion: int, id_categoria: int | None = None,
                        db: Session = Depends(get_db), user: dict = Depends(requiere_rol("cliente"))):
    dir_ = db.execute(text("SELECT id_zona, latitud, longitud FROM direccion_cliente WHERE id_direccion = :d AND id_cliente = :c"),
                      {"d": id_direccion, "c": user["id_perfil"]}).mappings().first()
    if dir_ is None:
        raise ErrorAPI("SIN_PERMISO", "La direccion no es del cliente.", 403)
    rows = db.execute(text("""
        SELECT r.id_restaurante, r.nombre, c.nombre AS categoria, r.direccion, r.calificacion_promedio, r.tiempo_prep_min,
               fn_restaurante_disponible(r.id_restaurante, :d) AS abierto_ahora,
               fn_distancia_km(r.latitud, r.longitud, :rlat, :rlon) AS distancia_km,
               fn_costo_envio(fn_distancia_km(r.latitud, r.longitud, :rlat, :rlon)) AS costo_envio
        FROM restaurante r JOIN categoria c ON c.id_categoria = r.id_categoria
        JOIN restaurante_zona rz ON rz.id_restaurante = r.id_restaurante
        WHERE r.activo = TRUE AND rz.id_zona = :z AND (:cat IS NULL OR r.id_categoria = :cat)
        ORDER BY r.nombre
    """), {"z": dir_["id_zona"], "rlat": dir_["latitud"], "rlon": dir_["longitud"],
           "d": id_direccion, "cat": id_categoria}).mappings().all()
    return [RestauranteListaOut(**r) for r in rows]


@router.get("/restaurantes/{id}", response_model=RestauranteDetalleOut)
def detalle_restaurante(id: int, db: Session = Depends(get_db),
                        user: dict = Depends(requiere_rol("cliente"))):
    r = db.execute(text("""
        SELECT r.id_restaurante, r.nombre, c.nombre AS categoria, r.direccion, r.telefono, r.calificacion_promedio, r.tiempo_prep_min
        FROM restaurante r JOIN categoria c ON c.id_categoria = r.id_categoria
        WHERE r.id_restaurante = :id
    """), {"id": id}).mappings().first()
    if r is None:
        raise ErrorAPI("NO_ENCONTRADO", "Restaurante no existe.", 404)
    hor = db.execute(text("SELECT dia_semana, hora_apertura, hora_cierre FROM horario_restaurante WHERE id_restaurante = :id ORDER BY dia_semana"),
                     {"id": id}).mappings().all()
    return RestauranteDetalleOut(**r, horario=[HorarioItem(**h) for h in hor])


@router.get("/restaurantes/{id}/productos", response_model=list[ProductoClienteOut])
def productos_restaurante(id: int, db: Session = Depends(get_db),
                          user: dict = Depends(requiere_rol("cliente"))):
    rows = db.execute(text("""
        SELECT id_producto, nombre, descripcion, precio, exento_iva
        FROM producto WHERE id_restaurante = :id AND disponible = TRUE ORDER BY id_producto
    """), {"id": id}).mappings().all()
    return [ProductoClienteOut(**r) for r in rows]


@router.post("/pedidos/cotizar", response_model=CotizarOut)
def cotizar(datos: CotizarIn, db: Session = Depends(get_db),
            user: dict = Depends(requiere_rol("cliente"))):
    productos = json.dumps([{"id_producto": p.id_producto, "cantidad": p.cantidad} for p in datos.productos])
    row = db.execute(text("SELECT * FROM fn_cotizar_pedido(:c, :r, :d, CAST(:p AS JSONB), :pr, :m)"),
                     {"c": user["id_perfil"], "r": datos.id_restaurante, "d": datos.id_direccion,
                      "p": productos, "pr": datos.propina, "m": datos.moneda_pago}).mappings().one()
    return CotizarOut(**row)


@router.post("/pedidos", response_model=PedidoCompleto, status_code=201)
def crear_pedido(datos: CrearPedidoIn, db: Session = Depends(get_db),
                 user: dict = Depends(requiere_rol("cliente"))):
    productos = json.dumps([{"id_producto": p.id_producto, "cantidad": p.cantidad} for p in datos.productos])
    id_pedido = db.execute(text("SELECT fn_crear_pedido(:c, :r, :d, CAST(:p AS JSONB), :pr, :m, :u4)"),
                           {"c": user["id_perfil"], "r": datos.id_restaurante, "d": datos.id_direccion,
                            "p": productos, "pr": datos.propina, "m": datos.moneda_pago,
                            "u4": datos.ultimos4}).scalar_one()
    db.commit()
    return armar_pedido_completo(db, id_pedido)


@router.get("/pedidos", response_model=list[PedidoResumenOut])
def historial_pedidos(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("cliente"))):
    rows = db.execute(text("""
        SELECT p.id_pedido, p.fecha_creacion, r.nombre AS restaurante, e.codigo AS estado_codigo, e.nombre AS estado_nombre, p.total
        FROM pedido p JOIN restaurante r ON r.id_restaurante = p.id_restaurante
        JOIN estado_pedido e ON e.id_estado = p.id_estado
        WHERE p.id_cliente = :c ORDER BY p.fecha_creacion DESC
    """), {"c": user["id_perfil"]}).mappings().all()
    return [PedidoResumenOut(**r) for r in rows]


@router.get("/pedidos/{id}", response_model=PedidoCompleto)
def detalle_pedido(id: int, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("cliente"))):
    duenio = db.execute(text("SELECT 1 FROM pedido WHERE id_pedido = :id AND id_cliente = :c"),
                        {"id": id, "c": user["id_perfil"]}).first()
    if duenio is None:
        raise ErrorAPI("SIN_PERMISO", "El pedido no es del cliente.", 403)
    return armar_pedido_completo(db, id)


@router.put("/datos-fiscales", response_model=OkRespuesta)
def datos_fiscales(datos: DatosFiscalesIn, db: Session = Depends(get_db),
                   user: dict = Depends(requiere_rol("cliente"))):
    db.execute(text("UPDATE cliente SET cedula_rif = :r WHERE id_cliente = :c"),
               {"r": datos.cedula_rif, "c": user["id_perfil"]})
    db.commit()
    return OkRespuesta()


@router.post("/pedidos/{id}/calificar", response_model=CalificarOut)
def calificar(id: int, datos: CalificarIn, db: Session = Depends(get_db),
              user: dict = Depends(requiere_rol("cliente"))):
    duenio = db.execute(text("SELECT 1 FROM pedido WHERE id_pedido = :id AND id_cliente = :c"),
                        {"id": id, "c": user["id_perfil"]}).first()
    if duenio is None:
        raise ErrorAPI("SIN_PERMISO", "El pedido no es del cliente.", 403)
    id_cal = db.execute(text("SELECT fn_calificar(:id, :t, :p, :co)"),
                        {"id": id, "t": datos.tipo, "p": datos.puntaje,
                         "co": datos.comentario}).scalar_one()
    db.commit()
    return CalificarOut(id_calificacion=id_cal)


@router.get("/recomendaciones", response_model=list[RecomendacionOut])
def recomendaciones(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("cliente"))):
    rows = db.execute(text("""
        SELECT id_producto, producto, id_restaurante, restaurante, categoria, veces_pedido
        FROM vw_recomendaciones_cliente WHERE id_cliente = :c AND ranking <= 5 ORDER BY ranking
    """), {"c": user["id_perfil"]}).mappings().all()
    return [RecomendacionOut(**r) for r in rows]