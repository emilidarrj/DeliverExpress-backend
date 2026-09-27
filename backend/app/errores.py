"""Manejador global de errores. Formato unico {error, mensaje}. roadmap §0."""
import re

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError

# Patron "CODIGO: descripcion" que producen las RAISE EXCEPTION de la BD.
_CODIGO_RE = re.compile(r"([A-Z][A-Z0-9_]{2,}):\s*(.+)")


class ErrorAPI(Exception):
    """Error de aplicacion con codigo y mensaje para mostrar al usuario."""

    def __init__(self, code: str, message: str, status: int = 400) -> None:
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


def _error(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "mensaje": message})


async def _handle_error_api(_req: Request, exc: ErrorAPI) -> JSONResponse:
    return _error(exc.code, exc.message, exc.status)


async def _handle_dbapi(_req: Request, exc: DBAPIError) -> JSONResponse:
    """La BD reporta 'CODIGO: descripcion'; lo separamos y respondemos 400.
    Si no trae codigo -> 500 ERROR_INTERNO (nunca soltamos el stack al front)."""
    texto = ""
    orig = getattr(exc, "orig", None)
    if orig is not None:
        texto = str(orig)
    if not texto:
        texto = str(exc)
    m = _CODIGO_RE.search(texto)
    if m:
        return _error(m.group(1), m.group(2).strip(), 400)
    return _error("ERROR_INTERNO", "Error interno del servidor.", 500)


async def _handle_http_exc(_req: Request, exc) -> JSONResponse:
    """Reformatea HTTPException de FastAPI al formato unico."""
    detail = getattr(exc, "detail", None)
    status = getattr(exc, "status_code", 500)
    if isinstance(detail, dict) and "error" in detail and "mensaje" in detail:
        return _error(detail["error"], detail["mensaje"], status)
    codigos = {401: "NO_AUTENTICADO", 403: "SIN_PERMISO", 404: "NO_ENCONTRADO",
               422: "VALIDACION"}
    code = codigos.get(status, "ERROR_INTERNO" if status >= 500 else "ERROR")
    msg = detail if isinstance(detail, str) else "Error en la peticion."
    return _error(code, msg, status)


async def _handle_validation(_req: Request, exc: RequestValidationError) -> JSONResponse:
    """Errores de Pydantic en el cuerpo/query -> 422 con mensaje legible."""
    errs = exc.errors()
    if errs:
        e0 = errs[0]
        campo = ".".join(str(x) for x in e0.get("loc", []) if x != "body") or "cuerpo"
        msg = f"Campo '{campo}': {e0.get('msg', 'valor invalido')}."
    else:
        msg = "Datos invalidos."
    return _error("VALIDACION", msg, 422)


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(ErrorAPI, _handle_error_api)
    app.add_exception_handler(DBAPIError, _handle_dbapi)
    app.add_exception_handler(RequestValidationError, _handle_validation)
    # HTTPException: import aqui para no crear ciclo en otros modulos.
    from starlette.exceptions import HTTPException as StarletteHTTPException
    app.add_exception_handler(StarletteHTTPException, _handle_http_exc)