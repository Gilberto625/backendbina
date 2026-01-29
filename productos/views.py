# productos/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
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
    serializar_usuario
)
from productos.models import Producto, Compra, OrdenCompra, OrdenCompraItem
from productos.services import ProductosService
from django.contrib.auth import get_user_model
from django.db import transaction

Usuario = get_user_model()


# ============================================
# ENDPOINTS PÚBLICOS
# ============================================

@csrf_exempt
@permite_invitado
def listar_productos(request):
    """Lista todos los productos disponibles (público) - Con cache"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        categoria = request.GET.get('categoria')
        solo_disponibles = request.GET.get('solo_disponibles', 'false').lower() == 'true'
        
        # Si hay filtros, no usar cache
        if categoria or solo_disponibles:
            productos = Producto.objects.filter(activo=True)
            if categoria:
                productos = productos.filter(categoria=categoria)
            if solo_disponibles:
                productos = productos.filter(stock_actual__gt=0)
            productos = productos.order_by('categoria', 'nombre')
            datos_productos = [{
                'id': p.id,
                'nombre': p.nombre,
                'descripcion': p.descripcion,
                'precio': float(p.precio),
                'categoria': p.categoria,
                'categoria_display': p.get_categoria_display(),
                'stock_actual': p.stock_actual,
                'stock_bajo': p.stock_bajo(),
                'imagen_url': p.imagen_url,
                'disponible': p.stock_actual > 0,
            } for p in productos]
        else:
            # Intentar obtener del cache
            cache_key = 'productos_activos'
            datos_productos = cache.get(cache_key)
            
            if datos_productos is None:
                productos = Producto.objects.filter(activo=True).order_by('categoria', 'nombre')
                datos_productos = [{
                    'id': p.id,
                    'nombre': p.nombre,
                    'descripcion': p.descripcion,
                    'precio': float(p.precio),
                    'categoria': p.categoria,
                    'categoria_display': p.get_categoria_display(),
                    'stock_actual': p.stock_actual,
                    'stock_bajo': p.stock_bajo(),
                    'imagen_url': p.imagen_url,
                    'disponible': p.stock_actual > 0,
                } for p in productos]
                # Cachear por 5 minutos
                cache.set(cache_key, datos_productos, getattr(settings, 'CACHE_TTL', 300))
        
        return respuesta_exito('Productos obtenidos', {'productos': datos_productos})
        
    except Exception as e:
        return respuesta_error('Error al obtener productos', detalles=str(e))


@csrf_exempt
@permite_invitado
def detalle_producto(request, producto_id):
    """Obtiene el detalle de un producto específico (público)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            producto = Producto.objects.get(id=producto_id, activo=True)
        except Producto.DoesNotExist:
            return respuesta_error('Producto no encontrado', codigo=404)
        
        datos_producto = {
            'id': producto.id,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio': float(producto.precio),
            'categoria': producto.categoria,
            'categoria_display': producto.get_categoria_display(),
            'stock_actual': producto.stock_actual,
            'stock_minimo': producto.stock_minimo,
            'stock_bajo': producto.stock_bajo(),
            'imagen_url': producto.imagen_url,
            'disponible': producto.stock_actual > 0,
            'fecha_creacion': producto.fecha_creacion.isoformat(),
        }
        
        return respuesta_exito('Producto obtenido', {'producto': datos_producto})
        
    except Exception as e:
        return respuesta_error('Error al obtener producto', detalles=str(e))


