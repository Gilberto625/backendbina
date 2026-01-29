# barberos/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
import json

from core.decorators import (
    requiere_autenticacion,
    requiere_cliente,
    requiere_secretaria,
    requiere_barbero,
    requiere_administrador,
    requiere_admin_o_secretaria,
    permite_invitado
)
from core.utils import (
    respuesta_exito,
    respuesta_error,
    obtener_usuario_desde_request,
)
from barberos.models import Barbero, ServicioBarbero
from barberos.services import BarberosService
from citas.models import Servicio
from accounts.models import Usuario
from django.contrib.auth import get_user_model

UsuarioModel = get_user_model()


# ============================================
# ENDPOINTS PÚBLICOS
# ============================================

@csrf_exempt
@permite_invitado
def listar_barberos(request):
    """Lista todos los barberos activos (público)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        barberos = Barbero.objects.filter(activo=True).select_related('usuario')
        
        datos_barberos = [{
            'id': b.id,
            'usuario_id': b.usuario.id,
            'nombre': b.usuario.get_full_name() or b.usuario.email,
            'email': b.usuario.email,
            'especialidades': b.especialidades,
            'fecha_contratacion': b.fecha_contratacion.isoformat() if b.fecha_contratacion else None,
        } for b in barberos]
        
        return respuesta_exito('Barberos obtenidos', {'barberos': datos_barberos})
        
    except Exception as e:
        return respuesta_error('Error al obtener barberos', detalles=str(e))


@csrf_exempt
@permite_invitado
def detalle_barbero(request, barbero_id):
    """Obtiene el detalle de un barbero específico (público)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            barbero = Barbero.objects.select_related('usuario').get(id=barbero_id, activo=True)
        except Barbero.DoesNotExist:
            return respuesta_error('Barbero no encontrado', codigo=404)
        
        datos_barbero = {
            'id': barbero.id,
            'usuario_id': barbero.usuario.id,
            'nombre': barbero.usuario.get_full_name() or barbero.usuario.email,
            'email': barbero.usuario.email,
            'telefono': barbero.usuario.telefono,
            'especialidades': barbero.especialidades,
            'fecha_contratacion': barbero.fecha_contratacion.isoformat() if barbero.fecha_contratacion else None,
            'activo': barbero.activo,
        }
        
        return respuesta_exito('Barbero obtenido', {'barbero': datos_barbero})
        
    except Exception as e:
        return respuesta_error('Error al obtener barbero', detalles=str(e))


@csrf_exempt
@permite_invitado
def servicios_barbero(request, barbero_id):
    """Lista los servicios que puede realizar un barbero (público)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            barbero = Barbero.objects.get(id=barbero_id, activo=True)
        except Barbero.DoesNotExist:
            return respuesta_error('Barbero no encontrado', codigo=404)
        
        servicios = BarberosService.obtener_servicios_barbero(barbero)
        
        datos_servicios = [{
            'id': sb.servicio.id,
            'servicio_id': sb.servicio.id,
            'nombre': sb.servicio.nombre,
            'descripcion': sb.servicio.descripcion,
            'precio_base': float(sb.servicio.precio_base),
            'duracion_minutos': sb.duracion_minutos,
            'duracion_base_minutos': sb.servicio.duracion_minutos,
            'categoria': sb.servicio.categoria,
        } for sb in servicios]
        
        return respuesta_exito('Servicios obtenidos', {'servicios': datos_servicios})
        
    except Exception as e:
        return respuesta_error('Error al obtener servicios', detalles=str(e))


@csrf_exempt
@permite_invitado
def disponibilidad_barbero(request, barbero_id):
    """Consulta la disponibilidad de un barbero para una fecha (público)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            barbero = Barbero.objects.get(id=barbero_id, activo=True)
        except Barbero.DoesNotExist:
            return respuesta_error('Barbero no encontrado', codigo=404)
        
        fecha_str = request.GET.get('fecha')
        if not fecha_str:
            return respuesta_error('El parámetro fecha es requerido')
        
        # Parsear fecha
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        # Validar que no sea fecha pasada
        if fecha < timezone.now().date():
            return respuesta_error('No se pueden consultar fechas pasadas')
        
        # Obtener horarios disponibles
        horarios = BarberosService.obtener_disponibilidad_barbero(barbero, fecha)
        
        horarios_str = [h.strftime('%H:%M') for h in horarios]
        
        return respuesta_exito('Disponibilidad obtenida', {
            'barbero_id': barbero.id,
            'barbero_nombre': barbero.usuario.get_full_name() or barbero.usuario.email,
            'fecha': fecha_str,
            'horarios': horarios_str,
            'total': len(horarios)
        })
        
    except ValueError:
        return respuesta_error('Formato de fecha inválido. Use YYYY-MM-DD')
    except Exception as e:
        return respuesta_error('Error al consultar disponibilidad', detalles=str(e))


