# accounts/decorators.py
from functools import wraps
from django.http import JsonResponse
import logging

security_logger = logging.getLogger('security')


def login_required_json(view_func):
    """
    Decorador que requiere que el usuario esté autenticado
    Devuelve JSON en lugar de redirigir
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('authenticated'):
            security_logger.warning(
                f'Intento de acceso no autenticado a {request.path} desde IP {get_client_ip(request)}'
            )
            return JsonResponse({
                'ok': False,
                'error': 'No autenticado. Por favor inicia sesión.'
            }, status=401)

        return view_func(request, *args, **kwargs)

    return wrapper


def require_verified_email(view_func):
    """
    Decorador que requiere que el usuario tenga email verificado
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'ok': False,
                'error': 'No autenticado'
            }, status=401)

        from django.contrib.auth import get_user_model
        Usuario = get_user_model()

        try:
            usuario = Usuario.objects.get(id=user_id)
            if not usuario.verificado:
                security_logger.warning(
                    f'Usuario {usuario.email} intentó acceder sin verificar email'
                )
                return JsonResponse({
                    'ok': False,
                    'error': 'Debes verificar tu correo electrónico primero'
                }, status=403)
        except Usuario.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': 'Usuario no encontrado'
            }, status=404)

        return view_func(request, *args, **kwargs)

    return wrapper


def admin_required(view_func):
    """
    Decorador que requiere que el usuario sea administrador
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'ok': False,
                'error': 'No autenticado'
            }, status=401)

        from django.contrib.auth import get_user_model
        Usuario = get_user_model()

        try:
            usuario = Usuario.objects.get(id=user_id)
            if not usuario.is_staff and not usuario.is_superuser:
                security_logger.warning(
                    f'Usuario {usuario.email} intentó acceder a recurso de admin sin permisos'
                )
                return JsonResponse({
                    'ok': False,
                    'error': 'Acceso denegado. Se requieren permisos de administrador.'
                }, status=403)
        except Usuario.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': 'Usuario no encontrado'
            }, status=404)

        return view_func(request, *args, **kwargs)

    return wrapper


def get_client_ip(request):
    """
    Obtener IP del cliente considerando proxies
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
