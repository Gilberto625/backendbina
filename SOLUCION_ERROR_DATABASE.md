# 🔧 Solución: Error de Conexión a Base de Datos

## Error
```
django.db.utils.OperationalError: could not translate host name "dpg-d42ghmbe5dus73cnegf0-a" to address: Name or service not known
```

## Causa
El `DATABASE_URL` en las variables de entorno está apuntando a una base de datos que ya no existe o fue recreada.

---

## ✅ Solución 1: Usar Conexión Automática de Render (Recomendado)

### Paso 1: Eliminar DATABASE_URL Manual

En Render Dashboard:
1. Ve a tu servicio web
2. Environment → Variables
3. **ELIMINA** la variable `DATABASE_URL` manual

### Paso 2: Verificar render.yaml

El `render.yaml` ya está configurado para obtener `DATABASE_URL` automáticamente:

```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: django-db
      property: connectionString
```

### Paso 3: Verificar que la Base de Datos Existe

En Render Dashboard:
1. Ve a **Databases**
2. Verifica que existe una base de datos llamada `django-db`
3. Si no existe, créala:
   - Name: `django-db`
   - Database: `django_production`
   - User: `django_user`

### Paso 4: Redesplegar

Render obtendrá automáticamente el `DATABASE_URL` correcto de la base de datos.

---

## ✅ Solución 2: Actualizar DATABASE_URL Manualmente

Si prefieres mantener el `DATABASE_URL` manual:

### Paso 1: Obtener Nueva URL de Base de Datos

En Render Dashboard:
1. Ve a tu base de datos PostgreSQL
2. **Settings** → **Connections**
3. Copia la **Internal Database URL** (para servicios en Render)
   - Formato: `postgresql://user:password@host:port/database`

### Paso 2: Actualizar Variable de Entorno

En tu servicio web → Environment → Variables:
1. Edita `DATABASE_URL`
2. Pega la nueva URL completa
3. Guarda

### Paso 3: Redesplegar

---

## 🔍 Verificación

### Verificar que la Base de Datos Existe

En Render Dashboard:
- **Databases** → Debe aparecer `django-db` o tu base de datos

### Verificar URL Correcta

La URL debe tener este formato:
```
postgresql://user:password@dpg-xxxxx-a.oregon-postgres.render.com/database_name
```

**Nota**: El hostname debe terminar en `.oregon-postgres.render.com` (o la región correspondiente), NO solo `-a`.

---

## ⚠️ Problema Común

Si tu `DATABASE_URL` actual es:
```
postgresql://...@dpg-d42ghmbe5dus73cnegf0-a/...
```

El problema es que falta el dominio completo. Debe ser:
```
postgresql://...@dpg-d42ghmbe5dus73cnegf0-a.oregon-postgres.render.com/...
```

---

## 📋 Checklist de Solución

- [ ] Verificar que la base de datos existe en Render
- [ ] Eliminar `DATABASE_URL` manual (Solución 1) O actualizarlo (Solución 2)
- [ ] Verificar que `render.yaml` está configurado correctamente
- [ ] Redesplegar el servicio
- [ ] Verificar que el despliegue fue exitoso

---

## 🚀 Recomendación

**Usa la Solución 1** (conexión automática):
- Render maneja la URL automáticamente
- Si la base de datos se recrea, la URL se actualiza sola
- Menos propenso a errores


