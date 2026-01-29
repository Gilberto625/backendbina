@echo off
REM Script para crear migraciones y datos iniciales en Windows

echo ========================================
echo Setup de Migraciones y Datos Iniciales
echo ========================================
echo.

REM Verificar si existe el entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Entorno virtual no encontrado.
    echo Por favor, crea el entorno virtual primero:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

echo [1/4] Activando entorno virtual...
call venv\Scripts\activate.bat

echo [2/4] Creando migraciones...
python manage.py makemigrations
if errorlevel 1 (
    echo [ERROR] Error al crear migraciones
    pause
    exit /b 1
)

echo.
echo [3/4] Aplicando migraciones...
python manage.py migrate
if errorlevel 1 (
    echo [ERROR] Error al aplicar migraciones
    pause
    exit /b 1
)

echo.
echo [4/4] Creando datos iniciales...
python manage.py crear_datos_iniciales
if errorlevel 1 (
    echo [ERROR] Error al crear datos iniciales
    pause
    exit /b 1
)

echo.
echo ========================================
echo ¡Proceso completado exitosamente!
echo ========================================
echo.
pause
