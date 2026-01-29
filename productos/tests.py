# productos/tests.py
from django.test import TestCase
from accounts.models import Usuario
from productos.models import Producto, Compra, OrdenCompra, OrdenCompraItem
from productos.services import ProductosService
from configuracion.models import ConfiguracionSistema


class ProductoModelTest(TestCase):
    """Tests para el modelo Producto"""
    
    def setUp(self):
        """Configuración inicial"""
        self.producto = Producto.objects.create(
            nombre='Cera para Cabello',
            descripcion='Cera profesional',
            precio=250.00,
            stock_actual=10,
            stock_minimo=5,
            activo=True
        )
    
    def test_tiene_stock(self):
        """Test: Verificar si tiene stock"""
        self.assertTrue(self.producto.tiene_stock(5))
        self.assertFalse(self.producto.tiene_stock(15))
    
    def test_stock_bajo(self):
        """Test: Verificar si el stock está bajo"""
        self.assertFalse(self.producto.stock_bajo())
        
        self.producto.stock_actual = 3
        self.producto.save()
        self.assertTrue(self.producto.stock_bajo())
    
    def test_reducir_stock(self):
        """Test: Reducir stock del producto"""
        stock_inicial = self.producto.stock_actual
        
        exito = self.producto.reducir_stock(3)
        
        self.assertTrue(exito)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, stock_inicial - 3)
    
    def test_aumentar_stock(self):
        """Test: Aumentar stock del producto"""
        stock_inicial = self.producto.stock_actual
        
        self.producto.aumentar_stock(5)
        
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, stock_inicial + 5)


class CompraModelTest(TestCase):
    """Tests para el modelo Compra"""
    
    def setUp(self):
        """Configuración inicial"""
        self.cliente = Usuario.objects.create_user(
            username='cliente@test.com',
            email='cliente@test.com',
            password='test123',
            rol='cliente'
        )
        self.producto = Producto.objects.create(
            nombre='Cera para Cabello',
            precio=250.00,
            stock_actual=10,
            activo=True
        )
    
    def test_crear_compra(self):
        """Test: Crear una compra"""
        compra = Compra.objects.create(
            cliente=self.cliente,
            producto=self.producto,
            cantidad=2,
            precio_unitario=250.00,
            precio_total=500.00,
            metodo_entrega='local',
            estado='apartado',
            registrado_por=self.cliente
        )
        
        self.assertEqual(compra.cliente, self.cliente)
        self.assertEqual(compra.producto, self.producto)
        self.assertEqual(compra.cantidad, 2)
        self.assertEqual(compra.estado, 'apartado')
    
    def test_confirmar_pago_reduce_stock(self):
        """Test: Confirmar pago reduce el stock"""
        compra = Compra.objects.create(
            cliente=self.cliente,
            producto=self.producto,
            cantidad=2,
            precio_unitario=250.00,
            precio_total=500.00,
            metodo_entrega='local',
            estado='apartado',
            registrado_por=self.cliente
        )
        
        stock_inicial = self.producto.stock_actual
        
        compra.confirmar_pago()
        
        self.assertTrue(compra.pagado)
        self.assertEqual(compra.estado, 'pagado')
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, stock_inicial - 2)


class ProductosServiceTest(TestCase):
    """Tests para el servicio de productos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.producto = Producto.objects.create(
            nombre='Cera para Cabello',
            precio=250.00,
            stock_actual=10,
            activo=True
        )
        
        # Crear configuración para costos de envío
        ConfiguracionSistema.objects.create(
            dia_semana=0,
            demanda='media',
            costo_moto_mandado=40.00,
            costo_paqueteria=150.00
        )
    
    def test_calcular_costo_envio_local(self):
        """Test: Calcular costo de envío local (gratis)"""
        costo = ProductosService.calcular_costo_envio('local')
        self.assertEqual(costo, 0)
    
    def test_calcular_costo_envio_moto(self):
        """Test: Calcular costo de envío moto mandado"""
        costo = ProductosService.calcular_costo_envio('moto_mandado')
        self.assertEqual(costo, 40.00)


class OrdenCompraModelTest(TestCase):
    """Tests para el modelo OrdenCompra (carrito)"""

    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            username='cliente2@test.com',
            email='cliente2@test.com',
            password='test123',
            rol='cliente'
        )
        self.p1 = Producto.objects.create(nombre='Pomada', precio=100.00, stock_actual=10, activo=True)
        self.p2 = Producto.objects.create(nombre='Shampoo', precio=50.00, stock_actual=10, activo=True)
        # Producto genérico para tests de servicio
        self.producto = Producto.objects.create(
            nombre='Cera para Cabello',
            precio=250.00,
            stock_actual=10,
            activo=True
        )
        # Configuración para costos de envío
        ConfiguracionSistema.objects.create(
            dia_semana=0,
            demanda='media',
            costo_moto_mandado=40.00,
            costo_paqueteria=150.00
        )

    def test_crear_orden_con_items(self):
        orden = OrdenCompra.objects.create(
            cliente=self.cliente,
            subtotal=200.00,
            costo_envio=0,
            total=200.00,
            metodo_entrega='local',
            estado='apartado',
            registrado_por=self.cliente
        )
        OrdenCompraItem.objects.create(orden=orden, producto=self.p1, cantidad=1, precio_unitario=100.00, subtotal=100.00)
        OrdenCompraItem.objects.create(orden=orden, producto=self.p2, cantidad=2, precio_unitario=50.00, subtotal=100.00)

        self.assertEqual(orden.items.count(), 2)
        self.assertEqual(float(orden.total), 200.00)

    def test_confirmar_pago_reduce_stock_items(self):
        orden = OrdenCompra.objects.create(
            cliente=self.cliente,
            subtotal=200.00,
            costo_envio=0,
            total=200.00,
            metodo_entrega='local',
            estado='apartado',
            registrado_por=self.cliente
        )
        OrdenCompraItem.objects.create(orden=orden, producto=self.p1, cantidad=1, precio_unitario=100.00, subtotal=100.00)
        OrdenCompraItem.objects.create(orden=orden, producto=self.p2, cantidad=2, precio_unitario=50.00, subtotal=100.00)

        stock1 = self.p1.stock_actual
        stock2 = self.p2.stock_actual

        orden.confirmar_pago()

        self.p1.refresh_from_db()
        self.p2.refresh_from_db()
        orden.refresh_from_db()

        self.assertTrue(orden.pagado)
        self.assertEqual(orden.estado, 'pagado')
        self.assertEqual(self.p1.stock_actual, stock1 - 1)
        self.assertEqual(self.p2.stock_actual, stock2 - 2)
    
    def test_verificar_stock_disponible(self):
        """Test: Verificar stock disponible"""
        disponible, mensaje = ProductosService.verificar_stock_disponible(self.producto, 5)
        self.assertTrue(disponible)
        self.assertIsNone(mensaje)
        
        disponible, mensaje = ProductosService.verificar_stock_disponible(self.producto, 15)
        self.assertFalse(disponible)
        self.assertIsNotNone(mensaje)
    
    def test_calcular_precio_total(self):
        """Test: Calcular precio total con envío"""
        precios = ProductosService.calcular_precio_total(self.producto, 2, 'moto_mandado')
        
        self.assertEqual(precios['precio_unitario'], 250.00)
        self.assertEqual(precios['precio_subtotal'], 500.00)
        self.assertEqual(precios['costo_envio'], 40.00)
        self.assertEqual(precios['precio_total'], 540.00)
