# productos/services.py
"""
Servicios y lógica de negocio para el módulo de productos
"""
from django.utils import timezone
from productos.models import Producto, Compra
from configuracion.models import ConfiguracionSistema
from django.contrib.auth import get_user_model
from django.db import transaction

Usuario = get_user_model()


class ProductosService:
    """Servicio para validaciones y lógica de negocio de productos"""
    
    @staticmethod
    def calcular_costo_envio(metodo_entrega):
        """
        Calcula el costo de envío según el método de entrega
        """
        config = ConfiguracionSistema.objects.first()
        
        if not config:
            # Valores por defecto
            costos = {
                'local': 0,
                'moto_mandado': 40.00,
                'paqueteria': 150.00,
            }
        else:
            costos = {
                'local': 0,
                'moto_mandado': float(config.costo_moto_mandado),
                'paqueteria': float(config.costo_paqueteria),
            }
        
        return costos.get(metodo_entrega, 0)
    
    @staticmethod
    def verificar_stock_disponible(producto, cantidad):
        """
        Verifica si hay stock suficiente para una compra
        
        Returns:
            (disponible: bool, mensaje: str)
        """
        if not producto.activo:
            return False, 'El producto no está disponible'
        
        if producto.stock_actual < cantidad:
            return False, f'Stock insuficiente. Disponible: {producto.stock_actual}, Solicitado: {cantidad}'
        
        return True, None
    
    @staticmethod
    def calcular_precio_total(producto, cantidad, metodo_entrega='local'):
        """
        Calcula el precio total de una compra incluyendo envío
        """
        precio_subtotal = float(producto.precio) * cantidad
        costo_envio = ProductosService.calcular_costo_envio(metodo_entrega)
        precio_total = precio_subtotal + costo_envio
        
        return {
            'precio_unitario': float(producto.precio),
            'precio_subtotal': precio_subtotal,
            'costo_envio': costo_envio,
            'precio_total': precio_total,
        }

    @staticmethod
    def calcular_precio_carrito(items, metodo_entrega='local'):
        """
        Calcula totales de un carrito:
        items: lista de dicts [{'producto': Producto, 'cantidad': int}]
        """
        subtotal = 0.0
        for it in items:
            subtotal += float(it['producto'].precio) * int(it['cantidad'])
        costo_envio = ProductosService.calcular_costo_envio(metodo_entrega)
        total = subtotal + costo_envio
        return {
            'subtotal': subtotal,
            'costo_envio': costo_envio,
            'total': total,
        }

    @staticmethod
    def verificar_stock_carrito(items):
        """
        Verifica stock para un carrito.
        items: lista de dicts [{'producto': Producto, 'cantidad': int}]
        """
        for it in items:
            producto = it['producto']
            cantidad = int(it['cantidad'])
            disponible, mensaje = ProductosService.verificar_stock_disponible(producto, cantidad)
            if not disponible:
                return False, mensaje
        return True, None
    
    @staticmethod
    def obtener_productos_bajo_stock():
        """
        Obtiene todos los productos con stock bajo
        """
        productos = Producto.objects.filter(activo=True)
        productos_bajo_stock = [p for p in productos if p.stock_bajo()]
        return productos_bajo_stock
    
    @staticmethod
    def procesar_compra(compra):
        """
        Procesa una compra: valida stock y reduce inventario si está pagada
        """
        # Verificar stock
        disponible, mensaje = ProductosService.verificar_stock_disponible(
            compra.producto, compra.cantidad
        )
        
        if not disponible:
            return False, mensaje
        
        # Si ya está pagada, reducir stock
        if compra.pagado and compra.estado == 'pagado':
            if not compra.producto.reducir_stock(compra.cantidad):
                return False, 'Error al reducir stock'
        
        return True, None
    
    @staticmethod
    def cancelar_compra(compra):
        """
        Cancela una compra y restaura el stock si ya se había reducido
        """
        if compra.estado == 'cancelado':
            return False, 'La compra ya está cancelada'
        
        # Si ya se había reducido el stock (estado pagado o superior), restaurarlo
        if compra.pagado and compra.estado in ['pagado', 'enviado', 'entregado']:
            compra.producto.aumentar_stock(compra.cantidad)
        
        compra.estado = 'cancelado'
        compra.save()
        
        return True, None
