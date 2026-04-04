__all__ = ["UsuarioController"]
from models.usuario_model import UsuarioModel, Usuario
import os
from werkzeug.utils import secure_filename

class UsuarioController:
    def __init__(self):
        # Movimos el modelo aquí adentro para que 'self.modelo' exista en todos los métodos
        self.modelo = UsuarioModel()

    def login_view(self):
        from flask import render_template, request, redirect, url_for, session, flash

        if request.method == "POST":
            correo = request.form.get("correo").strip() # .strip() quita espacios accidentales
            password = request.form.get("password")

            usuario = self.modelo.validar_usuario(correo, password)

            if usuario:
                # Si el estado es 'inactivo' o algo raro, podrías bloquearlo aquí.
                # Pero para Diana y Junior que son 'pendiente', debemos dejarlos pasar.
                
                session["usuario_id"] = usuario["id"]
                session["nombre"] = usuario["nombre"]
                session["rol"] = int(usuario["rol_id"]) 
                session["estado"] = usuario["estado"] # Guardamos el estado en sesión

                print(f"DEBUG LOGIN: {usuario['nombre']} (Rol: {usuario['rol_id']}, Estado: {usuario['estado']}) ha iniciado sesión.")

                rol_id = int(usuario["rol_id"])
                if rol_id == 1:
                    return redirect(url_for("home_administrador"))
                elif rol_id == 3:
                    return redirect(url_for("home_fundacion"))
                else:
                    return redirect(url_for("home_donador"))
            else:
                flash("Correo o contraseña incorrectos", "danger")
                return render_template("login.html")

        return render_template("login.html")

    def editar_perfil_view(self):
        from flask import session, render_template, request, redirect, url_for
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        if request.method == "POST":
            return redirect(url_for("home_donador"))
        usuario = {"nombre": session.get("nombre")}
        return render_template("editar_perfil.html", usuario=usuario)

    def registrar(self, nombre, correo, password, rol_id, nit=None, organizacion=None):
        import mysql.connector 
        import requests  # <-- IMPORTANTE: Necesario para hablar con Java
        print(f"DEBUG: --- PRUEBA DE CONEXIÓN MANUAL ---")
        
        conn = None 
        try:
            config = {
                'host': 'localhost',
                'user': 'root',
                'password': '', 
                'database': 'donaciones_db'
            }
            
            print(f"DEBUG: Intentando conectar a {config['database']}...")
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            print("DEBUG: ¡CONECTADO EXITOSAMENTE!")

            # 1. Insertar Usuario con estado 'pendiente' para fundaciones
            sql_user = "INSERT INTO usuarios (nombre, correo, password, rol_id, estado, fecha_registro) VALUES (%s, %s, %s, %s, %s, NOW())"
            estado_db = 'pendiente' if int(rol_id) == 3 else 'aprobado'
            
            print(f"DEBUG: Insertando usuario: {correo}")
            cursor.execute(sql_user, (nombre, correo, password, rol_id, estado_db))
            nuevo_id = cursor.lastrowid

            # 2. Insertar Fundación si aplica
            if int(rol_id) == 3:
                print(f"DEBUG: Insertando en tabla fundaciones para ID: {nuevo_id}")
                sql_fund = "INSERT INTO fundaciones (usuario_id, nombre_fundacion, nit) VALUES (%s, %s, %s)"
                cursor.execute(sql_fund, (nuevo_id, organizacion, nit))
            
            # GUARDAR CAMBIOS EN DB
            conn.commit()
            print("¡LOG: REGISTRO REALIZADO EN DB CON ÉXITO!")

            # --- NUEVO: LLAMADA AL MICROSERVICIO DE JAVA ---
            if int(rol_id) == 3:
                try:
                    print("DEBUG: Enviando petición de correo a Java...")
                    url_java = "http://localhost:8080/api/email/enviar"
                    payload = {
                        "destinatario": correo,
                        "nombreFundacion": organizacion if organizacion else nombre,
                        "estado": "PENDIENTE"
                    }
                    # Enviamos el JSON a Java
                    requests.post(url_java, json=payload, timeout=5)
                    print(f"✅ Notificación enviada a Java para {correo}")
                except Exception as e_mail:
                    # Si falla el correo, no detenemos el registro, solo avisamos en consola
                    print(f"⚠️ Error al conectar con Java Mail: {e_mail}")
            # -----------------------------------------------

            return True

        except Exception as e:
            print("********************************")
            print(f"¡ERROR DETECTADO!: {e}")
            print("********************************")
            return False
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
                print("DEBUG: Conexión cerrada.")

    def registro_view(self):
        from flask import request, redirect, url_for, render_template
        if request.method == "POST":
            print(f"DEBUG: Datos recibidos: {request.form}") 
            
            rol_id = request.form.get("rol")
            if not rol_id:
                print("ERROR: No se recibió rol_id")
                return render_template("registro.html", error="Debe seleccionar un rol")

            rol_id = int(rol_id)
            nombre = request.form.get("nombre")
            correo = request.form.get("correo")
            password = request.form.get("password")
            nit = request.form.get("nit")
            organizacion = request.form.get("organizacion")

            exito = self.registrar(nombre, correo, password, rol_id, nit, organizacion)
            
            if exito:
                return redirect(url_for("login"))
            else:
                print("ERROR: Falló la inserción en la base de datos")
                return render_template("registro.html", error="Error al registrar")
                
        return render_template("registro.html")

    def home_donador_view(self):
        from flask import session, redirect, url_for, render_template
        from models.donacion_model import DonacionModel
        
        if "rol" not in session:
            return redirect(url_for("login"))
        if int(session["rol"]) != 2: 
            return "Acceso no autorizado"

        # AGREGA ESTOS DATOS para que el HTML pueda mostrarlos
        usuario = {
            "nombre": session.get("nombre"),
            "foto_perfil": session.get("foto_perfil"), # Para la imagen circular
            "telefono": session.get("telefono")       # Para el formulario de edición
        }
        
        donaciones = DonacionModel().donaciones_por_usuario(session["usuario_id"])
        return render_template("home_donador.html", donador=usuario, donaciones=donaciones)

    def home_fundacion_view(self):
        from flask import session, redirect, url_for, render_template
        from models.donacion_model import DonacionModel 
        
        if "rol" not in session:
            return redirect(url_for("login"))
        
        if int(session["rol"]) != 3: 
            return "Acceso no autorizado"

        usuario_id = session["usuario_id"]
        fundacion = self.modelo.obtener_fundacion_por_usuario(usuario_id)
        
        if not fundacion:
            return "Error: No se encontraron datos de la fundación."

        # Aquí es donde ocurría el error:
        donacion_model = DonacionModel()
        mis_donaciones = donacion_model.obtener_donaciones_por_fundacion(fundacion['id'])

        return render_template(
            "home_fundacion.html", 
            fundacion=fundacion, 
            donaciones=mis_donaciones
        )
    
    def admin_panel_view(self):
        from flask import session, redirect, url_for, render_template
        if "rol" not in session:
            return redirect(url_for("login"))
        if int(session["rol"]) != 1:
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