"""ADMIN (roadmap_backend §4) [admin]. CRUD de catalogos, tasas BCV y registros cross-tabla en transaccion."""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores import ErrorAPI
from app.esquemas import (
    CategoriaAdminIn, CategoriaAdminOut, CoordinadorAdminIn, CoordinadorAdminOut,
    ParametroIn, ParametroOut, RepartidorAdminIn, RepartidorAdminOut, RepartidorAdminPutIn,
    RestauranteAdminIn, RestauranteAdminOut, RestauranteAdminPutIn, TasaBcvIn, TasaBcvOut,
    TarifaAdminIn, TarifaAdminOut, UsuarioActivoIn, ZonaAdminIn, ZonaAdminOut, OkRespuesta
)
from app.seguridad import requiere_rol

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/zonas", response_model=list[ZonaAdminOut])
def listar_zonas(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    rows = db.execute(text("SELECT id_zona, nombre, descripcion, latitud_centro, longitud_centro FROM zona ORDER BY id_zona")).mappings().all()
    return [ZonaAdminOut(**r) for r in rows]


@router.post("/zonas", response_model=ZonaAdminOut, status_code=201)
def crear_zona(datos: ZonaAdminIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    row = db.execute(text("INSERT INTO zona (nombre, descripcion, latitud_centro, longitud_centro) VALUES (:n, :d, :la, :lo) RETURNING id_zona, nombre, descripcion, latitud_centro, longitud_centro"),
                     {"n": datos.nombre, "d": datos.descripcion, "la": datos.latitud_centro, "lo": datos.longitud_centro}).mappings().one()
    db.commit()
    return ZonaAdminOut(**row)


@router.put("/zonas/{id}", response_model=ZonaAdminOut)
def actualizar_zona(id: int, datos: ZonaAdminIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    row = db.execute(text("UPDATE zona SET nombre = :n, descripcion = :d, latitud_centro = :la, longitud_centro = :lo WHERE id_zona = :id RETURNING id_zona, nombre, descripcion, latitud_centro, longitud_centro"),
                     {"n": datos.nombre, "d": datos.descripcion, "la": datos.latitud_centro, "lo": datos.longitud_centro, "id": id}).mappings().first()
    db.commit()
    if row is None:
        raise ErrorAPI("NO_ENCONTRADO", "Zona no existe.", 404)
    return ZonaAdminOut(**row)


@router.get("/categorias", response_model=list[CategoriaAdminOut])
def listar_categorias(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    rows = db.execute(text("SELECT id_categoria, nombre FROM categoria ORDER BY id_categoria")).mappings().all()
    return [CategoriaAdminOut(**r) for r in rows]


@router.post("/categorias", response_model=CategoriaAdminOut, status_code=201)
def crear_categoria(datos: CategoriaAdminIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    row = db.execute(text("INSERT INTO categoria (nombre) VALUES (:n) RETURNING id_categoria, nombre"), {"n": datos.nombre}).mappings().one()
    db.commit()
    return CategoriaAdminOut(**row)


@router.put("/categorias/{id}", response_model=CategoriaAdminOut)
def actualizar_categoria(id: int, datos: CategoriaAdminIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    row = db.execute(text("UPDATE categoria SET nombre = :n WHERE id_categoria = :id RETURNING id_categoria, nombre"), {"n": datos.nombre, "id": id}).mappings().first()
    db.commit()
    if row is None:
        raise ErrorAPI("NO_ENCONTRADO", "Categoria no existe.", 404)
    return CategoriaAdminOut(**row)


@router.get("/tarifas", response_model=list[TarifaAdminOut])
def listar_tarifas(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    rows = db.execute(text("SELECT id_tarifa, km_desde, km_hasta, precio FROM tarifa_envio ORDER BY km_desde")).mappings().all()
    return [TarifaAdminOut(**r) for r in rows]


@router.post("/tarifas", response_model=TarifaAdminOut, status_code=201)
def crear_tarifa(datos: TarifaAdminIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    row = db.execute(text("INSERT INTO tarifa_envio (km_desde, km_hasta, precio) VALUES (:di, :ha, :p) RETURNING id_tarifa, km_desde, km_hasta, precio"),
                     {"di": datos.km_desde, "ha": datos.km_hasta, "p": datos.precio}).mappings().one()
    db.commit()
    return TarifaAdminOut(**row)


@router.put("/tarifas/{id}", response_model=TarifaAdminOut)
def actualizar_tarifa(id: int, datos: TarifaAdminIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    row = db.execute(text("UPDATE tarifa_envio SET km_desde = :di, km_hasta = :ha, precio = :p WHERE id_tarifa = :id RETURNING id_tarifa, km_desde, km_hasta, precio"),
                     {"di": datos.km_desde, "ha": datos.km_hasta, "p": datos.precio, "id": id}).mappings().first()
    db.commit()
    if row is None:
        raise ErrorAPI("NO_ENCONTRADO", "Tarifa no existe.", 404)
    return TarifaAdminOut(**row)


@router.get("/parametros", response_model=list[ParametroOut])
def listar_parametros(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    rows = db.execute(text("SELECT clave, valor, descripcion FROM parametro_sistema ORDER BY clave")).mappings().all()
    return [ParametroOut(**r) for r in rows]


@router.put("/parametros/{clave}", response_model=ParametroOut)
def actualizar_parametro(clave: str, datos: ParametroIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    row = db.execute(text("UPDATE parametro_sistema SET valor = :v WHERE clave = :k RETURNING clave, valor, descripcion"), {"v": datos.valor, "k": clave}).mappings().first()
    db.commit()
    if row is None:
        raise ErrorAPI("NO_ENCONTRADO", "Parametro no existe.", 404)
    return ParametroOut(**row)


@router.get("/tasas-bcv", response_model=list[TasaBcvOut])
def listar_tasas(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    rows = db.execute(text("SELECT fecha, tasa_usd, fecha_registro FROM tasa_bcv ORDER BY fecha DESC LIMIT 60")).mappings().all()
    return [TasaBcvOut(**r) for r in rows]


@router.post("/tasas-bcv", response_model=TasaBcvOut, status_code=201)
def crear_tasa(datos: TasaBcvIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    if db.execute(text("SELECT 1 FROM tasa_bcv WHERE fecha = :f"), {"f": datos.fecha}).first() is not None:
        raise ErrorAPI("TASA_BCV_DUPLICADA", "Ya existe una tasa BCV para esa fecha.", 400)
    row = db.execute(text("INSERT INTO tasa_bcv (fecha, tasa_usd, id_usuario) VALUES (:f, :t, :u) RETURNING fecha, tasa_usd, fecha_registro"),
                     {"f": datos.fecha, "t": datos.tasa_usd, "u": int(user["sub"])}).mappings().one()
    db.commit()
    return TasaBcvOut(**row)


@router.get("/restaurantes", response_model=list[RestauranteAdminOut])
def listar_restaurantes(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    rows = db.execute(text("""
        SELECT r.id_restaurante, r.id_usuario, r.id_categoria, r.nombre, r.direccion, r.telefono, r.latitud, r.longitud,
               r.tiempo_prep_min, r.rif, r.razon_social, r.direccion_fiscal, r.calificacion_promedio, r.total_calificaciones, r.activo,
               COALESCE((SELECT array_agg(rz.id_zona ORDER BY rz.id_zona) FROM restaurante_zona rz WHERE rz.id_restaurante = r.id_restaurante), '{}'::int[]) AS zonas
        FROM restaurante r ORDER BY r.id_restaurante
    """)).mappings().all()
    return [RestauranteAdminOut(**r) for r in rows]


@router.post("/restaurantes", response_model=RestauranteAdminOut, status_code=201)
def crear_restaurante(datos: RestauranteAdminIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    with db.begin():
        id_usuario = db.execute(text("SELECT fn_registrar_usuario(:e, :p, 'restaurante')"), {"e": datos.email, "p": datos.password}).scalar_one()
        row = db.execute(text("""
            INSERT INTO restaurante (id_usuario, id_categoria, nombre, direccion, telefono, latitud, longitud, tiempo_prep_min, rif, razon_social, direccion_fiscal)
            VALUES (:u, :c, :n, :d, :t, :la, :lo, :tp, :r, :rs, :df)
            RETURNING id_restaurante, id_usuario, id_categoria, nombre, direccion, telefono, latitud, longitud, tiempo_prep_min, rif, razon_social, direccion_fiscal, calificacion_promedio, total_calificaciones, activo
        """), {"u": id_usuario, "c": datos.id_categoria, "n": datos.nombre, "d": datos.direccion, "t": datos.telefono,
               "la": datos.latitud, "lo": datos.longitud, "tp": datos.tiempo_prep_min, "r": datos.rif, "rs": datos.razon_social, "df": datos.direccion_fiscal}).mappings().one()
        for z in datos.zonas:
            db.execute(text("INSERT INTO restaurante_zona (id_restaurante, id_zona) VALUES (:r, :z)"), {"r": row["id_restaurante"], "z": z})
    return RestauranteAdminOut(**row, zonas=datos.zonas)


@router.put("/restaurantes/{id}", response_model=RestauranteAdminOut)
def actualizar_restaurante(id: int, datos: RestauranteAdminPutIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    with db.begin():
        row = db.execute(text("""
            UPDATE restaurante SET id_categoria = :c, nombre = :n, direccion = :d, telefono = :t, latitud = :la, longitud = :lo,
                   tiempo_prep_min = :tp, rif = :r, razon_social = :rs, direccion_fiscal = :df, activo = :a
            WHERE id_restaurante = :id
            RETURNING id_restaurante, id_usuario, id_categoria, nombre, direccion, telefono, latitud, longitud, tiempo_prep_min, rif, razon_social, direccion_fiscal, calificacion_promedio, total_calificaciones, activo
        """), {"c": datos.id_categoria, "n": datos.nombre, "d": datos.direccion, "t": datos.telefono, "la": datos.latitud,
               "lo": datos.longitud, "tp": datos.tiempo_prep_min, "r": datos.rif, "rs": datos.razon_social, "df": datos.direccion_fiscal, "a": datos.activo, "id": id}).mappings().first()
        if row is None:
            raise ErrorAPI("NO_ENCONTRADO", "Restaurante no existe.", 404)
        db.execute(text("DELETE FROM restaurante_zona WHERE id_restaurante = :id"), {"id": id})
        for z in datos.zonas:
            db.execute(text("INSERT INTO restaurante_zona (id_restaurante, id_zona) VALUES (:r, :z)"), {"r": id, "z": z})
    return RestauranteAdminOut(**row, zonas=datos.zonas)


@router.get("/repartidores", response_model=list[RepartidorAdminOut])
def listar_repartidores(db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    rows = db.execute(text("""
        SELECT id_repartidor, id_usuario, id_zona, nombre, telefono, cedula, tipo_vehiculo, disponibilidad, prioridad,
               latitud_actual, longitud_actual, calificacion_promedio, total_calificaciones, en_revision, activo
        FROM repartidor ORDER BY id_repartidor
    """)).mappings().all()
    return [RepartidorAdminOut(**r) for r in rows]


@router.post("/repartidores", response_model=RepartidorAdminOut, status_code=201)
def crear_repartidor(datos: RepartidorAdminIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    with db.begin():
        id_usuario = db.execute(text("SELECT fn_registrar_usuario(:e, :p, 'repartidor')"), {"e": datos.email, "p": datos.password}).scalar_one()
        row = db.execute(text("""
            INSERT INTO repartidor (id_usuario, id_zona, nombre, telefono, cedula, tipo_vehiculo)
            VALUES (:u, :z, :n, :t, :c, :v)
            RETURNING id_repartidor, id_usuario, id_zona, nombre, telefono, cedula, tipo_vehiculo, disponibilidad, prioridad, latitud_actual, longitud_actual, calificacion_promedio, total_calificaciones, en_revision, activo
        """), {"u": id_usuario, "z": datos.id_zona, "n": datos.nombre, "t": datos.telefono, "c": datos.cedula, "v": datos.tipo_vehiculo}).mappings().one()
    return RepartidorAdminOut(**row)


@router.put("/repartidores/{id}", response_model=RepartidorAdminOut)
def actualizar_repartidor(id: int, datos: RepartidorAdminPutIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    row = db.execute(text("""
        UPDATE repartidor SET nombre = :n, telefono = :t, cedula = :c, tipo_vehiculo = :v, id_zona = :z, activo = :a
        WHERE id_repartidor = :id
        RETURNING id_repartidor, id_usuario, id_zona, nombre, telefono, cedula, tipo_vehiculo, disponibilidad, prioridad, latitud_actual, longitud_actual, calificacion_promedio, total_calificaciones, en_revision, activo
    """), {"n": datos.nombre, "t": datos.telefono, "c": datos.cedula, "v": datos.tipo_vehiculo, "z": datos.id_zona, "a": datos.activo, "id": id}).mappings().first()
    db.commit()
    if row is None:
        raise ErrorAPI("NO_ENCONTRADO", "Repartidor no existe.", 404)
    return RepartidorAdminOut(**row)


@router.post("/coordinadores", response_model=CoordinadorAdminOut, status_code=201)
def crear_coordinador(datos: CoordinadorAdminIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    with db.begin():
        id_usuario = db.execute(text("SELECT fn_registrar_usuario(:e, :p, 'coordinador')"), {"e": datos.email, "p": datos.password}).scalar_one()
        row = db.execute(text("INSERT INTO coordinador (id_usuario, nombre, telefono) VALUES (:u, :n, :t) RETURNING id_coordinador, id_usuario, nombre, telefono"),
                         {"u": id_usuario, "n": datos.nombre, "t": datos.telefono}).mappings().one()
    return CoordinadorAdminOut(**row)


@router.put("/usuarios/{id}/activo", response_model=OkRespuesta)
def cambiar_activo(id: int, datos: UsuarioActivoIn, db: Session = Depends(get_db), user: dict = Depends(requiere_rol("admin"))):
    row = db.execute(text("UPDATE usuario SET activo = :a WHERE id_usuario = :id RETURNING id_usuario"), {"a": datos.activo, "id": id}).mappings().first()
    db.commit()
    if row is None:
        raise ErrorAPI("NO_ENCONTRADO", "Usuario no existe.", 404)
    return OkRespuesta()