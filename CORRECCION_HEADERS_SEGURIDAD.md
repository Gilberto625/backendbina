# 🔒 Corrección de Headers de Seguridad HTTP

## Problema Identificado

El reporte de SecurityHeaders.com muestra que faltan o están mal configurados los siguientes headers:

- ❌ `Strict-Transport-Security` (HSTS)
- ❌ `Content-Security-Policy` (CSP)
- ❌ `X-Frame-Options`
- ❌ `X-Content-Type-Options`
- ❌ `Referrer-Policy`
- ❌ `Permissions-Policy`

---

## ✅ Solución Implementada

### Backend (Django)

#### 1. Middleware Personalizado Creado

**Archivo**: `backendbina/core/middleware.py`

Se creó un middleware personalizado que asegura que todos los headers de seguridad se envíen en cada respuesta:

```python
class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware para agregar headers de seguridad HTTP
    """
    def process_response(self, request, response):
        # Agrega todos los headers de seguridad
        ...
```

#### 2. Middleware Agregado a settings.py

**Archivo**: `backendbina/core/settings.py`

```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'core.middleware.SecurityHeadersMiddleware',  # ← NUEVO
    ...
]
```

#### 3. Headers Configurados

El middleware agrega los siguientes headers:

| Header | Valor |
|--------|-------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` |
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `X-XSS-Protection` | `1; mode=block` |
| `Content-Security-Policy` | Configuración completa (ver abajo) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Restricciones de APIs del navegador |

#### 4. Content-Security-Policy (CSP)

Configuración completa del CSP:

```
default-src 'self';
script-src 'self' 'unsafe-inline' https://www.gstatic.com https://www.googleapis.com https://apis.google.com;
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
img-src 'self' data: https:;
font-src 'self' data: https://fonts.gstatic.com;
connect-src 'self' https://backendbina-1.onrender.com https://frontbina.vercel.app https://*.vercel.app https://www.googleapis.com;
frame-ancestors 'none';
base-uri 'self';
form-action 'self';
```

---

### Frontend (Angular/Vercel)

#### 1. Headers Configurados en vercel.json

**Archivo**: `FRONTBINA/vercel.json`

Se agregó la sección `headers` para que Vercel envíe los headers de seguridad:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Strict-Transport-Security",
          "value": "max-age=31536000; includeSubDomains; preload"
        },
        ...
      ]
    }
  ]
}
```

#### 2. Headers Configurados

Los mismos headers que en el backend se configuran en Vercel para el frontend.

---

## 📋 Verificación

### Backend

```bash
# Verificar headers
curl -I https://backendbina-1.onrender.com/api/usuarios/csrf/

# Debe mostrar:
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# Content-Security-Policy: ...
# Referrer-Policy: strict-origin-when-cross-origin
# Permissions-Policy: ...
```

### Frontend

```bash
# Verificar headers
curl -I https://frontbina.vercel.app/

# Debe mostrar los mismos headers
```

### SecurityHeaders.com

1. Visitar: https://securityheaders.com
2. Probar:
   - Backend: `https://backendbina-1.onrender.com`
   - Frontend: `https://frontbina.vercel.app`
3. **Resultado esperado**: Calificación A o A+

---

## 🚀 Pasos para Aplicar

### Backend

1. ✅ Middleware creado (`core/middleware.py`)
2. ✅ Middleware agregado a `settings.py`
3. ⏳ **Commit y push**:
   ```bash
   git add core/middleware.py core/settings.py
   git commit -m "Add security headers middleware"
   git push
   ```
4. ⏳ Render desplegará automáticamente

### Frontend

1. ✅ Headers agregados a `vercel.json`
2. ⏳ **Commit y push**:
   ```bash
   cd FRONTBINA
   git add vercel.json
   git commit -m "Add security headers to Vercel config"
   git push
   ```
3. ⏳ Vercel desplegará automáticamente

---

## ✅ Checklist

- [x] Middleware personalizado creado
- [x] Middleware agregado a settings.py
- [x] Headers configurados en backend
- [x] Headers configurados en vercel.json
- [ ] Commit y push backend
- [ ] Commit y push frontend
- [ ] Verificar despliegue backend
- [ ] Verificar despliegue frontend
- [ ] Probar en SecurityHeaders.com

---

## 📊 Resultado Esperado

Después del despliegue, SecurityHeaders.com debería mostrar:

- ✅ `Strict-Transport-Security`: Presente
- ✅ `Content-Security-Policy`: Presente
- ✅ `X-Frame-Options`: Presente
- ✅ `X-Content-Type-Options`: Presente
- ✅ `Referrer-Policy`: Presente
- ✅ `Permissions-Policy`: Presente

**Calificación**: A o A+ ✅

---

## 🔍 Notas Importantes

1. **CSP y Angular**: El CSP incluye `'unsafe-inline'` y `'unsafe-eval'` para scripts porque Angular los requiere. Esto es común en aplicaciones Angular.

2. **CSP y Google APIs**: Se permiten conexiones a `www.googleapis.com` y `apis.google.com` para OAuth2 con Google.

3. **CSP y Vercel**: Se permiten conexiones a `*.vercel.app` para preview deployments.

4. **HSTS Preload**: El header incluye `preload` para ser elegible para la lista de preload de HSTS de los navegadores.

---

## ✅ Estado Final

**Backend**: ✅ Headers configurados mediante middleware personalizado
**Frontend**: ✅ Headers configurados en vercel.json

**Listo para despliegue**: ✅ Sí

Solo falta hacer commit y push de los cambios.

