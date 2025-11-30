# 🚀 Pasos Finales para Redespliegue

## ✅ Configuración Actualizada

He actualizado `render.yaml` con la información de tu nueva base de datos:
- **Database name**: `backendbina_db_wuj1`
- **User**: `backendbina_db_user`

---

## ⚠️ IMPORTANTE: Verificar Nombre Real de la BD

El nombre en `render.yaml` (`backendbina_db_wuj1`) debe coincidir **exactamente** con el nombre que aparece en la lista de **Databases** en Render Dashboard.

**Si el nombre es diferente**, actualiza `render.yaml`:

```yaml
fromDatabase:
  name: NOMBRE_REAL_EN_RENDER  # ← Debe coincidir exactamente
```

---

## 📋 Pasos para Redesplegar

### 1. Verificar Nombre de Base de Datos en Render

1. Render Dashboard → **Databases**
2. Busca tu nueva base de datos
3. Anota el **nombre exacto** (el que aparece en la lista)
4. Si es diferente a `backendbina_db_wuj1`, actualiza `render.yaml`

### 2. Conectar Base de Datos al Servicio Web

1. Render Dashboard → Tu servicio web (`django-backend`)
2. **Settings** → **Connections**
3. Click **Connect Database**
4. Selecciona tu nueva base de datos
5. Render configurará automáticamente la conexión

### 3. Eliminar DATABASE_URL Manual

1. Tu servicio web → **Environment** → **Variables**
2. Si existe `DATABASE_URL` manual, **ELIMÍNALA**
3. Render usará automáticamente la conexión desde la BD conectada

### 4. Commit y Push

```bash
cd backendbina
git add render.yaml
git add accounts/migrations/0005_usuario_intentos_fallidos_and_more.py
git commit -m "Configure new database and add security migrations"
git push
```

### 5. Verificar Despliegue

Render desplegará automáticamente y:
- ✅ Conectará a la nueva base de datos
- ✅ Aplicará todas las migraciones (incluyendo la nueva `0005`)
- ✅ Iniciará el servidor

---

## 🔍 Si el Nombre de la BD es Diferente

Si en Render la base de datos se llama diferente (por ejemplo, solo `backendbina_db`), actualiza `render.yaml`:

```yaml
fromDatabase:
  name: backendbina_db  # ← Usar el nombre real
databases:
  - name: backendbina_db  # ← Usar el nombre real
    databaseName: backendbina_db_wuj1  # ← Este es el nombre de la BD dentro de PostgreSQL
    user: backendbina_db_user
```

**Diferencia**:
- `name`: Nombre del servicio de BD en Render
- `databaseName`: Nombre de la base de datos dentro de PostgreSQL

---

## ✅ Checklist Final

- [ ] Base de datos creada en Render
- [ ] Nombre real de la BD identificado
- [ ] `render.yaml` actualizado con nombre correcto
- [ ] Base de datos conectada al servicio web
- [ ] `DATABASE_URL` manual eliminada
- [ ] Migración `0005` commitada
- [ ] Commit y push realizado
- [ ] Despliegue exitoso verificado

---

## 🎯 Resumen

1. **Verificar** nombre real de la BD en Render
2. **Actualizar** `render.yaml` si es necesario
3. **Conectar** BD al servicio web
4. **Eliminar** `DATABASE_URL` manual
5. **Commit y push**
6. **Listo** ✅

El `render.yaml` ya está actualizado con `backendbina_db_wuj1`. Solo verifica que ese sea el nombre real en Render, o actualízalo si es diferente.

