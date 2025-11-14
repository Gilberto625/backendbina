# ✅ Verificación del Despliegue

## 📋 Checklist Inmediato

Sigue estos pasos **EN ORDEN** para verificar que tu backend esté funcionando:

### 1. Verificar que el Deploy Terminó

1. Ve a [Render Dashboard](https://dashboard.render.com/)
2. Selecciona tu servicio: **django-backend**
3. Ve a la pestaña **Events**
4. Verifica que el último deploy diga: **"Deploy live"** ✅

**Si aún dice "Build in progress" o "Deploy in progress"**: Espera unos 2-5 minutos más.

---

### 2. Verificar Logs de Deploy

En Render Dashboard → **Logs**, busca estos mensajes:

**✅ BUENOS (todo funciona)**:
```
==> Building...
Installing dependencies from requirements.txt
Collecting Django==5.2
Collecting pyotp==2.9.0
Collecting qrcode==7.4.2
...
Successfully installed all packages

==> Running build command './build.sh'
Operations to perform:
  Apply all migrations: accounts, admin, auth, contenttypes, sessions
Running migrations:
  Applying accounts.0002_add_security_fields... OK

==> Starting server
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:10000
```

**❌ MALOS (hay problemas)**:
```
ERROR: Could not find a version that satisfies the requirement pyotp
ERROR: No module named 'django_ratelimit'
ERROR: relation "accounts_usuario" does not exist
```

---

### 3. Verificar Variables de Entorno

En Render Dashboard → **Environment**, verifica que estén todas:

- ✅ `RESEND_API_KEY` = `re_VsDGc6Bs_P59jTYKMEcBjic7ymMRmHF3C`
- ✅ `CORS_ALLOWED_ORIGINS` = incluye `https://frontbina.vercel.app`
- ✅ `CSRF_TRUSTED_ORIGINS` = incluye `https://backendbina-1.onrender.com`
- ✅ `DEBUG` = `False`
- ✅ `FIREBASE_CREDENTIALS` = (JSON completo)

---

### 4. Probar el Backend Manualmente

#### Opción A: Usar cURL (Terminal)

```bash
# Test 1: Verificar que responde
curl https://backendbina-1.onrender.com/api/usuarios/csrf/

# Deberías ver: {"csrfToken":"..."}
```

```bash
# Test 2: Probar endpoint de estado de seguridad
curl -X POST https://backendbina-1.onrender.com/api/usuarios/seguridad/estado/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Deberías ver: {"error":"Usuario no encontrado"}
# Esto es BUENO - significa que el endpoint funciona
```

```bash
# Test 3: Probar registro (IMPORTANTE - cambia el email y username)
curl -X POST https://backendbina-1.onrender.com/api/usuarios/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Test",
    "apellidopaterno": "User",
    "apellidomaterno": "Demo",
    "username": "testuser123",
    "correo": "TU-EMAIL-REAL@example.com",
    "contrasena": "Test123!",
    "telefono": "5551234567",
    "preguntasecreta": "Color favorito",
    "respuestasecreta": "Azul"
  }'

# Deberías ver:
# {
#   "mensaje": "Usuario registrado con éxito",
#   "requires2fa": true,
#   "canal": "email",
#   "destino": "TU***@example.com",
#   "tempToken": "..."
# }

# Y deberías recibir un EMAIL con el código de 6 dígitos
```

#### Opción B: Usar el Script de Python

```bash
python test_production.py
```

Este script probará automáticamente varios endpoints y te dará un diagnóstico.

---

## 🔍 Diagnóstico de Problemas

### Problema 1: "Access denied" o "403 Forbidden"

**Causa**: Problema de CORS o permisos

**Solución**:
1. Verifica que `CORS_ALLOWED_ORIGINS` en Render incluya: `https://frontbina.vercel.app`
2. Verifica que `CSRF_TRUSTED_ORIGINS` incluya: `https://backendbina-1.onrender.com`
3. Reinicia el servicio en Render

### Problema 2: "No se pudo enviar el correo"

**Causa**: `RESEND_API_KEY` no está configurada o es inválida

**Solución**:
1. Ve a [Resend Dashboard](https://resend.com/api-keys)
2. Verifica que la API key sea válida
3. Si es necesario, genera una nueva API key
4. Actualiza la variable en Render
5. Reinicia el servicio

### Problema 3: "relation accounts_usuario does not exist"

**Causa**: Las migraciones no se ejecutaron

**Solución**:
1. Ve a Render Dashboard → **Shell**
2. Ejecuta:
   ```bash
   python manage.py migrate
   ```
3. Deberías ver:
   ```
   Running migrations:
     Applying accounts.0002_add_security_fields... OK
   ```

### Problema 4: "ModuleNotFoundError: No module named 'pyotp'"

**Causa**: Las dependencias no se instalaron correctamente

**Solución**:
1. Verifica que `requirements.txt` esté actualizado en el repositorio
2. En Render, haz un **Manual Deploy**:
   - Render Dashboard → tu servicio
   - Botón "Manual Deploy" → "Deploy latest commit"

### Problema 5: El registro funciona pero NO llega el email

**Posibles causas**:

1. **Email en spam**:
   - Revisa tu carpeta de spam/correo no deseado
   - Busca emails de: `onboarding@resend.dev`

2. **API Key inválida**:
   - Ve a Render Dashboard → Logs
   - Busca: `ERROR al enviar correo`
   - Si ves este error, verifica tu `RESEND_API_KEY`

3. **Dominio no verificado** (solo si NO usas `onboarding@resend.dev`):
   - Si configuraste un dominio personalizado en Resend
   - Verifica que el dominio esté verificado en [Resend Dashboard](https://resend.com/domains)

---

## 🎯 Prueba Completa del Flujo

### Paso 1: Registro

```bash
curl -X POST https://backendbina-1.onrender.com/api/usuarios/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan",
    "apellidopaterno": "Pérez",
    "apellidomaterno": "García",
    "username": "juanperez_test",
    "correo": "tu-email-real@gmail.com",
    "contrasena": "Password123!",
    "telefono": "5551234567",
    "preguntasecreta": "¿Nombre de tu primera mascota?",
    "respuestasecreta": "Firulais"
  }'
```

**Resultado esperado**:
- Código 201
- Mensaje: "Usuario registrado con éxito"
- `tempToken` recibido
- **EMAIL con código de 6 dígitos**

### Paso 2: Verificar Email

Usa el código que recibiste por email:

```bash
curl -X POST https://backendbina-1.onrender.com/api/usuarios/register/2fa/verificar/ \
  -H "Content-Type: application/json" \
  -d '{
    "tempToken": "PEGA-AQUI-EL-TEMP-TOKEN-DEL-PASO-1",
    "codigo": "123456"
  }'
```

**Resultado esperado**:
- Código 200
- Mensaje: "Verificación exitosa"
- **EMAIL de bienvenida**

### Paso 3: Login

```bash
curl -X POST https://backendbina-1.onrender.com/api/usuarios/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "tu-email-real@gmail.com",
    "password": "Password123!"
  }'
```

**Resultado esperado**:
- Código 200
- `requires2fa: true`
- Nuevo `tempToken`
- **EMAIL con código de 6 dígitos**

### Paso 4: Verificar Login

```bash
curl -X POST https://backendbina-1.onrender.com/api/usuarios/login/2fa/verificar/ \
  -H "Content-Type: application/json" \
  -d '{
    "tempToken": "PEGA-AQUI-EL-TEMP-TOKEN-DEL-PASO-3",
    "codigo": "654321",
    "tipo": "email"
  }'
```

**Resultado esperado**:
- Código 200
- Mensaje: "Inicio de sesión exitoso"
- Datos del usuario (id, email, username)

---

## 🎉 Si Todo Funciona

¡Felicidades! Tu backend está 100% funcional. Ahora puedes:

1. **Integrar el frontend**:
   - Lee `API_DOCUMENTATION.md` para los endpoints
   - Implementa los flujos de registro, login, y 2FA
   - Agrega soporte para TOTP (Google Authenticator)

2. **Probar funcionalidades adicionales**:
   - Configurar TOTP (Google Authenticator)
   - Generar códigos de respaldo
   - Recuperación de contraseña por email

3. **Monitorear**:
   - Revisa los logs en Render regularmente
   - Verifica que los emails se envíen correctamente
   - Monitorea el uso de la API de Resend

---

## 📞 Siguientes Pasos

### Inmediatos:
1. ✅ Verificar que el deploy terminó
2. ✅ Probar registro con tu email real
3. ✅ Confirmar que llegan los correos

### Frontend (próximo):
1. Actualizar componentes de login para soportar 2FA
2. Agregar página de configuración de TOTP
3. Implementar recuperación de contraseña
4. Agregar dashboard de seguridad

### Opcional (mejoras futuras):
1. Configurar dominio personalizado en Resend
2. Agregar SMS como método 2FA alternativo
3. Implementar rate limiting más granular
4. Agregar analytics de seguridad

---

## 📊 Información Importante

- **URL del Backend**: https://backendbina-1.onrender.com
- **URL del Frontend**: https://frontbina.vercel.app
- **Email del servicio**: onboarding@resend.dev (Resend gratuito)
- **Base de datos**: PostgreSQL en Render

---

## 🆘 Si Nada Funciona

1. **Verifica en Render Logs** si hay errores de Python
2. **Comprueba que todas las variables de entorno estén bien**
3. **Intenta un Manual Deploy** desde Render
4. **Ejecuta las migraciones manualmente** desde Shell en Render
5. **Revisa que la API key de Resend sea válida**

Si después de esto sigue sin funcionar, copia los logs de Render y podemos diagnosticar el problema específico.
