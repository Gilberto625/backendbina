# citas/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from datetime import datetime, timedelta
import json

from core.decorators import (
    requiere_autenticacion,
    requiere_cliente,
    requiere_secretaria,
    requiere_admin_o_secretaria,
    permite_invitado
)
from core.utils import (
    respuesta_exito,
    respuesta_error,
    obtener_usuario_desde_request,
    serializar_usuario
)
from citas.models import Cita, Silla, Servicio
from citas.services import ValidacionCitasService
from barberos.models import Barbero, ServicioBarbero
from accounts.models import Usuario


# ============================================
# ENDPOINTS PÚBLICOS
# ============================================

@csrf_exempt
@permite_invitado
def listar_servicios(request):
    """Lista todos los servicios disponibles (público) - Con cache"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        # Intentar obtener del cache
        cache_key = 'servicios_activos'
        datos_servicios = cache.get(cache_key)
        
        if datos_servicios is None:
            servicios = Servicio.objects.filter(activo=True).order_by('categoria', 'nombre')
            datos_servicios = [{
                'id': s.id,
                'nombre': s.nombre,
                'descripcion': s.descripcion,
                'precio_base': float(s.precio_base),
                'duracion_minutos': s.duracion_minutos,
                'categoria': s.categoria,
                'categoria_display': s.get_categoria_display(),
            } for s in servicios]
            # Cachear por 5 minutos (300 segundos)
            cache.set(cache_key, datos_servicios, getattr(settings, 'CACHE_TTL', 300))
        
        return respuesta_exito('Servicios obtenidos', {'servicios': datos_servicios})
    except Exception as e:
        return respuesta_error('Error al obtener servicios', detalles=str(e))


@csrf_exempt
@permite_invitado
def listar_barberos(request):
    """Lista todos los barberos activos (público) - Con cache"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        # Intentar obtener del cache
        cache_key = 'barberos_activos'
        datos_barberos = cache.get(cache_key)
        
        if datos_barberos is None:
            barberos = Barbero.objects.filter(activo=True).select_related('usuario')
            datos_barberos = [{
                'id': b.id,
                'usuario_id': b.usuario.id,
                'nombre': b.usuario.get_full_name() or b.usuario.email,
                'email': b.usuario.email,
                'especialidades': b.especialidades,
                'fecha_contratacion': b.fecha_contratacion.isoformat() if b.fecha_contratacion else None,
            } for b in barberos]
            # Cachear por 5 minutos
            cache.set(cache_key, datos_barberos, getattr(settings, 'CACHE_TTL', 300))
        
        return respuesta_exito('Barberos obtenidos', {'barberos': datos_barberos})
    except Exception as e:
        return respuesta_error('Error al obtener barberos', detalles=str(e))


