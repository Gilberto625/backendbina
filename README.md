# Backend Django - Autenticación con 2FA y Google Login

Backend desarrollado con Django 5.2.7 que proporciona autenticación completa con:
- Registro de usuarios con 2FA por email
- Login con 2FA
- Autenticación con Google (Firebase)
- Recuperación de contraseña
- CORS configurado para Angular frontend

## Características

- ✅ Autenticación 2FA mediante código de 6 dígitos por email
- ✅ Login con Google usando Firebase Authentication
- ✅ Códigos 2FA con expiración de 5 minutos
- ✅ Límite de 5 intentos fallidos en verificación 2FA
- ✅ Recuperación de contraseña con preguntas secretas
- ✅ CORS configurado para Angular (puerto 4200)
- ✅ Variables de entorno para credenciales sensibles

## Requisitos

- Python 3.8+
- SQLite3 (incluido con Python)

## Instalación

### 1. Clonar el repositorio

```bash
git clone <tu-repositorio>
cd backendDjango
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo `.env.example` a `.env`:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
SECRET_KEY=tu-secret-key-generada
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password-de-gmail

CORS_ALLOWED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
CSRF_TRUSTED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
```

**Nota sobre Gmail App Password:**
1. Ve a tu cuenta de Google
2. Activa verificación en dos pasos
3. Ve a "Contraseñas de aplicaciones"
4. Genera una nueva contraseña para "Correo"
5. Copia la contraseña de 16 dígitos en `EMAIL_HOST_PASSWORD`

### 5. Configurar Firebase (para Google Login)

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Crea un proyecto o usa uno existente
3. Ve a "Project Settings" > "Service Accounts"
4. Click en "Generate new private key"
5. Guarda el archivo JSON como `config/firebase-service-account.json`

### 6. Ejecutar migraciones

```bash
python manage.py migrate
```

### 7. Crear superusuario (opcional)

```bash
python manage.py createsuperuser
```

### 8. Ejecutar servidor

```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`

## Endpoints API

### Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/usuarios/csrf/` | Obtener CSRF token para Angular |
| POST | `/api/usuarios/register/` | Registrar nuevo usuario + enviar código 2FA |
| POST | `/api/usuarios/register/2fa/verificar/` | Verificar código 2FA de registro |
| POST | `/api/usuarios/login/` | Login + enviar código 2FA |
| POST | `/api/usuarios/login/2fa/verificar/` | Verificar código 2FA de login |
| POST | `/api/usuarios/login/google/` | Login con Google |
| POST | `/api/usuarios/recuperar/` | Recuperar contraseña |
| POST | `/api/usuarios/restablecer/` | Restablecer contraseña |

### Ejemplos de uso

#### 1. Registro de usuario

```bash
POST /api/usuarios/register/
Content-Type: application/json

{
  "nombre": "Juan",
  "apellidopaterno": "Pérez",
  "apellidomaterno": "García",
  "username": "juanperez",
  "correo": "juan@example.com",
  "contrasena": "MiPassword123",
  "telefono": "1234567890",
  "preguntasecreta": "Nombre de tu mascota",
  "respuestasecreta": "Firulais"
}
```

**Respuesta:**
```json
{
  "mensaje": "Usuario registrado con éxito",
  "requires2fa": true,
  "canal": "email",
  "destino": "ju***@example.com",
  "tempToken": "uuid-generado"
}
```

#### 2. Verificar código 2FA

```bash
POST /api/usuarios/register/2fa/verificar/
Content-Type: application/json

{
  "tempToken": "uuid-del-paso-anterior",
  "codigo": "123456"
}
```

#### 3. Login

```bash
POST /api/usuarios/login/
Content-Type: application/json

{
  "email": "juan@example.com",
  "password": "MiPassword123"
}
```

#### 4. Login con Google

```bash
POST /api/usuarios/login/google/
Content-Type: application/json

{
  "idToken": "token-de-google-firebase"
}
```

## Estructura del Proyecto

```
backendDjango/
├── accounts/              # App de autenticación
│   ├── models.py         # Modelo Usuario extendido
│   ├── views.py          # Endpoints API
│   └── urls.py           # Rutas
├── config/
│   ├── firebase.py       # Configuración Firebase
│   └── firebase-service-account.json  # Credenciales (no en git)
├── core/                 # Configuración Django
│   ├── settings.py       # Settings con CORS y variables de entorno
│   └── urls.py           # URLs principales
├── .env                  # Variables de entorno (no en git)
├── .env.example          # Ejemplo de variables de entorno
├── requirements.txt      # Dependencias
└── manage.py
```

## Desarrollo con Angular

Este backend está configurado para trabajar con un frontend Angular en `http://localhost:4200`.

### Pasos para integrar con Angular:

1. **Obtener CSRF Token:**
   ```typescript
   // En Angular
   this.http.get('http://localhost:8000/api/usuarios/csrf/', { withCredentials: true })
     .subscribe(response => {
       this.csrfToken = response.csrfToken;
     });
   ```

2. **Hacer peticiones con CSRF:**
   ```typescript
   const headers = new HttpHeaders({
     'X-CSRFToken': this.csrfToken
   });

   this.http.post('http://localhost:8000/api/usuarios/login/',
     { email, password },
     { headers, withCredentials: true }
   ).subscribe();
   ```

3. **Configurar HttpClient en Angular:**
   ```typescript
   // En tu módulo
   import { HttpClientModule, HttpClientXsrfModule } from '@angular/common/http';

   imports: [
     HttpClientModule,
     HttpClientXsrfModule.withOptions({
       cookieName: 'csrftoken',
       headerName: 'X-CSRFToken',
     })
   ]
   ```

## Seguridad

- ✅ Credenciales en variables de entorno
- ✅ CORS configurado solo para dominios permitidos
- ✅ CSRF protection habilitado
- ✅ Códigos 2FA con expiración
- ✅ Límite de intentos fallidos
- ✅ Sesiones seguras con HttpOnly cookies

**IMPORTANTE para producción:**
- Cambiar `DEBUG=False` en `.env`
- Usar SECRET_KEY fuerte y única
- Configurar ALLOWED_HOSTS correctamente
- Usar HTTPS (configurar `SESSION_COOKIE_SECURE=True`)

## Troubleshooting

### Error: "No module named 'decouple'"
```bash
pip install python-decouple
```

### Error: "Firebase app already initialized"
Reinicia el servidor Django.

### Error: "CORS policy blocking"
Verifica que `CORS_ALLOWED_ORIGINS` en `.env` incluya la URL de tu frontend Angular.

### Error al enviar emails
Verifica que `EMAIL_HOST_PASSWORD` sea un "App Password" de Gmail, no tu contraseña normal.

## Autor

Desarrollado para uso local con SQLite3.

## Licencia

MIT
