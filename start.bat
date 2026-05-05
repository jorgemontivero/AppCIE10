@echo off
chcp 65001 >nul 2>&1
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║   App CIE-10 — Causa Básica de Defunción            ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: ── Modo de inicio ────────────────────────────────────────────────────────
echo  ¿Cómo desea iniciar la aplicación?
echo.
echo    [1]  Solo este equipo     (http://localhost:8000)
echo    [2]  Modo red local       (accesible desde otros equipos en la red)
echo.
set /p MODO="  Ingrese 1 o 2 y presione Enter [1]: "
if "%MODO%"=="" set MODO=1

if "%MODO%"=="2" (
    set HOST=0.0.0.0
) else (
    set MODO=1
    set HOST=127.0.0.1
)

echo.

:: ── Verificar Python ──────────────────────────────────────────────────────
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

:: ── Mostrar información de acceso ─────────────────────────────────────────
echo  [3/3] Iniciando servidor...
echo.

if "%MODO%"=="2" (
    :: Obtener IP local
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
        set RAW_IP=%%a
        goto :found_ip
    )
    :found_ip
    :: Quitar espacio inicial
    for /f "tokens=* delims= " %%b in ("%RAW_IP%") do set LOCAL_IP=%%b

    echo  ┌──────────────────────────────────────────────────────────────┐
    echo  │   Este equipo:        http://localhost:8000                  │
    echo  │   Otros en la red:    http://%LOCAL_IP%:8000               │
    echo  │                                                              │
    echo  │   Comparta la segunda dirección con quienes quieran         │
    echo  │   conectarse desde la misma red WiFi o LAN.                 │
    echo  │                                                              │
    echo  │   Presione Ctrl+C para detener el servidor                  │
    echo  └──────────────────────────────────────────────────────────────┘
) else (
    echo  ┌──────────────────────────────────────────────────────┐
    echo  │   Abrir en el navegador:  http://localhost:8000      │
    echo  │   Presione Ctrl+C para detener el servidor           │
    echo  └──────────────────────────────────────────────────────┘
)
echo.

:: Abrir el navegador en este equipo tras 2 segundos
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

:: Iniciar uvicorn
python -m uvicorn main:app --host %HOST% --port 8000
