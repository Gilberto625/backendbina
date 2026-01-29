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

        self.stdout.write(f'📧 Buscando usuario con email: {email}')

        try:
            # Buscar usuario existente
            try:
                usuario = Usuario.objects.get(email=email)
                self.stdout.write(
                    self.style.WARNING(f'🔄 Usuario encontrado (ID: {usuario.id}). Rol actual: {usuario.rol}')
                )
                created = False
            except Usuario.DoesNotExist:
                # Crear nuevo usuario
                self.stdout.write(f'📝 Usuario no existe, creando nuevo...')
                usuario = Usuario(
                    email=email,
                    username=email.split('@')[0],
                )
                created = True
            
            # Configurar TODOS los campos
            self.stdout.write(f'⚙️ Configurando campos del administrador...')
            
            usuario.set_password(password)
            usuario.first_name = nombre
            usuario.last_name = apellido
            usuario.rol = 'administrador'
            usuario.is_staff = True
            usuario.is_superuser = True
            usuario.is_active = True
            usuario.activo = True
            usuario.verificado = False  # False para login sin 2FA
            usuario.confirmado = False
            usuario.intentos_fallidos = 0
            usuario.inasistencias_consecutivas = 0
            usuario.requiere_anticipo_obligatorio = False
            usuario.citas_penalizadas_restantes = 0
            
            # Guardar
            usuario.save()
            self.stdout.write(f'💾 Usuario guardado en base de datos')
            
            # Verificar que se guardó correctamente
            usuario_verificado = Usuario.objects.get(email=email)
            self.stdout.write(f'')
            self.stdout.write(self.style.SUCCESS(f'========================================'))
            self.stdout.write(self.style.SUCCESS(f'✅ ADMINISTRADOR {"CREADO" if created else "ACTUALIZADO"}'))
            self.stdout.write(self.style.SUCCESS(f'========================================'))
            self.stdout.write(f'   ID: {usuario_verificado.id}')
            self.stdout.write(f'   Email: {usuario_verificado.email}')
            self.stdout.write(f'   Username: {usuario_verificado.username}')
            self.stdout.write(f'   Nombre: {usuario_verificado.first_name} {usuario_verificado.last_name}')
            self.stdout.write(self.style.SUCCESS(f'   ROL: {usuario_verificado.rol}'))
            self.stdout.write(f'   is_staff: {usuario_verificado.is_staff}')
            self.stdout.write(f'   is_superuser: {usuario_verificado.is_superuser}')
            self.stdout.write(f'   verificado: {usuario_verificado.verificado}')
            self.stdout.write(f'   activo: {usuario_verificado.activo}')
            self.stdout.write(f'========================================')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear administrador: {str(e)}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())
            raise e  # Re-lanzar para que el build falle
