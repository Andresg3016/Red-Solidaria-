import os
from flask import Flask, render_template, request, redirect, url_for, session, flash # Añadido flash
from werkzeug.utils import secure_filename

# Controllers
from controllers.auth_controller import AuthController
from controllers.usuario_controller import UsuarioController
from controllers.donacion_controller import DonacionController
from controllers.home_administrador_controller import mostrar_home_administrador

# Inicializar app
app = Flask(__name__)
app.secret_key = "123456"

# Configuración subida de archivos
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Instancias de controllers
auth = AuthController()
usuario_ctrl = UsuarioController()
donacion_ctrl = DonacionController()

# ================= RUTAS DE AUTENTICACIÓN =================

import requests

# Esta función conecta Flask con el microservicio de Java
def enviar_al_correo_java(email, nombre, estado):
    url_java = "http://localhost:8080/api/email/enviar"
    datos = {
        "destinatario": email,
        "nombreFundacion": nombre,
        "estado": estado # PENDIENTE, APROBADO o RECHAZADO
    }
    try:
        response = requests.post(url_java, json=datos, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Error conectando con Java: {e}")
        return False

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
def donar():
    return donacion_ctrl.publicar_donacion_view(request, session)

# Acciones del Administrador sobre Fundaciones
# Acciones del Administrador sobre Fundaciones
@app.route("/aprobar/<int:id>")
def aprobar_fundacion_ruta(id):
    from controllers.home_administrador_controller import aprobar_fundacion_controller
    from models.usuario_model import UsuarioModel
    
    # 1. Buscamos los datos (correo y nombre) usando el ID que viene de la tabla
    modelo_usuario = UsuarioModel()
    datos = modelo_usuario.obtener_datos_aprobacion(id)
    
    if datos:
        correo = datos['correo']
        nombre = datos['nombre_fundacion']
        
        # 2. Ahora sí enviamos los 3 datos al controlador
        return aprobar_fundacion_controller(id, correo, nombre)
    
    flash("❌ No se pudieron obtener los datos de la fundación", "danger")
    return redirect(url_for('home_admin_panel'))

@app.route("/rechazar/<int:id>")
def rechazar_fundacion_ruta(id):
    from controllers.home_administrador_controller import rechazar_fundacion_controller
    # Aquí podrías hacer lo mismo si quieres enviar un correo de rechazo
    return rechazar_fundacion_controller(id)

# ================= RUTA SOLICITAR AYUDA (CONECTADA) =================

@app.route('/solicitar-ayuda', methods=['GET', 'POST'])
def solicitar_ayuda():
    # Borramos 'request' porque el controlador lo importa internamente
    return donacion_ctrl.solicitar_ayuda_view(session)
# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)