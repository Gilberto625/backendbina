# barberos/services.py
"""
Servicios y lógica de negocio para el módulo de barberos
"""
from django.utils import timezone
from datetime import datetime, timedelta
from barberos.models import Barbero, ServicioBarbero
from citas.models import Cita, Servicio
from citas.services import ValidacionCitasService
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class BarberosService:
    """Servicio para gestión de barberos"""
    
    @staticmethod
    def obtener_disponibilidad_barbero(barbero, fecha):
        """
        Obtiene los horarios disponibles de un barbero para una fecha específica
        
        Args:
            barbero: Objeto Barbero
            fecha: datetime.date
        
        Returns:
            Lista de horarios disponibles (datetime)
        """
        # Usar el servicio de validación de citas
        horarios = ValidacionCitasService.obtener_horarios_disponibles(
            fecha=fecha,
            barbero=barbero.usuario,
            servicio=None  # No filtrar por servicio específico
        )
        
        return horarios
    
    @staticmethod
    def obtener_citas_barbero(barbero, fecha_inicio=None, fecha_fin=None, estado=None):
        """
        Obtiene las citas de un barbero con filtros opcionales
        
        Args:
            barbero: Objeto Barbero
            fecha_inicio: datetime (opcional)
            fecha_fin: datetime (opcional)
            estado: str (opcional)
        
        Returns:
            QuerySet de citas
        """
        citas = Cita.objects.filter(barbero=barbero.usuario).select_related(
            'cliente', 'servicio', 'silla'
        )
        
        if fecha_inicio:
            citas = citas.filter(fecha_hora__gte=fecha_inicio)
        
        if fecha_fin:
            citas = citas.filter(fecha_hora__lte=fecha_fin)
        
        if estado:
            citas = citas.filter(estado=estado)
        
        return citas.order_by('fecha_hora')
    
    @staticmethod
    def obtener_servicios_barbero(barbero):
        """
        Obtiene los servicios que puede realizar un barbero
        
        Args:
            barbero: Objeto Barbero
        
        Returns:
            Lista de servicios con duración
        """
        servicios_barbero = ServicioBarbero.objects.filter(
            barbero=barbero,
            activo=True
        ).select_related('servicio')
        
        return servicios_barbero
    
    @staticmethod
    def asignar_servicio_barbero(barbero, servicio, duracion_minutos):
        """
        Asigna un servicio a un barbero con su duración específica
        
        Args:
            barbero: Objeto Barbero
            servicio: Objeto Servicio
            duracion_minutos: int
        
        Returns:
            (servicio_barbero: ServicioBarbero, created: bool)
        """
        servicio_barbero, created = ServicioBarbero.objects.get_or_create(
            barbero=barbero,
            servicio=servicio,
            defaults={
                'duracion_minutos': duracion_minutos,
                'activo': True
            }
        )
        
        if not created:
            # Actualizar duración si ya existe
            servicio_barbero.duracion_minutos = duracion_minutos
            servicio_barbero.activo = True
            servicio_barbero.save()
        
        return servicio_barbero, created
    
    @staticmethod
    def desactivar_servicio_barbero(barbero, servicio):
        """
        Desactiva un servicio de un barbero
        
        Args:
            barbero: Objeto Barbero
            servicio: Objeto Servicio
        
        Returns:
            bool (True si se desactivó)
        """
        try:
            servicio_barbero = ServicioBarbero.objects.get(
                barbero=barbero,
                servicio=servicio
            )
            servicio_barbero.activo = False
            servicio_barbero.save()
            return True
        except ServicioBarbero.DoesNotExist:
            return False
    
    @staticmethod
    def crear_barbero_desde_usuario(usuario, fecha_contratacion=None, especialidades=''):
        """
        Crea un perfil de barbero desde un usuario existente
        
        Args:
            usuario: Objeto Usuario (debe tener rol='barbero')
            fecha_contratacion: date (opcional)
            especialidades: str (opcional)
        
        Returns:
            Barbero creado
        """
        if usuario.rol != 'barbero':
            raise ValueError('El usuario debe tener rol barbero')
        
        barbero, created = Barbero.objects.get_or_create(
            usuario=usuario,
            defaults={
                'activo': True,
                'fecha_contratacion': fecha_contratacion,
                'especialidades': especialidades
            }
        )
        
        if not created:
            # Actualizar si ya existe
            barbero.activo = True
            if fecha_contratacion:
                barbero.fecha_contratacion = fecha_contratacion
            if especialidades:
                barbero.especialidades = especialidades
            barbero.save()
        
        return barbero
