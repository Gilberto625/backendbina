# 🔧 Corrección de DATABASE_URL

## Problema Identificado

Tu `DATABASE_URL` actual está **incompleto**:

```
postgresql://backendbina_db_user:tMCF9pM0PlY6Vj4XIVFhblxjTa4CpXzI@dpg-d42ghmbe5dus73cnegf0-a/backendbina_db
```

**Falta el dominio completo** después de `-a`.

---

## ✅ Solución

### Opción 1: Obtener URL Correcta desde Render (Recomendado)

1. **En Render Dashboard**:
   - Ve a tu base de datos PostgreSQL
   - Click en **Settings** → **Connections**
   - Busca **Internal Database URL**
   - Copia la URL completa

2. **La URL correcta debería verse así**:
   ```
   postgresql://backendbina_db_user:tMCF9pM0PlY6Vj4XIVFhblxjTa4CpXzI@dpg-d42ghmbe5dus73cnegf0-a.oregon-postgres.render.com/backendbina_db
   ```
   
   O puede ser otra región como:
   - `.oregon-postgres.render.com`
   - `.singapore-postgres.render.com`
   - `.frankfurt-postgres.render.com`
   - etc.

3. **Actualizar en Render**:
   - Ve a tu servicio web → **Environment** → **Variables**
   - Edita `DATABASE_URL`
   - Pega la URL completa con el dominio
   - Guarda

4. **Redesplegar**

---

### Opción 2: Usar Conexión Automática (Mejor Opción)

**Elimina `DATABASE_URL` manual** y deja que Render lo maneje automáticamente:

1. **En Render Dashboard**:
   - Ve a tu servicio web → **Environment** → **Variables**
   - **ELIMINA** la variable `DATABASE_URL`
   - Render usará automáticamente la URL desde `render.yaml`

2. **Verificar render.yaml**:
   ```yaml
   envVars:
     - key: DATABASE_URL
       fromDatabase:
         name: django-db
         property: connectionString
   ```

3. **Verificar nombre de base de datos**:
   - En `render.yaml` dice `django-db`
   - Pero tu base de datos se llama `backendbina_db`
   - **Actualiza render.yaml** para que coincida:

   ```yaml
   envVars:
     - key: DATABASE_URL
       fromDatabase:
         name: backendbina_db  # ← Cambiar a tu nombre real
         property: connectionString
   ```

4. **Redesplegar**

---

## 🔍 Cómo Encontrar el Nombre Correcto de la Base de Datos

1. En Render Dashboard → **Databases**
2. Busca tu base de datos PostgreSQL
3. El **nombre** aparece en la lista (puede ser `backendbina_db` o `django-db`)
4. Usa ese nombre en `render.yaml`

---

## 📋 Pasos Recomendados

### Paso 1: Verificar Base de Datos

1. Render Dashboard → **Databases**
2. Anota el **nombre exacto** de tu base de datos
3. Anota la **región** (Oregon, Singapore, etc.)

### Paso 2: Actualizar render.yaml

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
          name: backendbina_db  # ← Usar el nombre real de tu BD
          property: connectionString
databases:
  - name: backendbina_db  # ← Debe coincidir con el nombre real
    databaseName: backendbina_db
    user: backendbina_db_user
```

### Paso 3: Eliminar DATABASE_URL Manual

1. Servicio web → **Environment** → **Variables**
2. **ELIMINA** `DATABASE_URL` manual
3. Render usará automáticamente la de `render.yaml`

### Paso 4: Commit y Push

```bash
git add render.yaml
git commit -m "Fix database connection configuration"
git push
```

### Paso 5: Redesplegar

Render detectará el cambio y redesplegará automáticamente.

---

## ✅ Verificación

Después del despliegue, verifica en los logs:

```
✓ Database connection successful
✓ Migrations applied
✓ Server started
```

Si ves errores de conexión, verifica:
1. El nombre de la base de datos en `render.yaml` coincide con el real
2. La base de datos existe en Render
3. El servicio web tiene permisos para conectarse

---

## 🚀 Resumen

**Problema**: `DATABASE_URL` tiene hostname incompleto

**Solución**:
1. Actualizar `render.yaml` con el nombre correcto de la BD
2. Eliminar `DATABASE_URL` manual
3. Dejar que Render maneje la conexión automáticamente

**Resultado**: Conexión automática y confiable

