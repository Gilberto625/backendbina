# core/utils_cache.py
"""
Utilidades para invalidar cache cuando se actualizan datos
"""
from django.core.cache import cache


def invalidar_cache_servicios():
    """Invalida el cache de servicios"""
    cache.delete('servicios_activos')


def invalidar_cache_barberos():
    """Invalida el cache de barberos"""
    cache.delete('barberos_activos')


def invalidar_cache_productos():
    """Invalida el cache de productos"""
    cache.delete('productos_activos')


def invalidar_todo_cache():
    """Invalida todo el cache"""
    cache.clear()
