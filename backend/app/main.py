"""Punto de entrada FastAPI."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db import get_db
from app.errores import ErrorAPI, registrar_manejadores
from app.routers import publico, auth, restaurante, cliente, repartidor, coordinador, facturas, admin, ws


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # ---- ARRANQUE ----
    from app.tiempo_real.listener import arrancar_listener
    from app.tareas.expirar_ofertas import arrancar_expirar_ofertas
    await arrancar_listener(_app)
    await arrancar_expirar_ofertas(_app)
    yield
    # ---- APAGON ----
    print("[lifespan] apagando backend.")


app = FastAPI(
    title="DeliverExpress API",
    version="0.1.0",
    docs_url="/docs",
    lifespan=lifespan,
)

# CORS: settings.cors_origins YA es lista (config.py parte el .env por coma).
# NO lo envuelvas en [ ]: anidaria la lista y romperia el preflight del front.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REGISTRA los manejadores ANTES de cualquier ruta: fuerza {"error","mensaje"}
# en 404/422/DBAPIError/ErrorAPI. Sin esta linea el contrato §0 se rompe.
registrar_manejadores(app)


# ---------------------------------------------------------------------------
# MONTAJE DE ROUTERS.
# ---------------------------------------------------------------------------
app.include_router(publico.router)      # PUBLICO
app.include_router(auth.router)         # AUTH (fn_login/fn_registrar_cliente, §10 BD)
app.include_router(restaurante.router)  # RESTAURANTE
app.include_router(cliente.router)      # CLIENTE
app.include_router(repartidor.router)   # REPARTIDOR
app.include_router(coordinador.router)  # COORDINADOR
app.include_router(facturas.router)     # FACTURACION (/api/facturas + /api/coordinador/... + /api/admin/facturacion/...)
app.include_router(admin.router)        # ADMIN (/api/admin/...)
app.include_router(ws.router)           # /ws (sin prefijo /api)


# ---------------------------------------------------------------------------
# Smoke test (NO es ruta de negocio; las de negocio van bajo /api).
# ---------------------------------------------------------------------------
@app.get("/")
def ruta_raiz() -> dict:
    return {"mensaje": "Backend DeliverExpress activo. Rutas de negocio en /api."}


# ---------------------------------------------------------------------------
# SMOKE DE ERRORES (prefijo _, fuera de /docs). Red de seguridad de errores.py
# mientras la BD del Int.1/Int.2 no permita verificar el formato con rutas
# reales. El front (roadmap_frontend §0) asume 'mensaje' en TODO error no-401.
# Borrar las dos en la meta de FASE 3 (roadmap_backend §8: "un pedido recorre
# los 5 estados solo usando la API"), cuando fn_login de §11 responda.
# ---------------------------------------------------------------------------
@app.get("/api/_error-demo", include_in_schema=False)
def _error_demo() -> dict:
    """Prueba el camino ErrorAPI -> 400 {error, mensaje} (roadmap_backend §0).
    No necesita token ni BD: es la unica verificacion de errores.py pre-BD."""
    raise ErrorAPI("PRUEBA", "Esto es un error de prueba controlado.", 400)


@app.get("/api/_dbapi-demo", include_in_schema=False)
def _dbapi_demo(db=Depends(get_db)) -> dict:
    """Prueba el camino DBAPIError SIN CODIGO -> 500 ERROR_INTERNO (nunca stack).
    Con BD cargada, fn_no_existe_encuarenta() da 'function does not exist' sin
    CODIGO: -> 500, que es el contrato. No necesita token. Borrar con BD."""
    db.execute(text("SELECT fn_no_existe_encuarenta()"))
    return {"ok": True}