"""SIMULADOR DE REPARTIDORES (roadmap_backend §7). Proceso aparte: python simulador.py.
Self-contained (cero import app.*); psycopg crudo con %(nombre)s; no se engancha en main.py."""
import argparse
import json
import math
import os
import random
import sys
import time
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg import Connection
from psycopg.rows import dict_row, DictRow

DT_S = 3.0  # tick 3 s (§7)
DEFAULT_LISTEN_URL = "postgresql://de_app:CLAVE@localhost:5432/deliverexpress"

# pedido activo = estado 2,3,4 (igual que fn_registrar_ubicacion §6); RN-09 => 1 fila por repartidor.
QUERY_ESTADO = """
    SELECT r.id_repartidor, r.tipo_vehiculo, r.disponibilidad,
           r.latitud_actual::float8 AS lat, r.longitud_actual::float8 AS lon,
           z.latitud_centro::float8 AS zlat, z.longitud_centro::float8 AS zlon,
           p.id_pedido, p.id_estado,
           res.latitud::float8 AS rlat, res.longitud::float8 AS rlon,
           d.latitud::float8 AS dlat, d.longitud::float8 AS dlon
    FROM repartidor r
    JOIN zona z ON z.id_zona = r.id_zona
    LEFT JOIN pedido p ON p.id_repartidor = r.id_repartidor AND p.id_estado IN (2,3,4)
    LEFT JOIN restaurante res ON res.id_restaurante = p.id_restaurante
    LEFT JOIN direccion_cliente d ON d.id_direccion = p.id_direccion
    WHERE r.activo = TRUE AND r.disponibilidad <> 'desconectado'
"""


def _env_url() -> str:
    """backend/.env por __file__, con fallback de niveles: parents[1] si el archivo vive en
    backend/simulador/ (la ruta que manda roadmap_backend §1) o parents[2] si quedo en
    app/simulador/. Si ninguno tiene .env, avisa en vez de caer silencioso al DEFAULT."""
    here = Path(__file__).resolve()
    for up in (1, 2):
        cand = here.parents[up] / ".env"
        if cand.exists():
            load_dotenv(cand, override=False)
            return os.environ.get("LISTEN_URL", DEFAULT_LISTEN_URL)
    print("[simulador] AVISO: no encontre backend/.env (probe parents[1] y parents[2]); "
          "usare la URL por defecto, revisa que LISTEN_URL apunte a tu BD")
    return DEFAULT_LISTEN_URL


def _connect(url: str) -> Connection[DictRow]:
    # psycopg.connect con autocommit y search_path=deliverexpress (§7); row_factory dict_row para
    # que conn.execute() devuelva DictRow (como SQLAlchemy) y no tuplas
    return psycopg.connect(  # pyright: ignore[reportReturnType]
        url,
        autocommit=True,
        options="-c search_path=deliverexpress",
        row_factory=dict_row,  # pyright: ignore[reportArgumentType]
    )


def _load_speeds(conn) -> dict[str, float]:
    cur = conn.execute("SELECT clave AS k, valor AS v FROM parametro_sistema WHERE clave LIKE 'velocidad_%_kmh'")
    return {r["k"]: float(r["v"]) for r in cur.fetchall()}


def _step_km(speed_kmh: float) -> float:
    return speed_kmh * DT_S / 3600.0  # km/h * (3 s / 3600)


def _move_toward(conn, cur_lat, cur_lon, tgt_lat, tgt_lon, step_km):
    # distancia restante con fn_distancia_km (RNF-05: no Haversine en Python); paso interpolado en grados.
    fila = conn.execute(
        "SELECT fn_distancia_km(%(a)s,%(b)s,%(c)s,%(d)s)::float8 AS rem",
        {"a": cur_lat, "b": cur_lon, "c": tgt_lat, "d": tgt_lon},
    ).fetchone()
    rem = (fila["rem"] if fila else 0.0) or 0.0  # SELECT escalar de fn -> 1 fila; guard calma el Row|None del stub
    if rem <= step_km or rem == 0.0:
        return tgt_lat, tgt_lon, True
    ratio = step_km / rem
    return cur_lat + (tgt_lat - cur_lat) * ratio, cur_lon + (tgt_lon - cur_lon) * ratio, False


