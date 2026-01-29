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

        # Verificar si ya existe
        if Usuario.objects.filter(email=email).exists():
            usuario = Usuario.objects.get(email=email)
            self.stdout.write(
                self.style.WARNING(f'El usuario {email} ya existe.')
            )
            
            # Actualizar rol a administrador si no lo es
            if usuario.rol != 'administrador':
                usuario.rol = 'administrador'
                usuario.is_staff = True
                usuario.is_superuser = True
                usuario.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Usuario {email} actualizado a administrador.')
                )
            return

        # Crear usuario administrador
        try:
            usuario = Usuario.objects.create_user(
                email=email,
                password=password,
                username=email.split('@')[0],
                nombre=nombre,
                apellidopaterno=apellido,
                rol='administrador',
                is_staff=True,
                is_superuser=True,
                activo=True,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Administrador creado exitosamente!')
            )
            self.stdout.write(f'   Email: {email}')
            self.stdout.write(f'   Nombre: {nombre} {apellido}')
            self.stdout.write(f'   Rol: administrador')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear administrador: {str(e)}')
            )
