import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session
from controllers.auth_controller import AuthController
from controllers.usuario_controller import UsuarioController
from controllers.donacion_controller import DonacionController

app = Flask(__name__)
app.secret_key = "123456"



# Instancias de controllers
auth = AuthController()
usuario_ctrl = UsuarioController()
donacion_ctrl = DonacionController()

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session
from controllers.auth_controller import AuthController
from controllers.usuario_controller import UsuarioController
from controllers.donacion_controller import DonacionController

app = Flask(__name__)
app.secret_key = "123456"



# Instancias de controllers
auth = AuthController()
usuario_ctrl = UsuarioController()

UPLOAD_FOLDER = "static/uploads"

app = Flask(__name__)
app.secret_key = "123456"

# Instancias de controllers
auth = AuthController()
usuario_ctrl = UsuarioController()

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    return auth.login_view()

@app.route("/registro", methods=["GET", "POST"])
def registro():
    return usuario_ctrl.registro_view()

@app.route("/home_donador")
def home_donador():
    return usuario_ctrl.home_donador_view()

@app.route("/home_fundacion")
def home_fundacion():
    return usuario_ctrl.home_fundacion_view()

@app.route("/admin")
def admin_panel():
    return usuario_ctrl.admin_panel_view()

@app.route("/subir_foto", methods=["POST"])
def subir_foto():
    return usuario_ctrl.subir_foto(request, session, app)

@app.route("/editar_perfil", methods=["GET", "POST"])
def editar_perfil():
    return usuario_ctrl.editar_perfil_view()

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
@app.route("/donar", methods=["GET", "POST"])
def donar():
    return donacion_ctrl.publicar_donacion_view(request, session)

if __name__ == "__main__":
    app.run(debug=True)