@csrf_exempt
@permite_invitado
def consultar_stock(request, producto_id):
    """Consulta el stock disponible de un producto (público)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            producto = Producto.objects.get(id=producto_id, activo=True)
        except Producto.DoesNotExist:
            return respuesta_error('Producto no encontrado', codigo=404)
        
        cantidad = request.GET.get('cantidad', '1')
        try:
            cantidad = int(cantidad)
        except ValueError:
            cantidad = 1
        
        disponible, mensaje = ProductosService.verificar_stock_disponible(producto, cantidad)
        
        return respuesta_exito('Stock consultado', {
            'producto_id': producto.id,
            'producto_nombre': producto.nombre,
            'stock_actual': producto.stock_actual,
            'cantidad_solicitada': cantidad,
            'disponible': disponible,
            'mensaje': mensaje if not disponible else 'Stock disponible',
        })
        
    except Exception as e:
        return respuesta_error('Error al consultar stock', detalles=str(e))


# ============================================
# ENDPOINTS PARA CLIENTES
# ============================================

@csrf_exempt
@requiere_cliente
def crear_compra(request):
    """Crea una nueva compra/apartado (solo clientes).
    Soporta:
    - Legacy: {producto_id, cantidad, ...}
    - Nuevo carrito: {productos: [{producto_id, cantidad}, ...], ...}
    """
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        data = json.loads(request.body)
        cliente = obtener_usuario_desde_request(request)
        
        metodo_entrega = data.get('metodo_entrega', 'local')

        # Validar método de entrega
        if metodo_entrega not in ['local', 'moto_mandado', 'paqueteria']:
            return respuesta_error('Método de entrega inválido')

        # Dirección (si aplica)
        direccion_entrega = data.get('direccion_entrega', '')
        if metodo_entrega != 'local' and not direccion_entrega:
            return respuesta_error('direccion_entrega es requerida para envíos')

        # Normalizar payload a carrito
        carrito = data.get('productos')
        if not carrito:
            # Legacy
            producto_id = data.get('producto_id')
            cantidad = data.get('cantidad')
            if not producto_id or not cantidad:
                return respuesta_error('productos (carrito) o producto_id y cantidad son requeridos')
            carrito = [{'producto_id': producto_id, 'cantidad': cantidad}]

        if not isinstance(carrito, list) or len(carrito) == 0:
            return respuesta_error('productos debe ser una lista con al menos un item')

        # Cargar productos y validar cantidades
        items = []
        for it in carrito:
            pid = it.get('producto_id')
            cant = it.get('cantidad')
            if not pid or not cant:
                return respuesta_error('Cada item requiere producto_id y cantidad')
            try:
                cant = int(cant)
                if cant <= 0:
                    return respuesta_error('La cantidad debe ser mayor a 0')
            except (ValueError, TypeError):
                return respuesta_error('cantidad debe ser un número válido')

            try:
                producto = Producto.objects.get(id=pid, activo=True)
            except Producto.DoesNotExist:
                return respuesta_error('Producto no encontrado', codigo=404)

            items.append({'producto': producto, 'cantidad': cant})

        # Verificar stock para todo el carrito
        disponible, mensaje = ProductosService.verificar_stock_carrito(items)
        if not disponible:
            return respuesta_error(mensaje, codigo=409)

        # Calcular totales del carrito
        totales = ProductosService.calcular_precio_carrito(items, metodo_entrega)

        # Crear orden + items
        with transaction.atomic():
            orden = OrdenCompra.objects.create(
                cliente=cliente,
                subtotal=totales['subtotal'],
                costo_envio=totales['costo_envio'],
                total=totales['total'],
                metodo_entrega=metodo_entrega,
                direccion_entrega=direccion_entrega,
                estado='apartado',
                pagado=False,
                registrado_por=cliente,
                notas=data.get('notas', '')
            )

            for it in items:
                producto = it['producto']
                cant = it['cantidad']
                subtotal_item = float(producto.precio) * cant
                OrdenCompraItem.objects.create(
                    orden=orden,
                    producto=producto,
                    cantidad=cant,
                    precio_unitario=float(producto.precio),
                    subtotal=subtotal_item
                )
        
        datos_items = [{
            'producto': {
                'id': i.producto.id,
                'nombre': i.producto.nombre,
                'precio': float(i.producto.precio),
            },
            'cantidad': i.cantidad,
            'precio_unitario': float(i.precio_unitario),
            'subtotal': float(i.subtotal),
        } for i in orden.items.select_related('producto').all()]

        return respuesta_exito('Compra creada exitosamente', {
            'compra': {
                'id': orden.id,
                'subtotal': float(orden.subtotal),
                'costo_envio': float(orden.costo_envio),
                'total': float(orden.total),
                'metodo_entrega': orden.metodo_entrega,
                'metodo_entrega_display': orden.get_metodo_entrega_display(),
                'direccion_entrega': orden.direccion_entrega,
                'estado': orden.estado,
                'estado_display': orden.get_estado_display(),
                'pagado': orden.pagado,
                'fecha_creacion': orden.fecha_creacion.isoformat(),
                'productos': datos_items,
            }
        }, codigo=201)
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al crear compra', detalles=str(e))


@csrf_exempt
@requiere_cliente
def mis_compras(request):
    """Lista las compras del cliente autenticado"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        cliente = obtener_usuario_desde_request(request)
        estado = request.GET.get('estado')  # Filtro opcional

        ordenes = OrdenCompra.objects.filter(cliente=cliente).prefetch_related('items__producto').order_by('-fecha_creacion')
        if estado:
            ordenes = ordenes.filter(estado=estado)

        datos = []
        for o in ordenes:
            productos = [{
                'producto': {
                    'id': it.producto.id,
                    'nombre': it.producto.nombre,
                    'precio': float(it.producto.precio),
                },
                'cantidad': it.cantidad,
                'precio_unitario': float(it.precio_unitario),
                'subtotal': float(it.subtotal),
            } for it in o.items.select_related('producto').all()]

            datos.append({
                'id': o.id,
                'subtotal': float(o.subtotal),
                'costo_envio': float(o.costo_envio),
                'total': float(o.total),
                'metodo_entrega': o.metodo_entrega,
                'metodo_entrega_display': o.get_metodo_entrega_display(),
                'estado': o.estado,
                'estado_display': o.get_estado_display(),
                'pagado': o.pagado,
                'fecha_creacion': o.fecha_creacion.isoformat(),
                'fecha_entrega': o.fecha_entrega.isoformat() if o.fecha_entrega else None,
                'productos': productos,
            })

        return respuesta_exito('Compras obtenidas', {'compras': datos})
        
    except Exception as e:
        return respuesta_error('Error al obtener compras', detalles=str(e))


