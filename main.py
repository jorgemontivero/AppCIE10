"""
App CIE-10 – Causa Básica de Defunción
Backend FastAPI + servicio de frontend React (dist/)

Uso:  uvicorn main:app --reload
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database import get_description, init_db, search_codes
from engine import analyze_certificate

# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="CIE-10 Causa Básica de Defunción", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    init_db()


# ──────────────────────────────────────────────────────────────────────────────
# API
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/search")
async def api_search(q: str = Query(default="", min_length=0), limit: int = 20):
    """Busca códigos CIE-10 por código o texto de descripción."""
    return search_codes(q, limit)


@app.get("/api/code/{code}")
async def api_get_code(code: str):
    """Retorna información completa de un código CIE-10."""
    from database import get_code_info
    info = get_code_info(code)
    if not info:
        return JSONResponse({"error": f"Código '{code}' no encontrado"}, status_code=404)
    return info


class CodeEntry(BaseModel):
    """Un código CIE-10 dentro de una línea (Parte I o II)."""

    code: str = ""
    description: str = ""  # solo UI; opcional para el backend


class Part1Line(BaseModel):
    """Línea (a)-(d): puede incluir varias causas en la misma línea."""

    line: str = ""
    interval: str = ""
    codes: list[CodeEntry] = []


class Part2Line(BaseModel):
    """Bloque de Parte II: varias afecciones contribuyentes con intervalo común."""

    interval: str = ""
    codes: list[CodeEntry] = []


class CertificateRequest(BaseModel):
    part1: list[Part1Line]
    part2: list[Part2Line]
    sex: str = "M"
    age: Optional[int] = None
    pregnancy: str = "N"       # S | N | SE
    violence: bool = False
    violence_type: str = ""    # A | S | H


@app.post("/api/analyze")
async def api_analyze(req: CertificateRequest):
    """Determina la causa básica de defunción aplicando las reglas CIE-10 Vol. 2."""
    result = analyze_certificate(req.model_dump())

    # Enriquecer con la descripción del código seleccionado
    if result.get("selected_code"):
        result["code_description"] = get_description(result["selected_code"])

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Servicio del frontend React (producción – dist/)
# ──────────────────────────────────────────────────────────────────────────────

_DIST = Path(__file__).parent / "frontend" / "dist"

if _DIST.exists():
    _assets = _DIST / "assets"
    if _assets.exists():
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(_DIST / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        target = _DIST / full_path
        if target.exists() and target.is_file():
            return FileResponse(target)
        return FileResponse(_DIST / "index.html")

else:
    @app.get("/", include_in_schema=False)
    async def root_no_frontend():
        return JSONResponse(
            {
                "status": "backend OK",
                "message": "Frontend no construido. Ejecute: cd frontend && npm install && npm run build",
                "docs": "/docs",
            }
        )
