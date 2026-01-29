# core/decorators.py
"""
Decoradores para verificación de roles y permisos en endpoints

Roles del sistema (según requerimientos):
- cliente: Agenda citas, compra productos, recibe notificaciones
- secretaria: Valida pagos, gestiona citas/productos, asigna barberos/sillas
- barbero: Solo define tiempos de duración de servicios
- administrador: Gestiona TODO (empleados, productos, stock, reglas, métricas)

IMPORTANTE: El Administrador tiene acceso a TODAS las funciones del sistema
"""
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth import get_user_model

Usuario = get_user_model()


def obtener_usuario_autenticado(request):
    """
    Obtiene el usuario autenticado desde la sesión o token
    Retorna None si no está autenticado
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    return None


def requiere_autenticacion(view_func):
    """
    Decorador que verifica que el usuario esté autenticado
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        usuario = obtener_usuario_autenticado(request)
        if not usuario:
            return JsonResponse({
                'error': 'Autenticación requerida',
                'mensaje': 'Debes iniciar sesión para acceder a este recurso'
            }, status=401)
        
        # Agregar usuario al request para uso en la vista
        request.usuario_autenticado = usuario
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def requiere_rol(*roles_permitidos, admin_siempre_accede=True):
    """
    Decorador que verifica que el usuario tenga uno de los roles especificados
    
    Por defecto, el Administrador siempre tiene acceso (según requerimientos)
    
    Uso:
        @requiere_rol('secretaria')  # Secretaria Y Administrador pueden acceder
        def mi_vista(request):
            ...
            
        @requiere_rol('cliente', admin_siempre_accede=False)  # SOLO cliente
        def vista_exclusiva_cliente(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            usuario = obtener_usuario_autenticado(request)
            
            if not usuario:
                return JsonResponse({
                    'error': 'Autenticación requerida',
                    'mensaje': 'Debes iniciar sesión para acceder a este recurso'
                }, status=401)
            
            # El administrador siempre tiene acceso (a menos que se especifique lo contrario)
            if admin_siempre_accede and usuario.rol == 'administrador':
                request.usuario_autenticado = usuario
                return view_func(request, *args, **kwargs)
            
            # Verificar que el usuario tenga uno de los roles permitidos
            if usuario.rol not in roles_permitidos:
                return JsonResponse({
                    'error': 'Acceso denegado',
                    'mensaje': f'No tienes permisos para acceder a este recurso. Roles requeridos: {", ".join(roles_permitidos)}'
                }, status=403)
            
            # Agregar usuario al request
            request.usuario_autenticado = usuario
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator


# Decoradores específicos para cada rol
# NOTA: El Administrador siempre tiene acceso a TODAS las funciones

def requiere_cliente(view_func):
    """
    Decorador que verifica que el usuario sea Cliente
    El Administrador también tiene acceso
    """
    return requiere_rol('cliente')(view_func)


def requiere_secretaria(view_func):
    """
    Decorador que verifica que el usuario sea Secretaria
    El Administrador también tiene acceso
    """
    return requiere_rol('secretaria')(view_func)


def requiere_barbero(view_func):
    """
    Decorador que verifica que el usuario sea Barbero
    El Administrador también tiene acceso
    """
    return requiere_rol('barbero')(view_func)


def requiere_administrador(view_func):
    """
    Decorador que verifica que el usuario sea Administrador
    SOLO el Administrador tiene acceso
    """
    return requiere_rol('administrador', admin_siempre_accede=False)(view_func)


def requiere_staff(view_func):
    """
    Decorador que verifica que el usuario sea parte del staff
    (Secretaria, Barbero o Administrador)
    """
    return requiere_rol('secretaria', 'barbero', 'administrador')(view_func)


def requiere_admin_o_secretaria(view_func):
    """
    Decorador que verifica que el usuario sea Administrador o Secretaria
    Útil para funciones administrativas
    """
    return requiere_rol('administrador', 'secretaria')(view_func)


def permite_invitado(view_func):
    """
    Decorador que permite acceso tanto a usuarios autenticados como invitados
    El usuario autenticado (si existe) se agrega al request
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        usuario = obtener_usuario_autenticado(request)
        request.usuario_autenticado = usuario  # Puede ser None
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
