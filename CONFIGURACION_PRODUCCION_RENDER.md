# Configuración para Producción en Render

## 📋 Configuraciones Adicionales para Producción

Este documento explica cómo configurar las funcionalidades adicionales (Redis, Rate Limiting, Documentación API) en Render.

---

## 🔴 1. Redis para Cache

### ¿Por qué Redis?
- Cache más robusto y escalable que cache local
- Compartido entre múltiples workers
- Persistencia de datos
- Mejor rendimiento en producción

### Configuración en Render

#### Opción 1: Redis de Render (Recomendado)

1. **Crear Redis en Render**:
   - En el dashboard de Render, click en **"New +"**
   - Selecciona **"Redis"**
   - Configura:
     - **Name**: `barberia-redis` (o el nombre que prefieras)
     - **Plan**: **Free** (gratis) o **Starter** ($10/mes)
   - Click en **"Create Redis"**

2. **Obtener URL de Redis**:
   - En la página de Redis, copia la **"Internal Redis URL"**
   - Ejemplo: `redis://red-xxxxx:6379`

3. **Agregar Variable de Entorno**:
   - Ve a tu Web Service en Render
   - Sección **"Environment"**
   - Agrega:
     - **Key**: `REDIS_URL`
     - **Value**: La URL que copiaste (ej: `redis://red-xxxxx:6379`)

4. **Instalar django-redis** (si no está instalado):
   - Agrega a `requirements.txt`:
     ```
     django-redis==5.4.0
     ```

5. **El código ya está preparado**:
   - `settings.py` detecta automáticamente `REDIS_URL`
   - Si existe, usa Redis; si no, usa cache local

#### Opción 2: Redis Externo (Upstash, Redis Cloud, etc.)

1. Crear cuenta en el servicio de Redis
2. Obtener URL de conexión
3. Agregar como variable de entorno `REDIS_URL` en Render

### Verificar que Funciona

Después de configurar, el cache debería usar Redis automáticamente. No se requiere cambio de código.

---

## 🚦 2. Rate Limiting

### ¿Por qué Rate Limiting?
- Previene abuso de la API
- Protege contra ataques DDoS básicos
- Controla el uso de recursos

### Configuración en Render

1. **Habilitar Rate Limiting**:
   - Ve a tu Web Service en Render
   - Sección **"Environment"**
   - Agrega:
     - **Key**: `ENABLE_RATE_LIMIT`
     - **Value**: `True`

2. **Configurar Límites** (opcional):
   - Edita `core/middleware_rate_limit.py` para ajustar:
     ```python
     self.rate_limit = 100  # requests
     self.rate_window = 60  # segundos
     ```

3. **Alternativa: django-ratelimit**:
   - Si prefieres usar `django-ratelimit` (más robusto):
   - Ya está en `requirements.txt`
   - Agrega decoradores a las vistas según necesidad

### Límites Recomendados

- **Endpoints públicos**: 100 requests/minuto por IP
- **Endpoints autenticados**: 60 requests/minuto por usuario
- **Endpoints de creación**: 10 requests/minuto por usuario

---

## 📚 3. Documentación API con drf-yasg

### ¿Por qué drf-yasg?
- Documentación interactiva de la API
- Swagger UI para probar endpoints
- ReDoc para documentación legible
- Esquema OpenAPI estándar

### Configuración en Render

1. **Instalar drf-yasg**:
   - Ya está en `requirements.txt`
   - Se instalará automáticamente en el deploy

2. **Habilitar en settings.py**:
   - El código ya detecta automáticamente si está instalado
   - Si está instalado, se habilita automáticamente

3. **Acceder a la Documentación**:
   - **Swagger UI**: `https://tu-backend.onrender.com/swagger/`
   - **ReDoc**: `https://tu-backend.onrender.com/redoc/`
   - **JSON Schema**: `https://tu-backend.onrender.com/swagger.json`

### Personalizar Documentación

Edita `core/urls.py` para personalizar:
- Título de la API
- Descripción
- Información de contacto
- Términos de servicio

---

## 📝 Variables de Entorno en Render

