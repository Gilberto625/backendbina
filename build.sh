#!/usr/bin/env bash
# build.sh - Script de construcción para Render
# Este script se ejecuta durante el deploy

set -o errexit  # Exit on error

echo "=========================================="
echo "  INICIANDO BUILD - Sistema Barbería"
echo "=========================================="

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Recopilar archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --no-input

# Aplicar migraciones
echo "🔄 Aplicando migraciones..."
python manage.py migrate

# Crear superusuario administrador desde variables de entorno
# Variables de entorno requeridas:
#   ADMIN_EMAIL     - Correo del administrador (ejemplo: admin@barberia.com)
#   ADMIN_PASSWORD  - Contraseña del administrador
#   ADMIN_USERNAME  - Nombre de usuario (opcional, por defecto usa el email)
#   ADMIN_NOMBRE    - Nombre del administrador (opcional)
#   ADMIN_APELLIDO  - Apellido del administrador (opcional)

echo "👤 Configurando administrador..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
import os

Usuario = get_user_model()

# Obtener variables de entorno
admin_email = os.environ.get('ADMIN_EMAIL', '')
admin_password = os.environ.get('ADMIN_PASSWORD', '')
admin_username = os.environ.get('ADMIN_USERNAME', '')
admin_nombre = os.environ.get('ADMIN_NOMBRE', 'Administrador')
admin_apellido = os.environ.get('ADMIN_APELLIDO', 'Sistema')

if admin_email and admin_password:
    # Usar email como username si no se proporciona
    if not admin_username:
        admin_username = admin_email.split('@')[0] + '_admin'
    
    # Verificar si ya existe
    if Usuario.objects.filter(email=admin_email).exists():
        # Actualizar usuario existente
        admin = Usuario.objects.get(email=admin_email)
        admin.set_password(admin_password)
        admin.rol = 'admin'
        admin.is_staff = True
        admin.is_superuser = True
        admin.verificado = True
        admin.first_name = admin_nombre
        admin.last_name = admin_apellido
        admin.save()
        print(f"✅ Administrador actualizado: {admin_email}")
    else:
        # Crear nuevo administrador
        admin = Usuario.objects.create_user(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            first_name=admin_nombre,
            last_name=admin_apellido,
            rol='admin',
            is_staff=True,
            is_superuser=True,
            verificado=True
        )
        print(f"✅ Administrador creado: {admin_email}")
else:
    print("⚠️  Variables ADMIN_EMAIL y ADMIN_PASSWORD no configuradas")
    print("   El administrador debe crearse manualmente")

# Mostrar usuarios administradores existentes
admins = Usuario.objects.filter(rol='admin')
print(f"\n📋 Administradores registrados: {admins.count()}")
for a in admins:
    print(f"   - {a.email} ({a.first_name} {a.last_name})")

EOF

echo ""
echo "=========================================="
echo "  BUILD COMPLETADO EXITOSAMENTE ✅"
echo "=========================================="
echo ""
echo "Variables de entorno para crear admin:"
echo "  ADMIN_EMAIL=admin@ejemplo.com"
echo "  ADMIN_PASSWORD=tuPassword123"
echo "  ADMIN_USERNAME=admin (opcional)"
echo "  ADMIN_NOMBRE=Nombre (opcional)"
echo "  ADMIN_APELLIDO=Apellido (opcional)"
echo ""
