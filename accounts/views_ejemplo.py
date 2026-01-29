# accounts/views_ejemplo.py
"""
Ejemplos de endpoints usando los nuevos decoradores de permisos
Estos son ejemplos de cómo se usarán en los nuevos endpoints
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.decorators import (
    requiere_autenticacion,
    requiere_cliente,
    requiere_secretaria,
    requiere_administrador,
    requiere_staff
)
from core.utils import (
    respuesta_exito,
    respuesta_error,
    obtener_usuario_desde_request,
    serializar_usuario
)


# ============================================
# EJEMPLO: Endpoint para obtener perfil del usuario autenticado
# ============================================
@csrf_exempt
@requiere_autenticacion
def obtener_perfil(request):
    """Obtiene el perfil del usuario autenticado (cualquier rol)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    usuario = obtener_usuario_desde_request(request)
    datos_usuario = serializar_usuario(usuario)
    
    return respuesta_exito('Perfil obtenido', {'usuario': datos_usuario})


# ============================================
# EJEMPLO: Endpoint solo para clientes
# ============================================
@csrf_exempt
@requiere_cliente
def mis_citas(request):
    """Lista las citas del cliente autenticado"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    usuario = obtener_usuario_desde_request(request)
    
    # Obtener citas del cliente
    try:
        from citas.models import Cita
        citas = Cita.objects.filter(cliente=usuario).order_by('-fecha_hora')
        
        datos_citas = [{
            'id': cita.id,
            'fecha_hora': cita.fecha_hora.isoformat(),
            'servicio': cita.servicio.nombre,
            'estado': cita.estado,
            'precio_total': float(cita.precio_total),
        } for cita in citas]
        
        return respuesta_exito('Citas obtenidas', {'citas': datos_citas})
    except Exception as e:
        return respuesta_error('Error al obtener citas', detalles=str(e))


# ============================================
# EJEMPLO: Endpoint para secretaria
# ============================================
@csrf_exempt
@requiere_secretaria
def validar_pago_transferencia(request):
    """Valida un pago por transferencia (solo secretaria)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    import json
    from pagos.models import Pago
    
    try:
        data = json.loads(request.body)
        pago_id = data.get('pago_id')
        id_operacion = data.get('id_operacion')
        
        if not pago_id or not id_operacion:
            return respuesta_error('pago_id e id_operacion son requeridos')
        
        pago = Pago.objects.get(id=pago_id)
        secretaria = obtener_usuario_desde_request(request)
        
        if pago.validar_transferencia(secretaria):
            return respuesta_exito('Pago validado exitosamente')
        else:
            return respuesta_error('No se pudo validar el pago')
            
    except Pago.DoesNotExist:
        return respuesta_error('Pago no encontrado', codigo=404)
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al validar pago', detalles=str(e))


# ============================================
# EJEMPLO: Endpoint para administrador
# ============================================
@csrf_exempt
@requiere_administrador
def listar_empleados(request):
    """Lista todos los empleados (solo administrador)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        from accounts.models import Usuario
        empleados = Usuario.objects.filter(
            rol__in=['secretaria', 'barbero', 'administrador']
        ).exclude(rol='cliente')
        
        datos_empleados = [serializar_usuario(emp) for emp in empleados]
        
        return respuesta_exito('Empleados obtenidos', {'empleados': datos_empleados})
    except Exception as e:
        return respuesta_error('Error al obtener empleados', detalles=str(e))


# ============================================
# EJEMPLO: Endpoint para staff (secretaria, barbero, admin)
# ============================================
@csrf_exempt
@requiere_staff
def dashboard_staff(request):
    """Dashboard para miembros del staff"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    usuario = obtener_usuario_desde_request(request)
    
    # Datos según el rol
    datos = {
        'usuario': serializar_usuario(usuario),
        'rol': usuario.rol,
    }
    
    # Agregar información específica según rol
    if usuario.rol == 'secretaria':
        from citas.models import Cita
        citas_pendientes = Cita.objects.filter(estado='pendiente').count()
        datos['citas_pendientes'] = citas_pendientes
    elif usuario.rol == 'barbero':
        from citas.models import Cita
        mis_citas = Cita.objects.filter(barbero=usuario, estado__in=['pendiente', 'confirmada']).count()
        datos['mis_citas'] = mis_citas
    
    return respuesta_exito('Dashboard staff', datos)
