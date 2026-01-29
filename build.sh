#!/usr/bin/env bash

# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate

# Crear datos iniciales (sillas, servicios, configuración)
python manage.py crear_datos_iniciales || true

# Crear administrador automáticamente si las variables están configuradas
# Configurar en Render: ADMIN_EMAIL y ADMIN_PASSWORD
if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
    echo "🔐 Creando/actualizando usuario administrador..."
    python manage.py crear_admin --email="$ADMIN_EMAIL" --password="$ADMIN_PASSWORD" --nombre="${ADMIN_NOMBRE:-Admin}" --apellido="${ADMIN_APELLIDO:-Sistema}" || true
    echo "✅ Administrador configurado"
fi