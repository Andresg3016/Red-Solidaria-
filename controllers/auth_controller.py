from models.usuario_model import UsuarioModel

# Instancia global del modelo para uso en el controlador
modelo = UsuarioModel()

class AuthController:

    def login(self, correo, password):
        usuario = modelo.obtener_usuario_por_correo(correo)
        
        if not usuario:
            return None, "Usuario no existe"
            
        # CORCHETES AQUÍ
        if usuario['password'] != password:
            return None, "Contraseña incorrecta"
            
        # CORCHETES AQUÍ
        estado = usuario['estado'].lower()
        if estado not in ["activo", "aprobado", "pendiente"]:
            return None, "Cuenta no autorizada"
            
        return usuario, None

    def login_view(self):
        from flask import request, session, redirect, url_for, render_template, flash
        
        if request.method == "POST":
            correo = request.form["correo"]
            password = request.form["password"]
            
            usuario, error = self.login(correo, password)
            
            if error:
                flash(error, "danger") 
                return render_template("login.html")
                
            # --- CORRECCIÓN AQUÍ: TODO CON CORCHETES ---
            session["usuario_id"] = usuario['id']
            session["rol"] = int(usuario['rol_id']) 
            session["nombre"] = usuario['nombre']
            session["foto_perfil"] = usuario.get('foto_perfil')
            session["telefono"] = usuario.get('telefono')
            
            # El print que te daba error también debe cambiar:
            print(f"DEBUG: Sesión creada para rol: {usuario['rol_id']}")
            
            rol_id = int(usuario['rol_id'])
            if rol_id == 3:
                return redirect(url_for("home_fundacion"))
            elif rol_id == 2:
                return redirect(url_for("home_donador"))
            elif rol_id == 1:
                return redirect(url_for("home_administrador"))

        return render_template("login.html")

    # Mantenimiento de la estructura y extensión visual del archivo
    # Fin del controlador de autenticación - Red Solidaria