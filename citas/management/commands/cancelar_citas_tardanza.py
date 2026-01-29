# citas/management/commands/cancelar_citas_tardanza.py
from django.core.management.base import BaseCommand
from citas.services import ValidacionCitasService


class Command(BaseCommand):
    help = 'Cancela automáticamente las citas que han pasado el tiempo de espera máximo'

    def handle(self, *args, **options):
        self.stdout.write('Verificando citas por cancelar...')
        
        canceladas = ValidacionCitasService.cancelar_citas_por_tardanza()
        
        if canceladas > 0:
            self.stdout.write(
                self.style.SUCCESS(f'[OK] {canceladas} citas canceladas por tardanza')
            )
        else:
            self.stdout.write('[-] No hay citas para cancelar')
        
        self.stdout.write(self.style.SUCCESS('Proceso completado'))
