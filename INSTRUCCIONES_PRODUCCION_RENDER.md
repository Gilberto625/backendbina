# Instrucciones para Configurar en Producción (Render)

## 🎯 Resumen

**El código ya está preparado** para funcionar con Redis, Rate Limiting y Documentación API. Solo necesitas configurar las variables de entorno en Render.

## ✅ Lo que ya está hecho en el código

1. ✅ **Cache con Redis**: El código detecta automáticamente `REDIS_URL` y usa Redis si está disponible
2. ✅ **Rate Limiting**: El código se activa automáticamente con `ENABLE_RATE_LIMIT=True`
3. ✅ **Documentación API**: Se habilita automáticamente si `drf-yasg` está instalado (ya está en requirements.txt)

## 📋 Pasos para Configurar en Render

### 1. Redis para Cache (Opcional pero Recomendado)

**¿Por qué?** Mejora el rendimiento y permite cache compartido entre workers.

**Pasos**:
1. En Render Dashboard → **"New +"** → **"Redis"**
2. Nombre: `barberia-redis` (o el que prefieras)
3. Plan: **Free** (gratis) o **Starter** ($10/mes)
4. Click **"Create Redis"**
5. Copiar la **"Internal Redis URL"** (ej: `redis://red-xxxxx:6379`)
6. En tu Web Service → **Environment** → Agregar:
   - **Key**: `REDIS_URL`
   - **Value**: La URL que copiaste
7. **Re-deploy** el servicio

**Resultado**: El cache usará Redis automáticamente. No se requiere cambio de código.

---

### 2. Rate Limiting (Opcional)

**¿Por qué?** Protege la API contra abuso y ataques.

**Pasos**:
1. En tu Web Service en Render → **Environment**
2. Agregar variable:
   - **Key**: `ENABLE_RATE_LIMIT`
   - **Value**: `True`
3. **Re-deploy** el servicio

**Resultado**: Rate limiting activado automáticamente (100 requests/minuto por IP por defecto).

**Personalizar límites**: Editar `core/middleware_rate_limit.py` antes de hacer deploy.

---

### 3. Documentación API (Automático)

**¿Por qué?** Documentación interactiva de la API para desarrolladores.

**Pasos**:
1. **Ya está en `requirements.txt`**, se instalará automáticamente
2. Descomentar en `core/settings.py`:
   ```python
   INSTALLED_APPS = [
       # ...
       'drf_yasg',  # Descomentar esta línea
       # ...
   ]
   ```
3. Hacer commit y push
4. **Re-deploy** el servicio

**Acceder**:
- Swagger UI: `https://tu-backend.onrender.com/swagger/`
- ReDoc: `https://tu-backend.onrender.com/redoc/`

---

## 🔧 Variables de Entorno en Render

### Variables Básicas (Ya configuradas)
```
DEBUG=False
SECRET_KEY=<generada automáticamente>
DATABASE_URL=<de PostgreSQL>
```

### Variables Opcionales (Agregar manualmente)

#### Para Redis
```
REDIS_URL=redis://red-xxxxx:6379
CACHE_TTL=300  # Opcional, 5 minutos por defecto
```

#### Para Rate Limiting
```
ENABLE_RATE_LIMIT=True
```

#### Para Email
```
RESEND_API_KEY=tu-api-key
```

#### Para Mercado Pago
```
MERCADO_PAGO_ACCESS_TOKEN=tu-access-token
MERCADO_PAGO_SUCCESS_URL=https://tu-frontend.vercel.app/pago-exitoso
MERCADO_PAGO_FAILURE_URL=https://tu-frontend.vercel.app/pago-fallido
MERCADO_PAGO_PENDING_URL=https://tu-frontend.vercel.app/pago-pendiente
```

---

## ✅ Checklist Rápido

### Configuración Mínima (Funciona sin esto)
- [x] PostgreSQL configurado
- [x] Variables básicas configuradas
- [x] Deploy funcionando

### Configuración Recomendada (Mejora rendimiento)
- [ ] Redis creado y `REDIS_URL` configurada
- [ ] `ENABLE_RATE_LIMIT=True` configurada
- [ ] `drf-yasg` descomentado en `INSTALLED_APPS` y deploy

### Configuración Completa (Producción robusta)
- [ ] Todas las variables de entorno configuradas
- [ ] Redis funcionando
- [ ] Rate limiting activo
- [ ] Documentación API accesible
- [ ] Monitoreo configurado (opcional)

---

## 🚀 Orden Recomendado de Configuración

1. **Primero**: Asegurar que el deploy básico funciona
2. **Segundo**: Agregar Redis (`REDIS_URL`)
3. **Tercero**: Habilitar rate limiting (`ENABLE_RATE_LIMIT=True`)
4. **Cuarto**: Habilitar documentación API (descomentar `drf_yasg`)

---

## 📝 Notas Importantes

- **No se requiere cambio de código** para Redis y Rate Limiting
- **Solo se requiere descomentar** `drf_yasg` en `INSTALLED_APPS` para documentación
- **Todas las configuraciones son opcionales** - el sistema funciona sin ellas
- **Se pueden agregar en cualquier momento** sin afectar el funcionamiento actual

---

*Documento creado - 28 de enero de 2026*
*Ver también: CONFIGURACION_PRODUCCION_RENDER.md para detalles técnicos*
