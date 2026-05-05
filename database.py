"""
Módulo de acceso a la base de datos SQLite con los códigos CIE-10.
Importa automáticamente desde CodigosCIE10.csv al iniciar.
"""

from __future__ import annotations

import sqlite3
import csv
import re
from pathlib import Path

DB_PATH = Path(__file__).parent / "cie10.db"

_CSV_CANDIDATES = [
    Path(__file__).parent / "CodigosCIE10.csv",
    Path(__file__).parent.parent / "CodigosCIE10.csv",
]


def _get_csv_path() -> Path | None:
    for p in _CSV_CANDIDATES:
        if p.exists():
            return p
    return None


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cie10 (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_1      TEXT,
            categoria_1   TEXT,
            codigo_2      TEXT NOT NULL,
            categoria_2   TEXT,
            capitulo_num  TEXT,
            capitulo_nombre TEXT,
            grupo_enfermedad TEXT,
            observaciones TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_codigo2 ON cie10 (codigo_2)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_codigo1 ON cie10 (codigo_1)")

    count = cur.execute("SELECT COUNT(*) FROM cie10").fetchone()[0]
    if count == 0:
        csv_path = _get_csv_path()
        if csv_path:
            _load_csv(cur, csv_path)
            print(f"[DB] Importados códigos desde {csv_path}")
        else:
            print("[DB] ADVERTENCIA: No se encontró CodigosCIE10.csv. El buscador estará vacío.")

    conn.commit()
    conn.close()


def _load_csv(cur: sqlite3.Cursor, csv_path: Path) -> None:
    """
    Lee el CSV de códigos CIE-10.

    Acepta dos layouts:
      A) Cabeceras en español (el CSV provisto por DEIS/Argentina):
           Capítulo (Nro) ; Capítulo (Nombre) ; Grupo de Enfermedad ;
           Código 1ª Jerarquía ; Categoría 1ª Jerarquía ;
           Código 2ª Jerarquía ; Categoría 2ª Jerarquía ; Observaciones
         → separador: ;  columnas posicionales 0-7

      B) Cabeceras normalizadas:
           codigo_1, categoria_1, codigo_2, categoria_2,
           capitulo_num, capitulo_nombre, grupo_enfermedad, observaciones
         → separador: , o ;
    """
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]

    for enc in encodings:
        try:
            with open(csv_path, encoding=enc, newline="") as f:
                # Detectar separador leyendo la primera línea
                first_line = f.readline()
                f.seek(0)
                delimiter = ";" if first_line.count(";") > first_line.count(",") else ","

                reader = csv.reader(f, delimiter=delimiter)
                headers = [h.strip().lower() for h in next(reader)]

                # Determinar layout por cabeceras
                # Layout B: cabeceras normalizadas
                if "codigo_2" in headers:
                    i_cap_num  = _col(headers, "capitulo_num", 0)
                    i_cap_nom  = _col(headers, "capitulo_nombre", 1)
                    i_grupo    = _col(headers, "grupo_enfermedad", 2)
                    i_cod1     = _col(headers, "codigo_1", 3)
                    i_cat1     = _col(headers, "categoria_1", 4)
                    i_cod2     = _col(headers, "codigo_2", 5)
                    i_cat2     = _col(headers, "categoria_2", 6)
                    i_obs      = _col(headers, "observaciones", 7)
                else:
                    # Layout A (posicional): cap_num, cap_nom, grupo, cod1, cat1, cod2, cat2, obs
                    i_cap_num, i_cap_nom, i_grupo = 0, 1, 2
                    i_cod1, i_cat1, i_cod2, i_cat2, i_obs = 3, 4, 5, 6, 7

                rows = []
                for row in reader:
                    if len(row) <= i_cod2:
                        continue
                    cod2 = row[i_cod2].strip()
                    if not cod2:
                        continue
                    rows.append((
                        row[i_cod1].strip() if i_cod1 < len(row) else "",
                        row[i_cat1].strip() if i_cat1 < len(row) else "",
                        cod2,
                        row[i_cat2].strip() if i_cat2 < len(row) else "",
                        row[i_cap_num].strip() if i_cap_num < len(row) else "",
                        row[i_cap_nom].strip() if i_cap_nom < len(row) else "",
                        row[i_grupo].strip() if i_grupo < len(row) else "",
                        row[i_obs].strip() if i_obs < len(row) else "",
                    ))

                cur.executemany(
                    """INSERT INTO cie10
                       (codigo_1, categoria_1, codigo_2, categoria_2,
                        capitulo_num, capitulo_nombre, grupo_enfermedad, observaciones)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    rows,
                )
            return
        except UnicodeDecodeError:
            continue

    raise ValueError("No se pudo leer el CSV con ninguna codificación soportada.")


def _col(headers: list, name: str, fallback: int) -> int:
    """Retorna el índice de una columna por nombre, o el fallback si no existe."""
    try:
        return headers.index(name)
    except ValueError:
        return fallback


def search_codes(query: str, limit: int = 20) -> list[dict]:
    """Busca códigos CIE-10 por código o descripción (case-insensitive)."""
    if not query or len(query.strip()) < 2:
        return []

    q = f"%{query.strip().upper()}%"
    conn = get_connection()
    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT codigo_2, categoria_2, codigo_1, categoria_1,
               capitulo_num, capitulo_nombre
        FROM cie10
        WHERE UPPER(codigo_2) LIKE ?
           OR UPPER(categoria_2) LIKE ?
           OR UPPER(codigo_1) LIKE ?
           OR UPPER(categoria_1) LIKE ?
        ORDER BY
            CASE WHEN UPPER(codigo_2) LIKE ? THEN 0
                 WHEN UPPER(codigo_1) LIKE ? THEN 1
                 ELSE 2 END,
            codigo_2
        LIMIT ?
        """,
        (q, q, q, q, f"{query.strip().upper()}%", f"{query.strip().upper()}%", limit),
    ).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def get_code_info(code: str) -> dict | None:
    """Retorna la información completa de un código CIE-10."""
    if not code:
        return None
    code = code.strip().upper()
    conn = get_connection()
    cur = conn.cursor()

    # Prefer the 4-char subclassification; fall back to 3-char category
    row = cur.execute(
        "SELECT * FROM cie10 WHERE codigo_2 = ? ORDER BY LENGTH(codigo_2) DESC LIMIT 1",
        (code,),
    ).fetchone()

    if not row:
        row = cur.execute(
            "SELECT * FROM cie10 WHERE codigo_1 = ? ORDER BY LENGTH(codigo_2) DESC LIMIT 1",
            (code,),
        ).fetchone()

    conn.close()
    return dict(row) if row else None


def get_description(code: str) -> str:
    """Retorna solo la descripción de un código."""
    info = get_code_info(code)
    if not info:
        return ""
    return info.get("categoria_2") or info.get("categoria_1") or ""