def _walk(cur_lat, cur_lon, cz_lat, cz_lon, step_km):
    # zona sin radio ni poligono (§3): 70% azar + 30% sesgo al centro, contencion de mejor esfuerzo.
    lat_d, lon_d = cz_lat - cur_lat, cz_lon - cur_lon
    n = math.hypot(lat_d, lon_d)
    clat, clon = (lat_d / n, lon_d / n) if n > 1e-9 else (0.0, 0.0)
    th = random.uniform(0.0, 2.0 * math.pi)
    blat = 0.3 * clat + 0.7 * math.cos(th)
    blon = 0.3 * clon + 0.7 * math.sin(th)
    bn = math.hypot(blat, blon) or 1.0
    cos_lat = max(math.cos(math.radians(cur_lat)), 1e-6)
    return (cur_lat + (blat / bn) * step_km / 111.32,
            cur_lon + (blon / bn) * step_km / (111.32 * cos_lat))


def _tick(conn, speeds: dict[str, float], auto: bool) -> None:
    auto_acc = 0
    if auto:
        # aceptar ofertas ANTES de leer estado (si no, el recien aceptado caminaria al azar 1 tick).
        for r in conn.execute("SELECT id_oferta AS o FROM oferta_asignacion WHERE respuesta = 'pendiente'").fetchall():
            try:
                conn.execute("SELECT fn_responder_oferta(%(o)s, true)", {"o": r["o"]})
                auto_acc += 1
            except Exception as e:
                print(f"[simulador] oferta {r['o']} no aceptada ({type(e).__name__})")

    rows = conn.execute(QUERY_ESTADO).fetchall()
    moved = auto_st = errors = 0
    for row in rows:
        rid, tipo = row["id_repartidor"], row["tipo_vehiculo"]
        step = _step_km(speeds.get(f"velocidad_{tipo}_kmh", speeds.get("velocidad_moto_kmh", 30.0)))
        cur_lat, cur_lon = row["lat"], row["lon"]
        zlat, zlon = row["zlat"], row["zlon"]
        if cur_lat is None or cur_lon is None:
            cur_lat, cur_lon = zlat, zlon  # sin posicion previa: arranca en el centro de su zona
        idp, eid = row["id_pedido"], row["id_estado"]
        try:
            if idp is None:
                if row["disponibilidad"] == "ocupado":
                    continue  # race transitorio (ocupado sin pedido visible): no mover al azar
                nlat, nlon = _walk(cur_lat, cur_lon, zlat, zlon, step)
                arrived = False
            elif eid in (2, 3):
                tl, tn = row["rlat"], row["rlon"]
                if tl is None or tn is None:
                    errors += 1
                    continue
                nlat, nlon, arrived = _move_toward(conn, cur_lat, cur_lon, tl, tn, step)
            elif eid == 4:
                tl, tn = row["dlat"], row["dlon"]
                if tl is None or tn is None:
                    errors += 1
                    continue
                nlat, nlon, arrived = _move_toward(conn, cur_lat, cur_lon, tl, tn, step)
            else:
                continue
            conn.execute("SELECT fn_registrar_ubicacion(%(r)s,%(la)s,%(lo)s)",
                         {"r": rid, "la": nlat, "lo": nlon})
            moved += 1
            if auto and arrived:
                if eid in (2, 3):
                    # gap §7: asume estado 3 al llegar pero no dice quien pone 2->3 headless; el sim lo completa.
                    if eid == 2:
                        conn.execute("SELECT fn_cambiar_estado(%(p)s,3,%(u)s)", {"p": idp, "u": None})
                        auto_st += 1
                    conn.execute("SELECT fn_cambiar_estado(%(p)s,4,%(u)s)", {"p": idp, "u": None})
                    auto_st += 1
                elif eid == 4:
                    conn.execute("SELECT fn_cambiar_estado(%(p)s,5,%(u)s)", {"p": idp, "u": None})
                    auto_st += 1  # al entregar, la BD factura y libera sola (§8b): el sim no hace nada extra
        except Exception as e:
            errors += 1  # autocommit aisiа el statement: un repartidor malo no tapa a los demas
            print(f"[simulador] repartidor {rid} fallo este tick ({type(e).__name__}: {e})")
    print(f"[simulador] tick: {moved} movidos, {auto_acc} ofertas aceptadas, "
          f"{auto_st} estados avanzados, {errors} errores")


