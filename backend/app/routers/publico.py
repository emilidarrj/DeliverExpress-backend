"""Router PUBLICO (roadmap_backend §4). Sin auth: categorias y zonas para
dropdowns de registro/login. Rutas EXACTAS del contrato: GET /api/categorias
y GET /api/zonas (el prefijo /api vive aqui, no en main.py).
Errores de BD: NO se capturan localmente -> los formatea el handler global de
errores.py ({error,mensaje} en la raiz, roadmap_backend §0)."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.esquemas import CategoriaOut, ZonaOut

router = APIRouter(prefix="/api", tags=["publico"])   # /api aqui; rutas /categorias /zonas


@router.get("/categorias", response_model=list[CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)):
    # columnas = roadmap_bd §3 (categoria.id_categoria, categoria.nombre). search_path ya
    # resuelve "categoria" a deliverexpress.categoria (db.py), asi que no se hardcodea esquema.
    rows = db.execute(
        text("SELECT id_categoria, nombre FROM categoria ORDER BY id_categoria")
    ).mappings().all()
    return [CategoriaOut(**row) for row in rows]


@router.get("/zonas", response_model=list[ZonaOut])
def listar_zonas(db: Session = Depends(get_db)):
    # descripcion NO se trae: §4 no la pide y ZonaOut no la tiene ("no inventar", §0).
    rows = db.execute(
        text("SELECT id_zona, nombre, latitud_centro, longitud_centro FROM zona ORDER BY id_zona")
    ).mappings().all()
    return [ZonaOut(**row) for row in rows]