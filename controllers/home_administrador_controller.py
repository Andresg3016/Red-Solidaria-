from flask import render_template, redirect, url_for, flash, request
import requests  # Importante para conectar con el microservicio de Java

# --- MOSTRAR PANEL DEL ADMINISTRADOR ---
def mostrar_home_administrador():
    """
    Obtiene la lista de fundaciones pendientes y el conteo para mostrar en el dashboard.
    """
    from models.home_administrador_model import HomeAdminModel
    
    # Obtenemos los datos desde el modelo
    fundaciones = HomeAdminModel.obtener_fundaciones_pendientes()
    total_pendientes = HomeAdminModel.contar_pendientes()
    
    print(f"DEBUG: Mostrando panel admin. Fundaciones pendientes: {len(fundaciones)}") 

    return render_template(
        "home_administrador.html",
        fundaciones=fundaciones,
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

    # Redirigimos a la ruta que definiste en app.py para el panel del admin
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
