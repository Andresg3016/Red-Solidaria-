__all__ = ["UsuarioController"]
from models.usuario_model import UsuarioModel, Usuario

modelo = UsuarioModel()

class UsuarioController:
    def editar_perfil_view(self):
        from flask import session, render_template, request, redirect, url_for
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        if request.method == "POST":
            # Aquí puedes agregar la lógica para actualizar los datos del usuario
            # Por ahora solo redirige de vuelta
            return redirect(url_for("home_donador"))
        usuario = {"nombre": session.get("nombre")}
        return render_template("editar_perfil.html", usuario=usuario)

    def registrar(self, nombre, correo, password, rol_id):
        usuario = Usuario(
            nombre=nombre,
            correo=correo,
            password=password,
            rol_id=rol_id
        )
        modelo.crear_usuario(usuario)
        return True

    def registro_view(self):
        from flask import request, redirect, url_for, render_template
        if request.method == "POST":
            self.registrar(
                request.form["nombre"],
                request.form["correo"],
                request.form["password"],
                int(request.form["rol"])
            )
            return redirect(url_for("login"))
        return render_template("registro.html")

    def home_donador_view(self):
        from flask import session, redirect, url_for, render_template
        from models.donacion_model import DonacionModel
        if "rol" not in session:
            return redirect(url_for("login"))
        if session["rol"] != 3:
            return "Acceso no autorizado"
        usuario = {"nombre": session.get("nombre")}
        donaciones = DonacionModel().donaciones_por_usuario(session["usuario_id"])
        return render_template("home_donador.html", usuario=usuario, donaciones=donaciones)

    def home_fundacion_view(self):
        from flask import session, redirect, url_for, render_template
        if "rol" not in session:
            return redirect(url_for("login"))
        if session["rol"] != 2:
            return "Acceso no autorizado"
        return render_template("home_fundacion.html")

    def admin_panel_view(self):
        from flask import session, redirect, url_for, render_template
        if "rol" not in session:
            return redirect(url_for("login"))
        if session["rol"] != 1:
            return "Acceso no autorizado"
        return render_template("admin.html")

    def subir_foto(self, request, session, app):
        from flask import redirect, url_for
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        if "foto" not in request.files:
            return redirect(url_for("home_donador"))
        foto = request.files["foto"]
        if foto.filename == "":
            return redirect(url_for("home_donador"))
        filename = secure_filename(foto.filename)
        ruta = app.config["UPLOAD_FOLDER"]
        if not os.path.exists(ruta):
            os.makedirs(ruta)
        path_completo = os.path.join(ruta, filename)
        foto.save(path_completo)
        session["foto"] = filename
        return redirect(url_for("home_donador"))