# ============================================
# ENDPOINTS PARA ADMIN/SECRETARIA
# ============================================

@csrf_exempt
@requiere_administrador
def crear_barbero(request):
    """Crea un nuevo barbero desde un usuario existente (solo admin)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        data = json.loads(request.body)
        
        usuario_id = data.get('usuario_id')
        if not usuario_id:
            return respuesta_error('usuario_id es requerido')
        
        try:
            usuario = UsuarioModel.objects.get(id=usuario_id)
        except UsuarioModel.DoesNotExist:
            return respuesta_error('Usuario no encontrado', codigo=404)
        
        # Verificar que el usuario tenga rol barbero
        if usuario.rol != 'barbero':
            return respuesta_error('El usuario debe tener rol barbero', codigo=400)
        
        # Parsear fecha de contratación si se proporciona
        fecha_contratacion = None
        if data.get('fecha_contratacion'):
            try:
                fecha_contratacion = datetime.strptime(data['fecha_contratacion'], '%Y-%m-%d').date()
            except ValueError:
                return respuesta_error('Formato de fecha_contratacion inválido. Use YYYY-MM-DD')
        
        # Crear barbero
        barbero = BarberosService.crear_barbero_desde_usuario(
            usuario=usuario,
            fecha_contratacion=fecha_contratacion,
            especialidades=data.get('especialidades', '')
        )
        
        return respuesta_exito('Barbero creado exitosamente', {
            'barbero': {
                'id': barbero.id,
                'usuario_id': barbero.usuario.id,
                'nombre': barbero.usuario.get_full_name() or barbero.usuario.email,
            }
        }, codigo=201)
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except ValueError as e:
        return respuesta_error(str(e), codigo=400)
    except Exception as e:
        return respuesta_error('Error al crear barbero', detalles=str(e))


@csrf_exempt
@requiere_administrador
def actualizar_barbero(request, barbero_id):
    """Actualiza un barbero existente (solo admin)"""
    if request.method != 'PUT':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            barbero = Barbero.objects.select_related('usuario').get(id=barbero_id)
        except Barbero.DoesNotExist:
            return respuesta_error('Barbero no encontrado', codigo=404)
        
        data = json.loads(request.body)
        
        # Actualizar campos permitidos
        if 'activo' in data:
            barbero.activo = data['activo']
        
        if 'especialidades' in data:
            barbero.especialidades = data['especialidades']
        
        if 'fecha_contratacion' in data:
            if data['fecha_contratacion']:
                try:
                    barbero.fecha_contratacion = datetime.strptime(data['fecha_contratacion'], '%Y-%m-%d').date()
                except ValueError:
                    return respuesta_error('Formato de fecha_contratacion inválido. Use YYYY-MM-DD')
            else:
                barbero.fecha_contratacion = None
        
        barbero.save()
        
        return respuesta_exito('Barbero actualizado exitosamente', {
            'barbero': {
                'id': barbero.id,
                'nombre': barbero.usuario.get_full_name() or barbero.usuario.email,
                'activo': barbero.activo,
            }
        })
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al actualizar barbero', detalles=str(e))


@csrf_exempt
@requiere_admin_o_secretaria
def asignar_servicio_barbero(request, barbero_id):
    """Asigna un servicio a un barbero con duración específica (admin/secretaria)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            barbero = Barbero.objects.get(id=barbero_id)
        except Barbero.DoesNotExist:
            return respuesta_error('Barbero no encontrado', codigo=404)
        
        data = json.loads(request.body)
        
        servicio_id = data.get('servicio_id')
        duracion_minutos = data.get('duracion_minutos')
        
        if not servicio_id or duracion_minutos is None:
            return respuesta_error('servicio_id y duracion_minutos son requeridos')
        
        try:
            servicio = Servicio.objects.get(id=servicio_id, activo=True)
        except Servicio.DoesNotExist:
            return respuesta_error('Servicio no encontrado', codigo=404)
        
        try:
            duracion_minutos = int(duracion_minutos)
            if duracion_minutos <= 0:
                return respuesta_error('duracion_minutos debe ser mayor a 0')
        except (ValueError, TypeError):
            return respuesta_error('duracion_minutos debe ser un número válido')
        
        # Asignar servicio
        servicio_barbero, created = BarberosService.asignar_servicio_barbero(
            barbero=barbero,
            servicio=servicio,
            duracion_minutos=duracion_minutos
        )
        
        mensaje = 'Servicio asignado exitosamente' if created else 'Servicio actualizado exitosamente'
        
        return respuesta_exito(mensaje, {
            'servicio_barbero': {
                'id': servicio_barbero.id,
                'barbero_id': barbero.id,
                'servicio_id': servicio.id,
                'servicio_nombre': servicio.nombre,
                'duracion_minutos': servicio_barbero.duracion_minutos,
            }
        }, codigo=201 if created else 200)
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al asignar servicio', detalles=str(e))


