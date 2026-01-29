# configuracion/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime, timedelta
import json

from core.decorators import (
    requiere_administrador,
    requiere_admin_o_secretaria,
)
from core.utils import (
    respuesta_exito,
    respuesta_error,
    obtener_usuario_desde_request,
)
from configuracion.models import ConfiguracionSistema
from configuracion.services import AdminService
from accounts.models import Usuario
from barberos.models import Barbero
from django.contrib.auth import get_user_model

UsuarioModel = get_user_model()


# ============================================
# ENDPOINTS DE ADMINISTRACIÓN
# ============================================

@csrf_exempt
@requiere_administrador
def metricas(request):
    """Obtiene métricas de negocio (solo admin)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        
        fecha_inicio = None
        fecha_fin = None
        
        if fecha_inicio_str:
            try:
                fecha_inicio = datetime.fromisoformat(fecha_inicio_str.replace('Z', '+00:00'))
                if timezone.is_naive(fecha_inicio):
                    fecha_inicio = timezone.make_aware(fecha_inicio)
            except ValueError:
                return respuesta_error('Formato de fecha_inicio inválido. Use ISO 8601')
        
        if fecha_fin_str:
            try:
                fecha_fin = datetime.fromisoformat(fecha_fin_str.replace('Z', '+00:00'))
                if timezone.is_naive(fecha_fin):
                    fecha_fin = timezone.make_aware(fecha_fin)
            except ValueError:
                return respuesta_error('Formato de fecha_fin inválido. Use ISO 8601')
        
        metricas_data = AdminService.calcular_metricas(fecha_inicio, fecha_fin)
        
        return respuesta_exito('Métricas obtenidas', {'metricas': metricas_data})
        
    except Exception as e:
        return respuesta_error('Error al obtener métricas', detalles=str(e))


@csrf_exempt
@requiere_administrador
def reportes_financieros(request):
    """Genera reportes financieros (solo admin)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')
        
        fecha_inicio = None
        fecha_fin = None
        
        if fecha_inicio_str:
            try:
                fecha_inicio = datetime.fromisoformat(fecha_inicio_str.replace('Z', '+00:00'))
                if timezone.is_naive(fecha_inicio):
                    fecha_inicio = timezone.make_aware(fecha_inicio)
            except ValueError:
                return respuesta_error('Formato de fecha_inicio inválido. Use ISO 8601')
        
        if fecha_fin_str:
            try:
                fecha_fin = datetime.fromisoformat(fecha_fin_str.replace('Z', '+00:00'))
                if timezone.is_naive(fecha_fin):
                    fecha_fin = timezone.make_aware(fecha_fin)
            except ValueError:
                return respuesta_error('Formato de fecha_fin inválido. Use ISO 8601')
        
        reporte = AdminService.generar_reporte_financiero(fecha_inicio, fecha_fin)
        
        return respuesta_exito('Reporte generado', {'reporte': reporte})
        
    except Exception as e:
        return respuesta_error('Error al generar reporte', detalles=str(e))


@csrf_exempt
@requiere_administrador
def clasificar_dia_demanda(request):
    """Clasifica un día de la semana por demanda (solo admin)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        data = json.loads(request.body)
        
        dia_semana = data.get('dia_semana')
        demanda = data.get('demanda')
        
        if dia_semana is None or not demanda:
            return respuesta_error('dia_semana y demanda son requeridos')
        
        try:
            dia_semana = int(dia_semana)
            if dia_semana < 0 or dia_semana > 6:
                return respuesta_error('dia_semana debe ser un número entre 0 (Lunes) y 6 (Domingo)')
        except (ValueError, TypeError):
            return respuesta_error('dia_semana debe ser un número válido')
        
        if demanda not in ['alta', 'media', 'baja']:
            return respuesta_error('demanda debe ser: alta, media o baja')
        
        # Obtener configuración adicional si se proporciona
        configuracion = data.get('configuracion', {})
        
        # Clasificar día
        config_obj = AdminService.clasificar_dia_semana(
            dia_semana=dia_semana,
            demanda=demanda,
            configuracion=configuracion
        )
        
        return respuesta_exito('Día clasificado exitosamente', {
            'configuracion': {
                'id': config_obj.id,
                'dia_semana': config_obj.dia_semana,
                'dia_semana_display': config_obj.get_dia_semana_display(),
                'demanda': config_obj.demanda,
                'demanda_display': config_obj.get_demanda_display(),
            }
        })
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al clasificar día', detalles=str(e))


@csrf_exempt
@requiere_administrador
def listar_empleados(request):
    """Lista todos los empleados (admin/secretaria/barbero) (solo admin)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        rol = request.GET.get('rol')  # Filtro opcional
        
        empleados = UsuarioModel.objects.filter(
            rol__in=['secretaria', 'barbero', 'administrador']
        )
        
        if rol:
            empleados = empleados.filter(rol=rol)
        
        empleados = empleados.order_by('rol', 'first_name', 'last_name', 'email')
        
        datos_empleados = []
        for emp in empleados:
            empleado_data = {
                'id': emp.id,
                'email': emp.email,
                'nombre': emp.get_full_name() or emp.email,
                'first_name': emp.first_name,
                'last_name': emp.last_name,
                'telefono': emp.telefono,
                'rol': emp.rol,
                'rol_display': emp.get_rol_display(),
                'activo': emp.activo,
                'fecha_registro': emp.fecha_registro.isoformat(),
            }
            
            # Si es barbero, agregar información del perfil
            if emp.rol == 'barbero':
                try:
                    barbero = emp.perfil_barbero
                    empleado_data['barbero_id'] = barbero.id
                    empleado_data['fecha_contratacion'] = barbero.fecha_contratacion.isoformat() if barbero.fecha_contratacion else None
                    empleado_data['especialidades'] = barbero.especialidades
                    empleado_data['barbero_activo'] = barbero.activo
                except:
                    pass
            
            datos_empleados.append(empleado_data)
        
        return respuesta_exito('Empleados obtenidos', {'empleados': datos_empleados})
        
    except Exception as e:
        return respuesta_error('Error al obtener empleados', detalles=str(e))


