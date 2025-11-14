# API de Autenticación - Documentación

## Base URL
- **Desarrollo**: `http://localhost:8000/api/usuarios/`
- **Producción**: `https://backendbina-1.onrender.com/api/usuarios/`

---

## 📋 Índice
1. [Autenticación Básica](#autenticación-básica)
2. [Verificación 2FA](#verificación-2fa)
3. [Recuperación de Contraseña](#recuperación-de-contraseña)
4. [TOTP (Google Authenticator)](#totp-google-authenticator)
5. [Códigos de Respaldo](#códigos-de-respaldo)
6. [Estado de Seguridad](#estado-de-seguridad)

---

## Autenticación Básica

### 1. Obtener CSRF Token
**Endpoint**: `GET /csrf/`

**Respuesta**:
```json
{
  "csrfToken": "abc123..."
}
```

### 2. Registro de Usuario
**Endpoint**: `POST /register/`

**Body**:
```json
{
  "nombre": "Juan",
  "apellidopaterno": "Pérez",
  "apellidomaterno": "García",
  "username": "juanperez",
  "correo": "juan@example.com",
  "contrasena": "Password123!",
  "telefono": "5551234567",
  "preguntasecreta": "¿Nombre de tu primera mascota?",
  "respuestasecreta": "Firulais"
}
```

**Respuesta Exitosa**:
```json
{
  "mensaje": "Usuario registrado con éxito",
  "requires2fa": true,
  "canal": "email",
  "destino": "ju***@example.com",
  "tempToken": "uuid-temp-token"
}
```

### 3. Verificar Registro (2FA)
**Endpoint**: `POST /register/2fa/verificar/`

**Body**:
```json
{
  "tempToken": "uuid-temp-token",
  "codigo": "123456"
}
```

**Respuesta Exitosa**:
```json
{
  "ok": true,
  "mensaje": "Verificación exitosa"
}
```

### 4. Inicio de Sesión
**Endpoint**: `POST /login/`

**Body**:
```json
{
  "email": "juan@example.com",
  "password": "Password123!"
}
```

**Respuesta (Usuario sin TOTP)**:
```json
{
  "requires2fa": true,
  "tempToken": "uuid-temp-token",
  "metodos_disponibles": ["email", "backup"],
  "canal": "email",
  "destino": "ju***@example.com"
}
```

**Respuesta (Usuario con TOTP)**:
```json
{
  "requires2fa": true,
  "tempToken": "uuid-temp-token",
  "metodos_disponibles": ["email", "totp", "backup"],
  "mensaje": "Usa tu app de autenticación o solicita un código por email"
}
```

### 5. Solicitar Código por Email (para usuarios con TOTP)
**Endpoint**: `POST /login/2fa/solicitar-codigo/`

**Body**:
```json
{
  "tempToken": "uuid-temp-token"
}
```

**Respuesta**:
```json
{
  "ok": true,
  "canal": "email",
  "destino": "ju***@example.com",
  "mensaje": "Código enviado a tu correo"
}
```

### 6. Verificar 2FA en Login
**Endpoint**: `POST /login/2fa/verificar/`

**Body (Código de Email)**:
```json
{
  "tempToken": "uuid-temp-token",
  "codigo": "123456",
  "tipo": "email"
}
```

**Body (Código TOTP)**:
```json
{
  "tempToken": "uuid-temp-token",
  "codigo": "123456",
  "tipo": "totp"
}
```

**Body (Código de Respaldo)**:
```json
{
  "tempToken": "uuid-temp-token",
  "codigo": "ABC12345",
  "tipo": "backup"
}
```

**Respuesta Exitosa**:
```json
{
  "ok": true,
  "mensaje": "Inicio de sesión exitoso",
  "usuario": {
    "id": 1,
    "email": "juan@example.com",
    "username": "juanperez"
  }
}
```

### 7. Login con Google
**Endpoint**: `POST /login/google/`

**Body**:
```json
{
  "idToken": "firebase-id-token"
}
```

**Respuesta**:
```json
{
  "ok": true,
  "mensaje": "Inicio de sesión con Google exitoso",
  "usuario": {
    "id": 1,
    "email": "juan@gmail.com",
    "username": "juan_abc12345"
  }
}
```

---

## Recuperación de Contraseña

### 1. Recuperar con Preguntas Secretas (Método Antiguo)
**Endpoint**: `POST /recuperar/`

**Body**:
```json
{
  "email": "juan@example.com",
  "preguntaSecreta": "¿Nombre de tu primera mascota?",
  "respuestaSecreta": "Firulais"
}
```

**Respuesta**:
```json
{
  "ok": true,
  "tempToken": "uuid-temp-token"
}
```

### 2. Restablecer Contraseña (con preguntas secretas)
**Endpoint**: `POST /restablecer/`

**Body**:
```json
{
  "tempToken": "uuid-temp-token",
  "nuevaContrasena": "NuevaPassword123!"
}
```

**Respuesta**:
```json
{
  "ok": true,
  "mensaje": "Contraseña actualizada con éxito"
}
```

### 3. Solicitar Recuperación por Email (Nuevo Método)
**Endpoint**: `POST /recuperar/email/`

**Body**:
```json
{
  "email": "juan@example.com"
}
```

**Respuesta**:
```json
{
  "ok": true,
  "mensaje": "Si el correo existe, recibirás un enlace de recuperación"
}
```

**Email enviado al usuario**:
```
Enlace: https://frontbina.vercel.app/reset-password?token=uuid-token
Expira en: 30 minutos
```

### 4. Restablecer con Token de Email
**Endpoint**: `POST /restablecer/email/`

**Body**:
```json
{
  "token": "uuid-token-from-email",
  "nuevaContrasena": "NuevaPassword123!"
}
```

**Respuesta**:
```json
{
  "ok": true,
  "mensaje": "Contraseña actualizada con éxito"
}
```

---

## TOTP (Google Authenticator)

### 1. Configurar TOTP
**Endpoint**: `POST /totp/configurar/`

**Body**:
```json
{
  "email": "juan@example.com"
}
```

**Respuesta**:
```json
{
  "ok": true,
  "secret": "JBSWY3DPEHPK3PXP",
  "qrCode": "data:image/png;base64,iVBORw0KGgo...",
  "mensaje": "Escanea el QR con tu app de autenticación"
}
```

**Instrucciones para el usuario**:
1. Descarga Google Authenticator, Authy, o similar
2. Escanea el código QR mostrado
3. Ingresa el código de 6 dígitos generado

### 2. Habilitar TOTP
**Endpoint**: `POST /totp/habilitar/`

**Body**:
```json
{
  "email": "juan@example.com",
  "codigo": "123456"
}
```

**Respuesta Exitosa**:
```json
{
  "ok": true,
  "mensaje": "TOTP habilitado exitosamente"
}
```

### 3. Verificar TOTP en Login
**Endpoint**: `POST /totp/verificar/`

**Body**:
```json
{
  "tempToken": "uuid-temp-token",
  "codigo": "123456",
  "tipo": "totp"
}
```

**Respuesta**:
```json
{
  "ok": true,
  "mensaje": "Verificación exitosa",
  "usuario": {
    "id": 1,
    "email": "juan@example.com",
    "username": "juanperez"
  }
}
```

---

## Códigos de Respaldo

### 1. Generar Códigos de Respaldo
**Endpoint**: `POST /backup-codes/generar/`

**Body**:
```json
{
  "email": "juan@example.com"
}
```

**Respuesta**:
```json
{
  "ok": true,
  "codigos": [
    "A1B2C3D4",
    "E5F6G7H8",
    "I9J0K1L2",
    "M3N4O5P6",
    "Q7R8S9T0",
    "U1V2W3X4",
    "Y5Z6A7B8",
    "C9D0E1F2",
    "G3H4I5J6",
    "K7L8M9N0"
  ],
  "mensaje": "Guarda estos códigos en un lugar seguro. Solo se mostrarán una vez."
}
```

**⚠️ IMPORTANTE**:
- Cada código solo se puede usar **UNA VEZ**
- Guardar en un lugar seguro (no en la nube sin cifrar)
- Regenerar si se pierden todos

### 2. Usar Código de Respaldo
**Endpoint**: `POST /login/2fa/verificar/`

**Body**:
```json
{
  "tempToken": "uuid-temp-token",
  "codigo": "A1B2C3D4",
  "tipo": "backup"
}
```

**Respuesta**:
```json
{
  "ok": true,
  "mensaje": "Inicio de sesión exitoso",
  "usuario": {
    "id": 1,
    "email": "juan@example.com",
    "username": "juanperez"
  }
}
```

---

## Estado de Seguridad

### Verificar Estado de Seguridad del Usuario
**Endpoint**: `POST /seguridad/estado/`

**Body**:
```json
{
  "email": "juan@example.com"
}
```

**Respuesta**:
```json
{
  "ok": true,
  "email_2fa": true,
  "totp_enabled": true,
  "backup_codes_available": 8,
  "security_questions": true,
  "verificado": true
}
```

**Interpretación**:
- `email_2fa`: Siempre `true`, código por email disponible
- `totp_enabled`: Usuario tiene Google Authenticator configurado
- `backup_codes_available`: Cantidad de códigos de respaldo restantes
- `security_questions`: Usuario tiene preguntas secretas configuradas
- `verificado`: Cuenta verificada por email

---

## ⚠️ Códigos de Error Comunes

### 400 Bad Request
```json
{
  "error": "El campo correo es obligatorio"
}
```

### 401 Unauthorized
```json
{
  "error": "Credenciales inválidas"
}
```

### 429 Too Many Requests
```json
{
  "error": "Demasiados intentos"
}
```

### 500 Internal Server Error
```json
{
  "error": "No se pudo enviar el correo"
}
```

---

## 🔒 Métodos de Verificación

El sistema soporta **3 métodos de verificación**:

1. **Email (2FA)**: Código de 6 dígitos enviado por correo
   - ✅ Siempre disponible
   - ⏱️ Expira en 5 minutos
   - 🔢 Máximo 5 intentos

2. **TOTP (Google Authenticator)**: Código generado por app
   - 📱 Requiere configuración inicial
   - 🔄 Código rota cada 30 segundos
   - ✅ Funciona sin internet

3. **Códigos de Respaldo**: Códigos de un solo uso
   - 🆘 Para emergencias
   - 10 códigos por generación
   - ⚠️ Solo se muestran una vez

---

## 🛡️ Métodos de Seguridad

1. **Preguntas Secretas**: Para recuperación de contraseña
2. **Códigos de Respaldo**: Para acceso de emergencia

---

## 📧 Variables de Entorno Requeridas en Render

```bash
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxx
CORS_ALLOWED_ORIGINS=https://frontbina.vercel.app,https://backendbina-1.onrender.com
CSRF_TRUSTED_ORIGINS=https://frontbina.vercel.app,https://backendbina-1.onrender.com
FIREBASE_CREDENTIALS=<json-credentials-if-using-google-login>
```

---

## 🔧 Rate Limiting

- **Login**: 5 intentos por minuto por IP
- **Recuperación por email**: 3 intentos por hora por IP
- **Verificación 2FA**: 5 intentos por sesión

---

## 📝 Flujo Completo de Registro y Login

### Registro:
1. `POST /register/` → Obtener `tempToken`
2. Revisar email para código de 6 dígitos
3. `POST /register/2fa/verificar/` → Cuenta verificada

### Login (sin TOTP):
1. `POST /login/` → Obtener `tempToken`
2. Revisar email para código
3. `POST /login/2fa/verificar/` con `tipo: "email"`

### Login (con TOTP):
1. `POST /login/` → Obtener `tempToken` y `metodos_disponibles`
2. Opción A: Usar Google Authenticator
   - `POST /login/2fa/verificar/` con `tipo: "totp"`
3. Opción B: Solicitar código por email
   - `POST /login/2fa/solicitar-codigo/`
   - `POST /login/2fa/verificar/` con `tipo: "email"`
4. Opción C: Usar código de respaldo
   - `POST /login/2fa/verificar/` con `tipo: "backup"`

### Configurar TOTP:
1. `POST /totp/configurar/` → Obtener QR code
2. Escanear con Google Authenticator
3. `POST /totp/habilitar/` con código de la app

### Generar Códigos de Respaldo:
1. `POST /backup-codes/generar/`
2. Guardar los 10 códigos en lugar seguro
3. Usar cuando pierdas acceso a email o TOTP

---

## 🎯 Ejemplo de Flujo en Frontend (React/Angular)

```javascript
// 1. Login
const loginResponse = await fetch('/api/usuarios/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'juan@example.com',
    password: 'Password123!'
  })
});

const loginData = await loginResponse.json();

if (loginData.requires2fa) {
  const metodos = loginData.metodos_disponibles; // ["email", "totp", "backup"]

  // Si tiene TOTP, mostrar opciones
  if (metodos.includes('totp')) {
    // Mostrar: "Ingresa código de Google Authenticator"
    // O botón: "Enviar código por email"
  } else {
    // Código ya enviado por email automáticamente
    // Mostrar: "Revisa tu correo"
  }

  // 2. Verificar con el método elegido
  const verifyResponse = await fetch('/api/usuarios/login/2fa/verificar/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tempToken: loginData.tempToken,
      codigo: userInputCode,
      tipo: 'totp' // o 'email' o 'backup'
    })
  });

  const userData = await verifyResponse.json();
  // userData.usuario contiene la info del usuario
}
```

---

## ✅ Checklist de Implementación Frontend

- [ ] Página de registro con todos los campos
- [ ] Verificación de email post-registro
- [ ] Login con email y contraseña
- [ ] Verificación 2FA con opciones (email, TOTP, backup)
- [ ] Configuración de TOTP con QR code
- [ ] Generación y descarga de códigos de respaldo
- [ ] Recuperación de contraseña por email
- [ ] Recuperación de contraseña con preguntas secretas (legacy)
- [ ] Login con Google (Firebase)
- [ ] Dashboard de seguridad mostrando métodos habilitados

---

## 📞 Soporte

Para problemas o preguntas, contacta al equipo de desarrollo.
