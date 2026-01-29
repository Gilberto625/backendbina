# Instrucciones para Redesplegar Backend en Render

## 📋 Información del Commit

- **Branch**: `gilberto-28-01-2026-v2`
- **Commit**: `4e61582`
- **Fecha**: 29 de enero de 2026
- **Repositorio**: `https://github.com/Gilberto625/backendbina.git`

---

## 🚀 Pasos para Redesplegar en Render

### Opción 1: Deploy Automático (si ya está configurado)

Si Render ya está conectado a la branch `gilberto-28-01-2026-v2`, el deploy debería ser automático después del push.

### Opción 2: Deploy Manual

1. **Ir a Render Dashboard**:
   - https://dashboard.render.com

2. **Seleccionar el servicio backend** (backendbina-1 o similar)

3. **Verificar/Cambiar la Branch**:
   - Settings → Build & Deploy → Branch
   - Cambiar a: `gilberto-28-01-2026-v2`

4. **Trigger Manual Deploy**:
   - Manual Deploy → Deploy latest commit

---

## ⚙️ Variables de Entorno Requeridas

Asegúrate de que estas variables estén configuradas en Render:

### Obligatorias
```
SECRET_KEY=<tu-secret-key-segura>
DEBUG=False
DATABASE_URL=<se genera automáticamente con PostgreSQL de Render>
ALLOWED_HOSTS=backendbina-1.onrender.com,localhost,127.0.0.1,frontbina.vercel.app
```

### CORS y CSRF (Frontend)
```
CORS_ALLOWED_ORIGINS=https://frontbina.vercel.app,http://localhost:4200
CSRF_TRUSTED_ORIGINS=https://frontbina.vercel.app,http://localhost:4200
```

### Email (Resend)
```
RESEND_API_KEY=<tu-api-key-de-resend>
```

### Firebase Cloud Messaging (Push - Opcional)
```
FCM_ENABLED=True
```
> **Nota**: Requiere archivo `config/firebase-service-account.json` en el repositorio.

### Mercado Pago (Opcional - Pendiente)
```
MERCADO_PAGO_ACCESS_TOKEN=<tu-access-token>
MERCADO_PAGO_SUCCESS_URL=https://frontbina.vercel.app/pago-exitoso
MERCADO_PAGO_FAILURE_URL=https://frontbina.vercel.app/pago-fallido
MERCADO_PAGO_PENDING_URL=https://frontbina.vercel.app/pago-pendiente
```

### Cache (Opcional)
```
REDIS_URL=<url-de-redis-si-usas>
```

### Rate Limiting (Opcional)
```
ENABLE_RATE_LIMIT=True
```

---

## 📦 Migraciones

El script `build.sh` ejecuta las migraciones automáticamente:

```bash
#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

Si necesitas ejecutarlas manualmente desde la shell de Render:
```bash
python manage.py migrate
python manage.py crear_datos_iniciales  # Crea sillas, servicios, configuración por defecto
```

---

## ✅ Verificación Post-Deploy

1. **Verificar que el servicio está corriendo**:
   - https://backendbina-1.onrender.com/

2. **Verificar Swagger/Docs** (si drf-yasg está instalado):
   - https://backendbina-1.onrender.com/swagger/

3. **Verificar endpoint de CSRF**:
   - GET https://backendbina-1.onrender.com/api/usuarios/csrf/

4. **Verificar endpoints principales**:
   - GET https://backendbina-1.onrender.com/api/citas/servicios/
   - GET https://backendbina-1.onrender.com/api/citas/barberos/
   - GET https://backendbina-1.onrender.com/api/productos/

---

## 📝 Cambios Incluidos en este Deploy

### Apps Nuevas
- `citas` - Gestión de citas y servicios
- `productos` - Catálogo y compras
- `pagos` - Pagos y Mercado Pago (estructura)
- `barberos` - Gestión de barberos
- `configuracion` - Configuración del sistema y admin
- `notificaciones` - Email, SMS (pendiente) y Push (FCM)

### Características
- Sistema de permisos por roles (cliente, secretaria, barbero, admin)
- Decoradores para proteger endpoints
- Integración FCM para push notifications
- Email vía Resend
- CORS configurado para Vercel
- 28 tests unitarios y de integración

---

## 🔧 Solución de Problemas

### Error de migración
```bash
python manage.py migrate --fake-initial
```

### Error de CORS
Verificar que `CORS_ALLOWED_ORIGINS` incluya el dominio del frontend.

### Error de CSRF
Verificar que `CSRF_TRUSTED_ORIGINS` incluya el dominio del frontend.

### Push no funciona
1. Verificar `FCM_ENABLED=True` en variables de entorno
2. Verificar que `config/firebase-service-account.json` existe
3. Revisar logs en Render

---

*Generado: 29 de enero de 2026*