@csrf_exempt
@requiere_cliente
def detalle_compra(request, compra_id):
    """Obtiene el detalle de una compra específica"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        cliente = obtener_usuario_desde_request(request)
        
        try:
            compra = OrdenCompra.objects.prefetch_related('items__producto').get(id=compra_id, cliente=cliente)
        except OrdenCompra.DoesNotExist:
            return respuesta_error('Compra no encontrada', codigo=404)

        datos_items = [{
            'producto': {
                'id': it.producto.id,
                'nombre': it.producto.nombre,
                'descripcion': it.producto.descripcion,
                'precio': float(it.producto.precio),
                'imagen_url': it.producto.imagen_url,
            },
            'cantidad': it.cantidad,
            'precio_unitario': float(it.precio_unitario),
            'subtotal': float(it.subtotal),
        } for it in compra.items.select_related('producto').all()]

        datos_compra = {
            'id': compra.id,
            'subtotal': float(compra.subtotal),
            'costo_envio': float(compra.costo_envio),
            'total': float(compra.total),
            'productos': datos_items,
            'metodo_entrega': compra.metodo_entrega,
            'metodo_entrega_display': compra.get_metodo_entrega_display(),
            'direccion_entrega': compra.direccion_entrega,
            'estado': compra.estado,
            'estado_display': compra.get_estado_display(),
            'pagado': compra.pagado,
            'metodo_pago': compra.metodo_pago,
            'pago_validado': compra.pago_validado,
            'fecha_creacion': compra.fecha_creacion.isoformat(),
            'fecha_actualizacion': compra.fecha_actualizacion.isoformat(),
            'fecha_entrega': compra.fecha_entrega.isoformat() if compra.fecha_entrega else None,
            'notas': compra.notas,
        }
        
        return respuesta_exito('Compra obtenida', {'compra': datos_compra})
        
    except Exception as e:
        return respuesta_error('Error al obtener compra', detalles=str(e))


@csrf_exempt
@requiere_cliente
def cancelar_compra(request, compra_id):
    """Cancela una compra (solo clientes, antes de pagar)"""
    if request.method != 'PUT':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        cliente = obtener_usuario_desde_request(request)
        
        try:
            compra = OrdenCompra.objects.get(id=compra_id, cliente=cliente)
        except OrdenCompra.DoesNotExist:
            return respuesta_error('Compra no encontrada', codigo=404)
        
        # Solo se puede cancelar si no está pagada
        if compra.pagado:
            return respuesta_error('No se puede cancelar una compra ya pagada', codigo=400)
        
        if compra.estado == 'cancelado':
            return respuesta_error('La compra ya está cancelada', codigo=400)
        
        compra.estado = 'cancelado'
        compra.save(update_fields=['estado'])
        
        return respuesta_exito('Compra cancelada exitosamente')
        
    except Exception as e:
        return respuesta_error('Error al cancelar compra', detalles=str(e))


# ============================================
# ENDPOINTS PARA ADMIN/SECRETARIA
# ============================================

@csrf_exempt
@requiere_administrador
def crear_producto(request):
    """Crea un nuevo producto (solo admin)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        nombre = data.get('nombre')
        precio = data.get('precio')
        
        if not nombre or precio is None:
            return respuesta_error('nombre y precio son requeridos')
        
        try:
            precio = float(precio)
            if precio < 0:
                return respuesta_error('El precio debe ser mayor o igual a 0')
        except (ValueError, TypeError):
            return respuesta_error('precio debe ser un número válido')
        
        # Crear producto
        producto = Producto.objects.create(
            nombre=nombre,
            descripcion=data.get('descripcion', ''),
            precio=precio,
            categoria=data.get('categoria', 'otro'),
            stock_actual=data.get('stock_actual', 0),
            stock_minimo=data.get('stock_minimo', 5),
            imagen_url=data.get('imagen_url', ''),
            activo=data.get('activo', True),
        )
        
        return respuesta_exito('Producto creado exitosamente', {
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': float(producto.precio),
                'stock_actual': producto.stock_actual,
            }
        }, codigo=201)
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al crear producto', detalles=str(e))


