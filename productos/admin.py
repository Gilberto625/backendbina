from django.contrib import admin
from .models import Producto, Compra, OrdenCompra, OrdenCompraItem

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio', 'stock_actual', 'stock_minimo', 'activo']
    list_filter = ['categoria', 'activo']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['stock_actual', 'precio']

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'producto', 'cantidad', 'precio_total', 'estado', 'pagado', 'fecha_creacion']
    list_filter = ['estado', 'pagado', 'metodo_pago', 'metodo_entrega']
    search_fields = ['cliente__email', 'producto__nombre', 'id_pago_transferencia']
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


class OrdenCompraItemInline(admin.TabularInline):
    model = OrdenCompraItem
    extra = 0


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'total', 'estado', 'pagado', 'metodo_entrega', 'fecha_creacion']
    list_filter = ['estado', 'pagado', 'metodo_pago', 'metodo_entrega']
    search_fields = ['cliente__email', 'id_pago_transferencia']
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    inlines = [OrdenCompraItemInline]
