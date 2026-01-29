# pagos/models.py
from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import Usuario

# Estados de pago
ESTADO_PAGO_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('procesando', 'Procesando'),
    ('completado', 'Completado'),
    ('rechazado', 'Rechazado'),
    ('reembolsado', 'Reembolsado'),
]

# Métodos de pago
METODO_PAGO_CHOICES = [
    ('efectivo', 'Efectivo'),
    ('tarjeta', 'Tarjeta'),
    ('transferencia', 'Transferencia'),
    ('mercado_pago', 'Mercado Pago'),
]

class Pago(models.Model):
    """Registro de pagos realizados"""
    # Relación con cita o compra (puede ser null si es pago independiente)
    cita = models.ForeignKey('citas.Cita', on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos')
    # Compra por carrito (OrdenCompra)
    compra = models.ForeignKey('productos.OrdenCompra', on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos')
    
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='pagos_cliente')
    
    monto = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_PAGO_CHOICES, default='pendiente')
    
    # Información de transferencia
    id_operacion = models.CharField(max_length=100, blank=True, help_text="ID de operación bancaria")
    validado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos_validados',
        help_text="Secretaria que validó el pago"
    )
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    
    # Información de Mercado Pago
    mercado_pago_id = models.CharField(max_length=100, blank=True, help_text="ID de preferencia/pago de Mercado Pago")
    mercado_pago_status = models.CharField(max_length=50, blank=True)
    
    # Tracking
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['estado', 'metodo_pago']),
            models.Index(fields=['cita', 'compra']),
        ]

    def __str__(self):
        return f"Pago {self.id} - ${self.monto} - {self.get_metodo_pago_display()}"
    
    def marcar_completado(self):
        """Marca el pago como completado"""
        from django.utils import timezone
        self.estado = 'completado'
        self.fecha_completado = timezone.now()
        self.save()
    
    def validar_transferencia(self, validado_por):
        """Valida un pago por transferencia"""
        if self.metodo_pago == 'transferencia' and self.id_operacion:
            self.validado_por = validado_por
            from django.utils import timezone
            self.fecha_validacion = timezone.now()
            self.marcar_completado()
            return True
        return False
