# Documentación API - Módulo de Citas

## 📋 Base URL
```
http://localhost:8000/api/citas/
```

## 🔓 Endpoints Públicos (No requieren autenticación)

### 1. Listar Servicios
**GET** `/api/citas/servicios/`

Lista todos los servicios disponibles.

**Respuesta exitosa (200)**:
```json
{
    "ok": true,
    "mensaje": "Servicios obtenidos",
    "servicios": [
        {
            "id": 1,
            "nombre": "Corte de Cabello",
            "descripcion": "Corte profesional...",
            "precio_base": 150.0,
            "duracion_minutos": 30,
            "categoria": "corte",
            "categoria_display": "Corte de Cabello"
        }
    ]
}
```

---

### 2. Listar Barberos
**GET** `/api/citas/barberos/`

Lista todos los barberos activos.

**Respuesta exitosa (200)**:
```json
{
    "ok": true,
    "mensaje": "Barberos obtenidos",
    "barberos": [
        {
            "id": 1,
            "usuario_id": 5,
            "nombre": "Juan Pérez",
            "email": "juan@example.com",
            "especialidades": "Cortes modernos"
        }
    ]
}
```

---

### 3. Consultar Disponibilidad
**GET** `/api/citas/disponibilidad/?fecha=2026-02-01&barbero_id=2&servicio_id=1&silla_id=1`

Consulta horarios disponibles para una fecha específica.

**Parámetros de consulta**:
- `fecha` (requerido): Fecha en formato YYYY-MM-DD
- `barbero_id` (opcional): ID del barbero
- `silla_id` (opcional): ID de la silla
- `servicio_id` (opcional): ID del servicio (para calcular duración)

**Respuesta exitosa (200)**:
```json
{
    "ok": true,
    "mensaje": "Horarios disponibles",
    "fecha": "2026-02-01",
    "horarios": ["09:00", "09:30", "10:00", "10:30", "11:00"],
    "total": 5
}
```

---

## 👤 Endpoints para Clientes (Requieren autenticación)

### 4. Crear Cita
**POST** `/api/citas/crear/`

Crea una nueva cita. Requiere rol `cliente`.

**Headers**:
```
Content-Type: application/json
X-CSRFToken: <token>
Cookie: csrftoken=<token>
```

**Body**:
```json
{
    "servicio_id": 1,
    "fecha_hora": "2026-02-01T10:00:00Z",
    "barbero_id": 2,
    "silla_id": 1
}
```

**Validaciones**:
- Verifica reglas de anticipación según demanda del día
- Verifica disponibilidad de barbero y silla
- Calcula anticipo requerido (0 si es primera cita, 50% si hay penalización)

**Respuesta exitosa (201)**:
```json
{
    "ok": true,
    "mensaje": "Cita creada exitosamente",
    "cita": {
        "id": 1,
        "fecha_hora": "2026-02-01T10:00:00Z",
        "servicio": "Corte de Cabello",
        "precio_total": 150.0,
        "anticipo_requerido": 0.0,
        "estado": "pendiente"
    }
}
```

**Errores posibles**:
- `400`: Reglas de anticipación no cumplidas
- `409`: Conflicto de disponibilidad
- `404`: Servicio/Barbero/Silla no encontrado

---

### 5. Mis Citas
**GET** `/api/citas/mis-citas/?estado=pendiente`

Lista las citas del cliente autenticado.

**Parámetros de consulta**:
- `estado` (opcional): Filtrar por estado (pendiente, confirmada, completada, cancelada, no_asistio)

**Respuesta exitosa (200)**:
```json
{
    "ok": true,
    "mensaje": "Citas obtenidas",
    "citas": [
        {
            "id": 1,
            "fecha_hora": "2026-02-01T10:00:00Z",
            "servicio": {
                "id": 1,
                "nombre": "Corte de Cabello",
                "precio": 150.0
            },
            "barbero": {
                "id": 2,
                "nombre": "Juan Pérez"
            },
            "silla": {
                "id": 1,
                "nombre": "Silla 1"
            },
            "estado": "pendiente",
            "precio_total": 150.0,
            "anticipo_pagado": 0.0,
            "anticipo_requerido": 0.0
        }
    ]
}
```

---

### 6. Detalle de Cita
**GET** `/api/citas/{id}/`

Obtiene el detalle completo de una cita específica.

**Respuesta exitosa (200)**:
```json
{
    "ok": true,
    "mensaje": "Cita obtenida",
    "cita": {
        "id": 1,
        "fecha_hora": "2026-02-01T10:00:00Z",
        "servicio": {
            "id": 1,
            "nombre": "Corte de Cabello",
            "descripcion": "...",
            "precio": 150.0,
            "duracion_minutos": 30
        },
        "barbero": {
            "id": 2,
            "nombre": "Juan Pérez",
            "email": "juan@example.com"
        },
        "silla": {
            "id": 1,
            "nombre": "Silla 1"
        },
        "estado": "pendiente",
        "precio_total": 150.0,
        "anticipo_pagado": 0.0,
        "anticipo_requerido": 0.0,
        "duracion_minutos": 30,
        "notas": "",
        "puede_cancelar": true
    }
}
```

