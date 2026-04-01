from models.usuario_model import UsuarioModel

modelo = UsuarioModel()

class AuthController:

    def login(self, correo, password):
        usuario = modelo.obtener_usuario_por_correo(correo)
        if not usuario:
            return None, "Usuario no existe"
        if usuario.password != password:
            return None, "Contraseña incorrecta"
        if usuario.estado != "aprobado":
            return None, "Cuenta pendiente de aprobación"
        return usuario, None

    def login_view(self):
        from flask import request, session, redirect, url_for, render_template
        if request.method == "POST":
            correo = request.form["correo"]
            password = request.form["password"]
            usuario, error = self.login(correo, password)
            if error:
                return error
            session["usuario_id"] = usuario.id
            session["rol"] = usuario.rol_id
            session["nombre"] = usuario.nombre
            if usuario.rol_id == 3:
                return redirect(url_for("home_donador"))
            elif usuario.rol_id == 2:
                return redirect(url_for("home_fundacion"))
            elif usuario.rol_id == 1:
                return redirect(url_for("admin_panel"))
        return render_template("login.html")