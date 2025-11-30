#!/bin/bash
# Script para verificar vulnerabilidades en dependencias
# Uso: ./scripts/verificar_dependencias.sh

echo "=========================================="
echo "VERIFICACIÓN DE DEPENDENCIAS SEGURAS"
echo "=========================================="
echo ""

# Verificar si safety está instalado
if ! command -v safety &> /dev/null; then
    echo "⚠️  Safety no está instalado. Instalando..."
    pip install safety
fi

echo "1. Verificando con Safety (Python)..."
echo "----------------------------------------"
safety check --file requirements.txt
echo ""

# Verificar si snyk está instalado
if command -v snyk &> /dev/null; then
    echo "2. Verificando con Snyk..."
    echo "----------------------------------------"
    snyk test --file=requirements.txt
    echo ""
else
    echo "⚠️  Snyk no está instalado. Instalar con: npm install -g snyk"
    echo ""
fi

echo "3. Verificando versiones de Django..."
echo "----------------------------------------"
python -c "import django; print(f'Django version: {django.__version__}')"
echo ""

echo "=========================================="
echo "VERIFICACIÓN COMPLETA"
echo "=========================================="
echo ""
echo "Recomendaciones:"
echo "- Revisar CVEs críticas y actualizar dependencias"
echo "- Ejecutar este script semanalmente"
echo "- Mantener Django y dependencias actualizadas"

