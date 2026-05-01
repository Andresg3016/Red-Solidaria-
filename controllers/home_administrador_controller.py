
from flask import render_template, redirect, url_for, flash, request
import requests  # Importante para conectar con el microservicio de Java
from models.usuario_model import UsuarioModel
from models.home_administrador_model import HomeAdminModel
# ...existing code...
def mostrar_home_administrador():
    modelo = UsuarioModel()
    donantes = modelo.obtener_donantes()
    fundaciones_pendientes = HomeAdminModel.obtener_fundaciones_pendientes()
    fundaciones_aprobadas = HomeAdminModel.obtener_fundaciones_aprobadas()
    fundaciones_rechazadas = HomeAdminModel.obtener_fundaciones_rechazadas()
    total_fundaciones = (
        len(fundaciones_pendientes) +
        len(fundaciones_aprobadas) +
        len(fundaciones_rechazadas)
    )
    total_pendientes = len(fundaciones_pendientes)  # <-- Esto es clave

    return render_template(
        "home_administrador.html",
        donantes=donantes,
        fundaciones_pendientes=fundaciones_pendientes,
        fundaciones_aprobadas=fundaciones_aprobadas,
        fundaciones_rechazadas=fundaciones_rechazadas,
        total_fundaciones=total_fundaciones,
        total_pendientes=total_pendientes
    )

# --- APROBAR FUNDACIÓN Y NOTIFICAR POR CORREO ---
def aprobar_fundacion_controller(id_fundacion, correo_fundacion, nombre_fundacion):
    """
    Cambia el estado de la fundación en MySQL y envía la orden a Java para el email.
    """
    from models.home_administrador_model import HomeAdminModel
    
    print(f"DEBUG: Procesando aprobación para ID: {id_fundacion}, Email: {correo_fundacion}")

    # 1. Intentamos actualizar el estado en la Base de Datos MySQL
    if HomeAdminModel.aprobar_fundacion(id_fundacion):
        
        # 2. Si la DB se actualizó con éxito, intentamos hablar con Java (Spring Boot)
        try:
            url_java = "http://localhost:8080/api/email/enviar"
            payload = {
                "destinatario": correo_fundacion,
                "nombreFundacion": nombre_fundacion,
                "estado": "APROBADO"
            }
            
            # Enviamos el JSON a Java
            response = requests.post(url_java, json=payload, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Notificación enviada exitosamente a Java para: {correo_fundacion}")
                flash(f"✅ Fundación '{nombre_fundacion}' aprobada y correo enviado.", "success")
            else:
                print(f"⚠️ Java respondió con código: {response.status_code}")
                flash("✅ Fundación aprobada, pero hubo un problema con el servidor de correos.", "warning")
                
        except Exception as e:
            print(f"❌ Error crítico conectando con Java: {e}")
            flash("✅ Fundación aprobada, pero no se pudo conectar con el servicio de notificaciones.", "warning")
    else:
        flash("❌ Error técnico: No se pudo actualizar el estado en la base de datos.", "danger")

    # Redirigimos a la ruta correcta del panel admin
    return redirect(url_for("home_admin_panel"))
    return redirect(url_for('home_admin_panel'))

# --- RECHAZAR FUNDACIÓN ---

def rechazar_fundacion_controller(id_fundacion, correo_fundacion=None, nombre_fundacion=None):
    from models.home_administrador_model import HomeAdminModel  
   
    if HomeAdminModel.rechazar_fundacion(id_fundacion):        
      
        if correo_fundacion:
            try:
                url_java = "http://localhost:8080/api/email/enviar"
                payload = {
                    "destinatario": correo_fundacion,
                    "nombreFundacion": nombre_fundacion,
                    "estado": "RECHAZADO" # Esto activará el color ROJO y el mensaje de rechazo en Java
                }
                import requests
                requests.post(url_java, json=payload, timeout=5)
                print(f"❌ Notificación de RECHAZO enviada a {correo_fundacion}")
            except Exception as e:
                print(f"⚠️ Error avisando rechazo a Java: {e}")

        from flask import flash, redirect, url_for
        flash("La solicitud ha sido rechazada y el correo enviado.", "info")
    else:
        flash("Error al procesar el rechazo en la base de datos.", "danger")

    return redirect(url_for('home_admin_panel'))

from flask import jsonify
# --- API REST para aprobar fundación ---
def get_fundacion_info(fundacion_id):
    # Busca correo y nombre de la fundación
    from database.db import get_connection
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT f.id, f.nombre, f.nit, f.estado_validacion, u.correo
                FROM fundaciones f
                INNER JOIN usuarios u ON f.usuario_id = u.id
                WHERE f.id = %s
            """, (fundacion_id,))
            return cursor.fetchone()
    except Exception as ex:
        print(f"Error buscando fundación: {ex}")
        return None
    finally:
        if connection:
            connection.close()

from flask import Blueprint, request
api_admin = Blueprint('api_admin', __name__)

@api_admin.route('/aprobar_fundacion/<int:id>', methods=['POST'])
def api_aprobar_fundacion(id):
    info = get_fundacion_info(id)
    exito = HomeAdminModel.aprobar_fundacion(id)
    correo = info['correo'] if info else None
    nombre = info['nombre'] if info else None
    # Enviar correo si hay datos
    if exito and correo and nombre:
        try:
            url_java = "http://localhost:8080/api/email/enviar"
            payload = {
                "destinatario": correo,
                "nombreFundacion": nombre,
                "estado": "APROBADO"
            }
            requests.post(url_java, json=payload, timeout=5)
        except Exception as e:
            print(f"Error enviando correo aprobación: {e}")
    return jsonify(success=exito)

@api_admin.route('/rechazar_fundacion/<int:id>', methods=['POST'])
def api_rechazar_fundacion(id):
    info = get_fundacion_info(id)
    exito = HomeAdminModel.rechazar_fundacion(id)
    correo = info['correo'] if info else None
    nombre = info['nombre'] if info else None
    if exito and correo and nombre:
        try:
            url_java = "http://localhost:8080/api/email/enviar"
            payload = {
                "destinatario": correo,
                "nombreFundacion": nombre,
                "estado": "RECHAZADO",
                "mensaje": "Agradecemos su interés en nuestra plataforma. Tras revisar su solicitud, le informamos que el registro no pudo ser aprobado debido a inconsistencias en la validación de los datos suministrados.\n\nLe sugerimos realizar un nuevo registro verificando que toda la información legal de la organización coincida con sus documentos oficiales."
            }
            requests.post(url_java, json=payload, timeout=5)
        except Exception as e:
            print(f"Error enviando correo rechazo: {e}")
    return jsonify(success=exito)