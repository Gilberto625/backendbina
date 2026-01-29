# configuracion/services.py
"""
Servicios y lógica de negocio para administración y métricas
"""
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta
from decimal import Decimal

from citas.models import Cita
from productos.models import Compra
from pagos.models import Pago
from accounts.models import Usuario
from barberos.models import Barbero
from configuracion.models import ConfiguracionSistema


class AdminService:
    """Servicio para métricas y administración"""
    
    @staticmethod
    def calcular_metricas(fecha_inicio=None, fecha_fin=None):
        """
        Calcula métricas de negocio para un período
        
        Args:
            fecha_inicio: datetime (opcional)
            fecha_fin: datetime (opcional)
        
        Returns:
            dict con métricas
        """
        ahora = timezone.now()
        
        # Si no se especifican fechas, usar último mes
        if not fecha_inicio:
            fecha_inicio = ahora - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = ahora
        
        # Filtrar por fechas
        filtro_fecha = Q(fecha_creacion__gte=fecha_inicio, fecha_creacion__lte=fecha_fin)
        
        # Métricas de citas
        citas_totales = Cita.objects.filter(
            fecha_hora__gte=fecha_inicio,
            fecha_hora__lte=fecha_fin
        ).count()
        
        citas_completadas = Cita.objects.filter(
            fecha_hora__gte=fecha_inicio,
            fecha_hora__lte=fecha_fin,
            estado='completada'
        ).count()
        
        citas_canceladas = Cita.objects.filter(
            fecha_hora__gte=fecha_inicio,
            fecha_hora__lte=fecha_fin,
            estado='cancelada'
        ).count()
        
        citas_no_asistio = Cita.objects.filter(
            fecha_hora__gte=fecha_inicio,
            fecha_hora__lte=fecha_fin,
            estado='no_asistio'
        ).count()
        
        # Ingresos de citas
        ingresos_citas = Pago.objects.filter(
            filtro_fecha,
            cita__isnull=False,
            estado='completado'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
        
        # Métricas de compras
        compras_totales = Compra.objects.filter(filtro_fecha).count()
        compras_completadas = Compra.objects.filter(
            filtro_fecha,
            estado='entregado'
        ).count()
        
        # Ingresos de compras
        ingresos_compras = Pago.objects.filter(
            filtro_fecha,
            compra__isnull=False,
            estado='completado'
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
        
        # Ingresos totales
        ingresos_totales = ingresos_citas + ingresos_compras
        
        # Servicios más solicitados
        servicios_mas_solicitados = Cita.objects.filter(
            fecha_hora__gte=fecha_inicio,
            fecha_hora__lte=fecha_fin,
            estado='completada'
        ).values('servicio__nombre', 'servicio__categoria').annotate(
            cantidad=Count('id')
        ).order_by('-cantidad')[:5]
        
        # Días más concurridos
        dias_concurridos = Cita.objects.filter(
            fecha_hora__gte=fecha_inicio,
            fecha_hora__lte=fecha_fin,
            estado='completada'
        ).extra(
            select={'dia': "DATE(fecha_hora)"}
        ).values('dia').annotate(
            cantidad=Count('id')
        ).order_by('-cantidad')[:7]
        
        # Tasa de asistencia
        tasa_asistencia = 0
        if citas_totales > 0:
            tasa_asistencia = (citas_completadas / citas_totales) * 100
        
        # Tasa de cancelación
        tasa_cancelacion = 0
        if citas_totales > 0:
            tasa_cancelacion = (citas_canceladas / citas_totales) * 100
        
        return {
            'periodo': {
                'fecha_inicio': fecha_inicio.isoformat(),
                'fecha_fin': fecha_fin.isoformat(),
            },
            'citas': {
                'totales': citas_totales,
                'completadas': citas_completadas,
                'canceladas': citas_canceladas,
                'no_asistio': citas_no_asistio,
                'tasa_asistencia': round(tasa_asistencia, 2),
                'tasa_cancelacion': round(tasa_cancelacion, 2),
            },
            'compras': {
                'totales': compras_totales,
                'completadas': compras_completadas,
            },
            'ingresos': {
                'citas': float(ingresos_citas),
                'compras': float(ingresos_compras),
                'total': float(ingresos_totales),
            },
            'servicios_mas_solicitados': list(servicios_mas_solicitados),
            'dias_concurridos': list(dias_concurridos),
        }
    
    @staticmethod
    def generar_reporte_financiero(fecha_inicio=None, fecha_fin=None):
        """
        Genera un reporte financiero detallado
        
        Args:
            fecha_inicio: datetime (opcional)
            fecha_fin: datetime (opcional)
        
        Returns:
            dict con reporte financiero
        """
        ahora = timezone.now()
        
        if not fecha_inicio:
            fecha_inicio = ahora - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = ahora
        
        filtro_fecha = Q(fecha_creacion__gte=fecha_inicio, fecha_creacion__lte=fecha_fin)
        
        # Pagos completados
        pagos = Pago.objects.filter(
            filtro_fecha,
            estado='completado'
        ).select_related('cita', 'compra', 'cliente')
        
        # Agrupar por método de pago
        pagos_por_metodo = pagos.values('metodo_pago').annotate(
            total=Sum('monto'),
            cantidad=Count('id')
        )
        
        # Pagos por día
        pagos_por_dia = pagos.extra(
            select={'dia': "DATE(fecha_creacion)"}
        ).values('dia').annotate(
            total=Sum('monto'),
            cantidad=Count('id')
        ).order_by('dia')
        
        # Top clientes
        top_clientes = pagos.values('cliente__email', 'cliente__first_name', 'cliente__last_name').annotate(
            total=Sum('monto'),
            cantidad=Count('id')
        ).order_by('-total')[:10]
        
        # Ingresos por tipo
        ingresos_citas = pagos.filter(cita__isnull=False).aggregate(total=Sum('monto'))['total'] or Decimal('0')
        ingresos_compras = pagos.filter(compra__isnull=False).aggregate(total=Sum('monto'))['total'] or Decimal('0')
        
        return {
            'periodo': {
                'fecha_inicio': fecha_inicio.isoformat(),
                'fecha_fin': fecha_fin.isoformat(),
            },
            'resumen': {
                'total_ingresos': float(pagos.aggregate(total=Sum('monto'))['total'] or Decimal('0')),
                'total_pagos': pagos.count(),
                'ingresos_citas': float(ingresos_citas),
                'ingresos_compras': float(ingresos_compras),
            },
            'pagos_por_metodo': list(pagos_por_metodo),
            'pagos_por_dia': list(pagos_por_dia),
            'top_clientes': list(top_clientes),
        }
    
    @staticmethod
    def clasificar_dia_semana(dia_semana, demanda, configuracion=None):
        """
        Clasifica un día de la semana por demanda
        
        Args:
            dia_semana: int (0=Lunes, 6=Domingo)
            demanda: str ('alta', 'media', 'baja')
            configuracion: dict con configuración opcional
        
        Returns:
            ConfiguracionSistema actualizada o creada
        """
        config_obj, created = ConfiguracionSistema.objects.get_or_create(
            dia_semana=dia_semana,
            defaults={
                'demanda': demanda,
            }
        )
        
        if not created:
            config_obj.demanda = demanda
        
        # Actualizar configuración si se proporciona
        if configuracion:
            if 'dias_anticipacion_alta' in configuracion:
                config_obj.dias_anticipacion_alta = configuracion['dias_anticipacion_alta']
            if 'dias_anticipacion_media' in configuracion:
                config_obj.dias_anticipacion_media = configuracion['dias_anticipacion_media']
            if 'dias_anticipacion_baja' in configuracion:
                config_obj.dias_anticipacion_baja = configuracion['dias_anticipacion_baja']
            if 'dias_cancelacion_alta' in configuracion:
                config_obj.dias_cancelacion_alta = configuracion['dias_cancelacion_alta']
            if 'dias_cancelacion_media' in configuracion:
                config_obj.dias_cancelacion_media = configuracion['dias_cancelacion_media']
            if 'dias_cancelacion_baja' in configuracion:
                config_obj.dias_cancelacion_baja = configuracion['dias_cancelacion_baja']
        
        config_obj.save()
        return config_obj