@csrf_exempt
@requiere_admin_o_secretaria
def desactivar_servicio_barbero(request, barbero_id, servicio_id):
    """Desactiva un servicio de un barbero (admin/secretaria)"""
    if request.method != 'DELETE':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            barbero = Barbero.objects.get(id=barbero_id)
        except Barbero.DoesNotExist:
            return respuesta_error('Barbero no encontrado', codigo=404)
        
        try:
            servicio = Servicio.objects.get(id=servicio_id)
        except Servicio.DoesNotExist:
            return respuesta_error('Servicio no encontrado', codigo=404)
        
        exito = BarberosService.desactivar_servicio_barbero(barbero, servicio)
        
        if exito:
            return respuesta_exito('Servicio desactivado exitosamente')
        else:
            return respuesta_error('Servicio no encontrado para este barbero', codigo=404)
        
    except Exception as e:
        return respuesta_error('Error al desactivar servicio', detalles=str(e))


@csrf_exempt
@requiere_admin_o_secretaria
def citas_barbero(request, barbero_id):
    """Obtiene las citas de un barbero (admin/secretaria)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            barbero = Barbero.objects.get(id=barbero_id)
        except Barbero.DoesNotExist:
            return respuesta_error('Barbero no encontrado', codigo=404)
        
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        estado = request.GET.get('estado')
        
        fecha_inicio = None
        fecha_fin = None
        
        if fecha_inicio_str:
            try:
                fecha_inicio = datetime.fromisoformat(fecha_inicio_str.replace('Z', '+00:00'))
                if timezone.is_naive(fecha_inicio):
                    fecha_inicio = timezone.make_aware(fecha_inicio)
            except ValueError:
                return respuesta_error('Formato de fecha_inicio inválido')
        
        if fecha_fin_str:
            try:
                fecha_fin = datetime.fromisoformat(fecha_fin_str.replace('Z', '+00:00'))
                if timezone.is_naive(fecha_fin):
                    fecha_fin = timezone.make_aware(fecha_fin)
            except ValueError:
                return respuesta_error('Formato de fecha_fin inválido')
        
        citas = BarberosService.obtener_citas_barbero(
            barbero=barbero,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado=estado
        )
        
        datos_citas = [{
            'id': c.id,
            'fecha_hora': c.fecha_hora.isoformat(),
            'cliente': {
                'id': c.cliente.id,
                'nombre': c.cliente.get_full_name() or c.cliente.email,
                'email': c.cliente.email,
            },
            'servicio': {
                'id': c.servicio.id,
                'nombre': c.servicio.nombre,
            },
            'silla': {
                'id': c.silla.id if c.silla else None,
                'nombre': c.silla.nombre if c.silla else None,
            } if c.silla else None,
            'estado': c.estado,
            'duracion_minutos': c.duracion_minutos,
        } for c in citas]
        
        return respuesta_exito('Citas obtenidas', {'citas': datos_citas})
        
    except Exception as e:
        return respuesta_error('Error al obtener citas', detalles=str(e))


# ============================================
# ENDPOINTS PARA BARBERO (AUTENTICADO)
# ============================================

@csrf_exempt
@requiere_barbero
def mis_servicios(request):
    """Lista los servicios del barbero autenticado (barbero)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)

    try:
        usuario = obtener_usuario_desde_request(request)
        try:
            barbero = Barbero.objects.get(usuario=usuario, activo=True)
        except Barbero.DoesNotExist:
            return respuesta_error('Perfil de barbero no encontrado', codigo=404)

        servicios = BarberosService.obtener_servicios_barbero(barbero)
        datos = [{
            'servicio_id': sb.servicio.id,
            'nombre': sb.servicio.nombre,
            'categoria': sb.servicio.categoria,
            'duracion_minutos': sb.duracion_minutos,
            'duracion_base_minutos': sb.servicio.duracion_minutos,
            'activo': sb.activo,
        } for sb in servicios]

        return respuesta_exito('Servicios del barbero obtenidos', {'servicios': datos})
    except Exception as e:
        return respuesta_error('Error al obtener servicios', detalles=str(e))


