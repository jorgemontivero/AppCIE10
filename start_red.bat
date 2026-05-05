@echo off
chcp 65001 >nul 2>&1

echo.
echo  ====================================================
echo    App CIE-10 -- Causa Basica de Defuncion
echo    Modo: red local
echo  ====================================================
echo.

call "%~dp0_start_core.bat" 0.0.0.0
