# notificaciones/management/commands/procesar_notificaciones.py
from django.core.management.base import BaseCommand
from notificaciones.services import NotificacionesService


class Command(BaseCommand):
    help = 'Procesa las notificaciones programadas que deben enviarse'

    def handle(self, *args, **options):
        self.stdout.write('Procesando notificaciones programadas...')
        
        procesadas = NotificacionesService.procesar_notificaciones_programadas()
        
        if procesadas > 0:
            self.stdout.write(
                self.style.SUCCESS(f'[OK] {procesadas} notificaciones procesadas')
            )
        else:
            self.stdout.write('[-] No hay notificaciones para procesar')
        
        self.stdout.write(self.style.SUCCESS('Proceso completado'))
