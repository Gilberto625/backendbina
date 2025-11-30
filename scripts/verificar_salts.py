#!/usr/bin/env python
"""
Script para verificar que los salts son únicos para cada contraseña
Ejecutar: python manage.py shell < scripts/verificar_salts.py
"""
from accounts.models import Usuario
from django.contrib.auth import get_user_model

Usuario = get_user_model()

print("=" * 60)
print("VERIFICACIÓN DE SALTS ÚNICOS")
print("=" * 60)

# Crear dos usuarios con la misma contraseña
print("\n1. Creando dos usuarios con la misma contraseña...")
usuario1 = Usuario.objects.create_user(
    username='test_salt_1',
    email='test_salt_1@test.com',
    password='Password123!'
)

usuario2 = Usuario.objects.create_user(
    username='test_salt_2',
    email='test_salt_2@test.com',
    password='Password123!'
)

print("✅ Usuarios creados")

# Extraer salts de los hashes
hash1 = usuario1.password
hash2 = usuario2.password

# El formato es: algorithm$iterations$salt$hash
parts1 = hash1.split('$')
parts2 = hash2.split('$')

if len(parts1) >= 3 and len(parts2) >= 3:
    salt1 = parts1[2]
    salt2 = parts2[2]
    
    print(f"\n2. Salt del usuario 1: {salt1[:20]}...")
    print(f"   Salt del usuario 2: {salt2[:20]}...")
    
    if salt1 != salt2:
        print("✅ VERIFICADO: Los salts son DIFERENTES (único por contraseña)")
    else:
        print("❌ ERROR: Los salts son iguales (no debería pasar)")
    
    # Verificar que ambos pueden autenticarse
    print("\n3. Verificando autenticación...")
    if usuario1.check_password('Password123!'):
        print("✅ Usuario 1 puede autenticarse correctamente")
    else:
        print("❌ ERROR: Usuario 1 no puede autenticarse")
    
    if usuario2.check_password('Password123!'):
        print("✅ Usuario 2 puede autenticarse correctamente")
    else:
        print("❌ ERROR: Usuario 2 no puede autenticarse")
    
    # Verificar formato del hash
    print("\n4. Verificando formato del hash...")
    if hash1.startswith('pbkdf2_sha256$'):
        print("✅ Usuario 1 usa PBKDF2 con SHA256")
    else:
        print(f"⚠️  Usuario 1 usa: {parts1[0]}")
    
    if hash2.startswith('pbkdf2_sha256$'):
        print("✅ Usuario 2 usa PBKDF2 con SHA256")
    else:
        print(f"⚠️  Usuario 2 usa: {parts2[0]}")
    
    # Mostrar información completa
    print("\n5. Información completa del hash:")
    print(f"   Usuario 1: {hash1[:80]}...")
    print(f"   Usuario 2: {hash2[:80]}...")
    
else:
    print("❌ ERROR: Formato de hash inválido")

# Limpiar usuarios de prueba
print("\n6. Limpiando usuarios de prueba...")
Usuario.objects.filter(username__startswith='test_salt_').delete()
print("✅ Usuarios eliminados")

print("\n" + "=" * 60)
print("VERIFICACIÓN COMPLETA")
print("=" * 60)


