# accounts/admin_views.py
# APIs para el panel de administración

import json
import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta
from .models import Servicio, Producto, Cita, ConfiguracionSistema

# Cloudinary para subida de imágenes
import cloudinary
import cloudinary.uploader

Usuario = get_user_model()


def admin_required(view_func):
    """Decorador para verificar que el usuario es administrador"""
    def wrapper(request, *args, **kwargs):
        # Por ahora verificamos con un header simple
        # En producción deberías usar JWT o sesiones
        user_email = request.headers.get('X-User-Email')
        if not user_email:
            return JsonResponse({'error': 'No autorizado'}, status=401)
        
        try:
            usuario = Usuario.objects.get(email=user_email)
            if usuario.rol != 'admin':
                return JsonResponse({'error': 'Acceso denegado. Se requiere rol de administrador'}, status=403)
            request.admin_user = usuario
        except Usuario.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=401)
        
        return view_func(request, *args, **kwargs)
    return wrapper


# ============================================
# DASHBOARD - ESTADÍSTICAS
# ============================================
@csrf_exempt
def dashboard_stats(request):
    """Obtener estadísticas del dashboard"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    hoy = datetime.now().date()
    inicio_mes = hoy.replace(day=1)
    
    # Estadísticas básicas
    stats = {
        'ventas_dia': 0,  # Placeholder - se calculará cuando haya ventas
        'citas_hoy': Cita.objects.filter(fecha=hoy).count(),
        'citas_pendientes': Cita.objects.filter(fecha=hoy, estado='pendiente').count(),
        'productos_stock_bajo': Producto.objects.filter(stock__lte=F('stock_minimo'), activo=True).count(),
        'total_clientes': Usuario.objects.filter(rol='cliente').count(),
        'servicios_activos': Servicio.objects.filter(activo=True).count(),
        'productos_activos': Producto.objects.filter(activo=True).count(),
    }
    
    # Productos con stock bajo
    productos_bajo = list(Producto.objects.filter(
        stock__lte=F('stock_minimo'),
        activo=True
    ).values('id', 'nombre', 'stock', 'stock_minimo')[:10])
    
    # Top servicios (placeholder)
    top_servicios = list(Servicio.objects.filter(activo=True).values(
        'id', 'nombre', 'precio'
    )[:5])
    
    return JsonResponse({
        'ok': True,
        'stats': stats,
        'productos_stock_bajo': productos_bajo,
        'top_servicios': top_servicios
    })


# ============================================
# SERVICIOS CRUD
# ============================================
@csrf_exempt
def servicios_list(request):
    """Listar todos los servicios o crear uno nuevo"""
    if request.method == 'GET':
        servicios = list(Servicio.objects.all().values(
            'id', 'nombre', 'descripcion', 'precio', 'duracion_minutos',
            'categoria', 'imagen_url', 'activo', 'popular', 'fecha_creacion'
        ))
        return JsonResponse({'ok': True, 'servicios': servicios})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        
        # Validar campos requeridos
        if not data.get('nombre') or not data.get('precio'):
            return JsonResponse({'error': 'Nombre y precio son requeridos'}, status=400)
        
        servicio = Servicio.objects.create(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            precio=data['precio'],
            duracion_minutos=data.get('duracion_minutos', 30),
            categoria=data.get('categoria', 'corte'),
            imagen_url=data.get('imagen_url', ''),
            activo=data.get('activo', True),
            popular=data.get('popular', False)
        )
        
        return JsonResponse({
            'ok': True,
            'mensaje': 'Servicio creado exitosamente',
            'servicio': {
                'id': servicio.id,
                'nombre': servicio.nombre,
                'precio': str(servicio.precio),
                'imagen_url': servicio.imagen_url
            }
        }, status=201)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@csrf_exempt
def servicio_detail(request, servicio_id):
    """Obtener, actualizar o eliminar un servicio"""
    try:
        servicio = Servicio.objects.get(id=servicio_id)
    except Servicio.DoesNotExist:
        return JsonResponse({'error': 'Servicio no encontrado'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'ok': True,
            'servicio': {
                'id': servicio.id,
                'nombre': servicio.nombre,
                'descripcion': servicio.descripcion,
                'precio': str(servicio.precio),
                'duracion_minutos': servicio.duracion_minutos,
                'categoria': servicio.categoria,
                'imagen_url': servicio.imagen_url,
                'activo': servicio.activo,
                'popular': servicio.popular
            }
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        
        # Actualizar campos
        if 'nombre' in data:
            servicio.nombre = data['nombre']
        if 'descripcion' in data:
            servicio.descripcion = data['descripcion']
        if 'precio' in data:
            servicio.precio = data['precio']
        if 'duracion_minutos' in data:
            servicio.duracion_minutos = data['duracion_minutos']
        if 'categoria' in data:
            servicio.categoria = data['categoria']
        if 'imagen_url' in data:
            servicio.imagen_url = data['imagen_url']
        if 'activo' in data:
            servicio.activo = data['activo']
        if 'popular' in data:
            servicio.popular = data['popular']
        
        servicio.save()
        
        return JsonResponse({
            'ok': True,
            'mensaje': 'Servicio actualizado exitosamente'
        })
    
    elif request.method == 'DELETE':
        # Soft delete - solo desactivar
        servicio.activo = False
        servicio.save()
        return JsonResponse({
            'ok': True,
            'mensaje': 'Servicio eliminado exitosamente'
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ============================================
# PRODUCTOS CRUD
# ============================================
@csrf_exempt
def productos_list(request):
    """Listar todos los productos o crear uno nuevo"""
    if request.method == 'GET':
        productos = list(Producto.objects.all().values(
            'id', 'nombre', 'descripcion', 'precio', 'categoria',
            'stock', 'stock_minimo', 'activo', 'destacado', 'nuevo'
        ))
        return JsonResponse({'ok': True, 'productos': productos})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        
        if not data.get('nombre') or not data.get('precio'):
            return JsonResponse({'error': 'Nombre y precio son requeridos'}, status=400)
        
        producto = Producto.objects.create(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            precio=data['precio'],
            categoria=data.get('categoria', 'cabello'),
            stock=data.get('stock', 0),
            stock_minimo=data.get('stock_minimo', 10),
            activo=data.get('activo', True),
            destacado=data.get('destacado', False),
            nuevo=data.get('nuevo', False)
        )
        
        return JsonResponse({
            'ok': True,
            'mensaje': 'Producto creado exitosamente',
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre
            }
        }, status=201)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@csrf_exempt
def producto_detail(request, producto_id):
    """Obtener, actualizar o eliminar un producto"""
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'ok': True,
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion,
                'precio': str(producto.precio),
                'categoria': producto.categoria,
                'stock': producto.stock,
                'stock_minimo': producto.stock_minimo,
                'activo': producto.activo,
                'destacado': producto.destacado,
                'nuevo': producto.nuevo
            }
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        
        for field in ['nombre', 'descripcion', 'precio', 'categoria', 'stock', 
                      'stock_minimo', 'activo', 'destacado', 'nuevo']:
            if field in data:
                setattr(producto, field, data[field])
        
        producto.save()
        
        return JsonResponse({
            'ok': True,
            'mensaje': 'Producto actualizado exitosamente'
        })
    
    elif request.method == 'DELETE':
        producto.activo = False
        producto.save()
        return JsonResponse({
            'ok': True,
            'mensaje': 'Producto eliminado exitosamente'
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@csrf_exempt
def producto_stock(request, producto_id):
    """Actualizar stock de un producto"""
    if request.method != 'PUT':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    
    cantidad = data.get('cantidad', 0)
    operacion = data.get('operacion', 'sumar')  # 'sumar' o 'establecer'
    
    if operacion == 'establecer':
        producto.stock = cantidad
    else:
        producto.stock += cantidad
    
    if producto.stock < 0:
        producto.stock = 0
    
    producto.save()
    
    return JsonResponse({
        'ok': True,
        'mensaje': 'Stock actualizado',
        'stock_actual': producto.stock
    })


# ============================================
# EMPLEADOS (Usuarios) CRUD
# ============================================
@csrf_exempt
def empleados_list(request):
    """Listar empleados o crear uno nuevo"""
    if request.method == 'GET':
        # Filtrar por rol si se especifica
        rol = request.GET.get('rol', None)
        queryset = Usuario.objects.all()
        
        if rol:
            queryset = queryset.filter(rol=rol)
        
        empleados = list(queryset.values(
            'id', 'email', 'username', 'first_name', 'last_name',
            'telefono', 'rol', 'is_active', 'date_joined'
        ))
        
        return JsonResponse({'ok': True, 'empleados': empleados})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        
        # Validar campos requeridos
        required = ['email', 'password', 'nombre']
        for field in required:
            if not data.get(field):
                return JsonResponse({'error': f'El campo {field} es requerido'}, status=400)
        
        # Verificar que el email no exista
        if Usuario.objects.filter(email=data['email']).exists():
            return JsonResponse({'error': 'El correo ya está registrado'}, status=400)
        
        # Crear username basado en email si no se proporciona
        username = data.get('username', data['email'].split('@')[0])
        if Usuario.objects.filter(username=username).exists():
            username = f"{username}_{Usuario.objects.count()}"
        
        usuario = Usuario.objects.create_user(
            username=username,
            email=data['email'],
            password=data['password'],
            first_name=data.get('nombre', ''),
            last_name=data.get('apellido', ''),
            telefono=data.get('telefono', ''),
            rol=data.get('rol', 'cliente'),
            verificado=True
        )
        
        return JsonResponse({
            'ok': True,
            'mensaje': 'Empleado creado exitosamente',
            'empleado': {
                'id': usuario.id,
                'email': usuario.email,
                'rol': usuario.rol
            }
        }, status=201)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@csrf_exempt
def empleado_detail(request, empleado_id):
    """Obtener, actualizar o eliminar un empleado"""
    try:
        empleado = Usuario.objects.get(id=empleado_id)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Empleado no encontrado'}, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'ok': True,
            'empleado': {
                'id': empleado.id,
                'email': empleado.email,
                'username': empleado.username,
                'nombre': empleado.first_name,
                'apellido': empleado.last_name,
                'telefono': empleado.telefono,
                'rol': empleado.rol,
                'activo': empleado.is_active,
                'verificado': empleado.verificado
            }
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        
        if 'nombre' in data:
            empleado.first_name = data['nombre']
        if 'apellido' in data:
            empleado.last_name = data['apellido']
        if 'telefono' in data:
            empleado.telefono = data['telefono']
        if 'rol' in data:
            empleado.rol = data['rol']
        if 'activo' in data:
            empleado.is_active = data['activo']
        if 'password' in data and data['password']:
            empleado.set_password(data['password'])
        
        empleado.save()
        
        return JsonResponse({
            'ok': True,
            'mensaje': 'Empleado actualizado exitosamente'
        })
    
    elif request.method == 'DELETE':
        # Soft delete - desactivar usuario
        empleado.is_active = False
        empleado.save()
        return JsonResponse({
            'ok': True,
            'mensaje': 'Empleado desactivado exitosamente'
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ============================================
# CONFIGURACIÓN DEL SISTEMA
# ============================================
@csrf_exempt
def configuracion(request):
    """Obtener o actualizar la configuración del sistema"""
    # Obtener o crear la configuración
    config, created = ConfiguracionSistema.objects.get_or_create(id=1)
    
    if request.method == 'GET':
        return JsonResponse({
            'ok': True,
            'configuracion': {
                'nombre_negocio': config.nombre_negocio,
                'direccion': config.direccion,
                'telefono': config.telefono,
                'email_contacto': config.email_contacto,
                'horario_apertura': str(config.horario_apertura),
                'horario_cierre': str(config.horario_cierre),
                'porcentaje_anticipo': config.porcentaje_anticipo,
                'tiempo_espera_maximo': config.tiempo_espera_maximo,
                'citas_penalizacion': config.citas_penalizacion
            }
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        
        for field in ['nombre_negocio', 'direccion', 'telefono', 'email_contacto',
                      'porcentaje_anticipo', 'tiempo_espera_maximo', 'citas_penalizacion']:
            if field in data:
                setattr(config, field, data[field])
        
        # Manejar campos de tiempo especialmente
        if 'horario_apertura' in data:
            config.horario_apertura = data['horario_apertura']
        if 'horario_cierre' in data:
            config.horario_cierre = data['horario_cierre']
        
        config.save()
        
        return JsonResponse({
            'ok': True,
            'mensaje': 'Configuración actualizada exitosamente'
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ============================================
# REPORTES BÁSICOS
# ============================================
@csrf_exempt
def reportes(request):
    """Obtener datos para reportes"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    hoy = datetime.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    
    # Resumen general
    resumen = {
        'total_clientes': Usuario.objects.filter(rol='cliente').count(),
        'clientes_nuevos_mes': Usuario.objects.filter(
            rol='cliente',
            date_joined__gte=inicio_mes
        ).count(),
        'servicios_activos': Servicio.objects.filter(activo=True).count(),
        'productos_activos': Producto.objects.filter(activo=True).count(),
        'productos_stock_bajo': Producto.objects.filter(
            stock__lte=F('stock_minimo'),
            activo=True
        ).count(),
    }
    
    # Citas por estado
    citas_por_estado = dict(Cita.objects.values('estado').annotate(
        total=Count('id')
    ).values_list('estado', 'total'))
    
    return JsonResponse({
        'ok': True,
        'resumen': resumen,
        'citas_por_estado': citas_por_estado,
        'periodo': {
            'hoy': str(hoy),
            'inicio_semana': str(inicio_semana),
            'inicio_mes': str(inicio_mes)
        }
    })


