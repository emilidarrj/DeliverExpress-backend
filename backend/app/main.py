"""Punto de entrada FastAPI."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db import get_db
from app.errores import ErrorAPI, registrar_manejadores
from app.seguridad import crear_token, get_current_user, requiere_rol
from app.routers import publico, auth, restaurante, cliente, repartidor, coordinador, facturas, admin


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # ---- ARRANQUE ----
    # Cuando el Int.2 entregue las funciones SQL, descomentar:
    # from app.tiempo_real.listener import arrancar_listener
    # from app.tareas.expirar_ofertas import arrancar_expiracion
    # await arrancar_listener(_app)
    # await arrancar_expiracion()
    print("[lifespan] listener y tareas aun no activos (faltan BD y funciones SQL).")
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
app.include_router(cliente.router)       # CLIENTE 
app.include_router(repartidor.router)    # REPARTIDOR
app.include_router(coordinador.router)   # COORDINADOR
app.include_router(facturas.router)      # FACTURACION (/api/facturas + /api/coordinador/... + /api/admin/facturacion/...)
app.include_router(admin.router)         # ADMIN (/api/admin/...)
# app.include_router(ws.router)            # /ws (sin prefijo /api)


# ---------------------------------------------------------------------------
# Smoke test (NO es ruta de negocio; las de negocio van bajo /api).
# ---------------------------------------------------------------------------
@app.get("/")
def ruta_raiz() -> dict:
    return {"mensaje": "Backend DeliverExpress activo. Rutas de negocio en /api."}


# ---------------------------------------------------------------------------
# DEMO TEMPORALES (prefijo _). Borrar cuando cubran su funcion los routers reales.
# Validan JWT, requiere_rol y el formato de error SIN base de datos.
# ---------------------------------------------------------------------------
@app.post("/api/_token-demo")
def _token_demo(rol: str = "cliente") -> dict:
    """Emite un token fake por rol. En produccion lo hace fn_login (§2)."""
    return {"token": crear_token(1, rol, 7, f"{rol.capitalize()} Demo")}


@app.get("/api/_yo-demo")
def _yo_demo(user: dict = Depends(get_current_user)) -> dict:
    """Refleja las claims. La ruta REAL /api/auth/yo la da routers/auth.py con
    response_model=YoOut; aqui va con prefijo _ para no hacer shadowing."""
    return {
        "id_usuario": int(user["sub"]),
        "rol": user["rol"],
        "id_perfil": user["id_perfil"],
        "nombre": user["nombre"],
    }


@app.get("/api/_requiere-coordinador")
def _requiere_coordinador(user: dict = Depends(requiere_rol("coordinador", "admin"))) -> dict:
    """Prueba 403: con token de 'cliente' debe fallar con SIN_PERMISO."""
    return {"ok": True, "rol": user["rol"]}


@app.get("/api/_error-demo")
def _error_demo() -> dict:
    """Prueba el formato {error, mensaje} de un ErrorAPI controlado."""
    raise ErrorAPI("PRUEBA", "Esto es un error de prueba controlado.", 400)


@app.get("/api/_dbapi-demo")
def _dbapi_demo(db=Depends(get_db)) -> dict:
    """Prueba el parser de DBAPIError. Sin BD, la conexion falla y el manejador
    responde 500 ERROR_INTERNO sin filtrar el stack."""
    db.execute(text("SELECT fn_no_existe_encuarenta()"))  # noqa: RPG0901
    return {"ok": True}