# core/management/commands/crear_datos_iniciales.py
from django.core.management.base import BaseCommand
from citas.models import Silla, Servicio
from configuracion.models import ConfiguracionSistema
from django.db import transaction


class Command(BaseCommand):
    help = 'Crea datos iniciales del sistema: sillas, servicios y configuración'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando creación de datos iniciales...'))
        
        with transaction.atomic():
            # 1. Crear Sillas
            self.crear_sillas()
            
            # 2. Crear Servicios
            self.crear_servicios()
            
            # 3. Crear Configuración del Sistema
            self.crear_configuracion()
        
        self.stdout.write(self.style.SUCCESS('✓ Datos iniciales creados exitosamente!'))

    def crear_sillas(self):
        """Crea las sillas básicas de la barbería"""
        self.stdout.write('Creando sillas...')
        
        sillas_data = [
            {'numero': 1, 'nombre': 'Silla 1', 'descripcion': 'Silla principal'},
            {'numero': 2, 'nombre': 'Silla 2', 'descripcion': 'Silla secundaria'},
            {'numero': 3, 'nombre': 'Silla 3', 'descripcion': 'Silla adicional'},
        ]
        
        creadas = 0
        for silla_data in sillas_data:
            silla, created = Silla.objects.get_or_create(
                numero=silla_data['numero'],
                defaults={
                    'nombre': silla_data['nombre'],
                    'descripcion': silla_data['descripcion'],
                    'activa': True
                }
            )
            if created:
                creadas += 1
                self.stdout.write(f'  ✓ Creada: {silla}')
            else:
                self.stdout.write(f'  - Ya existe: {silla}')
        
        self.stdout.write(self.style.SUCCESS(f'  {creadas} sillas nuevas creadas'))

    def crear_servicios(self):
        """Crea los servicios básicos de la barbería"""
        self.stdout.write('Creando servicios...')
        
        servicios_data = [
            {
                'nombre': 'Corte de Cabello',
                'descripcion': 'Corte profesional de cabello con las últimas tendencias',
                'precio_base': 150.00,
                'duracion_minutos': 30,
                'categoria': 'corte'
            },
            {
                'nombre': 'Arreglo de Barba',
                'descripcion': 'Arreglo y diseño profesional de barba',
                'precio_base': 120.00,
                'duracion_minutos': 20,
                'categoria': 'barba'
            },
            {
                'nombre': 'Combo Corte + Barba',
                'descripcion': 'Corte de cabello y arreglo de barba completo',
                'precio_base': 250.00,
                'duracion_minutos': 50,
                'categoria': 'combo'
            },
            {
                'nombre': 'Tratamiento Capilar',
                'descripcion': 'Tratamiento reparador y revitalizante',
                'precio_base': 300.00,
                'duracion_minutos': 45,
                'categoria': 'tratamiento'
            },
            {
                'nombre': 'Tinte para Cabello',
                'descripcion': 'Tinte profesional de alta calidad',
                'precio_base': 350.00,
                'duracion_minutos': 60,
                'categoria': 'tinte'
            },
        ]
        
        creados = 0
        for servicio_data in servicios_data:
            servicio, created = Servicio.objects.get_or_create(
                nombre=servicio_data['nombre'],
                defaults={
                    'descripcion': servicio_data['descripcion'],
                    'precio_base': servicio_data['precio_base'],
                    'duracion_minutos': servicio_data['duracion_minutos'],
                    'categoria': servicio_data['categoria'],
                    'activo': True
                }
            )
            if created:
                creados += 1
                self.stdout.write(f'  ✓ Creado: {servicio}')
            else:
                self.stdout.write(f'  - Ya existe: {servicio}')
        
        self.stdout.write(self.style.SUCCESS(f'  {creados} servicios nuevos creados'))

    def crear_configuracion(self):
        """Crea la configuración del sistema para cada día de la semana"""
        self.stdout.write('Creando configuración del sistema...')
        
        # Configuración por defecto
        # Alta demanda: Viernes, Sábado, Domingo
        # Media demanda: Jueves
        # Baja demanda: Lunes, Martes, Miércoles
        
        configuraciones = [
            {'dia': 0, 'demanda': 'baja', 'nombre': 'Lunes'},
            {'dia': 1, 'demanda': 'baja', 'nombre': 'Martes'},
            {'dia': 2, 'demanda': 'baja', 'nombre': 'Miércoles'},
            {'dia': 3, 'demanda': 'media', 'nombre': 'Jueves'},
            {'dia': 4, 'demanda': 'alta', 'nombre': 'Viernes'},
            {'dia': 5, 'demanda': 'alta', 'nombre': 'Sábado'},
            {'dia': 6, 'demanda': 'alta', 'nombre': 'Domingo'},
        ]
        
        creadas = 0
        for config in configuraciones:
            config_obj, created = ConfiguracionSistema.objects.get_or_create(
                dia_semana=config['dia'],
                defaults={
                    'demanda': config['demanda'],
                    'dias_anticipacion_alta': 3,
                    'dias_anticipacion_media': 2,
                    'dias_anticipacion_baja': 1,
                    'dias_cancelacion_alta': 2,
                    'dias_cancelacion_media': 1,
                    'dias_cancelacion_baja': 1,
                    'tiempo_espera_maximo': 10,
                    'costo_moto_mandado': 40.00,
                    'costo_paqueteria': 150.00,
                    'porcentaje_anticipo_penalizado': 50.00,
                    'citas_penalizadas': 10,
                }
            )
            if created:
                creadas += 1
                self.stdout.write(f'  ✓ Configurado: {config["nombre"]} ({config["demanda"]})')
            else:
                self.stdout.write(f'  - Ya existe: {config["nombre"]}')
        
        self.stdout.write(self.style.SUCCESS(f'  {creadas} configuraciones nuevas creadas'))
