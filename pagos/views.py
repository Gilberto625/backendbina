# pagos/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json

from core.decorators import (
    requiere_autenticacion,
    requiere_cliente,
    requiere_secretaria,
    requiere_administrador,
    requiere_admin_o_secretaria,
    permite_invitado
)
from core.utils import (
    respuesta_exito,
    respuesta_error,
    obtener_usuario_desde_request,
)
from pagos.models import Pago
from pagos.services import PagosService
from citas.models import Cita
from productos.models import OrdenCompra
from django.contrib.auth import get_user_model

Usuario = get_user_model()


# ============================================
# ENDPOINTS PARA CLIENTES
# ============================================

@csrf_exempt
@requiere_cliente
def crear_pago(request):
    """Crea un nuevo pago (solo clientes)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        data = json.loads(request.body)
        cliente = obtener_usuario_desde_request(request)
        
        # Validar campos requeridos
        monto = data.get('monto')
        metodo_pago = data.get('metodo_pago')
        cita_id = data.get('cita_id')
        compra_id = data.get('compra_id')
        
        if not monto or not metodo_pago:
            return respuesta_error('monto y metodo_pago son requeridos')
        
        if not cita_id and not compra_id:
            return respuesta_error('Debe especificar cita_id o compra_id')
        
        if cita_id and compra_id:
            return respuesta_error('Solo se puede especificar cita_id o compra_id, no ambos')
        
        try:
            monto = float(monto)
            if monto <= 0:
                return respuesta_error('El monto debe ser mayor a 0')
        except (ValueError, TypeError):
            return respuesta_error('monto debe ser un número válido')
        
        # Validar método de pago
        metodos_validos = ['efectivo', 'tarjeta', 'transferencia', 'mercado_pago']
        if metodo_pago not in metodos_validos:
            return respuesta_error(f'metodo_pago debe ser uno de: {", ".join(metodos_validos)}')
        
        # Obtener cita o compra
        cita = None
        compra = None
        
        if cita_id:
            try:
                cita = Cita.objects.get(id=cita_id, cliente=cliente)
            except Cita.DoesNotExist:
                return respuesta_error('Cita no encontrada', codigo=404)
        
        if compra_id:
            try:
                compra = OrdenCompra.objects.get(id=compra_id, cliente=cliente)
            except OrdenCompra.DoesNotExist:
                return respuesta_error('Compra no encontrada', codigo=404)
        
        # Crear pago
        pago = Pago.objects.create(
            cita=cita,
            compra=compra,
            cliente=cliente,
            monto=monto,
            metodo_pago=metodo_pago,
            estado='pendiente',
            notas=data.get('notas', '')
        )
        
        # Si es Mercado Pago, crear preferencia
        mercado_pago_data = None
        if metodo_pago == 'mercado_pago':
            descripcion = f'Pago - Cita #{cita_id}' if cita_id else f'Pago - Compra #{compra_id}'
            referencia = f'pago_{pago.id}'
            
            mercado_pago_data = PagosService.crear_preferencia_mercado_pago(
                monto=monto,
                descripcion=descripcion,
                referencia_externa=referencia
            )
            
            if mercado_pago_data:
                pago.mercado_pago_id = mercado_pago_data.get('preference_id', '')
                pago.save()
            else:
                return respuesta_error('Error al crear preferencia de Mercado Pago. Verifique la configuración.', codigo=500)
        
        # Si es transferencia, guardar ID de operación si se proporciona
        if metodo_pago == 'transferencia' and data.get('id_operacion'):
            pago.id_operacion = data.get('id_operacion')
            pago.estado = 'procesando'  # Pendiente de validación
            pago.save()
        
        datos_pago = {
            'id': pago.id,
            'monto': float(pago.monto),
            'metodo_pago': pago.metodo_pago,
            'estado': pago.estado,
            'fecha_creacion': pago.fecha_creacion.isoformat(),
        }
        
        # Agregar datos de Mercado Pago si aplica
        if mercado_pago_data:
            datos_pago['mercado_pago'] = {
                'preference_id': mercado_pago_data.get('preference_id'),
                'init_point': mercado_pago_data.get('init_point'),
                'sandbox_init_point': mercado_pago_data.get('sandbox_init_point'),
            }
        
        return respuesta_exito('Pago creado exitosamente', {
            'pago': datos_pago
        }, codigo=201)
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al crear pago', detalles=str(e))


@csrf_exempt
@requiere_cliente
def historial_pagos(request):
    """Lista los pagos del cliente autenticado"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        cliente = obtener_usuario_desde_request(request)
        estado = request.GET.get('estado')  # Filtro opcional
        metodo_pago = request.GET.get('metodo_pago')  # Filtro opcional
        
        pagos = Pago.objects.filter(cliente=cliente).select_related(
            'cita', 'compra'
        ).order_by('-fecha_creacion')
        
        if estado:
            pagos = pagos.filter(estado=estado)
        
        if metodo_pago:
            pagos = pagos.filter(metodo_pago=metodo_pago)
        
        datos_pagos = [{
            'id': p.id,
            'monto': float(p.monto),
            'metodo_pago': p.metodo_pago,
            'metodo_pago_display': p.get_metodo_pago_display(),
            'estado': p.estado,
            'estado_display': p.get_estado_display(),
            'cita_id': p.cita.id if p.cita else None,
            'compra_id': p.compra.id if p.compra else None,
            'fecha_creacion': p.fecha_creacion.isoformat(),
            'fecha_completado': p.fecha_completado.isoformat() if p.fecha_completado else None,
        } for p in pagos]
        
        return respuesta_exito('Pagos obtenidos', {'pagos': datos_pagos})
        
    except Exception as e:
        return respuesta_error('Error al obtener pagos', detalles=str(e))


