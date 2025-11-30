# 🔧 Instrucciones para Solucionar Error de Base de Datos

## Error Actual
```
could not translate host name "dpg-d42ghmbe5dus73cnegf0-a" to address
```

## ✅ Solución Rápida

### Opción A: Usar Conexión Automática (Recomendado)

1. **En Render Dashboard**:
   - Ve a tu servicio web → **Environment**
   - **ELIMINA** la variable `DATABASE_URL` manual
   - Render usará automáticamente la URL de la base de datos configurada en `render.yaml`

2. **Verificar Base de Datos**:
   - Ve a **Databases** en Render
   - Asegúrate de que existe una base de datos llamada `django-db`
   - Si no existe, créala con ese nombre

3. **Redesplegar**:
   - Render obtendrá automáticamente la URL correcta

### Opción B: Actualizar DATABASE_URL Manual

1. **Obtener URL Correcta**:
   - En Render → Tu base de datos → **Settings** → **Connections**
   - Copia la **Internal Database URL**
   - Debe tener formato: `postgresql://user:pass@host.oregon-postgres.render.com/db`

2. **Actualizar Variable**:
   - En tu servicio web → **Environment** → **Variables**
   - Edita `DATABASE_URL`
   - Pega la nueva URL completa
   - **IMPORTANTE**: Debe incluir el dominio completo (`.oregon-postgres.render.com`)

3. **Redesplegar**

---

## 🔍 Verificación

### Formato Correcto de DATABASE_URL

✅ **CORRECTO**:
```
postgresql://user:password@dpg-xxxxx-a.oregon-postgres.render.com/database_name
```

❌ **INCORRECTO** (falta dominio):
```
postgresql://user:password@dpg-xxxxx-a/database_name
```

---

## 📋 Pasos Específicos en Render

### 1. Verificar Base de Datos

1. Login a Render Dashboard
2. Click en **Databases**
3. Busca base de datos llamada `django-db` o similar
4. Si no existe, créala:
   - Click **New** → **PostgreSQL**
   - Name: `django-db`
   - Plan: Free o según tu plan
   - Region: Misma región que tu servicio web

### 2. Obtener URL Correcta

En la base de datos:
- **Settings** → **Connections**
- Copia **Internal Database URL** (para servicios en Render)
- O **External Database URL** (si necesitas conexión externa)

### 3. Configurar Variable

En tu servicio web:
- **Environment** → **Variables**
- Si existe `DATABASE_URL`, edítala
- Si no existe, créala
- Pega la URL completa

### 4. Redesplegar

- Render detectará el cambio y redesplegará automáticamente
- O manualmente: **Manual Deploy** → **Deploy latest commit**

---

## ⚠️ Nota Importante

Si usas `render.yaml` con `fromDatabase`, **NO necesitas** configurar `DATABASE_URL` manualmente. Render lo hace automáticamente.

**Recomendación**: Elimina `DATABASE_URL` manual y deja que Render lo maneje automáticamente.

