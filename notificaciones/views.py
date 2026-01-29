# notificaciones/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
import json

from core.decorators import (
    requiere_autenticacion,
    requiere_administrador,
    requiere_admin_o_secretaria,
    permite_invitado
)
from core.utils import (
    respuesta_exito,
    respuesta_error,
    obtener_usuario_desde_request,
)
from notificaciones.models import Notificacion, DispositivoFCM
from notificaciones.services import NotificacionesService
from citas.models import Cita
from django.contrib.auth import get_user_model

Usuario = get_user_model()


# ============================================
# ENDPOINTS PARA USUARIOS
# ============================================

@csrf_exempt
@requiere_autenticacion
def mis_notificaciones(request):
    """Lista las notificaciones del usuario autenticado"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        usuario = obtener_usuario_desde_request(request)
        canal = request.GET.get('canal')  # Filtro opcional
        estado = request.GET.get('estado')  # Filtro opcional
        
        notificaciones = Notificacion.objects.filter(usuario=usuario).order_by('-fecha_creacion')
        
        if canal:
            notificaciones = notificaciones.filter(canal=canal)
        
        if estado:
            notificaciones = notificaciones.filter(estado=estado)
        
        datos_notificaciones = [{
            'id': n.id,
            'canal': n.canal,
            'canal_display': n.get_canal_display(),
            'tipo_evento': n.tipo_evento,
            'tipo_evento_display': n.get_tipo_evento_display(),
            'asunto': n.asunto,
            'mensaje': n.mensaje,
            'estado': n.estado,
            'estado_display': n.get_estado_display(),
            'fecha_creacion': n.fecha_creacion.isoformat(),
            'fecha_enviada': n.fecha_enviada.isoformat() if n.fecha_enviada else None,
            'cita_id': n.cita.id if n.cita else None,
            'compra_id': n.compra.id if n.compra else None,
        } for n in notificaciones]
        
        return respuesta_exito('Notificaciones obtenidas', {'notificaciones': datos_notificaciones})
        
    except Exception as e:
        return respuesta_error('Error al obtener notificaciones', detalles=str(e))


# ============================================
# ENDPOINTS PARA ADMIN/SECRETARIA
# ============================================

@csrf_exempt
@requiere_admin_o_secretaria
def enviar_notificacion(request):
    """Envía una notificación manualmente (admin/secretaria)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        data = json.loads(request.body)
        
        canal = data.get('canal', 'email')
        destinatario = data.get('destinatario')
        asunto = data.get('asunto', '')
        mensaje = data.get('mensaje')
        usuario_id = data.get('usuario_id')
        tipo_evento = data.get('tipo_evento', 'otro')
        
        if not destinatario or not mensaje:
            return respuesta_error('destinatario y mensaje son requeridos')
        
        if canal not in ['email', 'sms', 'push']:
            return respuesta_error('canal debe ser: email, sms o push')
        
        # Obtener usuario si se especifica
        usuario = None
        if usuario_id:
            try:
                usuario = Usuario.objects.get(id=usuario_id)
            except Usuario.DoesNotExist:
                return respuesta_error('Usuario no encontrado', codigo=404)
        
        # Enviar notificación según el canal
        if canal == 'email':
            exito, notificacion, error = NotificacionesService.enviar_email(
                destinatario=destinatario,
                asunto=asunto,
                mensaje=mensaje,
                usuario=usuario,
                metadata=data.get('metadata', {})
            )
        elif canal == 'sms':
            exito, notificacion, error = NotificacionesService.enviar_sms(
                destinatario=destinatario,
                mensaje=mensaje,
                usuario=usuario,
                metadata=data.get('metadata', {})
            )
        elif canal == 'push':
            exito, notificacion, error = NotificacionesService.enviar_push(
                destinatario=destinatario,
                titulo=asunto,
                mensaje=mensaje,
                usuario=usuario,
                metadata=data.get('metadata', {})
            )
        
        # Actualizar tipo de evento si se especificó
        if tipo_evento:
            notificacion.tipo_evento = tipo_evento
            notificacion.save()
        
        if exito:
            return respuesta_exito('Notificación enviada exitosamente', {
                'notificacion': {
                    'id': notificacion.id,
                    'canal': notificacion.canal,
                    'estado': notificacion.estado,
                }
            })
        else:
            return respuesta_error(f'Error al enviar notificación: {error}', codigo=500)
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al enviar notificación', detalles=str(e))