**Error 404**: Si la cita no existe o no pertenece al cliente

---

### 7. Cancelar Cita
**PUT** `/api/citas/{id}/cancelar/`

Cancela una cita. Valida reglas de cancelación.

**Body**:
```json
{
    "motivo": "Cambio de planes"
}
```

**Validaciones**:
- Verifica reglas de cancelación según demanda del día
- No permite cancelar citas pasadas o completadas

**Respuesta exitosa (200)**:
```json
{
    "ok": true,
    "mensaje": "Cita cancelada exitosamente"
}
```

**Errores posibles**:
- `400`: No se puede cancelar (reglas de negocio)
- `404`: Cita no encontrada

---

## 👩‍💼 Endpoints para Secretaria/Admin

### 8. Agenda Completa
**GET** `/api/citas/agenda/?fecha_inicio=2026-02-01&fecha_fin=2026-02-07&estado=pendiente&barbero_id=2`

Obtiene la agenda completa con filtros. Requiere rol `secretaria` o `administrador`.

**Parámetros de consulta**:
- `fecha_inicio` (opcional): Fecha inicio en formato ISO
- `fecha_fin` (opcional): Fecha fin en formato ISO
- `estado` (opcional): Filtrar por estado
- `barbero_id` (opcional): Filtrar por barbero

**Respuesta exitosa (200)**:
```json
{
    "ok": true,
    "mensaje": "Agenda obtenida",
    "citas": [
        {
            "id": 1,
            "fecha_hora": "2026-02-01T10:00:00Z",
            "cliente": {
                "id": 3,
                "nombre": "Cliente Ejemplo",
                "email": "cliente@example.com",
                "telefono": "1234567890"
            },
            "barbero": {
                "id": 2,
                "nombre": "Juan Pérez"
            },
            "servicio": {
                "id": 1,
                "nombre": "Corte de Cabello"
            },
            "silla": {
                "id": 1,
                "nombre": "Silla 1"
            },
            "estado": "pendiente",
            "precio_total": 150.0,
            "anticipo_pagado": 0.0
        }
    ]
}
```

---

### 9. Crear Cita Manualmente
**POST** `/api/citas/crear-manual/`

Crea una cita manualmente (para citas por teléfono/visita). Requiere rol `secretaria` o `administrador`.

**Body**:
```json
{
    "cliente_id": 3,
    "servicio_id": 1,
    "fecha_hora": "2026-02-01T10:00:00Z",
    "barbero_id": 2,
    "silla_id": 1,
    "anticipo_pagado": 75.0,
    "metodo_pago_anticipo": "efectivo",
    "notas": "Cliente llamó por teléfono"
}
```

**Respuesta exitosa (201)**:
```json
{
    "ok": true,
    "mensaje": "Cita creada manualmente",
    "cita": {
        "id": 1,
        "fecha_hora": "2026-02-01T10:00:00Z",
        "cliente": "cliente@example.com",
        "estado": "confirmada"
    }
}
```

---

### 10. Registrar Asistencia
**POST** `/api/citas/{id}/asistencia/`

Registra la asistencia o inasistencia de un cliente. Requiere rol `secretaria`.

**Body**:
```json
{
    "asistio": true
}
```

**Comportamiento**:
- Si `asistio: true`: Marca cita como completada, reinicia contador de inasistencias
- Si `asistio: false`: Marca como no asistió, actualiza penalizaciones

**Respuesta exitosa (200)**:
```json
{
    "ok": true,
    "mensaje": "Asistencia registrada exitosamente",
    "cita": {
        "id": 1,
        "estado": "completada"
    }
}
```

---

## 🔧 Comandos de Management

### Cancelar Citas por Tardanza
```bash
python manage.py cancelar_citas_tardanza
```

Cancela automáticamente las citas que han pasado el tiempo de espera máximo sin asistencia.

**Recomendación**: Ejecutar cada 5-10 minutos usando Celery o cron job.

---

## ⚠️ Códigos de Error

| Código | Significado |
|--------|-------------|
| 200 | Éxito |
| 201 | Creado exitosamente |
| 400 | Error de validación / Reglas de negocio |
| 401 | No autenticado |
| 403 | Acceso denegado (rol incorrecto) |
| 404 | Recurso no encontrado |
| 405 | Método no permitido |
| 409 | Conflicto (disponibilidad) |
| 500 | Error del servidor |

---

## 📝 Notas Importantes

1. **Formato de fechas**: Usar ISO 8601 (ej: `2026-02-01T10:00:00Z`)
2. **Autenticación**: Todos los endpoints de clientes requieren estar autenticado
3. **CSRF Token**: Requerido para métodos POST/PUT
4. **Reglas de negocio**: Se validan automáticamente en cada operación
5. **Penalizaciones**: Se actualizan automáticamente al marcar inasistencia

---

*Documentación actualizada - 28 de enero de 2026*
