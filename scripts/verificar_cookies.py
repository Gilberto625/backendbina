#!/usr/bin/env python
"""
Script para verificar atributos de cookies
Ejecutar: python manage.py shell < scripts/verificar_cookies.py
"""
from django.test import Client
from django.conf import settings

client = Client()

print("=" * 60)
print("VERIFICACIÓN DE COOKIES")
print("=" * 60)

# Obtener respuesta con cookies
response = client.get('/api/usuarios/csrf/')

print("\n1. Cookies en respuesta:")
print("-" * 60)

cookies = response.cookies

if 'sessionid' in cookies:
    sessionid = cookies['sessionid']
    print("\n📋 sessionid:")
    print(f"   HttpOnly: {sessionid.get('httponly', 'No configurado')}")
    print(f"   Secure: {sessionid.get('secure', 'No configurado')}")
    print(f"   SameSite: {sessionid.get('samesite', 'No configurado')}")
    print(f"   Path: {sessionid.get('path', 'No configurado')}")
    
    # Verificar configuración
    print("\n   Verificación:")
    if sessionid.get('httponly'):
        print("   ✅ HttpOnly: CORRECTO")
    else:
        print("   ❌ HttpOnly: FALTA")
    
    if sessionid.get('secure') or not settings.DEBUG:
        print("   ✅ Secure: CORRECTO (o en desarrollo)")
    else:
        print("   ⚠️  Secure: Solo en producción")
    
    if sessionid.get('samesite', '').lower() == 'lax':
        print("   ✅ SameSite: CORRECTO")
    else:
        print("   ⚠️  SameSite: Verificar configuración")
else:
    print("   ⚠️  No se encontró cookie sessionid")

if 'csrftoken' in cookies:
    csrftoken = cookies['csrftoken']
    print("\n📋 csrftoken:")
    print(f"   HttpOnly: {csrftoken.get('httponly', 'No configurado')}")
    print(f"   Secure: {csrftoken.get('secure', 'No configurado')}")
    print(f"   SameSite: {csrftoken.get('samesite', 'No configurado')}")
    
    # Verificar configuración
    print("\n   Verificación:")
    if not csrftoken.get('httponly'):
        print("   ✅ HttpOnly: False (necesario para Angular)")
    else:
        print("   ⚠️  HttpOnly: True (puede causar problemas con Angular)")
    
    if csrftoken.get('secure') or not settings.DEBUG:
        print("   ✅ Secure: CORRECTO")
    else:
        print("   ⚠️  Secure: Solo en producción")
else:
    print("   ⚠️  No se encontró cookie csrftoken")

# Verificar configuración en settings
print("\n2. Configuración en settings.py:")
print("-" * 60)
print(f"   SESSION_COOKIE_HTTPONLY: {settings.SESSION_COOKIE_HTTPONLY}")
print(f"   SESSION_COOKIE_SECURE: {settings.SESSION_COOKIE_SECURE}")
print(f"   SESSION_COOKIE_SAMESITE: {settings.SESSION_COOKIE_SAMESITE}")
print(f"   CSRF_COOKIE_SECURE: {settings.CSRF_COOKIE_SECURE}")
print(f"   CSRF_COOKIE_SAMESITE: {settings.CSRF_COOKIE_SAMESITE}")
print(f"   CSRF_COOKIE_HTTPONLY: {settings.CSRF_COOKIE_HTTPONLY}")
print(f"   DEBUG: {settings.DEBUG}")

print("\n" + "=" * 60)
print("VERIFICACIÓN COMPLETA")
print("=" * 60)