@csrf_exempt
@requiere_admin_o_secretaria
def historial_notificaciones(request):
    """Lista todas las notificaciones (admin/secretaria)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        canal = request.GET.get('canal')
        estado = request.GET.get('estado')
        tipo_evento = request.GET.get('tipo_evento')
        usuario_id = request.GET.get('usuario_id')
        
        notificaciones = Notificacion.objects.select_related('usuario', 'cita', 'compra').all()
        
        if canal:
            notificaciones = notificaciones.filter(canal=canal)
        if estado:
            notificaciones = notificaciones.filter(estado=estado)
        if tipo_evento:
            notificaciones = notificaciones.filter(tipo_evento=tipo_evento)
        if usuario_id:
            notificaciones = notificaciones.filter(usuario_id=usuario_id)
        
        notificaciones = notificaciones.order_by('-fecha_creacion')
        
        datos_notificaciones = [{
            'id': n.id,
            'usuario': {
                'id': n.usuario.id,
                'email': n.usuario.email,
                'nombre': n.usuario.get_full_name() or n.usuario.email,
            } if n.usuario else None,
            'canal': n.canal,
            'canal_display': n.get_canal_display(),
            'tipo_evento': n.tipo_evento,
            'tipo_evento_display': n.get_tipo_evento_display(),
            'asunto': n.asunto,
            'destinatario': n.destinatario,
            'estado': n.estado,
            'estado_display': n.get_estado_display(),
            'fecha_creacion': n.fecha_creacion.isoformat(),
            'fecha_enviada': n.fecha_enviada.isoformat() if n.fecha_enviada else None,
            'error': n.error if n.estado == 'fallida' else None,
        } for n in notificaciones]
        
        return respuesta_exito('Notificaciones obtenidas', {'notificaciones': datos_notificaciones})
        
    except Exception as e:
        return respuesta_error('Error al obtener notificaciones', detalles=str(e))


@csrf_exempt
@requiere_administrador
def programar_recordatorio_cita(request, cita_id):
    """Programa un recordatorio para una cita (admin)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            cita = Cita.objects.get(id=cita_id)
        except Cita.DoesNotExist:
            return respuesta_error('Cita no encontrada', codigo=404)
        
        data = json.loads(request.body) if request.body else {}
        horas_antes = data.get('horas_antes', 24)
        
        try:
            horas_antes = float(horas_antes)
            if horas_antes <= 0:
                return respuesta_error('horas_antes debe ser mayor a 0')
        except (ValueError, TypeError):
            return respuesta_error('horas_antes debe ser un número válido')
        
        notificacion = NotificacionesService.programar_recordatorio_cita(cita, horas_antes)
        
        if notificacion:
            return respuesta_exito('Recordatorio programado exitosamente', {
                'notificacion': {
                    'id': notificacion.id,
                    'fecha_programada': notificacion.fecha_programada.isoformat(),
                }
            })
        else:
            return respuesta_error('No se pudo programar el recordatorio (la fecha ya pasó)', codigo=400)
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al programar recordatorio', detalles=str(e))


