# pagos/urls.py
from django.urls import path
from . import views

app_name = 'pagos'

urlpatterns = [
    # Endpoints para clientes
    path('crear/', views.crear_pago, name='crear_pago'),
    path('historial/', views.historial_pagos, name='historial_pagos'),
    path('<int:pago_id>/', views.detalle_pago, name='detalle_pago'),
    
    # Endpoints para secretaria/admin
    path('listar/', views.listar_pagos, name='listar_pagos'),
    path('<int:pago_id>/validar-transferencia/', views.validar_transferencia, name='validar_transferencia'),
    
    # Webhooks
    path('webhook/mercado-pago/', views.webhook_mercado_pago, name='webhook_mercado_pago'),
]