### Variables Requeridas (Básicas)
```
DEBUG=False
SECRET_KEY=tu-secret-key-generada
DATABASE_URL=<de la base de datos PostgreSQL>
ALLOWED_HOSTS=.onrender.com
CORS_ALLOWED_ORIGINS=https://tu-frontend.vercel.app
CSRF_TRUSTED_ORIGINS=https://tu-backend.onrender.com,https://tu-frontend.vercel.app
```

### Variables Opcionales (Funcionalidades Adicionales)

#### Cache con Redis
```
REDIS_URL=redis://red-xxxxx:6379
CACHE_TTL=300  # 5 minutos (opcional)
```

#### Rate Limiting
```
ENABLE_RATE_LIMIT=True
```

#### Email (Resend)
```
RESEND_API_KEY=tu-api-key-de-resend
```

#### Mercado Pago
```
MERCADO_PAGO_ACCESS_TOKEN=tu-access-token
MERCADO_PAGO_SUCCESS_URL=https://tu-frontend.vercel.app/pago-exitoso
MERCADO_PAGO_FAILURE_URL=https://tu-frontend.vercel.app/pago-fallido
MERCADO_PAGO_PENDING_URL=https://tu-frontend.vercel.app/pago-pendiente
```

#### Firebase
```
FIREBASE_CREDENTIALS=<JSON completo de credenciales>
```

---

## 🚀 Pasos para Configurar en Render

### Paso 1: Crear Redis (Opcional pero Recomendado)

1. Dashboard Render → **"New +"** → **"Redis"**
2. Configurar y crear
3. Copiar Internal Redis URL
4. Agregar `REDIS_URL` en variables de entorno del Web Service

### Paso 2: Habilitar Rate Limiting (Opcional)

1. En variables de entorno del Web Service
2. Agregar `ENABLE_RATE_LIMIT=True`

### Paso 3: Verificar Documentación API

1. Después del deploy, visitar `https://tu-backend.onrender.com/swagger/`
2. Si no aparece, verificar que `drf-yasg` se instaló correctamente
3. Revisar logs si hay errores

### Paso 4: Verificar Cache

1. Hacer request a `/api/citas/servicios/`
2. Verificar en logs que se está usando Redis (si está configurado)
3. Probar que el cache funciona (segunda request más rápida)

---

## ✅ Checklist de Configuración en Producción

### Básico (Requerido)
- [x] PostgreSQL configurado
- [x] Variables de entorno básicas
- [x] DEBUG=False
- [x] SECRET_KEY configurada

### Opcional (Recomendado)
- [ ] Redis creado y configurado
- [ ] Rate limiting habilitado
- [ ] drf-yasg instalado (automático)
- [ ] Variables de email configuradas
- [ ] Variables de Mercado Pago configuradas (si se usa)

---

## 🔍 Verificar Configuración

### Verificar Redis
```bash
# En los logs de Render, deberías ver que se conecta a Redis
# O hacer un request y verificar que el cache funciona
```

### Verificar Rate Limiting
```bash
# Hacer múltiples requests rápidas
# Debería retornar 429 después del límite
```

### Verificar Documentación
```bash
# Visitar https://tu-backend.onrender.com/swagger/
# Debería mostrar la documentación interactiva
```

---

## 📊 Costos Estimados en Render

- **PostgreSQL**: Gratis (plan Free)
- **Web Service**: Gratis (plan Free) o $7/mes (Starter)
- **Redis**: Gratis (plan Free) o $10/mes (Starter)
- **Total Free**: $0/mes (con limitaciones)
- **Total Starter**: ~$17/mes (sin limitaciones)

---

## 🎉 Resumen

**Todo el código está preparado** para funcionar con estas configuraciones. Solo necesitas:

1. **Redis**: Crear en Render y agregar `REDIS_URL`
2. **Rate Limiting**: Agregar `ENABLE_RATE_LIMIT=True`
3. **Documentación**: Se habilita automáticamente si `drf-yasg` está instalado

**No se requiere cambio de código**, solo configuración en Render.

---

*Documento creado - 28 de enero de 2026*
