# citas/test_integration.py
"""
Tests de integración para endpoints de citas
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from citas.models import Cita, Servicio, Silla
from configuracion.models import ConfiguracionSistema
import json

Usuario = get_user_model()


class CitasEndpointsIntegrationTest(TestCase):
    """Tests de integración para endpoints de citas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        # Crear usuarios
        self.cliente = Usuario.objects.create_user(
            username='cliente@test.com',
            email='cliente@test.com',
            password='test123',
            rol='cliente'
        )
        self.barbero = Usuario.objects.create_user(
            username='barbero@test.com',
            email='barbero@test.com',
            password='test123',
            rol='barbero'
        )
        self.secretaria = Usuario.objects.create_user(
            username='secretaria@test.com',
            email='secretaria@test.com',
            password='test123',
            rol='secretaria'
        )
        
        # Crear datos necesarios
        self.servicio = Servicio.objects.create(
            nombre='Corte de Cabello',
            precio_base=150.00,
            duracion_minutos=30,
            activo=True
        )
        self.silla = Silla.objects.create(
            numero=1,
            nombre='Silla 1',
            activa=True
        )
        
        # Configuración del sistema
        ConfiguracionSistema.objects.create(
            dia_semana=0,  # Lunes
            demanda='baja',
            dias_anticipacion_baja=1,
            dias_cancelacion_baja=1
        )
    
    def test_listar_servicios_publico(self):
        """Test: Listar servicios (endpoint público)"""
        response = self.client.get('/api/citas/servicios/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get('ok'))
        self.assertIn('servicios', data)
        self.assertGreater(len(data['servicios']), 0)
    
    def test_crear_cita_cliente_autenticado(self):
        """Test: Cliente autenticado puede crear cita"""
        self.client.force_login(self.cliente)
        
        fecha_hora = timezone.now() + timedelta(days=2)
        fecha_str = fecha_hora.isoformat()
        
        data = {
            'servicio_id': self.servicio.id,
            'fecha_hora': fecha_str,
            'barbero_id': self.barbero.id,
            'silla_id': self.silla.id
        }
        
        response = self.client.post(
            '/api/citas/crear/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertTrue(response_data.get('ok'))
        self.assertIn('cita', response_data)
        
        # Verificar que la cita se creó
        cita = Cita.objects.get(cliente=self.cliente)
        self.assertEqual(cita.servicio, self.servicio)
        self.assertEqual(cita.barbero, self.barbero)
    
    def test_crear_cita_sin_autenticacion(self):
        """Test: No se puede crear cita sin autenticación"""
        fecha_hora = timezone.now() + timedelta(days=2)
        fecha_str = fecha_hora.isoformat()
        
        data = {
            'servicio_id': self.servicio.id,
            'fecha_hora': fecha_str,
        }
        
        response = self.client.post(
            '/api/citas/crear/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_mis_citas_cliente(self):
        """Test: Cliente puede ver sus citas"""
        self.client.force_login(self.cliente)
        
        # Crear una cita
        fecha_hora = timezone.now() + timedelta(days=2)
        Cita.objects.create(
            cliente=self.cliente,
            servicio=self.servicio,
            fecha_hora=fecha_hora,
            duracion_minutos=30,
            precio_total=150.00,
            estado='pendiente',
            registrado_por=self.cliente
        )
        
        response = self.client.get('/api/citas/mis-citas/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get('ok'))
        self.assertIn('citas', data)
        self.assertEqual(len(data['citas']), 1)
    
    def test_agenda_completa_secretaria(self):
        """Test: Secretaria puede ver agenda completa"""
        self.client.force_login(self.secretaria)
        
        # Crear una cita
        fecha_hora = timezone.now() + timedelta(days=2)
        Cita.objects.create(
            cliente=self.cliente,
            servicio=self.servicio,
            fecha_hora=fecha_hora,
            duracion_minutos=30,
            precio_total=150.00,
            estado='pendiente',
            registrado_por=self.cliente
        )
        
        response = self.client.get('/api/citas/agenda/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data.get('ok'))
        self.assertIn('citas', data)
    
    def test_agenda_completa_cliente_no_autorizado(self):
        """Test: Cliente no puede ver agenda completa"""
        self.client.force_login(self.cliente)
        
        response = self.client.get('/api/citas/agenda/')
        
        self.assertEqual(response.status_code, 403)