# ============================================
# CLOUDINARY - SUBIDA DE IMÁGENES
# ============================================
@csrf_exempt
def upload_image(request):
    """Subir imagen a Cloudinary"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Puede recibir la imagen como archivo o como base64
        if request.FILES.get('image'):
            # Archivo enviado como multipart/form-data
            image_file = request.FILES['image']
            folder = request.POST.get('folder', 'barberia')
            
            result = cloudinary.uploader.upload(
                image_file,
                folder=folder,
                resource_type='image',
                transformation=[
                    {'width': 800, 'height': 800, 'crop': 'limit'},
                    {'quality': 'auto:good'}
                ]
            )
        else:
            # Imagen enviada como JSON con base64
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'JSON inválido'}, status=400)
            
            if not data.get('image'):
                return JsonResponse({'error': 'No se proporcionó imagen'}, status=400)
            
            image_data = data['image']
            folder = data.get('folder', 'barberia')
            
            # Si viene con prefijo data:image/xxx;base64, lo procesamos
            if 'base64,' in image_data:
                image_data = image_data.split('base64,')[1]
            
            result = cloudinary.uploader.upload(
                f"data:image/png;base64,{image_data}",
                folder=folder,
                resource_type='image',
                transformation=[
                    {'width': 800, 'height': 800, 'crop': 'limit'},
                    {'quality': 'auto:good'}
                ]
            )
        
        return JsonResponse({
            'ok': True,
            'url': result['secure_url'],
            'public_id': result['public_id'],
            'width': result.get('width'),
            'height': result.get('height')
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error al subir imagen: {str(e)}'
        }, status=500)


@csrf_exempt
def delete_image(request):
    """Eliminar imagen de Cloudinary"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    
    public_id = data.get('public_id')
    if not public_id:
        return JsonResponse({'error': 'Se requiere public_id'}, status=400)
    
    try:
        result = cloudinary.uploader.destroy(public_id)
        return JsonResponse({
            'ok': True,
            'result': result
        })
    except Exception as e:
        return JsonResponse({
            'error': f'Error al eliminar imagen: {str(e)}'
        }, status=500)
