# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AppCIE10 is a tool for determining the "underlying cause of death" (causa básica de defunción) from Argentine death certificates, following ICD-10 Volume 2 (WHO) rules. The UI and all messages are in Spanish.

## Development Commands

### Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run backend with hot reload (dev)
uvicorn main:app --reload        # API at http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # Dev server at http://localhost:5173, proxies /api to :8000
npm run build    # Production build → frontend/dist/
```

### Full Production Run

```bash
cd frontend && npm run build && cd ..
uvicorn main:app                 # Serves API + static frontend at :8000
```

On Windows, `start.bat` automates install + build + launch.

### No test or lint tooling is configured.

## Architecture

### Data Flow

1. User fills in the death certificate form (CertificateForm.jsx)
2. React POSTs JSON to `/api/analyze`
3. `engine.py` applies SP1–SP8 selection steps and M1–M4 modifications
4. FastAPI enriches the result with code descriptions from SQLite
5. `Result.jsx` displays the selected code with a step-by-step justification

### Backend (`main.py`, `engine.py`, `database.py`)

- **FastAPI** app with three API endpoints: `/api/search`, `/api/code/{code}`, `/api/analyze`
- In production, FastAPI also serves the React build from `frontend/dist/`
- CORS is configured for `localhost:5173` (dev) and `localhost:8000` (prod)
- **SQLite** (`cie10.db`) is auto-created from `CodigosCIE10.csv` on first run; `database.py` handles CSV encoding detection (UTF-8/Latin-1/CP-1252) and delimiter detection (`,`/`;`)

### Rules Engine (`engine.py`)

The core of the application. Implements ICD-10 Vol. 2 Sections 4.2.3–4.2.7 deterministically via regex and code-prefix matching — no ML.

**Selection Steps (SP1–SP8)**:
- SP1: Single cause → select it
- SP2: Single line in Part I → select it
- SP3: General principle — lowest-line condition explains upper lines
- SP4: Rule 1 — valid causal sequence from lowest to top
- SP5: No valid sequence — select terminal condition
- SP6: Obvious cause — replace with more specific cause
- SP7: Ill-defined conditions (Chapter XVIII / R00–R94) — skip if better option exists
- SP8: Trivial conditions (superficial injuries / Chapter XXI) — skip if better option exists

**Modifications (M1–M4)**:
- M1: Linkages — combine condition pairs (e.g. hypertension + kidney disease → combined code)
- M2: Specificity — select most specific code variant
- M3: Re-evaluation loop for M1/M2 stability
- M4: Pregnancy/maternal death → reclassify to O99.8

Key helpers: `get_chapter()`, `is_valid_sequence()`, `is_obvious_cause()`, `is_ill_defined()`, `is_trivial()`.

### Frontend (`frontend/src/`)

React 18 + Vite, plain CSS (no UI library).

- **App.jsx**: Top-level state management via `useState`; orchestrates form ↔ API ↔ results
- **CertificateForm.jsx**: Death certificate form — Part I (causal sequence, lines a–d), Part II (contributing conditions), plus demographics (sex, age, pregnancy, violence indicators)
- **CodeSearch.jsx**: Autocomplete dropdown backed by `/api/search`
- **Result.jsx**: Displays selected cause code and the applied rule chain

Vite proxies `/api/*` to `http://localhost:8000` during development (`vite.config.js`).

## Key Data File

`CodigosCIE10.csv` must be present in the project root before the backend starts. The database table has columns: `codigo_1` (3-char category), `categoria_1`, `codigo_2` (4-char subclassification), `categoria_2`, `capitulo_num`, `capitulo_nombre`, `grupo_enfermedad`, `observaciones`. Indexed on both code columns.
