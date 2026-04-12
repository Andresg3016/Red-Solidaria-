__all__ = ["UsuarioController"]
from models.usuario_model import UsuarioModel, Usuario
import os
from werkzeug.utils import secure_filename

class UsuarioController:
    def ver_perfil_view(self):
        from flask import session, render_template, redirect, url_for
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        usuario_datos = {
            "nombre": session.get("nombre"),
            "telefono": session.get("telefono")
        }
        return render_template("ver_perfil.html", usuario=usuario_datos)
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
                # Guardar siempre el nombre de la persona, no el de la fundación
                session["nombre"] = usuario.get("nombre_usuario", usuario["nombre"])
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
        from flask import session, render_template, request, redirect, url_for, flash, current_app
        from models.usuario_model import UsuarioModel
        import os
        from werkzeug.utils import secure_filename

        if "usuario_id" not in session:
            return redirect(url_for("login"))
        


        if request.method == "POST":
            usuario_id = session["usuario_id"]
            rol = int(session.get("rol"))
            if rol == 3:
                # Fundación
                nombre = request.form.get("nombre_fundacion")
            else:
                # Donante
                nombre = request.form.get("nombre")
            telefono = request.form.get("telefono")
            archivo_foto = request.files.get("foto_perfil")
            nombre_archivo = None

            # Procesar la foto si el usuario subió una nueva
            if archivo_foto and archivo_foto.filename != '':
                nombre_archivo = secure_filename(f"perfil_{usuario_id}_{archivo_foto.filename}")
                ruta_carpeta = os.path.join('static', 'img')
                if not os.path.exists(ruta_carpeta):
                    os.makedirs(ruta_carpeta)
                archivo_foto.save(os.path.join(ruta_carpeta, nombre_archivo))
                print(f"DEBUG: Nueva foto guardada como {nombre_archivo}")

            modelo = UsuarioModel()
            exito = modelo.actualizar_perfil(usuario_id, nombre, telefono, nombre_archivo)

            # Si es fundación, también actualizamos la tabla fundaciones
            if rol == 3:
                from database.db import get_connection
                conn = get_connection()
                try:
                    cursor = conn.cursor()
                    query = "UPDATE fundaciones SET nombre = %s, telefono = %s WHERE usuario_id = %s"
                    cursor.execute(query, (nombre, telefono, usuario_id))
                    conn.commit()
                    print("DEBUG: Fundación actualizada correctamente en tabla fundaciones")
                except Exception as e:
                    print(f"ERROR al actualizar fundación: {e}")
                finally:
                    if conn:
                        conn.close()
            else:
                # Donante: aseguramos que el estado quede activo
                from database.db import get_connection
                conn = get_connection()
                try:
                    cursor = conn.cursor()
                    query = "UPDATE usuarios SET estado = 'aprobado' WHERE id = %s"
                    cursor.execute(query, (usuario_id,))
                    conn.commit()
                    print("DEBUG: Donante actualizado a estado aprobado")
                except Exception as e:
                    print(f"ERROR al actualizar estado donante: {e}")
                finally:
                    if conn:
                        conn.close()

            if exito:
                session["nombre"] = nombre
                session["telefono"] = telefono
                if nombre_archivo:
                    session["foto_perfil"] = nombre_archivo
                flash("✅ Perfil actualizado con éxito", "success")
            else:
                flash("❌ Error al actualizar los datos", "danger")

            if rol == 3:
                return redirect(url_for("home_fundacion"))
            return redirect(url_for("home_donador"))

        # Si es GET, preparamos los datos para el formulario
        usuario_datos = {
            "nombre": session.get("nombre"),
            "telefono": session.get("telefono"),
            "foto_perfil": session.get("foto_perfil")
        }
        return render_template("editar_perfil.html", usuario=usuario_datos)

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
                'database': 'donaciones_db',
                'port': 3307
            }
            print(f"DEBUG: Intentando conectar a {config['database']} en el puerto {config['port']}...")
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
                sql_fund = "INSERT INTO fundaciones (usuario_id, nombre, nit) VALUES (%s, %s, %s)"
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
            if rol_id == 3:
                # Fundación: nombre de la persona responsable y nombre de la fundación
                nombre = request.form.get("nombre_fundador") or request.form.get("nombre")
                organizacion = request.form.get("organizacion")
            else:
                # Donante: usar nombre_fundador si existe, si no, nombre
                nombre = request.form.get("nombre_fundador") or request.form.get("nombre")
                organizacion = None
            correo = request.form.get("correo")
            password = request.form.get("password")
            nit = request.form.get("nit")

            exito = self.registrar(nombre, correo, password, rol_id, nit, organizacion)
            if exito:
                return redirect(url_for("login"))
            else:
                print("ERROR: Falló la inserción en la base de datos")
                return render_template("registro.html", error="Error al registrar")
        return render_template("registro.html")

    def publicar_donacion_view(self, request, session, necesidad_id=None):
        from models.donacion_model import DonacionModel
        
        if "usuario_id" not in session:
            return redirect(url_for("login"))
            
        modelo = DonacionModel()
        necesidad_prellenada = None
        # 1. Traemos las categorías siempre para las donaciones generales
        todas_las_categorias = modelo.obtener_categorias()

        # 2. Si viene de una necesidad específica, buscamos sus detalles
        if necesidad_id:
            necesidad_prellenada = modelo.obtener_necesidad_por_id(necesidad_id)

        if request.method == "POST":
            donador_id = session["usuario_id"]
            # Prioridad al ID de la necesidad si existe, si no, al del formulario
            fundacion_id = request.form.get("fundacion_id")
            categoria_id = request.form.get("categoria_id")
            cantidad = request.form.get("cantidad")
            descripcion = request.form.get("descripcion")

            exito = modelo.registrar_donacion(donador_id, fundacion_id, categoria_id, cantidad, descripcion)

            if exito:
                flash("🎉 ¡Gracias! Tu ayuda ha sido registrada correctamente.", "success")
                return redirect(url_for("home_donador"))
            else:
                flash("❌ Hubo un problema al procesar la donación.", "danger")

        # 3. Enviamos tanto la necesidad como las categorías al HTML
        return render_template("donar.html", 
                            necesidad=necesidad_prellenada, 
                            categorias=todas_las_categorias)

    def home_fundacion_view(self):
        from flask import session, redirect, url_for, render_template, request, flash
        from models.donacion_model import DonacionModel 
        import requests 
        import json # <--- IMPORTANTE: Asegúrate de que esté aquí
        
        # Importamos la función de limpieza que creamos en app.py
        from app import serializar_datos 

        if "rol" not in session:
            return redirect(url_for("login"))
        
        if int(session["rol"]) != 3: 
            return "Acceso no autorizado"

        usuario_id = session["usuario_id"]
        fundacion = self.modelo.obtener_fundacion_por_usuario(usuario_id)
        if not fundacion:
            return "Error: No se encontraron datos de la fundación."

        fundacion_id = fundacion["id"] if "id" in fundacion else fundacion.get("fundacion_id")

        query = request.args.get('q', '')
        donante = request.args.get('donante', '')
        categoria = request.args.get('categoria', '')
        estado = request.args.get('est', '')
        accion = request.args.get('accion') 
        correo_reporte = request.args.get('correo_reporte')

        donacion_model = DonacionModel()
        mis_donaciones = donacion_model.obtener_donaciones_por_fundacion(
            fundacion_id,
            q=query, 
            donante=donante, 
            categoria=categoria, 
            estado=estado
        )

        if accion == 'reporte':
            if not correo_reporte:
                flash("Por favor, ingresa un correo para el reporte", "warning")
            else:
                try:
                    url_java = "http://localhost:8080/api/email/enviar-reporte"
                    # --- LÓGICA DE DESGLOSE POR CATEGORÍA REAL ---
                    print("DEBUG DONACIONES PARA REPORTE:", mis_donaciones)
                    desglose_dict = {}
                    for d in mis_donaciones:
                        desc = d.get('descripcion', 'Otros')
                        cant = int(d.get('cantidad', 0))
                        est = d.get('estado_fundacion', 'Verificado')
                        cat = d.get('nombre_categoria', 'Otros')
                        clave = (desc, est, cat)
                        if clave in desglose_dict:
                            desglose_dict[clave]['cantidad'] += cant
                        else:
                            desglose_dict[clave] = {
                                "descripcion": desc,
                                "cantidad": cant,
                                "estado": est,
                                "nombre_categoria": cat
                            }
                    lista_desglosada = list(desglose_dict.values())
                    total_donaciones = sum(item['cantidad'] for item in lista_desglosada)
                    payload = {
                        "destinatario": correo_reporte,
                        "nombreFundacion": fundacion.get('nombre_fundacion', fundacion.get('nombre')),
                        "nit": fundacion.get('nit', 'N/A'),
                        "cantidadDonaciones": total_donaciones,
                        "donaciones": lista_desglosada, # Enviamos la lista con el desglose real
                        "fundacionId": fundacion_id,
                        "categoriaFiltrada": categoria,
                        "estadoFiltrado": estado
                    }
                    # Limpiamos los datos antes de enviarlos a Java
                    datos_limpios = json.loads(json.dumps(payload, default=serializar_datos))
                    response = requests.post(url_java, json=datos_limpios, timeout=10)
                    if response.status_code == 200:
                        flash(f"✅ ¡Reporte enviado con éxito a {correo_reporte}!", "success")
                        print("✅ Éxito: Java procesó el PDF y el correo.")
                    else:
                        print(f"❌ Error en Java: {response.status_code} - {response.text}")
                        flash("Java recibió los datos pero hubo un error al generar el PDF", "danger")
                except Exception as e:
                    print(f"❌ Error de conexión: {e}")
                    flash("No se pudo conectar con el servicio de correos (Java)", "danger")

        # Obtener solicitudes de ayuda activas (puedes filtrar por fundación si lo deseas)
        solicitudes_ayuda = DonacionModel().obtener_necesidades_activas()
        # Puedes filtrar solo las de la fundación actual así:
        # solicitudes_ayuda = [s for s in solicitudes_ayuda if s['fundacion_id'] == usuario_id]

        return render_template(
            "home_fundacion.html",
            fundacion=fundacion,
            donaciones=mis_donaciones,
            solicitudes_ayuda=solicitudes_ayuda
        )
    
    def solicitar_ayuda_view(self):
        from flask import session, redirect, url_for, request, flash, render_template
        from models.donacion_model import DonacionModel

        # 1. Seguridad: Solo fundaciones pueden acceder
        if "usuario_id" not in session or int(session.get("rol")) != 3:
            return redirect(url_for("login"))

        if request.method == "POST":
            # 2. Captura de datos del formulario HTML
            fundacion_id = session["usuario_id"]
            categoria = request.form.get("categoria")
            cantidad = request.form.get("cantidad")
            urgencia = request.form.get("urgencia")
            fecha_limite = request.form.get("fecha_limite")
            ubicacion = request.form.get("ubicacion")
            telefono = request.form.get("telefono")
            descripcion = request.form.get("descripcion")

            # 3. Llamada al modelo para insertar en la tabla 'necesidades'
            modelo_donacion = DonacionModel()
            exito = modelo_donacion.crear_necesidad(
                fundacion_id, categoria, cantidad, urgencia, 
                fecha_limite, ubicacion, telefono, descripcion
            )

            if exito:
                flash("🚀 ¡Tu solicitud de ayuda ha sido publicada con éxito!", "success")
                return redirect(url_for("home_fundacion"))
            else:
                flash("❌ Hubo un error al publicar la solicitud.", "danger")
                return render_template("solicitar_ayuda.html") # Ajusta al nombre de tu archivo

        # Si es GET, simplemente mostramos el formulario
        return render_template("solicitar_ayuda.html")
    

    def home_donador_view(self):
        from flask import session, redirect, url_for, render_template, request, flash
        from models.donacion_model import DonacionModel
        import requests
        import json
        from app import serializar_datos

        if "usuario_id" not in session:
            return redirect(url_for("login"))

        datos_donador = {
            "nombre": session.get("nombre"),
            "foto_perfil": session.get("foto_perfil"),
            "telefono": session.get("telefono"),
            "estado": session.get("estado")
        }

        modelo_donacion = DonacionModel()

        # Filtros multicriterio
        q = request.args.get('q', '')
        cat = request.args.get('cat', '')
        est = request.args.get('est', '')
        accion = request.args.get('accion')
        correo_reporte = request.args.get('correo_reporte')

        necesidades = modelo_donacion.obtener_necesidades_activas(q, cat)
        mis_donaciones = modelo_donacion.obtener_donaciones_por_usuario_filtrado(session["usuario_id"], q=q, categoria=cat, estado=est)

        if accion == 'reporte':
            if not correo_reporte:
                flash("Por favor, ingresa un correo para el reporte", "warning")
            else:
                try:
                    url_java = "http://localhost:8080/api/email/enviar-reporte-donador"
                    # Desglose por categoría/estado igual que fundación
                    desglose_dict = {}
                    for d in mis_donaciones:
                        desc = d.get('descripcion', 'Otros')
                        cant = int(d.get('cantidad', 0))
                        est_don = d.get('estado_donante', 'Verificado')
                        cat_don = d.get('categoria_nombre', 'Otros')
                        fundacion_nombre = d.get('fundacion_nombre', 'N/A')
                        clave = (desc, est_don, cat_don, fundacion_nombre)
                        if clave in desglose_dict:
                            desglose_dict[clave]['cantidad'] += cant
                        else:
                            desglose_dict[clave] = {
                                "descripcion": desc,
                                "cantidad": cant,
                                "estado": est_don,
                                "nombre_categoria": cat_don,
                                "fundacion_nombre": fundacion_nombre
                            }
                    lista_desglosada = list(desglose_dict.values())
                    total_donaciones = sum(item['cantidad'] for item in lista_desglosada)
                    payload = {
                        "destinatario": correo_reporte,
                        "nombreDonador": datos_donador["nombre"],
                        "telefono": datos_donador.get("telefono", "N/A"),
                        "cantidadDonaciones": total_donaciones,
                        "donaciones": lista_desglosada,
                        "categoriaFiltrada": cat,
                        "estadoFiltrado": est
                    }
                    datos_limpios = json.loads(json.dumps(payload, default=serializar_datos))
                    response = requests.post(url_java, json=datos_limpios, timeout=10)
                    if response.status_code == 200:
                        flash(f"✅ ¡Reporte enviado con éxito a {correo_reporte}!", "success")
                    else:
                        print(f"❌ Error en Java: {response.status_code} - {response.text}")
                        flash("Java recibió los datos pero hubo un error al generar el PDF", "danger")
                except Exception as e:
                    print(f"❌ Error de conexión: {e}")
                    flash("No se pudo conectar con el servicio de correos (Java)", "danger")

        return render_template("home_donador.html", 
                               donador=datos_donador, 
                               necesidades=necesidades, 
                               donaciones=mis_donaciones)

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