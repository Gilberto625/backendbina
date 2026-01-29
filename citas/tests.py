# citas/tests.py
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import Usuario
from citas.models import Cita, Servicio, Silla
from citas.services import ValidacionCitasService
from configuracion.models import ConfiguracionSistema


class CitaModelTest(TestCase):
    """Tests para el modelo Cita"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
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
    
    def test_crear_cita(self):
        """Test: Crear una cita básica"""
        fecha_hora = timezone.now() + timedelta(days=2)
        cita = Cita.objects.create(
            cliente=self.cliente,
            barbero=self.barbero,
            servicio=self.servicio,
            silla=self.silla,
            fecha_hora=fecha_hora,
            duracion_minutos=30,
            precio_total=150.00,
            estado='pendiente',
            registrado_por=self.cliente
        )
        
        self.assertEqual(cita.cliente, self.cliente)
        self.assertEqual(cita.barbero, self.barbero)
        self.assertEqual(cita.servicio, self.servicio)
        self.assertEqual(cita.estado, 'pendiente')
        self.assertIsNotNone(cita.fecha_creacion)
    
    def test_calcular_fin_cita(self):
        """Test: Calcular fecha de fin de cita"""
        fecha_hora = timezone.now() + timedelta(days=2)
        cita = Cita.objects.create(
            cliente=self.cliente,
            servicio=self.servicio,
            fecha_hora=fecha_hora,
            duracion_minutos=30,
            precio_total=150.00,
            estado='pendiente',
            registrado_por=self.cliente
        )
        
        fin_esperado = fecha_hora + timedelta(minutes=30)
        self.assertEqual(cita.calcular_fin(), fin_esperado)
    
    def test_marcar_asistencia(self):
        """Test: Marcar cita como asistida"""
        fecha_hora = timezone.now() + timedelta(days=2)
        cita = Cita.objects.create(
            cliente=self.cliente,
            servicio=self.servicio,
            fecha_hora=fecha_hora,
            duracion_minutos=30,
            precio_total=150.00,
            estado='pendiente',
            registrado_por=self.cliente
        )
        
        cita.marcar_asistencia()
        
        self.assertEqual(cita.estado, 'completada')
        self.assertIsNotNone(cita.fecha_asistencia)
    
    def test_marcar_no_asistencia(self):
        """Test: Marcar cita como no asistida y actualizar penalización"""
        fecha_hora = timezone.now() + timedelta(days=2)
        cita = Cita.objects.create(
            cliente=self.cliente,
            servicio=self.servicio,
            fecha_hora=fecha_hora,
            duracion_minutos=30,
            precio_total=150.00,
            estado='pendiente',
            registrado_por=self.cliente
        )
        
        inasistencias_iniciales = self.cliente.inasistencias_consecutivas
        
        cita.marcar_no_asistencia()
        
        self.assertEqual(cita.estado, 'no_asistio')
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.inasistencias_consecutivas, inasistencias_iniciales + 1)
        self.assertTrue(self.cliente.requiere_anticipo_obligatorio)


class ValidacionCitasServiceTest(TestCase):
    """Tests para el servicio de validación de citas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.cliente = Usuario.objects.create_user(
            username='cliente@test.com',
            email='cliente@test.com',
            password='test123',
            rol='cliente'
        )
        self.servicio = Servicio.objects.create(
            nombre='Corte de Cabello',
            precio_base=150.00,
            duracion_minutos=30,
            activo=True
        )
        
        # Crear configuración para lunes (baja demanda)
        ConfiguracionSistema.objects.create(
            dia_semana=0,  # Lunes
            demanda='baja',
            dias_anticipacion_baja=1,
            dias_cancelacion_baja=1
        )
    
    def test_puede_agendar_en_fecha_baja_demanda(self):
        """Test: Puede agendar con 1 día de anticipación en baja demanda"""
        fecha = timezone.now() + timedelta(days=2)  # 2 días después (más de 1 día requerido)
        
        puede, mensaje = ValidacionCitasService.puede_agendar_en_fecha(self.cliente, fecha)
        
        self.assertTrue(puede)
        self.assertIsNone(mensaje)
    
    def test_no_puede_agendar_fecha_pasada(self):
        """Test: No puede agendar en fecha pasada"""
        fecha = timezone.now() - timedelta(days=1)
        
        puede, mensaje = ValidacionCitasService.puede_agendar_en_fecha(self.cliente, fecha)
        
        self.assertFalse(puede)
        self.assertIsNotNone(mensaje)
    
    def test_calcular_anticipo_primera_cita(self):
        """Test: Primera cita no requiere anticipo"""
        anticipo = ValidacionCitasService.calcular_anticipo_requerido(self.cliente, self.servicio)
        
        self.assertEqual(anticipo, 0)
    
    def test_calcular_anticipo_cliente_penalizado(self):
        """Test: Cliente penalizado requiere 50% de anticipo"""
        # Crear una cita previa para que no sea primera cita
        fecha_pasada = timezone.now() - timedelta(days=5)
        Cita.objects.create(
            cliente=self.cliente,
            servicio=self.servicio,
            fecha_hora=fecha_pasada,
            duracion_minutos=30,
            precio_total=150.00,
            estado='completada',
            registrado_por=self.cliente
        )
        
        self.cliente.requiere_anticipo_obligatorio = True
        self.cliente.save()
        
        anticipo = ValidacionCitasService.calcular_anticipo_requerido(self.cliente, self.servicio)
        
        self.assertEqual(anticipo, 75.00)  # 50% de 150.00
