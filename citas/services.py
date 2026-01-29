# citas/services.py
"""
Servicios y lógica de negocio para el módulo de citas
"""
from django.utils import timezone
from datetime import timedelta, datetime
from citas.models import Cita, Silla, Servicio
from barberos.models import Barbero, ServicioBarbero
from configuracion.models import ConfiguracionSistema
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class ValidacionCitasService:
    """Servicio para validar reglas de negocio de citas"""
    
    @staticmethod
    def obtener_configuracion_dia(fecha):
        """Obtiene la configuración del sistema para un día específico"""
        dia_semana = fecha.weekday()  # 0=Lunes, 6=Domingo
        return ConfiguracionSistema.get_configuracion_dia(dia_semana)
    
    @staticmethod
    def puede_agendar_en_fecha(cliente, fecha):
        """
        Verifica si el cliente puede agendar en la fecha especificada
        según las reglas de anticipación
        """
        ahora = timezone.now()
        dias_diferencia = (fecha.date() - ahora.date()).days
        
        if dias_diferencia < 0:
            return False, 'No se pueden agendar citas en fechas pasadas'
        
        config = ValidacionCitasService.obtener_configuracion_dia(fecha)
        
        # Determinar días mínimos según demanda
        if config.demanda == 'alta':
            dias_minimos = config.dias_anticipacion_alta
        elif config.demanda == 'media':
            dias_minimos = config.dias_anticipacion_media
        else:  # baja
            dias_minimos = config.dias_anticipacion_baja
        
        if dias_diferencia < dias_minimos:
            return False, f'Debes agendar con al menos {dias_minimos} día(s) de anticipación para este día'
        
        return True, None
    
    @staticmethod
    def puede_cancelar_cita(cita):
        """
        Verifica si una cita puede ser cancelada según las reglas de negocio
        """
        if cita.estado in ['cancelada', 'completada', 'no_asistio']:
            return False, 'La cita ya está cancelada o completada'
        
        ahora = timezone.now()
        tiempo_restante = cita.fecha_hora - ahora
        
        if tiempo_restante.total_seconds() < 0:
            return False, 'La cita ya pasó'
        
        config = ValidacionCitasService.obtener_configuracion_dia(cita.fecha_hora)
        
        # Determinar días mínimos según demanda
        if config.demanda == 'alta':
            dias_minimos = config.dias_cancelacion_alta
        elif config.demanda == 'media':
            dias_minimos = config.dias_cancelacion_media
        else:  # baja
            dias_minimos = config.dias_cancelacion_baja
        
        if tiempo_restante.days < dias_minimos:
            return False, f'Debes cancelar con al menos {dias_minimos} día(s) de anticipación'
        
        return True, None
    
    @staticmethod
    def calcular_anticipo_requerido(cliente, servicio):
        """
        Calcula el anticipo requerido según las reglas de negocio
        """
        # Primera cita: no requiere anticipo
        if cliente.puede_agendar_sin_anticipo():
            return 0
        
        # Cliente con penalización: 50% del precio
        if cliente.requiere_anticipo_obligatorio:
            config = ConfiguracionSistema.objects.first()
            if config:
                porcentaje = float(config.porcentaje_anticipo_penalizado) / 100
            else:
                porcentaje = 0.5  # Por defecto 50%
            
            return float(servicio.precio_base) * porcentaje
        
        # Por defecto: no requiere anticipo (primera cita)
        return 0
    
    @staticmethod
    def verificar_disponibilidad(barbero, silla, fecha_hora, duracion_minutos, cita_excluir=None):
        """
        Verifica si hay disponibilidad para un barbero y silla en un horario específico
        
        Args:
            barbero: Usuario barbero
            silla: Objeto Silla
            fecha_hora: datetime de inicio de la cita
            duracion_minutos: Duración de la cita en minutos
            cita_excluir: Cita a excluir de la verificación (para actualizaciones)
        
        Returns:
            (disponible: bool, mensaje: str)
        """
        # Calcular hora de fin
        hora_fin = fecha_hora + timedelta(minutes=duracion_minutos)
        
        # Verificar conflictos con otras citas
        citas_existentes = Cita.objects.filter(
            fecha_hora__lt=hora_fin,
            fecha_hora__gte=fecha_hora - timedelta(minutes=duracion_minutos),
            estado__in=['pendiente', 'confirmada', 'en_proceso']
        )
        
        # Excluir la cita actual si se está actualizando
        if cita_excluir:
            citas_existentes = citas_existentes.exclude(id=cita_excluir.id)
        
        # Verificar conflictos con barbero
        if barbero:
            citas_barbero = citas_existentes.filter(barbero=barbero)
            if citas_barbero.exists():
                return False, 'El barbero ya tiene una cita en ese horario'
        
        # Verificar conflictos con silla
        if silla:
            citas_silla = citas_existentes.filter(silla=silla)
            if citas_silla.exists():
                return False, 'La silla ya está ocupada en ese horario'
        
        return True, None
    
    @staticmethod
    def obtener_horarios_disponibles(fecha, barbero=None, silla=None, servicio=None):
        """
        Obtiene los horarios disponibles para una fecha específica
        
        Args:
            fecha: datetime.date
            barbero: Usuario barbero (opcional)
            silla: Objeto Silla (opcional)
            servicio: Objeto Servicio (para obtener duración)
        
        Returns:
            Lista de horarios disponibles (datetime)
        """
        # Horario de trabajo (ejemplo: 9:00 AM a 7:00 PM)
        hora_inicio = 9
        hora_fin = 19
        
        # Duración del servicio
        if servicio:
            duracion = servicio.duracion_minutos
        else:
            duracion = 30  # Por defecto 30 minutos
        
        # Obtener todas las citas del día
        inicio_dia = timezone.make_aware(datetime.combine(fecha, datetime.min.time().replace(hour=hora_inicio)))
        fin_dia = timezone.make_aware(datetime.combine(fecha, datetime.min.time().replace(hour=hora_fin)))
        
        citas_del_dia = Cita.objects.filter(
            fecha_hora__date=fecha,
            fecha_hora__gte=inicio_dia,
            fecha_hora__lt=fin_dia,
            estado__in=['pendiente', 'confirmada', 'en_proceso']
        )
        
        # Filtrar por barbero si se especifica
        if barbero:
            citas_del_dia = citas_del_dia.filter(barbero=barbero)
        
        # Filtrar por silla si se especifica
        if silla:
            citas_del_dia = citas_del_dia.filter(silla=silla)
        
        # Generar horarios posibles
        horarios_disponibles = []
        hora_actual = inicio_dia
        
        while hora_actual < fin_dia:
            hora_fin_cita = hora_actual + timedelta(minutes=duracion)
            
            # Verificar si hay conflicto
            conflicto = citas_del_dia.filter(
                fecha_hora__lt=hora_fin_cita,
                fecha_hora__gte=hora_actual - timedelta(minutes=duracion)
            ).exists()
            
            if not conflicto:
                horarios_disponibles.append(hora_actual)
            
            # Avanzar en intervalos de 30 minutos
            hora_actual += timedelta(minutes=30)
        
        return horarios_disponibles
    
    @staticmethod
    def cancelar_citas_por_tardanza():
        """
        Cancela automáticamente las citas que han pasado el tiempo de espera máximo
        Se debe ejecutar periódicamente (ej: cada minuto con Celery)
        """
        ahora = timezone.now()
        config = ConfiguracionSistema.objects.first()
        
        if not config:
            tiempo_espera = 10  # Por defecto 10 minutos
        else:
            tiempo_espera = config.tiempo_espera_maximo
        
        # Buscar citas que deberían haberse iniciado pero no tienen asistencia
        citas_pendientes = Cita.objects.filter(
            estado__in=['pendiente', 'confirmada'],
            fecha_hora__lt=ahora - timedelta(minutes=tiempo_espera),
            fecha_asistencia__isnull=True
        )
        
        canceladas = 0
        for cita in citas_pendientes:
            cita.marcar_no_asistencia()
            canceladas += 1
        
        return canceladas