@csrf_exempt
@requiere_barbero
def actualizar_duracion_servicio(request, servicio_id):
    """Actualiza la duración del servicio para el barbero autenticado (barbero)"""
    if request.method != 'PUT':
        return respuesta_error('Método no permitido', codigo=405)

    try:
        usuario = obtener_usuario_desde_request(request)
        try:
            barbero = Barbero.objects.get(usuario=usuario, activo=True)
        except Barbero.DoesNotExist:
            return respuesta_error('Perfil de barbero no encontrado', codigo=404)

        data = json.loads(request.body) if request.body else {}
        duracion_minutos = data.get('duracion_minutos')
        if duracion_minutos is None:
            return respuesta_error('duracion_minutos es requerido')

        try:
            duracion_minutos = int(duracion_minutos)
            if duracion_minutos <= 0:
                return respuesta_error('duracion_minutos debe ser mayor a 0')
        except (ValueError, TypeError):
            return respuesta_error('duracion_minutos debe ser un número válido')

        try:
            servicio = Servicio.objects.get(id=servicio_id, activo=True)
        except Servicio.DoesNotExist:
            return respuesta_error('Servicio no encontrado', codigo=404)

        servicio_barbero, _ = BarberosService.asignar_servicio_barbero(
            barbero=barbero,
            servicio=servicio,
            duracion_minutos=duracion_minutos
        )

        return respuesta_exito('Duración actualizada', {
            'servicio': {
                'servicio_id': servicio.id,
                'nombre': servicio.nombre,
                'duracion_minutos': servicio_barbero.duracion_minutos,
            }
        })

    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al actualizar duración', detalles=str(e))


@csrf_exempt
@requiere_barbero
def mis_citas(request):
    """Lista las citas asignadas al barbero autenticado (barbero)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)

    try:
        usuario = obtener_usuario_desde_request(request)
        try:
            barbero = Barbero.objects.get(usuario=usuario, activo=True)
        except Barbero.DoesNotExist:
            return respuesta_error('Perfil de barbero no encontrado', codigo=404)

        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        estado = request.GET.get('estado')

        fecha_inicio = None
        fecha_fin = None

        if fecha_inicio_str:
            try:
                fecha_inicio = datetime.fromisoformat(fecha_inicio_str.replace('Z', '+00:00'))
                if timezone.is_naive(fecha_inicio):
                    fecha_inicio = timezone.make_aware(fecha_inicio)
            except ValueError:
                return respuesta_error('Formato de fecha_inicio inválido')

        if fecha_fin_str:
            try:
                fecha_fin = datetime.fromisoformat(fecha_fin_str.replace('Z', '+00:00'))
                if timezone.is_naive(fecha_fin):
                    fecha_fin = timezone.make_aware(fecha_fin)
            except ValueError:
                return respuesta_error('Formato de fecha_fin inválido')

        citas = BarberosService.obtener_citas_barbero(
            barbero=barbero,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado=estado
        )

        datos_citas = [{
            'id': c.id,
            'fecha_hora': c.fecha_hora.isoformat(),
            'cliente': {
                'id': c.cliente.id,
                'nombre': c.cliente.get_full_name() or c.cliente.email,
                'email': c.cliente.email,
            },
            'servicio': {
                'id': c.servicio.id,
                'nombre': c.servicio.nombre,
            },
            'silla': {
                'id': c.silla.id if c.silla else None,
                'nombre': c.silla.nombre if c.silla else None,
            } if c.silla else None,
            'estado': c.estado,
            'duracion_minutos': c.duracion_minutos,
        } for c in citas]

        return respuesta_exito('Mis citas obtenidas', {'citas': datos_citas})

    except Exception as e:
        return respuesta_error('Error al obtener mis citas', detalles=str(e))
