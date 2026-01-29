# pagos/services.py
"""
Servicios y lógica de negocio para el módulo de pagos
"""
from django.utils import timezone
from django.conf import settings
from pagos.models import Pago
from citas.models import Cita
from productos.models import OrdenCompra
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
Usuario = get_user_model()

# NOTA: La integración con Mercado Pago requiere las credenciales (ACCESS_TOKEN)
# que deben configurarse en las variables de entorno
# Por ahora, se implementa la estructura base


class PagosService:
    """Servicio para gestión de pagos"""
    
    @staticmethod
    def crear_preferencia_mercado_pago(monto, descripcion, referencia_externa=None):
        """
        Crea una preferencia de pago en Mercado Pago
        
        NOTA: Requiere configurar MERCADO_PAGO_ACCESS_TOKEN en settings
        
        Args:
            monto: Monto del pago
            descripcion: Descripción del pago
            referencia_externa: ID de referencia (ej: cita_id, compra_id)
        
        Returns:
            dict con preference_id y init_point, o None si hay error
        """
        try:
            # Intentar importar Mercado Pago SDK
            try:
                import mercadopago
            except ImportError:
                logger.warning("Mercado Pago SDK no instalado. Ejecutar: pip install mercadopago")
                return None
            
            # Obtener access token desde settings
            access_token = getattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN', None)
            
            if not access_token:
                logger.warning("MERCADO_PAGO_ACCESS_TOKEN no configurado en settings")
                return None
            
            # Crear instancia de SDK
            sdk = mercadopago.SDK(access_token)
            
            # Crear preferencia
            preference_data = {
                "items": [
                    {
                        "title": descripcion,
                        "quantity": 1,
                        "unit_price": float(monto)
                    }
                ],
                "back_urls": {
                    "success": getattr(settings, 'MERCADO_PAGO_SUCCESS_URL', 'http://localhost:4200/pago-exitoso'),
                    "failure": getattr(settings, 'MERCADO_PAGO_FAILURE_URL', 'http://localhost:4200/pago-fallido'),
                    "pending": getattr(settings, 'MERCADO_PAGO_PENDING_URL', 'http://localhost:4200/pago-pendiente'),
                },
                "auto_return": "approved",
                "external_reference": referencia_externa or "",
            }
            
            preference_response = sdk.preference().create(preference_data)
            
            if preference_response["status"] == 201:
                preference = preference_response["response"]
                return {
                    "preference_id": preference["id"],
                    "init_point": preference["init_point"],
                    "sandbox_init_point": preference.get("sandbox_init_point"),
                }
            else:
                logger.error(f"Error al crear preferencia Mercado Pago: {preference_response}")
                return None
                
        except Exception as e:
            logger.error(f"Error en crear_preferencia_mercado_pago: {str(e)}")
            return None
    
    @staticmethod
    def procesar_webhook_mercado_pago(data):
        """
        Procesa un webhook de Mercado Pago
        
        Args:
            data: Datos del webhook de Mercado Pago
        
        Returns:
            (exito: bool, mensaje: str, pago: Pago o None)
        """
        try:
            # Mercado Pago envía diferentes tipos de notificaciones
            tipo = data.get("type")
            data_obj = data.get("data", {})
            
            if tipo == "payment":
                payment_id = data_obj.get("id")
                
                # Buscar pago por mercado_pago_id
                try:
                    pago = Pago.objects.get(mercado_pago_id=payment_id)
                except Pago.DoesNotExist:
                    logger.warning(f"Pago no encontrado para payment_id: {payment_id}")
                    return False, "Pago no encontrado", None
                
                # Obtener información del pago desde Mercado Pago
                try:
                    import mercadopago
                    access_token = getattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN', None)
                    
                    if not access_token:
                        return False, "MERCADO_PAGO_ACCESS_TOKEN no configurado", None
                    
                    sdk = mercadopago.SDK(access_token)
                    payment_response = sdk.payment().get(payment_id)
                    
                    if payment_response["status"] == 200:
                        payment = payment_response["response"]
                        status = payment.get("status")
                        
                        # Actualizar estado del pago
                        pago.mercado_pago_status = status
                        
                        if status == "approved":
                            pago.marcar_completado()
                            # Si está asociado a una cita, actualizar anticipo
                            if pago.cita:
                                pago.cita.anticipo_pagado += pago.monto
                                pago.cita.estado = 'confirmada'
                                pago.cita.save()
                            # Si está asociado a una compra, confirmar pago
                            if pago.compra:
                                pago.compra.confirmar_pago()
                            
                            return True, "Pago aprobado", pago
                        elif status in ["rejected", "cancelled"]:
                            pago.estado = 'rechazado'
                            pago.save()
                            return True, "Pago rechazado", pago
                        elif status == "pending":
                            pago.estado = 'procesando'
                            pago.save()
                            return True, "Pago pendiente", pago
                        else:
                            return True, f"Estado: {status}", pago
                    else:
                        return False, "Error al obtener información del pago", None
                        
                except ImportError:
                    return False, "Mercado Pago SDK no instalado", None
                except Exception as e:
                    logger.error(f"Error al procesar webhook: {str(e)}")
                    return False, str(e), None
            else:
                return False, f"Tipo de notificación no manejado: {tipo}", None
                
        except Exception as e:
            logger.error(f"Error en procesar_webhook_mercado_pago: {str(e)}")
            return False, str(e), None
    
    @staticmethod
    def validar_transferencia_bancaria(pago, id_operacion, validado_por):
        """
        Valida un pago por transferencia bancaria
        
        NOTA: La integración específica con el banco está pendiente
        hasta que se defina qué banco utilizará el negocio.
        Por ahora, solo se valida manualmente por la secretaria.
        
        Args:
            pago: Objeto Pago
            id_operacion: ID de la operación bancaria
            validado_por: Usuario que valida (secretaria)
        
        Returns:
            (exito: bool, mensaje: str)
        """
        if pago.metodo_pago != 'transferencia':
            return False, 'El pago no es por transferencia'
        
        if pago.estado == 'completado':
            return False, 'El pago ya está completado'
        
        # Validar transferencia
        if pago.validar_transferencia(validado_por):
            pago.id_operacion = id_operacion
            pago.save()
            
            # Si está asociado a una cita, actualizar anticipo
            if pago.cita:
                pago.cita.anticipo_pagado += pago.monto
                pago.cita.estado = 'confirmada'
                pago.cita.save()
            
            # Si está asociado a una compra, confirmar pago
            if pago.compra:
                pago.compra.confirmar_pago()
            
            return True, 'Transferencia validada exitosamente'
        else:
            return False, 'Error al validar la transferencia'
    
    @staticmethod
    def crear_pago_anticipo_cita(cita, monto):
        """
        Crea un pago de anticipo para una cita
        
        Args:
            cita: Objeto Cita
            monto: Monto del anticipo
        
        Returns:
            Pago creado
        """
        pago = Pago.objects.create(
            cita=cita,
            cliente=cita.cliente,
            monto=monto,
            metodo_pago='pendiente',  # Se definirá después
            estado='pendiente',
            notas=f'Anticipo para cita #{cita.id}'
        )
        return pago
    
    @staticmethod
    def crear_pago_compra(compra, monto):
        """
        Crea un pago para una compra
        
        Args:
            compra: Objeto Compra
            monto: Monto del pago
        
        Returns:
            Pago creado
        """
        pago = Pago.objects.create(
            compra=compra,
            cliente=compra.cliente,
            monto=monto,
            metodo_pago='pendiente',  # Se definirá después
            estado='pendiente',
            notas=f'Pago para compra #{compra.id}'
        )
        return pago