def _seed_orders(url: str, n: int) -> None:
    """--pedidos N: crea pedidos con fn_crear_pedido y los acepta (estado 2). Combinaciones
    aleatorias FALLARAN a veces (la BD valida, §0 BD); el sim las trata como retry-no-crash."""
    with _connect(url) as conn:
        cids = [r["c"] for r in conn.execute(
            "SELECT DISTINCT id_cliente AS c FROM direccion_cliente").fetchall()]
        if not cids:
            print("[simulador] --pedidos: no hay clientes con direcciones; no creo nada")
            return
        creado = 0
        for i in range(n):
            ok = False
            for attempt in range(8):  # cap: datos escasos no colgar el seed
                cid = random.choice(cids)
                dr = conn.execute(
                    "SELECT id_direccion AS d, id_zona AS z FROM direccion_cliente "
                    "WHERE id_cliente=%(c)s ORDER BY random() LIMIT 1", {"c": cid}).fetchone()
                if not dr:
                    break
                did, dz = dr["d"], dr["z"]
                rr = conn.execute(
                    "SELECT r.id_restaurante AS r FROM restaurante r "
                    "JOIN restaurante_zona rz ON rz.id_restaurante = r.id_restaurante "
                    "WHERE r.activo = TRUE AND rz.id_zona = %(z)s "
                    "  AND fn_restaurante_disponible(r.id_restaurante, %(d)s) "
                    "ORDER BY random() LIMIT 1", {"z": dz, "d": did}).fetchone()
                if not rr:
                    continue  # ninguna direccion abierta cubre esta zona: prueba otro cliente
                rid = rr["r"]
                prods = [x["p"] for x in conn.execute(
                    "SELECT id_producto AS p FROM producto "
                    "WHERE id_restaurante=%(r)s AND disponible=TRUE ORDER BY random() LIMIT %(k)s",
                    {"r": rid, "k": random.randint(1, 3)}).fetchall()]
                if not prods:
                    continue
                productos = json.dumps([{"id_producto": p, "cantidad": random.randint(1, 3)} for p in prods])
                propina = float(random.choice([0, 1, 2, 3]))
                moneda = random.choice(["USD", "VES"])  # §7: moneda al azar
                u4 = f"{random.randint(0, 9999):04d}"   # RNF-09: solo ultimos 4
                try:
                    fila = conn.execute(
                        "SELECT fn_crear_pedido(%(c)s,%(r)s,%(d)s,CAST(%(p)s AS JSONB),"
                        "%(pr)s,%(m)s,%(u)s) AS idp",
                        {"c": cid, "r": rid, "d": did, "p": productos,
                         "pr": propina, "m": moneda, "u": u4}).fetchone()
                    if fila is None:
                        continue  # SELECT escalar de fn -> 1 fila; guard calma el Row|None del stub
                    idp = fila["idp"]
                    conn.execute("SELECT fn_cambiar_estado(%(p)s,2,%(u)s)", {"p": idp, "u": None})
                    ok = True
                    creado += 1
                    print(f"[simulador] --pedidos: pedido {idp} creado y aceptado (estado 2)")
                    break
                except Exception as e:
                    print(f"[simulador] --pedidos intento {attempt + 1} rechazado por la BD "
                          f"({type(e).__name__}: {e})")
            if not ok:
                print(f"[simulador] --pedidos: no pude crear el pedido #{i + 1} tras 8 intentos")
        print(f"[simulador] --pedidos: {creado}/{n} pedidos creados")


def main() -> None:
    ap = argparse.ArgumentParser(description="Simulador de repartidores (roadmap_backend §7)")
    ap.add_argument("--auto", action="store_true", help="acepta ofertas y avanza estados al llegar")
    ap.add_argument("--pedidos", type=int, default=0, metavar="N", help="crea N pedidos (estado 2) antes de mover")
    args = ap.parse_args()
    if args.pedidos < 0:
        ap.error("--pedidos debe ser >= 0")
    url = _env_url()

    # fail-fast temprano: si la BD o el .env estan mal, sale ya (los blips despues si se reintentan).
    try:
        conn = _connect(url)
    except Exception as e:
        print(f"[simulador] no pude conectar (revisa backend/.env / LISTEN_URL y PostgreSQL): "
              f"{type(e).__name__}: {e}")
        sys.exit(1)
    try:
        speeds = _load_speeds(conn)
    finally:
        conn.close()
    if not speeds:
        print("[simulador] AVISO: parametro_sistema sin velocidad_*_kmh (§4); usare 30 kmh")

    if args.pedidos > 0:
        _seed_orders(url, args.pedidos)

    try:
        while True:
            try:
                with _connect(url) as conn:  # conexion efimera por tick (poll stateless)
                    _tick(conn, speeds, args.auto)
            except (psycopg.OperationalError, psycopg.InterfaceError) as e:
                print(f"[simulador] conexion caída ({type(e).__name__}); reintenta en 3 s")
            except Exception as e:
                print(f"[simulador] tick fallido ({type(e).__name__}: {e}); reintenta en 3 s")
            time.sleep(DT_S)
    except KeyboardInterrupt:
        print("[simulador] detenido.")


if __name__ == "__main__":
    main()