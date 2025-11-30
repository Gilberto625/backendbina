# ✅ Variables de Entorno para Render - Verificación

## Variables Actuales (Todas Correctas) ✅

Tienes todas las variables necesarias configuradas. Solo hay una **opcional** que puedes agregar:

### Variable Opcional (Recomendada)

```
Key: FRONTEND_URL
Value: https://frontbina.vercel.app
```

**Nota**: Esta variable tiene un default en el código, pero es mejor especificarla explícitamente.

---

## ⚠️ IMPORTANTE: Migración Requerida

### Antes de Redesplegar

Debes crear la migración para los nuevos campos de seguridad:

```bash
cd backendbina
python manage.py makemigrations accounts
```

Esto creará un archivo como:
```
accounts/migrations/0005_usuario_intentos_fallidos_and_more.py
```

### Campos que se Agregarán

- `intentos_fallidos` (IntegerField, default=0)
- `bloqueado_hasta` (DateTimeField, null=True, blank=True)
- `ultimo_intento` (DateTimeField, null=True, blank=True)

### Proceso Completo

1. **Crear migración localmente**:
   ```bash
   cd backendbina
   python manage.py makemigrations accounts
   ```

2. **Verificar que se creó**:
   ```bash
   ls accounts/migrations/0005_*.py
   ```

3. **Commit y push**:
   ```bash
   git add accounts/migrations/
   git commit -m "Add migration for brute force protection fields"
   git push
   ```

4. **Render aplicará la migración automáticamente** durante el despliegue (build.sh ya incluye `python manage.py migrate`)

---

## 📋 Resumen de Variables

### ✅ Todas las Variables Necesarias Están Configuradas

| Variable | Estado | Valor |
|----------|--------|-------|
| `ALLOWED_HOSTS` | ✅ | `.onrender.com,frontbina.vercel.app` |
| `CORS_ALLOWED_ORIGINS` | ✅ | URLs del frontend |
| `CSRF_TRUSTED_ORIGINS` | ✅ | URLs confiables |
| `DATABASE_URL` | ✅ | PostgreSQL de Render |
| `DEBUG` | ✅ | `False` ✅ |
| `FIREBASE_CREDENTIALS` | ✅ | JSON completo |
| `RESEND_API_KEY` | ✅ | API key |
| `SECRET_KEY` | ✅ | Clave secreta |
| `SENDGRID_API_KEY` | ✅ | API key |
| `SENDGRID_FROM_EMAIL` | ✅ | Email verificado |
| `SENDGRID_FROM_NAME` | ✅ | Nombre remitente |

### Opcional (Recomendada)

| Variable | Valor Recomendado |
|----------|-------------------|
| `FRONTEND_URL` | `https://frontbina.vercel.app` |

---

## ✅ Checklist Final

- [x] Todas las variables de entorno están configuradas
- [ ] **Crear migración** para nuevos campos (REQUERIDO)
- [ ] Commit y push de la migración
- [ ] (Opcional) Agregar `FRONTEND_URL`

---

## 🚀 Pasos para Redesplegar

1. **Crear migración** (si no lo has hecho):
   ```bash
   python manage.py makemigrations accounts
   ```

2. **Commit todo**:
   ```bash
   git add .
   git commit -m "Add security improvements: brute force protection, XSS, CSRF, etc."
   git push
   ```

3. **Render desplegará automáticamente** y aplicará la migración

4. **Verificar** después del despliegue:
   - Probar registro
   - Probar login con 3 intentos fallidos (debe bloquear)
   - Verificar headers de seguridad

---

## ✅ Conclusión

**Variables de entorno**: ✅ **Completas** (solo falta FRONTEND_URL opcional)

**Acción requerida**: ⚠️ **Crear migración** antes de redesplegar

**Listo para redesplegar**: ✅ (después de crear la migración)


