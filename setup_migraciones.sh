#!/bin/bash
# Script para crear migraciones y datos iniciales en Linux/Mac

echo "========================================"
echo "Setup de Migraciones y Datos Iniciales"
echo "========================================"
echo ""

# Verificar si existe el entorno virtual
if [ ! -f "venv/bin/activate" ]; then
    echo "[ERROR] Entorno virtual no encontrado."
    echo "Por favor, crea el entorno virtual primero:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

echo "[1/4] Activando entorno virtual..."
source venv/bin/activate

echo "[2/4] Creando migraciones..."
python manage.py makemigrations
if [ $? -ne 0 ]; then
    echo "[ERROR] Error al crear migraciones"
    exit 1
fi

echo ""
echo "[3/4] Aplicando migraciones..."
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "[ERROR] Error al aplicar migraciones"
    exit 1
fi

echo ""
echo "[4/4] Creando datos iniciales..."
python manage.py crear_datos_iniciales
if [ $? -ne 0 ]; then
    echo "[ERROR] Error al crear datos iniciales"
    exit 1
fi

echo ""
echo "========================================"
echo "¡Proceso completado exitosamente!"
echo "========================================"
