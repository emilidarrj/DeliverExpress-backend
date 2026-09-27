"""Punto de entrada FastAPI. roadmap_backend.txt §1 y §5."""
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database.db import get_db
from app.errores import ErrorAPI, registrar_manejadores
from app.seguridad import crear_token, get_current_user, requiere_rol

app = FastAPI(title="DeliverExpress API", version="0.1.0", docs_url="/docs")

# CORS: 'settings.cors_origins' YA es una lista (config.py parte el .env por coma).
# NO lo envuelvas en [ ]: eso anidaría la lista y rompería el preflight del front.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,   # <-- sin corchetes extra
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REGISTRA los manejadores ANTES de cualquier ruta: esto fuerza que TODO error
# salga como {"error","mensaje"} (404, 422, DBAPIError, ErrorAPI). Sin esta
# línea el contrato §0 del roadmap se rompe.
registrar_manejadores(app)


# ---------------------------------------------------------------------------
# Smoke test: verifica que el proceso levanta. NO es ruta de negocio.
# ---------------------------------------------------------------------------
@app.get("/")
def ruta_raiz() -> dict:
    return {"mensaje": "Backend DeliverExpress activo. Rutas de negocio en /api."}


# ---------------------------------------------------------------------------
# ROUTER DE PRUEBA (TEMPORAL). Borrar cuando exista routers/auth.py real.
# Permite validar JWT, requiere_rol y el formato de error SIN base de datos.
# ---------------------------------------------------------------------------
@app.post("/api/auth/_token-demo")
def _token_demo(rol: str = "cliente") -> dict:
    """Emite un token fake por rol para probar /yo y los 403. Sin BD.
    En produccion esto lo hace fn_login(email, password) -> roadmap §2."""
    return {"token": crear_token(1, rol, 7, f"{rol.capitalize()} Demo")}


@app.get("/api/auth/yo")
def _yo(user: dict = Depends(get_current_user)) -> dict:
    """Refleja las claims. Forma segun roadmap §4: GET /api/auth/yo."""
    return {
        "id_usuario": int(user["sub"]),
        "rol": user["rol"],
        "id_perfil": user["id_perfil"],
        "nombre": user["nombre"],
    }


@app.get("/api/_requiere-coordinador")
def _requiere_coordinador(
    user: dict = Depends(requiere_rol("coordinador", "admin")),
) -> dict:
    """Prueba 403: con token de 'cliente' debe fallar con SIN_PERMISO."""
    return {"ok": True, "rol": user["rol"]}


@app.get("/api/_error-demo")
def _error_demo() -> dict:
    """Prueba el formato {error, mensaje} de un ErrorAPI controlado."""
    raise ErrorAPI("PRUEBA", "Esto es un error de prueba controlado.", 400)


@app.get("/api/_dbapi-demo")
def _dbapi_demo(db=Depends(get_db)) -> dict:
    """Prueba el parser de DBAPIError. Sin BD, la conexion falla (OperationalError,
    subclase de DBAPIError) y el manejador responde 500 ERROR_INTERNO sin filtrar
    el stack. Con BD, cambia a un SELECT fn_inexistente() para ver un 400 con
    codigo real tipo 'CODIGO: descripcion'."""
    db.execute(text("SELECT fn_no_existe_encuarenta()"))  # noqa: RPG0901
    return {"ok": True}


# ---------------------------------------------------------------------------
# Arranque de tiempo real y tareas periodicas (listener, expirar_ofertas).
# Se activa en cuanto exista la BD. Por ahora solo un aviso para que la app
# levante limpia aunque PostgreSQL no este disponible. roadmap §5, §6.
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def _startup() -> None:
    # Cuando el Int.2 entregue las funciones SQL, descomentar:
    # from app.tiempo_real.listener import arrancar_listener
    # from app.tareas.expirar_ofertas import arrancar_expiracion
    # await arrancar_listener(app)
    # await arrancar_expiracion()
    print("[startup] listener y tareas aun no activos (faltan BD y funciones SQL).")