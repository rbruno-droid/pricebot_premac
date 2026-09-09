@echo off
cd /d "%~dp0"
echo =========================================
echo PREMAC PRICEBOT - INSTALADOR PYTHON 3.12
echo =========================================
echo.
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo No se encontro Python 3.12.
    echo Ejecuta: py -0
    echo Debe aparecer Python 3.12 64-bit.
    pause
    exit /b 1
)

if exist .venv (
    echo Borrando entorno virtual anterior...
    rmdir /s /q .venv
)

echo Creando entorno virtual con Python 3.12...
py -3.12 -m venv .venv
if errorlevel 1 (
    echo Error creando el entorno virtual.
    pause
    exit /b 1
)

echo Actualizando pip...
.venv\Scripts\python.exe -m pip install --upgrade pip

echo Instalando dependencias...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Fallo la instalacion de dependencias.
    echo Verifica que este usando Python 3.12 y no Python 3.13.
    echo Ejecuta: .venv\Scripts\python.exe --version
    pause
    exit /b 1
)

echo.
echo Instalacion finalizada correctamente.
echo Para iniciar usa: iniciar_pricebot.bat
pause
