# citas/serializers.py
"""
Funciones para serializar objetos de citas a diccionarios
"""
from citas.models import Cita, Servicio, Silla


def serializar_cita(cita, incluir_detalles=False):
    """
    Serializa una cita a diccionario
    
    Args:
        cita: Objeto Cita
        incluir_detalles: Si True, incluye información detallada de relaciones
    
    Returns:
        dict con datos de la cita
    """
    datos = {
        'id': cita.id,
        'fecha_hora': cita.fecha_hora.isoformat(),
        'estado': cita.estado,
        'precio_total': float(cita.precio_total),
        'anticipo_pagado': float(cita.anticipo_pagado),
        'anticipo_requerido': float(cita.anticipo_requerido),
        'duracion_minutos': cita.duracion_minutos,
    }
    
    if incluir_detalles:
        datos.update({
            'fecha_creacion': cita.fecha_creacion.isoformat(),
            'fecha_actualizacion': cita.fecha_actualizacion.isoformat(),
            'fecha_asistencia': cita.fecha_asistencia.isoformat() if cita.fecha_asistencia else None,
            'fecha_cancelacion': cita.fecha_cancelacion.isoformat() if cita.fecha_cancelacion else None,
            'notas': cita.notas,
            'motivo_cancelacion': cita.motivo_cancelacion,
            'servicio': {
                'id': cita.servicio.id,
                'nombre': cita.servicio.nombre,
                'descripcion': cita.servicio.descripcion,
                'precio_base': float(cita.servicio.precio_base),
                'categoria': cita.servicio.categoria,
            },
            'cliente': {
                'id': cita.cliente.id,
                'email': cita.cliente.email,
                'nombre': cita.cliente.get_full_name() or cita.cliente.email,
            },
            'barbero': {
                'id': cita.barbero.id,
                'nombre': cita.barbero.get_full_name() if cita.barbero else None,
                'email': cita.barbero.email if cita.barbero else None,
            } if cita.barbero else None,
            'silla': {
                'id': cita.silla.id,
                'nombre': cita.silla.nombre,
                'numero': cita.silla.numero,
            } if cita.silla else None,
        })
    else:
        datos.update({
            'servicio': {
                'id': cita.servicio.id,
                'nombre': cita.servicio.nombre,
            },
        })
    
    return datos


def serializar_servicio(servicio):
    """Serializa un servicio a diccionario"""
    return {
        'id': servicio.id,
        'nombre': servicio.nombre,
        'descripcion': servicio.descripcion,
        'precio_base': float(servicio.precio_base),
        'duracion_minutos': servicio.duracion_minutos,
        'categoria': servicio.categoria,
        'categoria_display': servicio.get_categoria_display(),
    }


def serializar_silla(silla):
    """Serializa una silla a diccionario"""
    return {
        'id': silla.id,
        'numero': silla.numero,
        'nombre': silla.nombre,
        'activa': silla.activa,
    }
