# productos/urls.py
from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    # Endpoints públicos
    path('', views.listar_productos, name='listar_productos'),
    path('<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('<int:producto_id>/stock/', views.consultar_stock, name='consultar_stock'),
    
    # Endpoints para clientes
    path('crear-compra/', views.crear_compra, name='crear_compra'),
    path('mis-compras/', views.mis_compras, name='mis_compras'),
    path('compras/<int:compra_id>/', views.detalle_compra, name='detalle_compra'),
    path('compras/<int:compra_id>/cancelar/', views.cancelar_compra, name='cancelar_compra'),
    
    # Endpoints para admin
    path('crear/', views.crear_producto, name='crear_producto'),
    path('<int:producto_id>/actualizar/', views.actualizar_producto, name='actualizar_producto'),
    path('<int:producto_id>/stock/actualizar/', views.actualizar_stock, name='actualizar_stock'),
    path('<int:producto_id>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    
    # Endpoints para secretaria/admin
    path('compras/', views.listar_compras, name='listar_compras'),
    path('compras/<int:compra_id>/validar-pago/', views.validar_pago_compra, name='validar_pago_compra'),
    path('stock-bajo/', views.productos_bajo_stock, name='productos_bajo_stock'),
]
