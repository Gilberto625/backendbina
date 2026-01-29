# Configuración de Cache y Rate Limiting

## 📦 Cache

### Configuración Actual

El sistema usa **cache local en memoria** (LocMemCache) para desarrollo. En producción, se recomienda usar Redis.

### Configuración en `settings.py`

```python
# Desarrollo: Cache local
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Producción: Redis (descomentar y configurar)
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#     }
# }
```

### Endpoints con Cache Implementado

- ✅ `GET /api/citas/servicios/` - Cache de 5 minutos
- ✅ `GET /api/citas/barberos/` - Cache de 5 minutos
- ✅ `GET /api/productos/` - Cache de 5 minutos (sin filtros)

### Invalidar Cache

Usar funciones en `core/utils_cache.py`:

```python
from core.utils_cache import invalidar_cache_servicios, invalidar_cache_productos

# Invalidar cache de servicios
invalidar_cache_servicios()

# Invalidar cache de productos
invalidar_cache_productos()
```

### Migrar a Redis en Producción

1. Instalar Redis:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
```

2. Instalar django-redis:
```bash
pip install django-redis
```

3. Actualizar `settings.py`:
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

---

## 🚦 Rate Limiting

### Configuración Actual

Se ha creado un middleware básico de rate limiting (`core/middleware_rate_limit.py`). Está **deshabilitado por defecto** en `settings.py`.

### Habilitar Rate Limiting

1. Descomentar en `settings.py`:
```python
MIDDLEWARE = [
    # ... otros middlewares ...
    'core.middleware_rate_limit.RateLimitMiddleware',  # Descomentar
    # ...
]
```

2. Configurar límites en `core/middleware_rate_limit.py`:
```python
self.rate_limit = 100  # requests
self.rate_window = 60  # segundos
```

### Usar django-ratelimit (Recomendado)

Para un rate limiting más robusto, usar `django-ratelimit`:

1. Instalar:
```bash
pip install django-ratelimit
```

2. Usar en vistas:
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/h', method='GET')
def mi_vista(request):
    # ...
```

3. Configurar por endpoint:
```python
@ratelimit(key='user', rate='10/m', method='POST')
@requiere_cliente
def crear_cita(request):
    # ...
```

### Límites Recomendados

- **Endpoints públicos**: 100 requests/minuto por IP
- **Endpoints autenticados**: 60 requests/minuto por usuario
- **Endpoints de creación**: 10 requests/minuto por usuario
- **Endpoints de administración**: 30 requests/minuto por usuario

---

## 📚 Documentación de API

### Configuración con drf-yasg

1. Instalar:
```bash
pip install drf-yasg
```

2. Agregar a `INSTALLED_APPS` en `settings.py`:
```python
INSTALLED_APPS = [
    # ...
    'drf_yasg',
]
```

3. Las URLs ya están configuradas en `core/urls.py`

### Acceder a la Documentación

- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/
- **JSON Schema**: http://localhost:8000/swagger.json
- **YAML Schema**: http://localhost:8000/swagger.yaml

### Personalizar Documentación

Editar `core/urls.py` para personalizar la información de la API.

---

## ✅ Checklist de Configuración

### Cache
- [x] Cache local configurado
- [x] Endpoints principales con cache
- [x] Funciones de invalidación creadas
- [ ] Redis configurado (producción)
- [ ] Cache de métricas y reportes

### Rate Limiting
- [x] Middleware básico creado
- [ ] Middleware habilitado (opcional)
- [ ] django-ratelimit instalado (opcional)
- [ ] Límites configurados por endpoint

### Documentación API
- [x] Estructura de drf-yasg configurada
- [ ] drf-yasg instalado
- [ ] Documentación personalizada
- [ ] Ejemplos de requests agregados

---

*Documento creado - 28 de enero de 2026*
