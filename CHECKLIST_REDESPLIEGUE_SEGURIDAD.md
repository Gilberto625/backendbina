# ✅ Checklist de Redespliegue - Mejoras de Seguridad

## 📋 Variables de Entorno en Render

### Variables Requeridas (Ya tienes todas) ✅

| Variable | Estado | Nota |
|----------|--------|------|
| `ALLOWED_HOSTS` | ✅ | `.onrender.com,frontbina.vercel.app` |
| `CORS_ALLOWED_ORIGINS` | ✅ | URLs del frontend |
| `CSRF_TRUSTED_ORIGINS` | ✅ | URLs confiables |
| `DATABASE_URL` | ✅ | PostgreSQL de Render |
| `DEBUG` | ✅ | `False` (correcto para producción) |
| `FIREBASE_CREDENTIALS` | ✅ | JSON completo |
| `RESEND_API_KEY` | ✅ | API key de Resend |
| `SECRET_KEY` | ✅ | Clave secreta |
| `SENDGRID_API_KEY` | ✅ | API key de SendGrid |
| `SENDGRID_FROM_EMAIL` | ✅ | Email verificado |
| `SENDGRID_FROM_NAME` | ✅ | Nombre del remitente |

### Variable Opcional (Recomendada)

| Variable | Valor Recomendado | Nota |
|----------|-------------------|------|
| `FRONTEND_URL` | `https://frontbina.vercel.app` | Tiene default, pero es mejor especificarla |

**Agregar si quieres**:
```
Key: FRONTEND_URL
Value: https://frontbina.vercel.app
```

---

## ⚠️ IMPORTANTE: Migración de Base de Datos

### Campos Nuevos Agregados

Se agregaron nuevos campos al modelo `Usuario` para protección contra fuerza bruta:
- `intentos_fallidos` (IntegerField)
- `bloqueado_hasta` (DateTimeField)
- `ultimo_intento` (DateTimeField)

### Verificación Pre-Despliegue

**El `build.sh` ya ejecuta migraciones automáticamente**:
```bash
python manage.py migrate
```

**Pero debes asegurarte de que la migración esté creada**:

1. **Localmente, crear la migración**:
```bash
cd backendbina
python manage.py makemigrations accounts
```

2. **Verificar que se creó el archivo**:
```
backendbina/accounts/migrations/0005_usuario_intentos_fallidos_and_more.py
```

3. **Commit y push a Git**:
```bash
git add accounts/migrations/
git commit -m "Add migration for brute force protection fields"
git push
```

4. **Render aplicará la migración automáticamente** durante el despliegue

---

## 📝 Checklist Pre-Despliegue

### 1. Código ✅
- [x] Todos los cambios están en Git
- [x] Migración creada para nuevos campos
- [x] build.sh actualizado (ya incluye migrate)

### 2. Variables de Entorno ✅
- [x] Todas las variables requeridas están configuradas
- [ ] (Opcional) Agregar FRONTEND_URL

### 3. Base de Datos
- [ ] Migración creada localmente
- [ ] Migración commitada a Git
- [ ] Render aplicará migración automáticamente

### 4. Verificación Post-Despliegue
- [ ] Verificar que el despliegue fue exitoso
- [ ] Probar endpoint de registro (debe funcionar)
- [ ] Probar login con 3 intentos fallidos (debe bloquear)
- [ ] Verificar que las nuevas funcionalidades funcionan

---

## 🔧 Comandos para Verificar

### Después del Despliegue

```bash
# 1. Verificar que el servidor responde
curl https://backendbina-1.onrender.com/api/usuarios/csrf/

# 2. Verificar headers de seguridad
curl -I https://backendbina-1.onrender.com/api/usuarios/csrf/

# 3. Probar registro (debe funcionar)
curl -X POST https://backendbina-1.onrender.com/api/usuarios/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Test",
    "apellidopaterno": "User",
    "apellidomaterno": "Test",
    "username": "testuser",
    "correo": "test@test.com",
    "contrasena": "Password123!",
    "telefono": "1234567890",
    "preguntasecreta": "Test",
    "respuestasecreta": "Test123"
  }'
```

---

## 📋 Resumen

### ✅ Variables de Entorno
**Tienes todas las variables necesarias**. Solo falta (opcional):
- `FRONTEND_URL` (tiene default, pero es mejor especificarla)

### ⚠️ Acción Requerida
**Crear y commitear la migración** antes de redesplegar:
```bash
cd backendbina
python manage.py makemigrations accounts
git add accounts/migrations/
git commit -m "Add migration for security fields"
git push
```

### ✅ Build Script
El `build.sh` ya está configurado correctamente y aplicará las migraciones automáticamente.

---

## 🚀 Proceso de Redespliegue

1. **Crear migración localmente** (si no lo has hecho):
   ```bash
   python manage.py makemigrations accounts
   ```

2. **Commit y push**:
   ```bash
   git add .
   git commit -m "Add security improvements and migrations"
   git push
   ```

3. **Render detectará el push** y desplegará automáticamente

4. **Verificar despliegue**:
   - Revisar logs en Render
   - Probar endpoints
   - Verificar que las nuevas funcionalidades funcionan

---

## ✅ Estado Final

**Variables de entorno**: ✅ Completas (solo falta FRONTEND_URL opcional)

**Migración**: ⚠️ **DEBES CREARLA** antes de redesplegar

**Build script**: ✅ Configurado correctamente

**Listo para redesplegar**: ✅ (después de crear la migración)