@csrf_exempt
@requiere_administrador
def crear_empleado(request):
    """Crea un nuevo empleado (solo admin)"""
    if request.method != 'POST':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        data = json.loads(request.body)
        
        email = data.get('email')
        password = data.get('password')
        rol = data.get('rol')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        telefono = data.get('telefono', '')
        
        if not email or not password or not rol:
            return respuesta_error('email, password y rol son requeridos')
        
        if rol not in ['secretaria', 'barbero', 'administrador']:
            return respuesta_error('rol debe ser: secretaria, barbero o administrador')
        
        # Verificar que el email no exista
        if UsuarioModel.objects.filter(email=email).exists():
            return respuesta_error('El email ya está registrado', codigo=409)
        
        # Crear usuario
        usuario = UsuarioModel.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            telefono=telefono,
            rol=rol,
            activo=True,
            verificado=True  # Los empleados se crean verificados
        )
        
        # Si es barbero, crear perfil de barbero
        if rol == 'barbero':
            from barberos.services import BarberosService
            fecha_contratacion = None
            if data.get('fecha_contratacion'):
                try:
                    fecha_contratacion = datetime.strptime(data['fecha_contratacion'], '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            BarberosService.crear_barbero_desde_usuario(
                usuario=usuario,
                fecha_contratacion=fecha_contratacion,
                especialidades=data.get('especialidades', '')
            )
        
        return respuesta_exito('Empleado creado exitosamente', {
            'empleado': {
                'id': usuario.id,
                'email': usuario.email,
                'nombre': usuario.get_full_name() or usuario.email,
                'rol': usuario.rol,
            }
        }, codigo=201)
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al crear empleado', detalles=str(e))