@csrf_exempt
@requiere_administrador
def actualizar_producto(request, producto_id):
    """Actualiza un producto existente (solo admin)"""
    if request.method != 'PUT':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return respuesta_error('Producto no encontrado', codigo=404)
        
        data = json.loads(request.body)
        
        # Actualizar campos permitidos
        if 'nombre' in data:
            producto.nombre = data['nombre']
        if 'descripcion' in data:
            producto.descripcion = data['descripcion']
        if 'precio' in data:
            try:
                precio = float(data['precio'])
                if precio < 0:
                    return respuesta_error('El precio debe ser mayor o igual a 0')
                producto.precio = precio
            except (ValueError, TypeError):
                return respuesta_error('precio debe ser un número válido')
        if 'categoria' in data:
            producto.categoria = data['categoria']
        if 'imagen_url' in data:
            producto.imagen_url = data['imagen_url']
        if 'activo' in data:
            producto.activo = data['activo']
        if 'stock_minimo' in data:
            try:
                producto.stock_minimo = int(data['stock_minimo'])
            except (ValueError, TypeError):
                return respuesta_error('stock_minimo debe ser un número válido')
        
        producto.save()
        
        return respuesta_exito('Producto actualizado exitosamente', {
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': float(producto.precio),
                'stock_actual': producto.stock_actual,
            }
        })
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al actualizar producto', detalles=str(e))


@csrf_exempt
@requiere_administrador
def actualizar_stock(request, producto_id):
    """Actualiza el stock de un producto (solo admin)"""
    if request.method != 'PUT':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return respuesta_error('Producto no encontrado', codigo=404)
        
        data = json.loads(request.body)
        cantidad = data.get('cantidad')
        operacion = data.get('operacion', 'aumentar')  # 'aumentar' o 'reducir'
        
        if cantidad is None:
            return respuesta_error('cantidad es requerida')
        
        try:
            cantidad = int(cantidad)
            if cantidad <= 0:
                return respuesta_error('La cantidad debe ser mayor a 0')
        except (ValueError, TypeError):
            return respuesta_error('cantidad debe ser un número válido')
        
        # Realizar operación
        if operacion == 'aumentar':
            producto.aumentar_stock(cantidad)
            mensaje = f'Stock aumentado en {cantidad} unidades'
        elif operacion == 'reducir':
            if not producto.reducir_stock(cantidad):
                return respuesta_error('Stock insuficiente para reducir')
            mensaje = f'Stock reducido en {cantidad} unidades'
        else:
            return respuesta_error('operacion debe ser "aumentar" o "reducir"')
        
        return respuesta_exito(mensaje, {
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'stock_actual': producto.stock_actual,
                'stock_bajo': producto.stock_bajo(),
            }
        })
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al actualizar stock', detalles=str(e))


