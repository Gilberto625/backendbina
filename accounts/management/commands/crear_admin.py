# accounts/management/commands/crear_admin.py
"""
Comando para crear un usuario administrador
Uso: python manage.py crear_admin --email=admin@example.com --password=tu_password
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Crea un usuario administrador'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email del administrador',
            required=True
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Contraseña del administrador',
            required=True
        )
        parser.add_argument(
            '--nombre',
            type=str,
            help='Nombre del administrador',
            default='Admin'
        )
        parser.add_argument(
            '--apellido',
            type=str,
            help='Apellido del administrador',
            default='Sistema'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        nombre = options['nombre']
        apellido = options['apellido']

        try:
            # Buscar o crear usuario
            usuario, created = Usuario.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                }
            )
            
            if not created:
                self.stdout.write(
                    self.style.WARNING(f'🔄 Usuario {email} ya existe. Actualizando a administrador...')
                )
            
            # Configurar TODOS los campos requeridos
            usuario.set_password(password)
            usuario.first_name = nombre
            usuario.last_name = apellido
            usuario.rol = 'administrador'
            usuario.is_staff = True
            usuario.is_superuser = True
            usuario.activo = True
            usuario.verificado = False  # False para permitir login sin 2FA
            usuario.confirmado = False
            usuario.intentos_fallidos = 0
            usuario.inasistencias_consecutivas = 0
            usuario.requiere_anticipo_obligatorio = False
            usuario.citas_penalizadas_restantes = 0
            usuario.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Administrador {"creado" if created else "actualizado"} exitosamente!')
            )
            self.stdout.write(f'   Email: {email}')
            self.stdout.write(f'   Nombre: {nombre} {apellido}')
            self.stdout.write(f'   Rol: {usuario.rol}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear administrador: {str(e)}')
            )