@csrf_exempt
@requiere_cliente
def detalle_pago(request, pago_id):
    """Obtiene el detalle de un pago específico"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        cliente = obtener_usuario_desde_request(request)
        
        try:
            pago = Pago.objects.select_related('cita', 'compra').get(id=pago_id, cliente=cliente)
        except Pago.DoesNotExist:
            return respuesta_error('Pago no encontrado', codigo=404)
        
        datos_pago = {
            'id': pago.id,
            'monto': float(pago.monto),
            'metodo_pago': pago.metodo_pago,
            'metodo_pago_display': pago.get_metodo_pago_display(),
            'estado': pago.estado,
            'estado_display': pago.get_estado_display(),
            'cita': {
                'id': pago.cita.id,
                'fecha_hora': pago.cita.fecha_hora.isoformat(),
            } if pago.cita else None,
            'compra': {
                'id': pago.compra.id,
                'total': float(pago.compra.total),
                'estado': pago.compra.estado,
            } if pago.compra else None,
            'id_operacion': pago.id_operacion,
            'mercado_pago_id': pago.mercado_pago_id,
            'mercado_pago_status': pago.mercado_pago_status,
            'fecha_creacion': pago.fecha_creacion.isoformat(),
            'fecha_completado': pago.fecha_completado.isoformat() if pago.fecha_completado else None,
            'fecha_validacion': pago.fecha_validacion.isoformat() if pago.fecha_validacion else None,
            'validado_por': pago.validado_por.email if pago.validado_por else None,
            'notas': pago.notas,
        }
        
        return respuesta_exito('Pago obtenido', {'pago': datos_pago})
        
    except Exception as e:
        return respuesta_error('Error al obtener pago', detalles=str(e))


# ============================================
# ENDPOINTS PARA SECRETARIA/ADMIN
# ============================================

@csrf_exempt
@requiere_secretaria
def validar_transferencia(request, pago_id):
    """
    Valida un pago por transferencia bancaria (secretaria)
    
    NOTA: La integración específica con el banco está pendiente
    hasta que se defina qué banco utilizará el negocio.
    Por ahora, la validación es manual.
    """
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        secretaria = obtener_usuario_desde_request(request)
        
        try:
            pago = Pago.objects.select_related('cita', 'compra').get(id=pago_id)
        except Pago.DoesNotExist:
            return respuesta_error('Pago no encontrado', codigo=404)
        
        data = json.loads(request.body) if request.body else {}
        id_operacion = data.get('id_operacion', pago.id_operacion)
        
        if not id_operacion:
            return respuesta_error('id_operacion es requerido')
        
        # Validar transferencia
        exito, mensaje = PagosService.validar_transferencia_bancaria(
            pago=pago,
            id_operacion=id_operacion,
            validado_por=secretaria
        )
        
        if exito:
            return respuesta_exito(mensaje, {
                'pago': {
                    'id': pago.id,
                    'estado': pago.estado,
                    'fecha_validacion': pago.fecha_validacion.isoformat() if pago.fecha_validacion else None,
                }
            })
        else:
            return respuesta_error(mensaje, codigo=400)
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al validar transferencia', detalles=str(e))


@csrf_exempt
@requiere_admin_o_secretaria
def listar_pagos(request):
    """Lista todos los pagos (secretaria/admin)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        estado = request.GET.get('estado')
        metodo_pago = request.GET.get('metodo_pago')
        cliente_id = request.GET.get('cliente_id')
        cita_id = request.GET.get('cita_id')
        compra_id = request.GET.get('compra_id')
        
        pagos = Pago.objects.select_related('cliente', 'cita', 'compra').all()
        
        if estado:
            pagos = pagos.filter(estado=estado)
        if metodo_pago:
            pagos = pagos.filter(metodo_pago=metodo_pago)
        if cliente_id:
            pagos = pagos.filter(cliente_id=cliente_id)
        if cita_id:
            pagos = pagos.filter(cita_id=cita_id)
        if compra_id:
            pagos = pagos.filter(compra_id=compra_id)
        
        pagos = pagos.order_by('-fecha_creacion')
        
        datos_pagos = [{
            'id': p.id,
            'cliente': {
                'id': p.cliente.id,
                'nombre': p.cliente.get_full_name() or p.cliente.email,
                'email': p.cliente.email,
            },
            'monto': float(p.monto),
            'metodo_pago': p.metodo_pago,
            'metodo_pago_display': p.get_metodo_pago_display(),
            'estado': p.estado,
            'estado_display': p.get_estado_display(),
            'cita_id': p.cita.id if p.cita else None,
            'compra_id': p.compra.id if p.compra else None,
            'id_operacion': p.id_operacion,
            'mercado_pago_id': p.mercado_pago_id,
            'fecha_creacion': p.fecha_creacion.isoformat(),
            'fecha_completado': p.fecha_completado.isoformat() if p.fecha_completado else None,
            'validado_por': p.validado_por.email if p.validado_por else None,
        } for p in pagos]
        
        return respuesta_exito('Pagos obtenidos', {'pagos': datos_pagos})
        
    except Exception as e:
        return respuesta_error('Error al obtener pagos', detalles=str(e))


# ============================================
# WEBHOOKS (Públicos, pero protegidos por firma)
# ============================================

@csrf_exempt
@permite_invitado
def webhook_mercado_pago(request):
    """
    Webhook para recibir notificaciones de Mercado Pago
    
    NOTA: En producción, debería validarse la firma del webhook
    para asegurar que viene de Mercado Pago
    """
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        data = json.loads(request.body)
        
        # Procesar webhook
        exito, mensaje, pago = PagosService.procesar_webhook_mercado_pago(data)
        
        if exito:
            return respuesta_exito(mensaje, {
                'pago_id': pago.id if pago else None,
                'estado': pago.estado if pago else None,
            })
        else:
            return respuesta_error(mensaje, codigo=400)
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al procesar webhook', detalles=str(e))
