# 🚀 Instrucciones de Despliegue en Render

## ⚠️ IMPORTANTE: Configurar Variables de Entorno

Para que el sistema de correos funcione correctamente en producción, **DEBES** configurar las siguientes variables de entorno en el Dashboard de Render:

### 1. Ir a Render Dashboard
1. Accede a [https://dashboard.render.com/](https://dashboard.render.com/)
2. Selecciona tu servicio: **django-backend**
3. Ve a la pestaña **Environment**

### 2. Agregar Variables de Entorno

#### 📧 RESEND_API_KEY (CRÍTICO - Sin esto no funcionan los correos)

1. Ve a [https://resend.com/api-keys](https://resend.com/api-keys)
2. Crea una nueva API key
3. Cópiala y agrégala en Render:
   ```
   Key: RESEND_API_KEY
   Value: re_xxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

**⚠️ Sin esta variable, NO se enviarán correos de verificación**

#### 🔐 FIREBASE_CREDENTIALS (Opcional - Solo si usas Google Login)

Si estás usando Google Login con Firebase:

1. Ve a Firebase Console → Project Settings → Service Accounts
2. Genera una nueva clave privada (archivo JSON)
3. Copia TODO el contenido del JSON
4. Agrégalo en Render:
   ```
   Key: FIREBASE_CREDENTIALS
   Value: <pegar-todo-el-json-aquí>
   ```

#### ✅ Variables ya configuradas en render.yaml

Las siguientes variables ya están configuradas automáticamente:
- `CORS_ALLOWED_ORIGINS`: Frontend de Vercel permitido
- `CSRF_TRUSTED_ORIGINS`: Dominios de confianza
- `DATABASE_URL`: Base de datos PostgreSQL
- `SECRET_KEY`: Generada automáticamente

---

## 🔄 Pasos para Desplegar

### 1. Hacer Push de los Cambios
```bash
git add .
git commit -m "Add enhanced authentication system with TOTP and backup codes"
git push origin claude/backend-deployment-setup-01EkTh9qSrwNaaw3GUwGhVKn
```

### 2. Render Detectará el Push
Render detectará automáticamente el push y comenzará a construir y desplegar.

### 3. Ejecutar Migraciones

**⚠️ MUY IMPORTANTE**: Después del primer deploy, debes ejecutar las migraciones en Render:

1. Ve a tu servicio en Render
2. Haz clic en **Shell** (terminal web)
3. Ejecuta:
   ```bash
   python manage.py migrate
   ```

### 4. Verificar Variables de Entorno

En el Shell de Render, verifica que las variables estén configuradas:
```bash
echo $RESEND_API_KEY
echo $CORS_ALLOWED_ORIGINS
```

---

## 📧 Configurar Resend (Email Service)

### Opción 1: Usar Email Gratuito de Resend (Desarrollo)

Resend proporciona un email gratuito: `onboarding@resend.dev`
- ✅ No requiere verificación de dominio
- ⚠️ Solo para desarrollo/testing
- 📨 Emails se envían desde `onboarding@resend.dev`

**Ya está configurado** en `settings.py`:
```python
DEFAULT_FROM_EMAIL = 'onboarding@resend.dev'
```

### Opción 2: Usar tu Propio Dominio (Producción)

Para usar un dominio personalizado (ej: `noreply@tudominio.com`):

1. **Agregar dominio en Resend**:
   - Ve a [Resend Dashboard → Domains](https://resend.com/domains)
   - Haz clic en "Add Domain"
   - Ingresa tu dominio (ej: `tudominio.com`)

2. **Configurar DNS**:
   Resend te dará 3 registros DNS para agregar:
   - 1 registro TXT (verificación)
   - 2 registros MX (autenticación)

   Agrégalos en tu proveedor de DNS (GoDaddy, Namecheap, etc.)

3. **Esperar Verificación** (24-48 horas)

4. **Actualizar settings.py**:
   ```python
   DEFAULT_FROM_EMAIL = 'noreply@tudominio.com'
   ```

---

## 🧪 Probar el Sistema

### 1. Probar Registro
```bash
curl -X POST https://backendbina-1.onrender.com/api/usuarios/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Test",
    "apellidopaterno": "User",
    "apellidomaterno": "Demo",
    "username": "testuser",
    "correo": "tu-email@example.com",
    "contrasena": "Test123!",
    "telefono": "5551234567",
    "preguntasecreta": "¿Tu color favorito?",
    "respuestasecreta": "Azul"
  }'
```

**Verifica tu correo**: Deberías recibir un código de 6 dígitos.

### 2. Verificar que no hay errores en Logs

En Render, ve a la pestaña **Logs** y verifica:
- ✅ `INFO Correo de verificación enviado a ...`
- ❌ NO debe haber `ERROR al enviar correo`

---

## 🐛 Troubleshooting

### Problema: "No se pudo enviar el correo"

**Solución**:
1. Verifica que `RESEND_API_KEY` esté configurada
2. Verifica que la API key sea válida en [Resend Dashboard](https://resend.com/api-keys)
3. Revisa los logs en Render para ver el error específico

### Problema: "Token de Google inválido"

**Solución**:
1. Verifica que `FIREBASE_CREDENTIALS` esté configurada
2. Verifica que el JSON sea válido
3. Asegúrate de que el proyecto de Firebase esté activo

### Problema: Usuario no recibe código

**Posibles causas**:
1. Email en spam/correo no deseado
2. API key de Resend incorrecta
3. Dominio no verificado (si no usas `onboarding@resend.dev`)

**Solución**:
- Revisar carpeta de spam
- Verificar logs en Render
- Usar `onboarding@resend.dev` temporalmente

---

## 📊 Monitoreo

### Logs Importantes

En Render → Logs, busca:

**Correos exitosos**:
```
INFO Correo de verificación enviado a user@example.com
INFO Usuario user@example.com verificado exitosamente
```

**Errores de autenticación**:
```
WARNING Demasiados intentos fallidos para user@example.com
WARNING Código TOTP incorrecto para user@example.com
```

**Recuperación de contraseña**:
```
INFO Correo de recuperación enviado a user@example.com
INFO Contraseña restablecida para user@example.com
```

---

## 🔐 Seguridad en Producción

### 1. Verificar DEBUG está en False
En Render, verifica:
```bash
echo $DEBUG
```
Debe retornar: `False`

### 2. Verificar HTTPS
Todos los requests deben ir por HTTPS:
- ✅ `https://backendbina-1.onrender.com`
- ❌ `http://backendbina-1.onrender.com`

### 3. Verificar CORS
Solo el frontend de Vercel debe estar permitido:
```bash
echo $CORS_ALLOWED_ORIGINS
```
Debe incluir: `https://frontbina.vercel.app`

---

## 📝 Checklist de Despliegue

- [ ] Variables de entorno configuradas en Render
  - [ ] `RESEND_API_KEY`
  - [ ] `FIREBASE_CREDENTIALS` (si usas Google Login)
- [ ] Push realizado a la rama correcta
- [ ] Build exitoso en Render
- [ ] Migraciones ejecutadas (`python manage.py migrate`)
- [ ] Logs sin errores
- [ ] Registro funciona y envía código
- [ ] Login funciona con 2FA
- [ ] Recuperación de contraseña funciona

---

## 🆘 Soporte Adicional

Si después de seguir estos pasos aún tienes problemas:

1. **Revisa los logs detallados** en Render
2. **Verifica las variables de entorno** están correctas
3. **Prueba endpoints manualmente** con cURL o Postman
4. **Contacta al equipo** con los logs del error

---

## 🎉 ¡Todo Listo!

Una vez completados estos pasos, tu backend estará completamente funcional con:
- ✅ Registro y verificación por email
- ✅ Login con 2FA (email, TOTP, backup codes)
- ✅ Recuperación de contraseña por email
- ✅ Google Login
- ✅ Rate limiting
- ✅ Logging de eventos de seguridad
