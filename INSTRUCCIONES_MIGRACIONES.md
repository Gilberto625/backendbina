# Instrucciones para Crear Migraciones y Datos Iniciales

## 📋 Pasos a Seguir

### 1. Activar Entorno Virtual

**Windows:**
```bash
cd backendbina
venv\Scripts\activate
```

**Linux/Mac:**
```bash
cd backendbina
source venv/bin/activate
```

Si no tienes entorno virtual, créalo primero:
```bash
python -m venv venv
```

### 2. Instalar Dependencias (si no están instaladas)

```bash
pip install -r requirements.txt
```

### 3. Crear Migraciones

Este comando creará los archivos de migración para todos los modelos nuevos:

```bash
python manage.py makemigrations
```

Esto creará migraciones para:
- `accounts` (extensión del modelo Usuario)
- `citas` (Silla, Servicio, Cita)
- `productos` (Producto, Compra)
- `pagos` (Pago)
- `barberos` (Barbero, ServicioBarbero)
- `core` (ConfiguracionSistema)

### 4. Aplicar Migraciones

Este comando aplicará las migraciones a la base de datos:

```bash
python manage.py migrate
```

### 5. Crear Datos Iniciales

Ejecuta el comando personalizado que crea los datos iniciales:

```bash
python manage.py crear_datos_iniciales
```

Este comando creará:
- **3 Sillas** (Silla 1, Silla 2, Silla 3)
- **5 Servicios**:
  - Corte de Cabello ($150, 30 min)
  - Arreglo de Barba ($120, 20 min)
  - Combo Corte + Barba ($250, 50 min)
  - Tratamiento Capilar ($300, 45 min)
  - Tinte para Cabello ($350, 60 min)
- **7 Configuraciones** (una por cada día de la semana):
  - Lunes, Martes, Miércoles: Baja demanda
  - Jueves: Media demanda
  - Viernes, Sábado, Domingo: Alta demanda

## ✅ Verificación

Después de ejecutar los comandos, puedes verificar que todo se creó correctamente:

```bash
# Abrir shell de Django
python manage.py shell

# En el shell:
from citas.models import Silla, Servicio
from core.models import ConfiguracionSistema

# Verificar sillas
print(f"Sillas: {Silla.objects.count()}")

# Verificar servicios
print(f"Servicios: {Servicio.objects.count()}")

# Verificar configuración
print(f"Configuraciones: {ConfiguracionSistema.objects.count()}")
```

## 🔧 Solución de Problemas

### Error: "No module named 'django'"
- Asegúrate de tener el entorno virtual activado
- Instala las dependencias: `pip install -r requirements.txt`

### Error: "ModuleNotFoundError: No module named 'citas'"
- Verifica que todas las apps estén en `INSTALLED_APPS` en `settings.py`
- Ya están agregadas, pero verifica si hay algún problema

### Error en migraciones
- Si hay conflictos, puedes resetear las migraciones (solo en desarrollo):
  ```bash
  # CUIDADO: Esto borra la base de datos
  rm db.sqlite3
  rm -rf */migrations/0*.py
  python manage.py makemigrations
  python manage.py migrate
  ```

## 📝 Notas

- El comando `crear_datos_iniciales` es idempotente: puedes ejecutarlo múltiples veces sin crear duplicados
- Si los datos ya existen, el comando solo mostrará que ya están creados
- Los datos iniciales son configurables y se pueden modificar después desde el admin de Django

---

*Una vez completados estos pasos, el sistema estará listo para continuar con la implementación de endpoints.*
