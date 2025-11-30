# 🗄️ Configurar Nueva Base de Datos en Render

## Pasos para Crear y Configurar la Nueva Base de Datos

### Paso 1: Crear Nueva Base de Datos en Render

1. **En Render Dashboard**:
   - Ve a **Databases** → **New**
   - Selecciona **PostgreSQL**
   - Configura:
     - **Name**: `backendbina_db` (o el nombre que prefieras)
     - **Database**: `backendbina_db`
     - **User**: `backendbina_db_user` (o el que prefieras)
     - **Region**: Misma región que tu servicio web (recomendado)
     - **Plan**: Free o según tu necesidad

2. **Esperar** a que se cree (puede tardar unos minutos)

---

### Paso 2: Configurar render.yaml

El `render.yaml` ya está actualizado para usar conexión automática. Solo necesitas verificar que el nombre coincida:

```yaml
services:
  - type: web
    name: django-backend
    env: python
    buildCommand: "./build.sh"
    startCommand: "gunicorn core.wsgi:application --timeout 120 --workers 2 --bind 0.0.0.0:$PORT"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DEBUG
        value: False
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: backendbina_db  # ← Debe coincidir con el nombre de tu nueva BD
          property: connectionString
databases:
  - name: backendbina_db  # ← Debe coincidir con el nombre de tu nueva BD
    databaseName: backendbina_db
    user: backendbina_db_user
```

**IMPORTANTE**: El nombre en `fromDatabase.name` y `databases.name` debe ser **exactamente igual** al nombre que le diste a la base de datos en Render.

---

### Paso 3: Conectar Base de Datos al Servicio Web

1. **En Render Dashboard**:
   - Ve a tu servicio web (django-backend)
   - Ve a **Settings** → **Connections**
   - Click **Connect Database**
   - Selecciona tu nueva base de datos
   - Render configurará automáticamente `DATABASE_URL`

2. **O usar render.yaml** (ya configurado):
   - Si el nombre coincide, Render lo conectará automáticamente

---

### Paso 4: Eliminar DATABASE_URL Manual (Si Existe)

1. **En Render Dashboard**:
   - Ve a tu servicio web → **Environment** → **Variables**
   - Si existe `DATABASE_URL` manual, **ELIMÍNALA**
   - Render usará automáticamente la de la base de datos conectada

---

### Paso 5: Commit y Push

```bash
cd backendbina
git add render.yaml
git commit -m "Update database configuration for new database"
git push
```

---

### Paso 6: Verificar Despliegue

Después del despliegue, verifica en los logs:

```
✓ Database connection successful
✓ Running migrations...
✓ Migrations applied successfully
✓ Server started
```

---

## ⚠️ Si el Nombre de la BD es Diferente

Si creaste la base de datos con un nombre diferente (por ejemplo, `django-db`), actualiza `render.yaml`:

```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: TU_NOMBRE_REAL_AQUI  # ← Cambiar aquí
      property: connectionString
databases:
  - name: TU_NOMBRE_REAL_AQUI  # ← Cambiar aquí
    databaseName: backendbina_db
    user: backendbina_db_user
```

---

## 📋 Checklist

- [ ] Base de datos creada en Render
- [ ] Nombre de la BD anotado
- [ ] `render.yaml` actualizado con el nombre correcto
- [ ] Base de datos conectada al servicio web
- [ ] `DATABASE_URL` manual eliminada (si existía)
- [ ] Commit y push realizado
- [ ] Despliegue exitoso verificado

---

## ✅ Resumen

1. **Crear** nueva base de datos en Render
2. **Actualizar** `render.yaml` con el nombre correcto
3. **Conectar** BD al servicio web
4. **Eliminar** `DATABASE_URL` manual
5. **Commit y push**
6. **Verificar** despliegue

¡Listo! 🚀

