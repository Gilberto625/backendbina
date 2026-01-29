# accounts/tests.py
from django.test import TestCase
from accounts.models import Usuario


class UsuarioModelTest(TestCase):
    """Tests para el modelo Usuario"""
    
    def test_crear_usuario_cliente(self):
        """Test: Crear usuario con rol cliente"""
        usuario = Usuario.objects.create_user(
            username='cliente@test.com',
            email='cliente@test.com',
            password='test123',
            rol='cliente'
        )
        
        self.assertEqual(usuario.rol, 'cliente')
        self.assertTrue(usuario.es_cliente())
        self.assertFalse(usuario.es_secretaria())
        self.assertFalse(usuario.es_barbero())
        self.assertFalse(usuario.es_administrador())
    
    def test_crear_usuario_barbero(self):
        """Test: Crear usuario con rol barbero"""
        usuario = Usuario.objects.create_user(
            username='barbero@test.com',
            email='barbero@test.com',
            password='test123',
            rol='barbero'
        )
        
        self.assertEqual(usuario.rol, 'barbero')
        self.assertTrue(usuario.es_barbero())
    
    def test_puede_agendar_sin_anticipo_primera_cita(self):
        """Test: Cliente puede agendar sin anticipo en primera cita"""
        cliente = Usuario.objects.create_user(
            username='cliente@test.com',
            email='cliente@test.com',
            password='test123',
            rol='cliente'
        )
        
        self.assertTrue(cliente.puede_agendar_sin_anticipo())
    
    def test_requiere_anticipo_obligatorio_penalizado(self):
        """Test: Cliente penalizado requiere anticipo obligatorio"""
        from citas.models import Cita, Servicio
        from django.utils import timezone
        from datetime import timedelta
        
        cliente = Usuario.objects.create_user(
            username='cliente@test.com',
            email='cliente@test.com',
            password='test123',
            rol='cliente'
        )
        
        # Crear una cita previa para que no sea primera cita
        servicio = Servicio.objects.create(
            nombre='Corte',
            precio_base=150.00,
            duracion_minutos=30,
            activo=True
        )
        fecha_pasada = timezone.now() - timedelta(days=5)
        Cita.objects.create(
            cliente=cliente,
            servicio=servicio,
            fecha_hora=fecha_pasada,
            duracion_minutos=30,
            precio_total=150.00,
            estado='completada',
            registrado_por=cliente
        )
        
        cliente.requiere_anticipo_obligatorio = True
        cliente.citas_penalizadas_restantes = 5
        cliente.save()
        
        self.assertFalse(cliente.puede_agendar_sin_anticipo())