@csrf_exempt
@permite_invitado
def sillas_disponibles(request):
    """Lista sillas disponibles para una fecha y servicio (público)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        fecha_str = request.GET.get('fecha')
        servicio_id = request.GET.get('servicio_id')
        
        # Obtener todas las sillas activas
        sillas = Silla.objects.filter(activa=True).order_by('numero')
        
        # Si se proporciona fecha y servicio, filtrar sillas ocupadas
        if fecha_str and servicio_id:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                servicio = Servicio.objects.get(id=servicio_id, activo=True)
                
                # Obtener citas existentes para esa fecha
                fecha_inicio = timezone.make_aware(datetime.combine(fecha, datetime.min.time()))
                fecha_fin = timezone.make_aware(datetime.combine(fecha, datetime.max.time()))
                
                citas_existentes = Cita.objects.filter(
                    fecha_hora__date=fecha,
                    estado__in=['pendiente', 'confirmada']
                ).values_list('silla_id', flat=True)
                
                # Filtrar sillas que no están ocupadas
                sillas = sillas.exclude(id__in=citas_existentes)
                
            except (ValueError, Servicio.DoesNotExist):
                pass  # Si hay error, devolver todas las sillas activas
        
        datos_sillas = [{
            'id': s.id,
            'numero': s.numero,
            'nombre': s.nombre,
            'activa': s.activa,
        } for s in sillas]
        
        return respuesta_exito('Sillas disponibles', {'sillas': datos_sillas})
        
    except Exception as e:
        return respuesta_error('Error al obtener sillas disponibles', detalles=str(e))


@csrf_exempt
@permite_invitado
def consultar_disponibilidad(request):
    """Consulta horarios disponibles para una fecha (público)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        fecha_str = request.GET.get('fecha')
        barbero_id = request.GET.get('barbero_id')
        silla_id = request.GET.get('silla_id')
        servicio_id = request.GET.get('servicio_id')
        
        if not fecha_str:
            return respuesta_error('El parámetro fecha es requerido')
        
        # Parsear fecha
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        # Validar que no sea fecha pasada
        if fecha < timezone.now().date():
            return respuesta_error('No se pueden consultar fechas pasadas')
        
        # Obtener objetos si se especifican
        barbero = None
        if barbero_id:
            try:
                barbero = Usuario.objects.get(id=barbero_id, rol='barbero')
            except Usuario.DoesNotExist:
                return respuesta_error('Barbero no encontrado', codigo=404)
        
        silla = None
        if silla_id:
            try:
                silla = Silla.objects.get(id=silla_id, activa=True)
            except Silla.DoesNotExist:
                return respuesta_error('Silla no encontrada', codigo=404)
        
        servicio = None
        if servicio_id:
            try:
                servicio = Servicio.objects.get(id=servicio_id, activo=True)
            except Servicio.DoesNotExist:
                return respuesta_error('Servicio no encontrado', codigo=404)
        
        # Obtener horarios disponibles
        horarios = ValidacionCitasService.obtener_horarios_disponibles(
            fecha=fecha,
            barbero=barbero,
            silla=silla,
            servicio=servicio
        )
        
        horarios_str = [h.strftime('%H:%M') for h in horarios]
        
        return respuesta_exito('Horarios disponibles', {
            'fecha': fecha_str,
            'horarios': horarios_str,
            'total': len(horarios)
        })
        
    except ValueError:
        return respuesta_error('Formato de fecha inválido. Use YYYY-MM-DD')
    except Exception as e:
        return respuesta_error('Error al consultar disponibilidad', detalles=str(e))


# ============================================
# ENDPOINTS PARA CLIENTES
# ============================================

