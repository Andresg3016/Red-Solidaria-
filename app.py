import os
import json  # AGREGADO
import requests
from datetime import date, datetime # AGREGADO
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

# Controllers
from controllers.auth_controller import AuthController
from controllers.usuario_controller import UsuarioController
from controllers.donacion_controller import DonacionController
from controllers.home_administrador_controller import mostrar_home_administrador

# ================= FUNCIONES DE UTILIDAD (COLOCAR AQUÍ) =================

def serializar_datos(obj):
    """Convierte fechas de MySQL a texto para que Java las entienda."""
    if isinstance(obj, (date, datetime)):
        return obj.strftime('%Y-%m-%d')
    return str(obj)

# ================= CONFIGURACIÓN APP =================


app = Flask(__name__)
app.secret_key = "123456"

# ================= RUTA PARA GESTIONAR DONACIONES (ACEPTAR/RECHAZAR) =================
@app.route("/gestionar_donacion", methods=["POST"])
def gestionar_donacion():
    from models.donacion_model import DonacionModel
    if "usuario_id" not in session or int(session.get("rol")) != 3:
        flash("Acceso no autorizado", "danger")
        return redirect(url_for("home_fundacion"))
    donacion_id = request.form.get("donacion_id")
    accion = request.form.get("accion")
    if not donacion_id or accion not in ["aceptar", "rechazar"]:
        flash("Solicitud inválida", "danger")
        return redirect(url_for("home_fundacion"))
    nuevo_estado = "aceptada" if accion == "aceptar" else "rechazada"
    # Actualizar estado en la tabla intermedia donaciones_fundaciones
    conn = None
    try:
        conn = __import__('database.db').db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE donaciones_fundaciones SET estado = %s WHERE donacion_id = %s AND fundacion_id = (SELECT id FROM fundaciones WHERE usuario_id = %s)",
                       (nuevo_estado, donacion_id, session["usuario_id"]))
        conn.commit()
        if accion == "aceptar":
            flash("✅ Donación recibida correctamente.", "success")
        else:
            flash("❌ Donación rechazada correctamente.", "danger")
    except Exception as e:
        print(f"Error al actualizar estado de donación: {e}")
        flash("Error al actualizar el estado de la donación.", "danger")
    finally:
        if conn:
            conn.close()
    return redirect(url_for("home_fundacion"))

# Configuración subida de archivos
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Instancias de controllers
auth = AuthController()
usuario_ctrl = UsuarioController()
donacion_ctrl = DonacionController()

# ================= FUNCIONES DE COMUNICACIÓN CON JAVA =================

def enviar_al_correo_java(email, nombre, estado):
    url_java = "http://localhost:8080/api/email/enviar"
    datos = {
        "destinatario": email,
        "nombreFundacion": nombre,
        "estado": estado 
    }
    try:
        response = requests.post(url_java, json=datos, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Error conectando con Java: {e}")
        return False

# NUEVA FUNCIÓN PARA EL PDF (REPORTES)
def enviar_reporte_pdf_java(payload):
    url_java = "http://localhost:8080/api/email/enviar-reporte"
    try:
        # Aquí usamos la función serializar_datos para limpiar las fechas
        datos_limpios = json.loads(json.dumps(payload, default=serializar_datos))
        response = requests.post(url_java, json=datos_limpios, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error enviando PDF a Java: {e}")
        return False

# ================= RUTAS DE AUTENTICACIÓN =================

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    return auth.login_view()

@app.route("/registro", methods=["GET", "POST"])
def registro():
    return usuario_ctrl.registro_view()

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= RUTAS DE USUARIO / ROLES =================

@app.route("/home_donador")
def home_donador():
    return usuario_ctrl.home_donador_view()

@app.route("/home_fundacion")
def home_fundacion():
    # El controlador 'home_fundacion_view' ya debe manejar la lógica 
    # de llamar a enviar_reporte_pdf_java si detecta 'accion=reporte'
    return usuario_ctrl.home_fundacion_view()

@app.route("/admin")
def admin_panel():
    return usuario_ctrl.admin_panel_view()

@app.route("/home_administrador")
def home_admin_panel():
    return mostrar_home_administrador()

# ================= RUTAS DE ACCIONES =================

@app.route("/subir_foto", methods=["POST"])
def subir_foto():
    return usuario_ctrl.subir_foto(request, session, app)

@app.route("/editar_perfil", methods=["GET", "POST"])
def editar_perfil():
    return usuario_ctrl.editar_perfil_view()

@app.route("/donar", methods=["GET", "POST"])
@app.route("/donar/<int:necesidad_id>", methods=["GET", "POST"])
def donar(necesidad_id=None):
    return donacion_ctrl.publicar_donacion_view(request, session, necesidad_id)

@app.route("/aprobar/<int:id>")
def aprobar_fundacion_ruta(id):
    from controllers.home_administrador_controller import aprobar_fundacion_controller
    from models.usuario_model import UsuarioModel
    modelo_usuario = UsuarioModel()
    datos = modelo_usuario.obtener_datos_aprobacion(id)
    if datos:
        return aprobar_fundacion_controller(id, datos['correo'], datos['nombre'])
    flash("❌ No se pudieron obtener los datos de la fundación", "danger")
    return redirect(url_for('home_admin_panel'))

@app.route("/rechazar/<int:id>")
def rechazar_fundacion_ruta(id):
    from controllers.home_administrador_controller import rechazar_fundacion_controller
    from models.usuario_model import UsuarioModel
    modelo_usuario = UsuarioModel()
    datos = modelo_usuario.obtener_datos_aprobacion(id)
    if datos:
        return rechazar_fundacion_controller(id, datos['correo'], datos['nombre'])

@app.route('/solicitar-ayuda', methods=['GET', 'POST'])
def solicitar_ayuda():
    return donacion_ctrl.solicitar_ayuda_view(session)

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
