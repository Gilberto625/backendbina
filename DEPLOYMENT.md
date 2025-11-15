 

## Requisitos Previos

- Cuenta en GitHub (gratuita)

- Cuenta en Render (gratuita): https://render.com

 

---

 

## Paso 1: Preparar el Repositorio en GitHub

 

### 1.1 Subir el código a GitHub (si no lo has hecho)

 

```bash

cd /ruta/a/tu/backendDjango

 

# Inicializar git si no está inicializado

git init

 

# Agregar todos los archivos

git add .

 

# Hacer commit

git commit -m "Preparar backend para deployment en Render"

 

# Crear repositorio en GitHub y conectarlo

git remote add origin https://github.com/TU-USUARIO/TU-REPO.git

git branch -M main

git push -u origin main

```

 

---

 

## Paso 2: Crear Cuenta en Render

 

1. Ve a https://render.com

2. Click en "Get Started"

3. Regístrate con tu cuenta de GitHub (recomendado)

4. Autoriza a Render para acceder a tus repositorios

 

---

 

## Paso 3: Crear Base de Datos PostgreSQL

 

1. En el dashboard de Render, click en **"New +"**

2. Selecciona **"PostgreSQL"**

3. Configura:

   - **Name**: `django-db` (o el nombre que prefieras)

   - **Database**: `django_production`

   - **User**: `django_user`

   - **Region**: Selecciona el más cercano a ti

   - **Plan**: **Free** (gratis)

4. Click en **"Create Database"**

5. **IMPORTANTE**: Copia la **"Internal Database URL"** (la necesitarás después)

 

---

 

## Paso 4: Crear Web Service

 

1. En el dashboard, click en **"New +"**

2. Selecciona **"Web Service"**

3. Conecta tu repositorio de GitHub

4. Configura:

   - **Name**: `django-backend` (o el nombre que prefieras)

   - **Region**: El mismo que la base de datos

   - **Branch**: `main`

   - **Root Directory**: (dejar vacío)

   - **Runtime**: **Python 3**

   - **Build Command**: `./build.sh`

   - **Start Command**: `gunicorn core.wsgi:application`

   - **Plan**: **Free** (gratis)

 

---

 

## Paso 5: Configurar Variables de Entorno

 

En la sección **"Environment"**, agrega estas variables:

 

```

DEBUG=False

SECRET_KEY=tu-secret-key-super-segura-aqui

ALLOWED_HOSTS=.onrender.com

DATABASE_URL=<la URL que copiaste de PostgreSQL>

 

# Email Configuration

EMAIL_HOST_USER=tu-email@gmail.com

EMAIL_HOST_PASSWORD=tu-app-password-aqui

 

# CORS (agrega aquí la URL de tu frontend cuando lo despliegues)

CORS_ALLOWED_ORIGINS=https://tu-frontend.vercel.app

 

# CSRF Trusted Origins

CSRF_TRUSTED_ORIGINS=https://tu-backend.onrender.com,https://tu-frontend.vercel.app

```

 

**Generar SECRET_KEY segura:**

```bash

python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

```

 

---

 

## Paso 6: Deploy

 

1. Click en **"Create Web Service"**

2. Render comenzará a:

   - Instalar dependencias

   - Ejecutar `build.sh` (collectstatic y migraciones)

   - Iniciar el servidor con Gunicorn

3. **Espera 5-10 minutos** para el primer deploy

 

---

 

## Paso 7: Verificar el Deployment

 

Una vez que el deploy termine:

 

1. Verás un mensaje "Live" en verde

2. Tu backend estará disponible en: `https://tu-backend.onrender.com`

3. Prueba el endpoint de salud: `https://tu-backend.onrender.com/api/usuarios/csrf/`

 

---

 

## Paso 8: Subir Credenciales de Firebase

 

**IMPORTANTE**: Las credenciales de Firebase (`firebase-service-account.json`) NO deben estar en Git por seguridad.

 

### Opción 1: Variables de Entorno (Recomendado)

 

1. Abre tu `firebase-service-account.json`

2. Copia TODO el contenido

3. En Render, agrega variable de entorno:

   - Key: `FIREBASE_CREDENTIALS`

   - Value: Pega el contenido JSON completo

 

4. Modifica `config/firebase.py`:

 

```python

import firebase_admin

from firebase_admin import credentials

import os

import json

 

# En producción, usar variable de entorno

if os.getenv('FIREBASE_CREDENTIALS'):

    cred_dict = json.loads(os.getenv('FIREBASE_CREDENTIALS'))

    cred = credentials.Certificate(cred_dict)

else:

    # En desarrollo, usar archivo local

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    cred_path = os.path.join(base_dir, 'config', 'firebase-service-account.json')

    cred = credentials.Certificate(cred_path)

 

firebase_admin.initialize_app(cred)

```

 

---

 

## 📋 Troubleshooting

 

### El deploy falla

 

- Revisa los logs en Render

- Verifica que todas las variables de entorno estén configuradas

- Asegúrate que `build.sh` tiene permisos de ejecución

 

### Error de base de datos

 

- Verifica que `DATABASE_URL` esté correctamente configurada

- Asegúrate que la base de datos PostgreSQL esté "Available"

 

### Error 500 en producción

 

- Revisa los logs en Render: Logs > Events

- Verifica las variables de entorno

- Asegúrate que `DEBUG=False`

 

### El servicio se "duerme"

 

- En el plan Free, Render duerme el servicio después de 15 minutos sin uso

- La primera petición después tarda ~30 segundos en despertar

- Solución: Upgrade a plan pagado ($7/mes) para mantenerlo siempre activo

 

---

 

## 🎉 ¡Listo!

 

Tu backend Django ahora está desplegado en producción con:

- ✅ PostgreSQL como base de datos

- ✅ HTTPS automático

- ✅ Deploy automático cuando hagas push a GitHub

- ✅ Logs accesibles en tiempo real

 

**URL del backend**: `https://tu-backend.onrender.com`

 

---

 

## 📱 Siguiente Paso: Desplegar el Frontend Angular

 

Una vez que tu backend esté funcionando, el siguiente paso es desplegar el frontend Angular en Vercel o Netlify.

 

¿Necesitas ayuda con el deployment del frontend? ¡Solo pregunta!