@csrf_exempt
@requiere_cliente
def crear_cita(request):
    """Crea una nueva cita (solo clientes)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        data = json.loads(request.body)
        cliente = obtener_usuario_desde_request(request)
        
        # Validar campos requeridos
        servicio_id = data.get('servicio_id')
        fecha_hora_str = data.get('fecha_hora')
        barbero_id = data.get('barbero_id')
        silla_id = data.get('silla_id')
        
        if not servicio_id or not fecha_hora_str:
            return respuesta_error('servicio_id y fecha_hora son requeridos')
        
        # Obtener servicio
        try:
            servicio = Servicio.objects.get(id=servicio_id, activo=True)
        except Servicio.DoesNotExist:
            return respuesta_error('Servicio no encontrado', codigo=404)
        
        # Parsear fecha_hora
        try:
            fecha_hora = datetime.fromisoformat(fecha_hora_str.replace('Z', '+00:00'))
            if timezone.is_naive(fecha_hora):
                fecha_hora = timezone.make_aware(fecha_hora)
        except ValueError:
            return respuesta_error('Formato de fecha_hora inválido. Use ISO 8601')
        
        # Validar reglas de anticipación
        puede_agendar, mensaje_error = ValidacionCitasService.puede_agendar_en_fecha(
            cliente, fecha_hora
        )
        if not puede_agendar:
            return respuesta_error(mensaje_error, codigo=400)
        
        # Obtener barbero si se especifica
        barbero = None
        if barbero_id:
            try:
                barbero = Usuario.objects.get(id=barbero_id, rol='barbero')
                # Obtener duración específica del barbero si existe
                try:
                    servicio_barbero = ServicioBarbero.objects.get(
                        barbero__usuario=barbero,
                        servicio=servicio,
                        activo=True
                    )
                    duracion = servicio_barbero.duracion_minutos
                except ServicioBarbero.DoesNotExist:
                    duracion = servicio.duracion_minutos
            except Usuario.DoesNotExist:
                return respuesta_error('Barbero no encontrado', codigo=404)
        else:
            duracion = servicio.duracion_minutos
        
        # Obtener silla si se especifica
        silla = None
        if silla_id:
            try:
                silla = Silla.objects.get(id=silla_id, activa=True)
            except Silla.DoesNotExist:
                return respuesta_error('Silla no encontrada', codigo=404)
        
        # Verificar disponibilidad
        disponible, mensaje = ValidacionCitasService.verificar_disponibilidad(
            barbero=barbero,
            silla=silla,
            fecha_hora=fecha_hora,
            duracion_minutos=duracion
        )
        
        if not disponible:
            return respuesta_error(mensaje, codigo=409)  # 409 Conflict
        
        # Calcular anticipo requerido
        anticipo_requerido = ValidacionCitasService.calcular_anticipo_requerido(
            cliente, servicio
        )
        
        # Crear cita
        cita = Cita.objects.create(
            cliente=cliente,
            barbero=barbero,
            servicio=servicio,
            silla=silla,
            fecha_hora=fecha_hora,
            duracion_minutos=duracion,
            precio_total=servicio.precio_base,
            anticipo_requerido=anticipo_requerido,
            anticipo_pagado=0,
            estado='pendiente',
            registrado_por=cliente
        )
        
        # Reducir contador de citas penalizadas si aplica
        if cliente.requiere_anticipo_obligatorio and cliente.citas_penalizadas_restantes > 0:
            cliente.citas_penalizadas_restantes -= 1
            if cliente.citas_penalizadas_restantes == 0:
                cliente.requiere_anticipo_obligatorio = False
            cliente.save()
        
        return respuesta_exito('Cita creada exitosamente', {
            'cita': {
                'id': cita.id,
                'fecha_hora': cita.fecha_hora.isoformat(),
                'servicio': servicio.nombre,
                'precio_total': float(cita.precio_total),
                'anticipo_requerido': float(anticipo_requerido),
                'estado': cita.estado,
            }
        }, codigo=201)
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al crear cita', detalles=str(e))


@csrf_exempt
@requiere_cliente
def mis_citas(request):
    """Lista las citas del cliente autenticado"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        cliente = obtener_usuario_desde_request(request)
        estado = request.GET.get('estado')  # Filtro opcional
        
        citas = Cita.objects.filter(cliente=cliente).select_related(
            'servicio', 'barbero', 'silla'
        ).order_by('-fecha_hora')
        
        if estado:
            citas = citas.filter(estado=estado)
        
        datos_citas = [{
            'id': c.id,
            'fecha_hora': c.fecha_hora.isoformat(),
            'servicio': {
                'id': c.servicio.id,
                'nombre': c.servicio.nombre,
                'precio': float(c.servicio.precio_base),
            },
            'barbero': {
                'id': c.barbero.id if c.barbero else None,
                'nombre': c.barbero.get_full_name() if c.barbero else None,
            } if c.barbero else None,
            'silla': {
                'id': c.silla.id if c.silla else None,
                'nombre': c.silla.nombre if c.silla else None,
            } if c.silla else None,
            'estado': c.estado,
            'precio_total': float(c.precio_total),
            'anticipo_pagado': float(c.anticipo_pagado),
            'anticipo_requerido': float(c.anticipo_requerido),
        } for c in citas]
        
        return respuesta_exito('Citas obtenidas', {'citas': datos_citas})
        
    except Exception as e:
        return respuesta_error('Error al obtener citas', detalles=str(e))