@csrf_exempt
@requiere_administrador
def actualizar_empleado(request, empleado_id):
    """Actualiza un empleado existente (solo admin)"""
    if request.method != 'PUT':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        try:
            empleado = UsuarioModel.objects.get(id=empleado_id)
        except UsuarioModel.DoesNotExist:
            return respuesta_error('Empleado no encontrado', codigo=404)
        
        # Solo se pueden actualizar empleados (no clientes)
        if empleado.rol == 'cliente':
            return respuesta_error('No se puede actualizar un cliente desde este endpoint', codigo=400)
        
        data = json.loads(request.body)
        
        # Actualizar campos permitidos
        if 'first_name' in data:
            empleado.first_name = data['first_name']
        if 'last_name' in data:
            empleado.last_name = data['last_name']
        if 'telefono' in data:
            empleado.telefono = data['telefono']
        if 'activo' in data:
            empleado.activo = data['activo']
        if 'password' in data and data['password']:
            empleado.set_password(data['password'])
        
        # Cambiar rol (con precaución)
        if 'rol' in data:
            nuevo_rol = data['rol']
            if nuevo_rol not in ['secretaria', 'barbero', 'administrador']:
                return respuesta_error('rol inválido')
            empleado.rol = nuevo_rol
        
        empleado.save()
        
        # Si es barbero, actualizar perfil si se proporciona
        if empleado.rol == 'barbero' and (data.get('especialidades') is not None or data.get('fecha_contratacion') is not None):
            try:
                barbero = empleado.perfil_barbero
                if 'especialidades' in data:
                    barbero.especialidades = data['especialidades']
                if 'fecha_contratacion' in data:
                    if data['fecha_contratacion']:
                        try:
                            barbero.fecha_contratacion = datetime.strptime(data['fecha_contratacion'], '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    else:
                        barbero.fecha_contratacion = None
                barbero.save()
            except:
                pass
        
        return respuesta_exito('Empleado actualizado exitosamente', {
            'empleado': {
                'id': empleado.id,
                'email': empleado.email,
                'nombre': empleado.get_full_name() or empleado.email,
                'rol': empleado.rol,
            }
        })
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al actualizar empleado', detalles=str(e))


@csrf_exempt
@requiere_administrador
def actualizar_configuracion(request):
    """Actualiza la configuración del sistema (solo admin)"""
    if request.method != 'PUT':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        data = json.loads(request.body)
        
        dia_semana = data.get('dia_semana')
        
        if dia_semana is None:
            return respuesta_error('dia_semana es requerido')
        
        try:
            dia_semana = int(dia_semana)
            if dia_semana < 0 or dia_semana > 6:
                return respuesta_error('dia_semana debe ser un número entre 0 y 6')
        except (ValueError, TypeError):
            return respuesta_error('dia_semana debe ser un número válido')
        
        try:
            config_obj = ConfiguracionSistema.objects.get(dia_semana=dia_semana)
        except ConfiguracionSistema.DoesNotExist:
            return respuesta_error('Configuración no encontrada para este día', codigo=404)
        
        # Actualizar campos permitidos
        if 'demanda' in data:
            if data['demanda'] not in ['alta', 'media', 'baja']:
                return respuesta_error('demanda debe ser: alta, media o baja')
            config_obj.demanda = data['demanda']
        
        if 'dias_anticipacion_alta' in data:
            config_obj.dias_anticipacion_alta = int(data['dias_anticipacion_alta'])
        if 'dias_anticipacion_media' in data:
            config_obj.dias_anticipacion_media = int(data['dias_anticipacion_media'])
        if 'dias_anticipacion_baja' in data:
            config_obj.dias_anticipacion_baja = int(data['dias_anticipacion_baja'])
        
        if 'dias_cancelacion_alta' in data:
            config_obj.dias_cancelacion_alta = int(data['dias_cancelacion_alta'])
        if 'dias_cancelacion_media' in data:
            config_obj.dias_cancelacion_media = int(data['dias_cancelacion_media'])
        if 'dias_cancelacion_baja' in data:
            config_obj.dias_cancelacion_baja = int(data['dias_cancelacion_baja'])
        
        if 'tiempo_espera_maximo' in data:
            config_obj.tiempo_espera_maximo = int(data['tiempo_espera_maximo'])
        
        if 'costo_moto_mandado' in data:
            config_obj.costo_moto_mandado = float(data['costo_moto_mandado'])
        if 'costo_paqueteria' in data:
            config_obj.costo_paqueteria = float(data['costo_paqueteria'])
        
        if 'porcentaje_anticipo_penalizado' in data:
            config_obj.porcentaje_anticipo_penalizado = float(data['porcentaje_anticipo_penalizado'])
        if 'citas_penalizadas' in data:
            config_obj.citas_penalizadas = int(data['citas_penalizadas'])
        
        config_obj.save()
        
        return respuesta_exito('Configuración actualizada exitosamente', {
            'configuracion': {
                'id': config_obj.id,
                'dia_semana': config_obj.dia_semana,
                'dia_semana_display': config_obj.get_dia_semana_display(),
                'demanda': config_obj.demanda,
                'demanda_display': config_obj.get_demanda_display(),
            }
        })
        
    except json.JSONDecodeError:
        return respuesta_error('JSON inválido')
    except Exception as e:
        return respuesta_error('Error al actualizar configuración', detalles=str(e))


@csrf_exempt
@requiere_administrador
def obtener_configuracion(request):
    """Obtiene la configuración del sistema (solo admin)"""
    if request.method != 'GET':
        return respuesta_error('Método no permitido', codigo=405)
    
    try:
        dia_semana = request.GET.get('dia_semana')
        
        if dia_semana is not None:
            try:
                dia_semana = int(dia_semana)
                configs = [ConfiguracionSistema.objects.get(dia_semana=dia_semana)]
            except (ValueError, TypeError):
                return respuesta_error('dia_semana debe ser un número válido')
            except ConfiguracionSistema.DoesNotExist:
                return respuesta_error('Configuración no encontrada', codigo=404)
        else:
            configs = ConfiguracionSistema.objects.all().order_by('dia_semana')
        
        datos_configs = [{
            'id': c.id,
            'dia_semana': c.dia_semana,
            'dia_semana_display': c.get_dia_semana_display(),
            'demanda': c.demanda,
            'demanda_display': c.get_demanda_display(),
            'dias_anticipacion_alta': c.dias_anticipacion_alta,
            'dias_anticipacion_media': c.dias_anticipacion_media,
            'dias_anticipacion_baja': c.dias_anticipacion_baja,
            'dias_cancelacion_alta': c.dias_cancelacion_alta,
            'dias_cancelacion_media': c.dias_cancelacion_media,
            'dias_cancelacion_baja': c.dias_cancelacion_baja,
            'tiempo_espera_maximo': c.tiempo_espera_maximo,
            'costo_moto_mandado': float(c.costo_moto_mandado),
            'costo_paqueteria': float(c.costo_paqueteria),
            'porcentaje_anticipo_penalizado': float(c.porcentaje_anticipo_penalizado),
            'citas_penalizadas': c.citas_penalizadas,
        } for c in configs]
        
        return respuesta_exito('Configuración obtenida', {'configuracion': datos_configs})
        
    except Exception as e:
        return respuesta_error('Error al obtener configuración', detalles=str(e))
