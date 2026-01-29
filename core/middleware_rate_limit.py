# core/middleware_rate_limit.py
"""
Middleware básico para rate limiting
NOTA: Para producción, usar django-ratelimit es más robusto
"""
from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone
import time


class RateLimitMiddleware:
    """
    Middleware básico para rate limiting
    
    Limita el número de requests por IP y endpoint
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Configuración por defecto
        self.rate_limit = 100  # requests
        self.rate_window = 60  # segundos
    
    def __call__(self, request):
        # Solo aplicar rate limiting a endpoints de API
        if request.path.startswith('/api/'):
            # Obtener IP del cliente
            ip = self.get_client_ip(request)
            endpoint = request.path
            
            # Crear clave de cache
            cache_key = f'ratelimit:{ip}:{endpoint}'
            
            # Obtener contador actual
            count = cache.get(cache_key, 0)
            
            if count >= self.rate_limit:
                return JsonResponse({
                    'ok': False,
                    'error': 'Rate limit exceeded',
                    'mensaje': f'Has excedido el límite de {self.rate_limit} requests por {self.rate_window} segundos'
                }, status=429)
            
            # Incrementar contador
            cache.set(cache_key, count + 1, self.rate_window)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Obtiene la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