@csrf_exempt
@requiere_cliente
def detalle_cita(request, cita_id):
    """Obtiene el detalle de una cita específica"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        cliente = obtener_usuario_desde_request(request)
        
        try:
            cita = Cita.objects.select_related(
                'servicio', 'barbero', 'silla', 'cliente'
            ).get(id=cita_id, cliente=cliente)
        except Cita.DoesNotExist:
            return respuesta_error('Cita no encontrada', codigo=404)
        
        datos_cita = {
            'id': cita.id,
            'fecha_hora': cita.fecha_hora.isoformat(),
            'fecha_creacion': cita.fecha_creacion.isoformat(),
            'servicio': {
                'id': cita.servicio.id,
                'nombre': cita.servicio.nombre,
                'descripcion': cita.servicio.descripcion,
                'precio': float(cita.servicio.precio_base),
                'duracion_minutos': cita.servicio.duracion_minutos,
            },
            'barbero': {
                'id': cita.barbero.id if cita.barbero else None,
                'nombre': cita.barbero.get_full_name() if cita.barbero else None,
                'email': cita.barbero.email if cita.barbero else None,
            } if cita.barbero else None,
            'silla': {
                'id': cita.silla.id if cita.silla else None,
                'nombre': cita.silla.nombre if cita.silla else None,
            } if cita.silla else None,
            'estado': cita.estado,
            'precio_total': float(cita.precio_total),
            'anticipo_pagado': float(cita.anticipo_pagado),
            'anticipo_requerido': float(cita.anticipo_requerido),
            'duracion_minutos': cita.duracion_minutos,
            'notas': cita.notas,
            'puede_cancelar': ValidacionCitasService.puede_cancelar_cita(cita)[0],
        }
        
        return respuesta_exito('Cita obtenida', {'cita': datos_cita})
        
    except Exception as e:
        return respuesta_error('Error al obtener cita', detalles=str(e))


@csrf_exempt
@requiere_cliente
def cancelar_cita(request, cita_id):
    """Cancela una cita (solo clientes, con validación de reglas)"""
    if request.method != 'PUT':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        cliente = obtener_usuario_desde_request(request)
        
        try:
            cita = Cita.objects.get(id=cita_id, cliente=cliente)
        except Cita.DoesNotExist:
            return respuesta_error('Cita no encontrada', codigo=404)
        
        # Validar que se puede cancelar
        puede_cancelar, mensaje = ValidacionCitasService.puede_cancelar_cita(cita)
        if not puede_cancelar:
            return respuesta_error(mensaje, codigo=400)
        
        # Cancelar cita
        cita.estado = 'cancelada'
        cita.fecha_cancelacion = timezone.now()
        data = json.loads(request.body) if request.body else {}
        cita.motivo_cancelacion = data.get('motivo', '')
        cita.save()
        
        return respuesta_exito('Cita cancelada exitosamente')
        
    except Exception as e:
        return respuesta_error('Error al cancelar cita', detalles=str(e))


# ============================================
# ENDPOINTS PARA SECRETARIA/ADMIN
# ============================================

@csrf_exempt
@requiere_admin_o_secretaria
def agenda_completa(request):
    """Obtiene la agenda completa (secretaria/admin)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        estado = request.GET.get('estado')
        barbero_id = request.GET.get('barbero_id')
        
        citas = Cita.objects.select_related(
            'cliente', 'barbero', 'servicio', 'silla'
        ).all()
        
        # Filtros opcionales
        if fecha_inicio:
            fecha_inicio_dt = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
            if timezone.is_naive(fecha_inicio_dt):
                fecha_inicio_dt = timezone.make_aware(fecha_inicio_dt)
            citas = citas.filter(fecha_hora__gte=fecha_inicio_dt)
        
        if fecha_fin:
            fecha_fin_dt = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
            if timezone.is_naive(fecha_fin_dt):
                fecha_fin_dt = timezone.make_aware(fecha_fin_dt)
            citas = citas.filter(fecha_hora__lte=fecha_fin_dt)
        
        if estado:
            citas = citas.filter(estado=estado)
        
        if barbero_id:
            citas = citas.filter(barbero_id=barbero_id)
        
        citas = citas.order_by('fecha_hora')
        
        datos_citas = [{
            'id': c.id,
            'fecha_hora': c.fecha_hora.isoformat(),
            'cliente': {
                'id': c.cliente.id,
                'nombre': c.cliente.get_full_name() or c.cliente.email,
                'email': c.cliente.email,
                'telefono': c.cliente.telefono,
            },
            'barbero': {
                'id': c.barbero.id if c.barbero else None,
                'nombre': c.barbero.get_full_name() if c.barbero else None,
            } if c.barbero else None,
            'servicio': {
                'id': c.servicio.id,
                'nombre': c.servicio.nombre,
            },
            'silla': {
                'id': c.silla.id if c.silla else None,
                'nombre': c.silla.nombre if c.silla else None,
            } if c.silla else None,
            'estado': c.estado,
            'precio_total': float(c.precio_total),
            'anticipo_pagado': float(c.anticipo_pagado),
        } for c in citas]
        
        return respuesta_exito('Agenda obtenida', {'citas': datos_citas})
        
    except Exception as e:
        return respuesta_error('Error al obtener agenda', detalles=str(e))


