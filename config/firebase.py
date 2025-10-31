# config/firebase.py
import firebase_admin
from firebase_admin import credentials
import os
import json
# En producción, usar variable de entorno para las credenciales
# En desarrollo, usar archivo local
if os.getenv('FIREBASE_CREDENTIALS'):
    # Producción: credenciales desde variable de entorno
    cred_dict = json.loads(os.getenv('FIREBASE_CREDENTIALS'))
    cred = credentials.Certificate(cred_dict)
else:
    # Desarrollo: credenciales desde archivo local
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cred_path = os.path.join(base_dir, 'config', 'firebase-service-account.json')
    cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)