@csrf_exempt
@requiere_administrador
def procesar_notificaciones_programadas(request):
    """Procesa las notificaciones programadas pendientes (admin)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        procesadas = NotificacionesService.procesar_notificaciones_programadas()
        
        return respuesta_exito(f'{procesadas} notificaciones procesadas', {
            'procesadas': procesadas
        })
        
    except Exception as e:
        return respuesta_error('Error al procesar notificaciones', detalles=str(e))


# ============================================
# ENDPOINTS PARA DISPOSITIVOS FCM
# ============================================

@csrf_exempt
@requiere_autenticacion
def registrar_dispositivo_fcm(request):
    """
    Registra un dispositivo para recibir notificaciones push.
    Si el token ya existe para otro usuario, lo reasigna.
    """
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        usuario = obtener_usuario_desde_request(request)
        data = json.loads(request.body)
        
        token = data.get('token')
        plataforma = data.get('plataforma', 'android')
        nombre_dispositivo = data.get('nombre_dispositivo', '')
        
        if not token:
            return respuesta_error('token es requerido')
        
        if plataforma not in ['android', 'ios', 'web']:
            return respuesta_error('plataforma debe ser: android, ios o web')
        
        # Verificar si el token ya existe
        dispositivo_existente = DispositivoFCM.objects.filter(token=token).first()
        
        if dispositivo_existente:
            # Si ya existe, actualizar usuario y reactivar
            dispositivo_existente.usuario = usuario
            dispositivo_existente.plataforma = plataforma
            dispositivo_existente.nombre_dispositivo = nombre_dispositivo
            dispositivo_existente.activo = True
            dispositivo_existente.save()
            dispositivo = dispositivo_existente
            mensaje = 'Dispositivo actualizado exitosamente'
        else:
            # Crear nuevo dispositivo
            dispositivo = DispositivoFCM.objects.create(
                usuario=usuario,
                token=token,
                plataforma=plataforma,
                nombre_dispositivo=nombre_dispositivo,
                activo=True
            )
            mensaje = 'Dispositivo registrado exitosamente'
        
        return respuesta_exito(mensaje, {
            'dispositivo': {
                'id': dispositivo.id,
                'plataforma': dispositivo.plataforma,
                'nombre_dispositivo': dispositivo.nombre_dispositivo,
                'activo': dispositivo.activo,
                'fecha_registro': dispositivo.fecha_registro.isoformat(),
            }
        })
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al registrar dispositivo', detalles=str(e))


@csrf_exempt
@requiere_autenticacion
def eliminar_dispositivo_fcm(request):
    """Elimina un dispositivo FCM del usuario"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        usuario = obtener_usuario_desde_request(request)
        data = json.loads(request.body)
        
        token = data.get('token')
        dispositivo_id = data.get('dispositivo_id')
        
        if not token and not dispositivo_id:
            return respuesta_error('token o dispositivo_id es requerido')
        
        # Buscar el dispositivo
        if token:
            dispositivo = DispositivoFCM.objects.filter(
                usuario=usuario,
                token=token
            ).first()
        else:
            dispositivo = DispositivoFCM.objects.filter(
                usuario=usuario,
                id=dispositivo_id
            ).first()
        
        if not dispositivo:
            return respuesta_error('Dispositivo no encontrado', codigo=404)
        
        # Eliminar el dispositivo
        dispositivo.delete()
        
        return respuesta_exito('Dispositivo eliminado exitosamente')
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al eliminar dispositivo', detalles=str(e))


@csrf_exempt
@requiere_autenticacion
def listar_dispositivos_fcm(request):
    """Lista los dispositivos FCM del usuario autenticado"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        usuario = obtener_usuario_desde_request(request)
        
        dispositivos = DispositivoFCM.objects.filter(usuario=usuario).order_by('-fecha_ultimo_uso')
        
        datos_dispositivos = [{
            'id': d.id,
            'plataforma': d.plataforma,
            'plataforma_display': d.get_plataforma_display(),
            'nombre_dispositivo': d.nombre_dispositivo,
            'activo': d.activo,
            'fecha_registro': d.fecha_registro.isoformat(),
            'fecha_ultimo_uso': d.fecha_ultimo_uso.isoformat(),
        } for d in dispositivos]
        
        return respuesta_exito('Dispositivos obtenidos', {
            'dispositivos': datos_dispositivos,
            'total': len(datos_dispositivos)
        })
        
    except Exception as e:
        return respuesta_error('Error al obtener dispositivos', detalles=str(e))
