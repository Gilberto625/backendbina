# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    ROL_CHOICES = [
        ('cliente', 'Cliente'),
        ('admin', 'Administrador'),
    ]
    
    telefono = models.CharField(max_length=15, blank=True)
    pregunta_secreta = models.CharField(max_length=255, blank=True)
    respuesta_secreta = models.CharField(max_length=255, blank=True)
    verificado = models.BooleanField(default=False)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='cliente')

    def __str__(self):
        return self.email
    
    @property
    def es_admin(self):
        return self.rol == 'admin'
    
    @property
    def es_cliente(self):
        return self.rol == 'cliente'


# ============================================
# MODELOS DE SERVICIOS
# ============================================
class Servicio(models.Model):
    CATEGORIA_CHOICES = [
        ('corte', 'Corte'),
        ('barba', 'Barba'),
        ('combo', 'Combo'),
        ('tratamiento', 'Tratamiento'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_minutos = models.IntegerField(default=30)
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default='corte')
    imagen_url = models.URLField(blank=True)  # URL de Cloudinary
    activo = models.BooleanField(default=True)
    popular = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio}"


# ============================================
# MODELOS DE PRODUCTOS
# ============================================
class Producto(models.Model):
    CATEGORIA_CHOICES = [
        ('cabello', 'Cabello'),
        ('barba', 'Barba'),
        ('accesorios', 'Accesorios'),
        ('kit', 'Kit'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default='cabello')
    stock = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=10)
    imagen_url = models.URLField(blank=True)
    activo = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    nuevo = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - Stock: {self.stock}"
    
    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo


# ============================================
# MODELOS DE CITAS
# ============================================
class Cita(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('en_curso', 'En Curso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('no_asistio', 'No Asistió'),
    ]
    
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='citas_cliente')
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    duracion_minutos = models.IntegerField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)
    notas = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha', '-hora']
    
    def __str__(self):
        return f"Cita {self.cliente.email} - {self.fecha} {self.hora}"


# ============================================
# MODELOS DE CONFIGURACIÓN
# ============================================
class ConfiguracionSistema(models.Model):
    nombre_negocio = models.CharField(max_length=100, default='Stylo Barber')
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email_contacto = models.EmailField(blank=True)
    horario_apertura = models.TimeField(default='09:00')
    horario_cierre = models.TimeField(default='20:00')
    porcentaje_anticipo = models.IntegerField(default=30)
    tiempo_espera_maximo = models.IntegerField(default=10, help_text='Minutos de espera máxima')
    citas_penalizacion = models.IntegerField(default=10, help_text='Citas requeridas para liberar penalización')
    
    class Meta:
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuración del Sistema'
    
    def __str__(self):
        return self.nombre_negocio