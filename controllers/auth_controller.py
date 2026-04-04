from models.usuario_model import UsuarioModel

# Instancia global del modelo para uso en el controlador
modelo = UsuarioModel()

class AuthController:

    def login(self, correo, password):
        # Buscamos al usuario por su correo electrónico
        usuario = modelo.obtener_usuario_por_correo(correo)
        
        if not usuario:
            print(f"DEBUG: El correo {correo} no existe en la BD")
            return None, "Usuario no existe"
            
        if usuario.password != password:
            print(f"DEBUG: Contraseña incorrecta para {correo}")
            return None, "Contraseña incorrecta"
            
        # CORRECCIÓN DEFINITIVA: Aceptamos 'activo' o 'aprobado'
        # Esto soluciona el rebote que viste en la consola
        estados_validos = ["activo", "aprobado"]
        
        if usuario.estado.lower() not in estados_validos:
            print(f"DEBUG: Acceso denegado. Estado actual: {usuario.estado}")
            return None, "Cuenta pendiente de aprobación por el administrador"
            
        print(f"DEBUG: Acceso concedido para {usuario.nombre}")
        return usuario, None

    def login_view(self):
        from flask import request, session, redirect, url_for, render_template, flash
        
        if request.method == "POST":
            correo = request.form["correo"]
            password = request.form["password"]
            
            print(f"DEBUG: Procesando formulario de login para {correo}")
            usuario, error = self.login(correo, password)
            
            # SI HAY ERROR (No existe, clave mal, o no está aprobado aún)
            if error:
                flash(error, "danger") 
                return render_template("login.html")
                
            # SI TODO ESTÁ BIEN, GUARDAMOS LOS DATOS EN LA SESIÓN
            session["usuario_id"] = usuario.id
            session["rol"] = int(usuario.rol_id) 
            session["nombre"] = usuario.nombre
            session["foto_perfil"] = usuario.foto_perfil
            session["telefono"] = usuario.telefono
            
            print(f"DEBUG: Sesión creada. Redirigiendo según Rol: {usuario.rol_id}")
            
            # REDIRECCIONES SEGÚN EL ROL DEL USUARIO
            # Asegúrate de que estos nombres coincidan con tus rutas en app.py
            if int(usuario.rol_id) == 3:  # FUNDACIÓN
                return redirect(url_for("home_fundacion"))
                
            elif int(usuario.rol_id) == 2: # DONADOR
                return redirect(url_for("home_donador"))
                
            elif int(usuario.rol_id) == 1: # ADMINISTRADOR
                return redirect(url_for("admin_panel"))

        # Si el método es GET, simplemente mostramos la página de login
        return render_template("login.html")

    # Mantenimiento de la estructura y extensión visual del archivo
    # Fin del controlador de autenticación - Red Solidaria