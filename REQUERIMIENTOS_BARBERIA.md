# 📋 Documento de Requerimientos - Sistema Web y Móvil para Barbería

## 📌 Índice

1. [Introducción](#introducción)
2. [Descripción General](#descripción-general-del-sistema)
3. [Actores del Sistema](#actores-del-sistema)
4. [Requerimientos Funcionales](#requerimientos-funcionales)
5. [Requerimientos No Funcionales](#requerimientos-no-funcionales)
6. [Reglas de Negocio](#reglas-de-negocio)
7. [Casos de Uso](#casos-de-uso-principales)
8. [Análisis Técnico](#análisis-técnico)
9. [Modelo de Datos Propuesto](#modelo-de-datos-propuesto)
10. [Consideraciones de Implementación](#consideraciones-de-implementación)

---

## Introducción

El presente documento describe los requerimientos funcionales y no funcionales para el desarrollo de un **sistema web y aplicación móvil** destinados a una barbería local.

### Objetivo Principal
Mejorar la administración de citas, la venta, control de productos y la organización interna de barberos y secretario/a, con un sistema flexible que permita crecer en el futuro.

---

## Descripción General del Sistema

El sistema permitirá a los clientes:
- ✅ Agendar citas con pago anticipado
- ✅ Recibir notificaciones de sus reservas
- ✅ Comprar productos en línea
- ✅ Visualizar catálogos de servicios y productos

### Perfiles del Sistema

| Perfil | Descripción |
|--------|-------------|
| **Cliente** | Agenda citas, compra productos, recibe notificaciones |
| **Secretaria** | Control central de citas, validación de pagos, asignación de sillas |
| **Barbero** | Define y actualiza tiempos de duración de servicios |
| **Administrador** | Gestión de empleados, productos, stock y métricas |

---

## Actores del Sistema

### 👤 Cliente
- Agenda citas y compra productos
- Recibe notificaciones
- Puede acceder como **invitado** (solo visualizar)
- Debe **registrarse** para reservar en línea

### 👩‍💼 Secretaria
- Valida pagos
- Gestiona citas y productos
- Asigna barberos/sillas
- Registra ventas
- Confirma asistencias

### 💈 Barbero
- Solo define y actualiza tiempos de duración de sus servicios
- **NO gestiona citas ni cobros**

### 👔 Administrador (Dueño)
- Gestiona empleados y roles
- Administra productos y stock
- Configura reglas del sistema
- Visualiza métricas de negocio

---

## Requerimientos Funcionales

### 📱 Cliente

| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-C01 | Acceder como invitado sin registrarse | Alta |
| RF-C02 | Registrarse e iniciar sesión para agendar citas en línea | Alta |
| RF-C03 | Visualizar catálogo de servicios (cortes, barba, combos) | Alta |
| RF-C04 | Visualizar catálogo de productos disponibles | Alta |
| RF-C05 | Agendar citas seleccionando fecha, hora y servicio | Alta |
| RF-C06 | Recibir notificaciones de confirmación o cambios en su cita | Alta |
| RF-C07 | Recibir recordatorios de cita (1 día antes y 1.5 horas antes) | Alta |
| RF-C08 | Pagar anticipo mediante Banorte, tarjeta, transferencia o efectivo | Alta |
| RF-C09 | Cancelar citas según reglas de negocio | Media |
| RF-C10 | Comprar productos en línea o apartarlos (afectando stock) | Media |
| RF-C11 | Elegir método de entrega: recoger en local o motomandado regional ($40-50 MXN) | Media |
| RF-C12 | Seleccionar envío nacional por paquetería (futuro) | Baja |
| RF-C13 | Consultar historial de citas, compras y pagos | Media |

### 👩‍💼 Secretaria

| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-S01 | Validar pagos por transferencia mediante ID de operación | Alta |
| RF-S02 | Confirmar compras y apartados (teléfono, persona o web) | Alta |
| RF-S03 | Gestionar catálogo de productos (altas, bajas, cambios de precio) | Alta |
| RF-S04 | Registrar manualmente citas de clientes (llamada, mensaje, visita) | Alta |
| RF-S05 | Asignar citas a barberos y sillas disponibles | Alta |
| RF-S06 | Registrar ventas de productos indicando método de pago | Alta |
| RF-S07 | Confirmar pagos restantes de citas | Alta |
| RF-S08 | Consultar y modificar agenda general | Alta |
| RF-S09 | Recibir notificaciones de recordatorio de citas (1.5 horas antes) | Alta |

### 💈 Barbero / Colaborador

| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-B01 | Iniciar sesión en el sistema con perfil de barbero | Alta |
| RF-B02 | Definir tiempo estimado de duración de cada servicio | Alta |
| RF-B03 | Editar o actualizar los tiempos estimados cuando se requiera | Media |

### 👔 Administrador

| ID | Requerimiento | Prioridad |
|----|---------------|-----------|
| RF-A01 | Registrar y gestionar empleados (secretarias, barberos) | Alta |
| RF-A02 | Asignar roles a colaboradores | Alta |
| RF-A03 | Visualizar métricas de negocio (días concurridos, servicios populares, ingresos) | Alta |
| RF-A04 | Clasificar días en alta, media o baja demanda | Alta |
| RF-A05 | Gestionar catálogo de productos y servicios | Alta |
| RF-A06 | Gestionar stock de productos (entrada de lotes, control de existencias) | Alta |
| RF-A07 | Configurar reglas del sistema (anticipación, políticas de cancelación) | Media |
| RF-A08 | Acceder a reportes de rendimiento y finanzas | Media |

---

## Requerimientos No Funcionales

| ID | Categoría | Descripción |
|----|-----------|-------------|
| RNF-01 | **Usabilidad** | Interfaz sencilla e intuitiva para clientes y personal no técnico |
| RNF-02 | **Disponibilidad** | Sistema disponible 24/7 para consultas y agendado de citas |
| RNF-03 | **Seguridad** | Pagos en línea mediante Mercado Pago con transacciones seguras y encriptación |
| RNF-04 | **Escalabilidad** | Permitir agregar más servicios, barberos o sucursales en el futuro |
| RNF-05 | **Multiplataforma** | Disponible como sitio web y aplicación móvil |

---

## Reglas de Negocio

### 📅 Reglas de Anticipación de Citas

| ID | Regla |
|----|-------|
| RN-01 | Clientes pueden agendar con **3 días** de anticipación en días de **alta demanda** (viernes, sábado, domingo) |
| RN-02 | Clientes pueden agendar con **1 día** de anticipación en días de **baja/media demanda** (lunes a jueves) |

### ❌ Reglas de Cancelación

| ID | Regla |
|----|-------|
| RN-03 | Citas deben cancelarse con **2 días** de anticipación en alta demanda y **1 día** en baja/media demanda |
| RN-13 | Espera máxima de cliente: **5-10 minutos** después de la hora programada. Si no llega, cita se cancela automáticamente |

### 💰 Reglas de Anticipos y Pagos

| ID | Regla |
|----|-------|
| RN-04 | En la **primera cita** del cliente **NO se cobra anticipo** |
| RN-05 | Si un cliente **falta a una cita**, deberá pagar **50% de anticipo** en las siguientes **10 citas** |
| RN-06 | Si cumple las 10 citas sin faltar, se **libera del pago de anticipo** |
| RN-07 | Los anticipos **NO son reembolsables** en caso de inasistencia |
| RN-08 | El anticipo se **descuenta del pago total** del servicio |
| RN-09 | Para apartados por transferencia, el cliente debe proporcionar **ID de pago** que valida la secretaria |

### 👥 Reglas de Roles

| ID | Regla |
|----|-------|
| RN-10 | El barbero **NO gestiona citas ni cobros**; solo define tiempos de servicio |
| RN-11 | La secretaria puede registrar clientes sin cita siempre que se reciba anticipo |

### 📦 Reglas de Envío

| ID | Regla |
|----|-------|
| RN-12 | Envíos disponibles solo en la región vía **moto mandado** ($30-$45 MXN). Futuro: envíos nacionales |

---

## Casos de Uso Principales

### UC1: Acceder como invitado y visualizar catálogo

```
Actor principal: Cliente (invitado)

Precondiciones:
- No requiere registro ni inicio de sesión

Flujo principal:
1. El usuario entra al sistema como invitado
2. Visualiza catálogo de servicios y productos

Postcondiciones:
- Puede decidir registrarse para agendar cita o comprar productos
```

### UC2: Registrarse e iniciar sesión para agendar cita

```
Actor principal: Cliente

Precondiciones:
- El cliente no debe tener cuenta previa (si es registro)

Flujo principal:
1. El cliente ingresa sus datos personales y crea cuenta
2. El sistema valida datos y crea perfil
3. El cliente inicia sesión con sus credenciales

Postcondiciones:
- El cliente tiene acceso a funciones como agendar cita o comprar productos
```

### UC3: Agendar cita con pago en línea o en persona

```
Actor principal: Cliente
Actores secundarios: Secretaria, Mercado Pago

Precondiciones:
- Debe haber disponibilidad de barbero y silla

Flujo principal:
1. El cliente selecciona servicio, fecha y hora
2. El sistema valida reglas de anticipación (1 o 3 días según demanda)
3. El cliente elige forma de pago: en línea o en persona (anticipo)
4. El sistema confirma la cita

Flujos alternativos:
- A1: Primera cita → no requiere anticipo
- A2: Cliente con inasistencia previa → sistema obliga a pagar anticipo del 50%

Postcondiciones:
- La cita queda registrada en la agenda general
```

### UC4: Validar pago por transferencia (secretaria)

```
Actor principal: Secretaria

Precondiciones:
- El cliente debe haber enviado comprobante o ID de operación

Flujo principal:
1. La secretaria revisa el comprobante bancario
2. Valida si el pago es correcto
3. Marca el pago como confirmado o rechazado en el sistema

Postcondiciones:
- La cita o producto queda confirmado solo si el pago fue válido
```

### UC5: Registrar asistencia de cliente (secretaria)

```
Actor principal: Secretaria

Precondiciones:
- El cliente debe tener cita confirmada

Flujo principal:
1. El cliente llega a la barbería
2. La secretaria marca asistencia en el sistema
3. Se notifica al barbero correspondiente

Flujos alternativos:
- A1: Cliente no llega en 5-10 min → sistema cancela automáticamente la cita y libera silla
- A2: Cliente sin cita presencial ocupa la silla → secretaria registra nueva cita sin anticipo

Postcondiciones:
- El historial del cliente se actualiza con asistencia o inasistencia
```

### UC6: Comprar producto en línea con entrega en local

```
Actor principal: Cliente

Precondiciones:
- Debe haber stock disponible

Flujo principal:
1. El cliente elige producto
2. Selecciona método de entrega: recoger en local
3. Realiza pago en línea o elige pagar en local
4. La secretaria aparta el producto

Postcondiciones:
- El cliente recoge el producto y se descuenta stock
```

### UC7: Comprar producto en línea con entrega regional

```
Actor principal: Cliente
Actores secundarios: Secretaria, Repartidor

Precondiciones:
- Debe haber stock disponible

Flujo principal:
1. El cliente selecciona producto y método de entrega: moto mandado
2. Realiza pago completo
3. La secretaria gestiona envío con costo adicional ($30-$45)
4. El repartidor entrega el producto

Postcondiciones:
- Stock actualizado
- El cliente recibe producto en su domicilio regional
```

### UC8: Administrador visualiza métricas y clasifica demanda

```
Actor principal: Administrador

Precondiciones:
- Debe haber datos registrados en el sistema

Flujo principal:
1. El administrador accede a reportes de citas, ingresos y ventas
2. El sistema muestra días con más flujo de clientes
3. El administrador clasifica días en alta, media o baja demanda

Postcondiciones:
- Las reglas de anticipación se ajustan según clasificación
```

### UC9: Barbero define y actualiza tiempos de servicio

```
Actor principal: Barbero

Precondiciones:
- El barbero debe tener cuenta de colaborador

Flujo principal:
1. El barbero inicia sesión en el sistema
2. Define tiempos estimados por servicio (corte, barba, combo)
3. Si es necesario, actualiza los tiempos

Postcondiciones:
- La secretaria agenda citas en función de los tiempos definidos
```

### UC10: Sistema envía notificación de recordatorio

```
Actor principal: Sistema
Actores secundarios: Cliente, Secretaria

Precondiciones:
- El cliente debe tener cita confirmada

Flujo principal:
1. El sistema envía recordatorio 1 día antes de la cita
2. Envía notificación 1.5 horas antes de la cita
3. La secretaria recibe el mismo aviso en su panel
4. La secretaria puede enviar WhatsApp o llamar al cliente

Postcondiciones:
- El cliente está informado y la barbería mejora el seguimiento
```

---

## Análisis Técnico

### 🔄 Flujos de Proceso Identificados

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO DE CITAS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐    │
│  │ Cliente │───▶│ Selección│───▶│ Validar │───▶│  Pago    │    │
│  │ agenda  │    │ servicio │    │ reglas  │    │ anticipo │    │
│  └─────────┘    └──────────┘    └─────────┘    └──────────┘    │
│                                       │              │          │
│                                       ▼              ▼          │
│                               ┌─────────────────────────┐       │
│                               │  Confirmar y asignar    │       │
│                               │  barbero + silla        │       │
│                               └─────────────────────────┘       │
│                                       │                         │
│                                       ▼                         │
│                               ┌─────────────────────────┐       │
│                               │  Notificaciones         │       │
│                               │  (1 día y 1.5 hrs antes)│       │
│                               └─────────────────────────┘       │
│                                       │                         │
│                                       ▼                         │
│                               ┌─────────────────────────┐       │
│                               │  Registrar asistencia   │       │
│                               │  o cancelar por timeout │       │
│                               └─────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO DE PRODUCTOS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐    │
│  │ Cliente │───▶│ Selección│───▶│ Elegir  │───▶│  Pago    │    │
│  │ compra  │    │ producto │    │ entrega │    │          │    │
│  └─────────┘    └──────────┘    └─────────┘    └──────────┘    │
│                                       │              │          │
│                       ┌───────────────┼──────────────┘          │
│                       │               │                         │
│                       ▼               ▼                         │
│               ┌────────────┐  ┌────────────────┐                │
│               │ Recoger en │  │ Moto mandado   │                │
│               │ local      │  │ ($30-$45 MXN)  │                │
│               └────────────┘  └────────────────┘                │
│                       │               │                         │
│                       └───────┬───────┘                         │
│                               ▼                                 │
│                       ┌─────────────┐                           │
│                       │ Actualizar  │                           │
│                       │ stock       │                           │
│                       └─────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

### 🛠️ Stack Tecnológico Recomendado

| Capa | Tecnología | Justificación |
|------|------------|---------------|
| **Backend** | Django + Django REST Framework | Ya existe base, robusto para APIs |
| **Base de datos** | PostgreSQL | Soporte para consultas complejas, escalable |
| **Frontend Web** | Angular | Ya está configurado CORS para Angular |
| **App Móvil** | Flutter / React Native | Multiplataforma (iOS + Android) |
| **Pagos** | Mercado Pago | Requisito del cliente (RNF-03) |
| **Notificaciones** | Firebase Cloud Messaging | Push notifications móvil |
| **Emails** | Resend (ya configurado) | Recordatorios y confirmaciones |
| **Hosting** | Render (backend) + Vercel (frontend) | Ya está preparado |

---

## Modelo de Datos Propuesto

### Entidades Principales

```
┌─────────────────────────────────────────────────────────────────┐
│                       USUARIOS                                   │
├─────────────────────────────────────────────────────────────────┤
│ Usuario (base)                                                   │
│ ├── id, email, password, nombre, apellidos, telefono            │
│ ├── rol: CLIENTE | SECRETARIA | BARBERO | ADMIN                 │
│ ├── verificado, fecha_registro                                  │
│ └── estado_anticipo: LIBRE | EN_PENALIZACION                    │
│     └── citas_restantes_penalizacion (contador de 10)           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       SERVICIOS                                  │
├─────────────────────────────────────────────────────────────────┤
│ Servicio                                                         │
│ ├── id, nombre, descripcion, precio                             │
│ └── activo                                                       │
│                                                                  │
│ TiempoServicioBarbero                                           │
│ ├── id, barbero_id, servicio_id                                 │
│ └── duracion_minutos                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       CITAS                                      │
├─────────────────────────────────────────────────────────────────┤
│ Cita                                                             │
│ ├── id, cliente_id, barbero_id, servicio_id                     │
│ ├── fecha, hora_inicio, hora_fin                                │
│ ├── silla (1, 2, 3...)                                          │
│ ├── estado: PENDIENTE | CONFIRMADA | COMPLETADA | CANCELADA     │
│ ├── requiere_anticipo, anticipo_pagado                          │
│ ├── metodo_pago_anticipo                                        │
│ ├── pago_restante_confirmado                                    │
│ ├── asistio (boolean)                                           │
│ └── creado_por: CLIENTE | SECRETARIA                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       PRODUCTOS                                  │
├─────────────────────────────────────────────────────────────────┤
│ Producto                                                         │
│ ├── id, nombre, descripcion, precio                             │
│ ├── stock_actual, stock_minimo                                  │
│ ├── imagen_url                                                  │
│ └── activo                                                       │
│                                                                  │
│ MovimientoStock                                                  │
│ ├── id, producto_id, cantidad                                   │
│ ├── tipo: ENTRADA | SALIDA | APARTADO                           │
│ ├── motivo, fecha                                               │
│ └── usuario_id (quien registró)                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       VENTAS                                     │
├─────────────────────────────────────────────────────────────────┤
│ Venta                                                            │
│ ├── id, cliente_id                                              │
│ ├── fecha, total                                                │
│ ├── metodo_pago: EFECTIVO | TARJETA | TRANSFERENCIA             │
│ ├── estado: PENDIENTE | PAGADA | CANCELADA                      │
│ ├── metodo_entrega: LOCAL | MOTOMANDADO                         │
│ ├── costo_envio                                                 │
│ ├── direccion_envio (si aplica)                                 │
│ └── id_operacion_pago (para validación)                         │
│                                                                  │
│ DetalleVenta                                                     │
│ ├── id, venta_id, producto_id                                   │
│ ├── cantidad, precio_unitario                                   │
│ └── subtotal                                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       CONFIGURACIÓN                              │
├─────────────────────────────────────────────────────────────────┤
│ ConfiguracionDia                                                 │
│ ├── id, dia_semana (0-6)                                        │
│ ├── nivel_demanda: ALTA | MEDIA | BAJA                          │
│ ├── dias_anticipacion_minima                                    │
│ └── dias_anticipacion_cancelacion                               │
│                                                                  │
│ Silla                                                            │
│ ├── id, numero, activa                                          │
│ └── descripcion                                                  │
│                                                                  │
│ ConfiguracionSistema                                             │
│ ├── tiempo_espera_maximo_minutos (5-10)                         │
│ ├── porcentaje_anticipo_penalizacion (50%)                      │
│ ├── citas_para_liberar_penalizacion (10)                        │
│ └── costo_envio_regional_min, costo_envio_regional_max          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       NOTIFICACIONES                             │
├─────────────────────────────────────────────────────────────────┤
│ Notificacion                                                     │
│ ├── id, usuario_id, cita_id (opcional)                          │
│ ├── tipo: CONFIRMACION | RECORDATORIO_1D | RECORDATORIO_1_5H    │
│ ├── mensaje, fecha_envio                                        │
│ ├── enviada, leida                                              │
│ └── canal: EMAIL | PUSH | SMS                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Diagrama de Relaciones

```
Usuario ─────────┬──────────── Cita
    │            │               │
    │            │               ├── Servicio
    │            │               │
    │            └───────────── Barbero (Usuario con rol BARBERO)
    │                               │
    │                               └── TiempoServicioBarbero
    │
    └─────────────────────────── Venta
                                    │
                                    └── DetalleVenta ── Producto
                                                           │
                                                           └── MovimientoStock
```

---

## Consideraciones de Implementación

### 🚀 Fases de Desarrollo Sugeridas

#### Fase 1: MVP (Mínimo Producto Viable) - 6-8 semanas
- [ ] Sistema de usuarios con roles (Cliente, Secretaria, Barbero, Admin)
- [ ] Gestión de servicios y tiempos por barbero
- [ ] Agenda de citas básica
- [ ] Validación de reglas de demanda
- [ ] Panel de secretaria

#### Fase 2: Pagos y Notificaciones - 4-6 semanas
- [ ] Integración con Mercado Pago
- [ ] Sistema de anticipos y penalizaciones
- [ ] Notificaciones por email (recordatorios)
- [ ] Validación de pagos por transferencia

#### Fase 3: Productos y Ventas - 4-5 semanas
- [ ] Catálogo de productos
- [ ] Carrito de compras
- [ ] Gestión de stock
- [ ] Métodos de entrega (local y moto mandado)

#### Fase 4: Métricas y Optimización - 3-4 semanas
- [ ] Dashboard de administrador
- [ ] Reportes de ingresos y rendimiento
- [ ] Clasificación automática de demanda
- [ ] Optimización de agenda

#### Fase 5: App Móvil - 6-8 semanas
- [ ] Desarrollo de app móvil (Flutter/React Native)
- [ ] Push notifications
- [ ] Sincronización con backend

### ⚠️ Puntos Críticos a Considerar

1. **Concurrencia de citas**: Evitar que dos clientes agenden la misma hora/silla
2. **Zonas horarias**: Manejar correctamente para notificaciones
3. **Caché de disponibilidad**: Para evitar consultas pesadas al verificar horarios
4. **Jobs programados**: Para cancelación automática y notificaciones
5. **Webhooks de Mercado Pago**: Para confirmar pagos en tiempo real

### 🔐 Seguridad

- Implementar JWT para autenticación en APIs
- Rate limiting para evitar abuso
- Validación de pagos en el backend (nunca confiar en el frontend)
- Sanitización de inputs
- HTTPS obligatorio

### 📊 Integraciones Externas

| Servicio | Propósito |
|----------|-----------|
| **Mercado Pago** | Procesamiento de pagos |
| **Firebase** | Auth con Google, Push notifications |
| **Resend/SendGrid** | Envío de emails |
| **WhatsApp Business API** | Notificaciones opcionales (futuro) |

---

## 📝 Notas Finales

Este documento servirá como base para el desarrollo del sistema. Se recomienda:

1. **Validar con el cliente** las reglas de negocio antes de implementar
2. **Priorizar el MVP** con funcionalidades core
3. **Iterar rápidamente** con feedback del usuario
4. **Documentar APIs** con Swagger/OpenAPI
5. **Implementar tests** desde el inicio

---

*Documento generado para el proyecto de Sistema de Barbería*
*Última actualización: Enero 2026*
