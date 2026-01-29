# productos/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.db import transaction

# Categorías de productos
CATEGORIA_PRODUCTO_CHOICES = [
    ('cera', 'Cera para Cabello'),
    ('shampoo', 'Shampoo'),
    ('acondicionador', 'Acondicionador'),
    ('pomada', 'Pomada'),
    ('aceite_barba', 'Aceite para Barba'),
    ('tratamiento', 'Tratamiento Capilar'),
    ('otro', 'Otro'),
]

# Métodos de entrega
METODO_ENTREGA_CHOICES = [
    ('local', 'Recoger en Local'),
    ('moto_mandado', 'Moto Mandado Regional'),
    ('paqueteria', 'Paquetería Nacional'),
]

class Producto(models.Model):
    """Productos físicos que se venden en la barbería"""
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    categoria = models.CharField(max_length=50, choices=CATEGORIA_PRODUCTO_CHOICES, default='otro')
    
    # Stock
    stock_actual = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stock_minimo = models.IntegerField(default=5, help_text="Stock mínimo antes de alertar")
    
    # Imagen (URL por ahora, después se puede usar ImageField)
    imagen_url = models.URLField(blank=True)
    
    # Estado
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['categoria', 'nombre']
        indexes = [
            models.Index(fields=['categoria', 'activo']),
            models.Index(fields=['stock_actual']),
        ]

    def __str__(self):
        return f"{self.nombre} - Stock: {self.stock_actual}"
    
    def tiene_stock(self, cantidad=1):
        """Verifica si hay stock suficiente"""
        return self.stock_actual >= cantidad
    
    def stock_bajo(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock_actual <= self.stock_minimo
    
    def reducir_stock(self, cantidad):
        """Reduce el stock del producto"""
        if self.stock_actual >= cantidad:
            self.stock_actual -= cantidad
            self.save()
            return True
        return False
    
    def aumentar_stock(self, cantidad):
        """Aumenta el stock del producto (entrada de mercancía)"""
        self.stock_actual += cantidad
        self.save()

class Compra(models.Model):
    """Compra o apartado de productos por un cliente"""
    cliente = models.ForeignKey('accounts.Usuario', on_delete=models.CASCADE, related_name='compras')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Método de entrega
    metodo_entrega = models.CharField(max_length=20, choices=METODO_ENTREGA_CHOICES, default='local')
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    direccion_entrega = models.TextField(blank=True, help_text="Dirección si es envío")
    
    # Estado
    estado = models.CharField(
        max_length=20,
        choices=[
            ('apartado', 'Apartado'),
            ('pagado', 'Pagado'),
            ('enviado', 'Enviado'),
            ('entregado', 'Entregado'),
            ('cancelado', 'Cancelado'),
        ],
        default='apartado'
    )
    
    # Pago
    pagado = models.BooleanField(default=False)
    metodo_pago = models.CharField(
        max_length=20,
        choices=[
            ('efectivo', 'Efectivo'),
            ('tarjeta', 'Tarjeta'),
            ('transferencia', 'Transferencia'),
            ('mercado_pago', 'Mercado Pago'),
        ],
        blank=True
    )
    id_pago_transferencia = models.CharField(max_length=100, blank=True, help_text="ID de operación bancaria")
    pago_validado = models.BooleanField(default=False, help_text="Validado por secretaria")
    
    # Tracking
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    
    # Registrado por
    registrado_por = models.ForeignKey(
        'accounts.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='compras_registradas',
        help_text="Usuario que registró la compra (secretaria o cliente)"
    )
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['estado', 'pagado']),
        ]

    def __str__(self):
        return f"Compra {self.id} - {self.cliente.email} - {self.producto.nombre}"
    
    def confirmar_pago(self):
        """Confirma el pago y reduce el stock"""
        if not self.pagado:
            self.pagado = True
            self.estado = 'pagado'
            self.producto.reducir_stock(self.cantidad)
            self.save()
            return True
        return False
    
    def validar_transferencia(self, validado_por):
        """Valida un pago por transferencia"""
        if self.metodo_pago == 'transferencia' and self.id_pago_transferencia:
            self.pago_validado = True
            self.confirmar_pago()
            self.registrado_por = validado_por
            self.save()
            return True
        return False


# ============================================================
# NUEVO: COMPRA POR CARRITO (ORDEN + ITEMS)
# ============================================================

class OrdenCompra(models.Model):
    """
    Orden de compra (carrito) con múltiples items.
    Mantiene compatibilidad con endpoints actuales (crear-compra, mis-compras, etc.).
    """
    cliente = models.ForeignKey('accounts.Usuario', on_delete=models.CASCADE, related_name='ordenes_compra')

    # Totales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Método de entrega
    metodo_entrega = models.CharField(max_length=20, choices=METODO_ENTREGA_CHOICES, default='local')
    direccion_entrega = models.TextField(blank=True, help_text="Dirección si es envío")

    # Estado
    estado = models.CharField(
        max_length=20,
        choices=[
            ('apartado', 'Apartado'),
            ('pagado', 'Pagado'),
            ('enviado', 'Enviado'),
            ('entregado', 'Entregado'),
            ('cancelado', 'Cancelado'),
        ],
        default='apartado'
    )

    # Pago
    pagado = models.BooleanField(default=False)
    metodo_pago = models.CharField(
        max_length=20,
        choices=[
            ('efectivo', 'Efectivo'),
            ('tarjeta', 'Tarjeta'),
            ('transferencia', 'Transferencia'),
            ('mercado_pago', 'Mercado Pago'),
        ],
        blank=True
    )
    id_pago_transferencia = models.CharField(max_length=100, blank=True, help_text="ID de operación bancaria")
    pago_validado = models.BooleanField(default=False, help_text="Validado por secretaria")

    # Tracking
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)

    # Registrado por
    registrado_por = models.ForeignKey(
        'accounts.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='ordenes_compra_registradas',
        help_text="Usuario que registró la compra (secretaria o cliente)"
    )
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Orden de compra'
        verbose_name_plural = 'Órdenes de compra'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['estado', 'pagado']),
        ]

    def __str__(self):
        return f"Orden {self.id} - {self.cliente.email} - Total: {self.total}"

    def recalcular_totales(self):
        items = list(self.items.all())
        subtotal = sum([float(i.subtotal) for i in items]) if items else 0
        self.subtotal = subtotal
        self.total = float(self.subtotal) + float(self.costo_envio)
        self.save(update_fields=['subtotal', 'total'])

    def confirmar_pago(self):
        """Confirma el pago y reduce el stock de todos los items"""
        if self.pagado:
            return False
        with transaction.atomic():
            for item in self.items.select_related('producto').all():
                item.producto.reducir_stock(item.cantidad)
            self.pagado = True
            self.estado = 'pagado'
            self.save(update_fields=['pagado', 'estado'])
        return True

    def validar_transferencia(self, validado_por):
        """Valida un pago por transferencia"""
        if self.metodo_pago == 'transferencia' and self.id_pago_transferencia:
            self.pago_validado = True
            self.confirmar_pago()
            self.registrado_por = validado_por
            self.save(update_fields=['pago_validado', 'registrado_por'])
            return True
        return False


class OrdenCompraItem(models.Model):
    """Item de una orden de compra"""
    orden = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item de orden'
        verbose_name_plural = 'Items de orden'

    def __str__(self):
        return f"Orden {self.orden_id} - {self.producto.nombre} x{self.cantidad}"