@csrf_exempt
@requiere_secretaria
def registrar_asistencia(request, cita_id):
    """Registra la asistencia de un cliente a su cita (secretaria)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            cita = Cita.objects.select_related('cliente').get(id=cita_id)
        except Cita.DoesNotExist:
            return respuesta_error('Cita no encontrada', codigo=404)
        
        data = json.loads(request.body) if request.body else {}
        asistio = data.get('asistio', True)
        
        if asistio:
            cita.marcar_asistencia()
            # Reiniciar contador de inasistencias si el cliente tenía penalización
            if cita.cliente.inasistencias_consecutivas > 0:
                cita.cliente.inasistencias_consecutivas = 0
                cita.cliente.save()
            mensaje = 'Asistencia registrada exitosamente'
        else:
            cita.marcar_no_asistencia()
            mensaje = 'Inasistencia registrada'
        
        return respuesta_exito(mensaje, {
            'cita': {
                'id': cita.id,
                'estado': cita.estado,
            }
        })
        
    except Exception as e:
        return respuesta_error('Error al registrar asistencia', detalles=str(e))


@csrf_exempt
@requiere_admin_o_secretaria
def crear_cita_manual(request):
    """Crea una cita manualmente (secretaria/admin)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        data = json.loads(request.body)
        secretaria = obtener_usuario_desde_request(request)
        
        # Validar campos requeridos
        cliente_id = data.get('cliente_id')
        servicio_id = data.get('servicio_id')
        fecha_hora_str = data.get('fecha_hora')
        
        if not cliente_id or not servicio_id or not fecha_hora_str:
            return respuesta_error('cliente_id, servicio_id y fecha_hora son requeridos')
        
        # Obtener cliente
        try:
            cliente = Usuario.objects.get(id=cliente_id, rol='cliente')
        except Usuario.DoesNotExist:
            return respuesta_error('Cliente no encontrado', codigo=404)
        
        # Obtener servicio
        try:
            servicio = Servicio.objects.get(id=servicio_id, activo=True)
        except Servicio.DoesNotExist:
            return respuesta_error('Servicio no encontrado', codigo=404)
        
        # Parsear fecha_hora
        try:
            fecha_hora = datetime.fromisoformat(fecha_hora_str.replace('Z', '+00:00'))
            if timezone.is_naive(fecha_hora):
                fecha_hora = timezone.make_aware(fecha_hora)
        except ValueError:
            return respuesta_error('Formato de fecha_hora inválido')
        
        # Obtener barbero y silla si se especifican
        barbero = None
        if data.get('barbero_id'):
            try:
                barbero = Usuario.objects.get(id=data['barbero_id'], rol='barbero')
            except Usuario.DoesNotExist:
                return respuesta_error('Barbero no encontrado', codigo=404)
        
        silla = None
        if data.get('silla_id'):
            try:
                silla = Silla.objects.get(id=data['silla_id'], activa=True)
            except Silla.DoesNotExist:
                return respuesta_error('Silla no encontrada', codigo=404)
        
        # Obtener duración
        if barbero:
            try:
                servicio_barbero = ServicioBarbero.objects.get(
                    barbero__usuario=barbero,
                    servicio=servicio,
                    activo=True
                )
                duracion = servicio_barbero.duracion_minutos
            except ServicioBarbero.DoesNotExist:
                duracion = servicio.duracion_minutos
        else:
            duracion = servicio.duracion_minutos
        
        # Verificar disponibilidad
        disponible, mensaje = ValidacionCitasService.verificar_disponibilidad(
            barbero=barbero,
            silla=silla,
            fecha_hora=fecha_hora,
            duracion_minutos=duracion
        )
        
        if not disponible:
            return respuesta_error(mensaje, codigo=409)
        
        # Calcular anticipo (puede ser 0 si es primera cita)
        anticipo_requerido = ValidacionCitasService.calcular_anticipo_requerido(
            cliente, servicio
        )
        
        # Crear cita
        cita = Cita.objects.create(
            cliente=cliente,
            barbero=barbero,
            servicio=servicio,
            silla=silla,
            fecha_hora=fecha_hora,
            duracion_minutos=duracion,
            precio_total=servicio.precio_base,
            anticipo_requerido=anticipo_requerido,
            anticipo_pagado=data.get('anticipo_pagado', 0),
            metodo_pago_anticipo=data.get('metodo_pago_anticipo', ''),
            estado='confirmada' if anticipo_requerido == 0 or data.get('anticipo_pagado', 0) > 0 else 'pendiente',
            registrado_por=secretaria,
            notas=data.get('notas', '')
        )
        
        return respuesta_exito('Cita creada manualmente', {
            'cita': {
                'id': cita.id,
                'fecha_hora': cita.fecha_hora.isoformat(),
                'cliente': cliente.email,
                'estado': cita.estado,
            }
        }, codigo=201)
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al crear cita', detalles=str(e))
