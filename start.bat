@echo off
chcp 65001 >nul 2>&1
cls

echo.
echo  ====================================================
echo    App CIE-10 -- Causa Basica de Defuncion
echo  ====================================================
echo.
echo  Como desea iniciar la aplicacion?
echo.
echo    1  -  Solo este equipo  (localhost)
echo    2  -  Modo red local    (otros equipos en la red)
echo.

choice /c 12 /n /m "Presione 1 o 2: "

if errorlevel 2 (
    set HOST=0.0.0.0
    set MODO=red
) else (
    set HOST=127.0.0.1
    set MODO=local
)

echo.

:: ── Verificar Python ──────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python no encontrado.
    echo  Instale Python 3.10+ desde https://www.python.org
    echo  Asegurese de marcar "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

:: ── Instalar dependencias Python ──────────────────────────────────────────
echo  [1/3] Verificando dependencias Python...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  ERROR: No se pudieron instalar las dependencias Python.
    pause
    exit /b 1
)
echo        OK

:: ── Construir frontend (solo si no existe dist/) ──────────────────────────
if not exist "frontend\dist\index.html" (
    echo  [2/3] Construyendo el frontend (solo la primera vez)...

    node --version >nul 2>&1
    if errorlevel 1 (
        echo  ERROR: Node.js no encontrado.
        echo  Instale Node.js LTS desde https://nodejs.org
        pause
        exit /b 1
    )

    pushd frontend
    call npm install --silent
    call npm run build
    popd

    if not exist "frontend\dist\index.html" (
        echo  ERROR: No se pudo construir el frontend.
        pause
        exit /b 1
    )
    echo        OK
) else (
    echo  [2/3] Frontend ya construido -- omitiendo.
)

:: ── Mostrar informacion de acceso ─────────────────────────────────────────
echo  [3/3] Iniciando servidor...
echo.

if "%MODO%"=="red" (
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
        for /f "tokens=* delims= " %%b in ("%%a") do set LOCAL_IP=%%b
        goto :show_info
    )
    :show_info
    echo  -------------------------------------------------------
    echo   Este equipo  :  http://localhost:8000
    echo   Otros en red :  http://%LOCAL_IP%:8000
    echo.
    echo   Comparta la segunda URL con quienes quieran conectarse
    echo   desde la misma red WiFi o LAN.
    echo  -------------------------------------------------------
) else (
    echo  -------------------------------------------------------
    echo   Abrir en el navegador: http://localhost:8000
    echo  -------------------------------------------------------
)
echo.
echo  Presione Ctrl+C para detener el servidor.
echo.

:: Abrir el navegador en este equipo tras 3 segundos
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8000"

:: Iniciar uvicorn
python -m uvicorn main:app --host %HOST% --port 8000
