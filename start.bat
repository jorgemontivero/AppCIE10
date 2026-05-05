@echo off
chcp 65001 >nul 2>&1
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║   App CIE-10 — Causa Básica de Defunción            ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: ── Verificar Python ─────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python no encontrado.
    echo  Instale Python 3.10+ desde https://www.python.org
    echo  Asegúrese de marcar "Add Python to PATH" durante la instalación.
    pause
    exit /b 1
)

:: ── Instalar dependencias Python ──────────────────────────────────────────
echo  [1/3] Instalando dependencias Python...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  ERROR: No se pudieron instalar las dependencias Python.
    pause
    exit /b 1
)
echo        OK

:: ── Construir frontend (solo si no existe dist/) ──────────────────────────
if not exist "frontend\dist\index.html" (
    echo  [2/3] Construyendo el frontend ^(solo la primera vez^)...

    node --version >nul 2>&1
    if errorlevel 1 (
        echo  ERROR: Node.js no encontrado.
        echo  Instale Node.js LTS desde https://nodejs.org
        pause
        exit /b 1
    )

    cd frontend
    call npm install --silent
    call npm run build
    cd ..
    if errorlevel 1 (
        echo  ERROR: No se pudo construir el frontend.
        pause
        exit /b 1
    )
    echo        OK
) else (
    echo  [2/3] Frontend ya construido — omitiendo.
)

:: ── Iniciar el servidor ───────────────────────────────────────────────────
echo  [3/3] Iniciando servidor en http://localhost:8000
echo.
echo  ┌──────────────────────────────────────────────────────┐
echo  │   Abrir en el navegador:  http://localhost:8000      │
echo  │   Presione Ctrl+C para detener el servidor           │
echo  └──────────────────────────────────────────────────────┘
echo.

:: Abrir el navegador tras 2 segundos
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

:: Iniciar uvicorn
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
