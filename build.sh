#!/usr/bin/env bash

# exit on error
set -o errexit

echo "=========================================="
echo "🚀 INICIANDO BUILD DE STYLO BARBER CONNECT"
echo "=========================================="

pip install -r requirements.txt

python manage.py collectstatic --no-input

echo "📦 Ejecutando migraciones..."
python manage.py migrate

# Crear datos iniciales (sillas, servicios, configuración)
echo "📋 Creando datos iniciales..."
python manage.py crear_datos_iniciales || echo "⚠️ crear_datos_iniciales falló o ya existe"

# Crear administrador automáticamente si las variables están configuradas
echo "=========================================="
echo "🔐 CONFIGURANDO ADMINISTRADOR"
echo "=========================================="

if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
    echo "📧 Email configurado: $ADMIN_EMAIL"
    echo "🔑 Password configurado: [OCULTO]"
    echo "👤 Nombre: ${ADMIN_NOMBRE:-Admin}"
    echo "👤 Apellido: ${ADMIN_APELLIDO:-Sistema}"
    echo ""
    echo "Ejecutando comando crear_admin..."
    python manage.py crear_admin --email="$ADMIN_EMAIL" --password="$ADMIN_PASSWORD" --nombre="${ADMIN_NOMBRE:-Admin}" --apellido="${ADMIN_APELLIDO:-Sistema}"
    echo ""
    echo "=========================================="
    echo "✅ PROCESO DE ADMINISTRADOR COMPLETADO"
    echo "=========================================="
else
    echo "⚠️ Variables ADMIN_EMAIL y/o ADMIN_PASSWORD no configuradas"
    echo "   No se creará administrador automáticamente"
fi

echo ""
echo "=========================================="
echo "🎉 BUILD COMPLETADO EXITOSAMENTE"
echo "=========================================="