@csrf_exempt
@requiere_administrador
def eliminar_producto(request, producto_id):
    """Elimina (desactiva) un producto (solo admin)"""
    if request.method != 'DELETE':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return respuesta_error('Producto no encontrado', codigo=404)
        
        # No eliminar físicamente, solo desactivar
        producto.activo = False
        producto.save()
        
        return respuesta_exito('Producto desactivado exitosamente')
        
    except Exception as e:
        return respuesta_error('Error al eliminar producto', detalles=str(e))


@csrf_exempt
@requiere_admin_o_secretaria
def listar_compras(request):
    """Lista todas las compras (secretaria/admin)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        estado = request.GET.get('estado')
        cliente_id = request.GET.get('cliente_id')
        pagado = request.GET.get('pagado')
        
        compras = OrdenCompra.objects.select_related('cliente').prefetch_related('items__producto').all()
        
        if estado:
            compras = compras.filter(estado=estado)
        if cliente_id:
            compras = compras.filter(cliente_id=cliente_id)
        if pagado is not None:
            compras = compras.filter(pagado=pagado.lower() == 'true')
        
        compras = compras.order_by('-fecha_creacion')
        
        datos_compras = []
        for c in compras:
            datos_compras.append({
                'id': c.id,
                'cliente': {
                    'id': c.cliente.id,
                    'nombre': c.cliente.get_full_name() or c.cliente.email,
                    'email': c.cliente.email,
                },
                'subtotal': float(c.subtotal),
                'costo_envio': float(c.costo_envio),
                'total': float(c.total),
                'estado': c.estado,
                'pagado': c.pagado,
                'metodo_pago': c.metodo_pago,
                'fecha_creacion': c.fecha_creacion.isoformat(),
                'productos': [{
                    'producto': {'id': it.producto.id, 'nombre': it.producto.nombre},
                    'cantidad': it.cantidad,
                    'subtotal': float(it.subtotal),
                } for it in c.items.select_related('producto').all()]
            })
        
        return respuesta_exito('Compras obtenidas', {'compras': datos_compras})
        
    except Exception as e:
        return respuesta_error('Error al obtener compras', detalles=str(e))


@csrf_exempt
@requiere_secretaria
def validar_pago_compra(request, compra_id):
    """Valida un pago por transferencia de una compra (secretaria)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        secretaria = obtener_usuario_desde_request(request)
        
        try:
            compra = OrdenCompra.objects.prefetch_related('items__producto').get(id=compra_id)
        except OrdenCompra.DoesNotExist:
            return respuesta_error('Compra no encontrada', codigo=404)
        
        data = json.loads(request.body) if request.body else {}
        id_pago = data.get('id_pago_transferencia', compra.id_pago_transferencia)
        
        if not id_pago:
            return respuesta_error('id_pago_transferencia es requerido')
        
        # Validar pago
        compra.id_pago_transferencia = id_pago
        compra.metodo_pago = 'transferencia'
        
        if compra.validar_transferencia(secretaria):
            return respuesta_exito('Pago validado exitosamente', {
                'compra': {
                    'id': compra.id,
                    'estado': compra.estado,
                    'pagado': compra.pagado,
                    'total': float(compra.total),
                }
            })
        else:
            return respuesta_error('Error al validar el pago', codigo=400)
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al validar pago', detalles=str(e))


@csrf_exempt
@requiere_admin_o_secretaria
def productos_bajo_stock(request):
    """Obtiene productos con stock bajo (secretaria/admin)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        productos = ProductosService.obtener_productos_bajo_stock()
        
        datos_productos = [{
            'id': p.id,
            'nombre': p.nombre,
            'stock_actual': p.stock_actual,
            'stock_minimo': p.stock_minimo,
            'diferencia': p.stock_minimo - p.stock_actual,
        } for p in productos]
        
        return respuesta_exito('Productos con stock bajo', {'productos': datos_productos})
        
    except Exception as e:
        return respuesta_error('Error al obtener productos', detalles=str(e))
