from flask import render_template, redirect, url_for, flash, request

class DonacionController:
    
    # --- MÉTODO PARA QUE LA FUNDACIÓN SOLICITE AYUDA (NECESIDADES) ---
    def solicitar_ayuda_view(self, session):
        from models.donacion_model import DonacionModel

        # 1. Seguridad: Solo fundaciones (Rol 3) pueden entrar
        if "usuario_id" not in session or int(session.get("rol")) != 3:
            return redirect(url_for("login"))

        if request.method == "POST":
            # 2. Captura de los campos del formulario HTML
            usuario_id = session["usuario_id"]

            fundacion = None
            # Buscar fundación por usuario_id
            try:
                from database.db import get_connection
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id FROM fundaciones WHERE usuario_id = %s", (usuario_id,))
                fundacion = cursor.fetchone()
                conn.close()
            except Exception as e:
                fundacion = None

            if not fundacion:
                flash("❌ No se encontró la fundación asociada a este usuario.", "danger")
                return render_template("solicitar_ayuda.html")

            fundacion_id = fundacion["id"]
            categoria_id = request.form.get("categoria")
            cantidad = request.form.get("cantidad")
            urgencia = request.form.get("urgencia")
            fecha_limite = request.form.get("fecha_limite")
            ubicacion = request.form.get("ubicacion")
            telefono = request.form.get("telefono")
            descripcion = request.form.get("descripcion")

            modelo = DonacionModel()
            # 3. Guardar la necesidad en la base de datos
            exito = modelo.crear_necesidad(
                fundacion_id, 
                categoria_id, 
                cantidad, 
                urgencia, 
                fecha_limite, 
                ubicacion, 
                telefono, 
                descripcion
            )

            if exito:
                flash("🚀 ¡Tu solicitud de ayuda ha sido publicada!", "success")
                return redirect(url_for("home_fundacion"))
            else:
                flash("❌ Error al guardar en la base de datos.", "danger")

        return render_template("solicitar_ayuda.html")

    # --- MÉTODO PARA QUE EL DONADOR PUBLIQUE UNA DONACIÓN ---
    def publicar_donacion_view(self, request, session, necesidad_id=None):
        from models.donacion_model import DonacionModel
        
        # 1. Seguridad: El usuario debe estar logueado
        if "usuario_id" not in session:
            return redirect(url_for("login"))
            
        modelo = DonacionModel()
        necesidad_prellenada = None

        # 2. Si viene desde una necesidad específica en el muro, traemos los datos
        if necesidad_id:
            necesidad_prellenada = modelo.obtener_necesidad_por_id(necesidad_id)

        # Obtener fundaciones activas (usuarios con estado aprobado y rol fundación)
        from database.db import get_connection
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT f.id, f.nombre
            FROM fundaciones f
            JOIN usuarios u ON f.usuario_id = u.id
            WHERE u.estado = 'aprobado' AND u.rol_id = 3
            ORDER BY f.nombre ASC
        """)
        fundaciones_activas = cursor.fetchall()
        conn.close()

        if request.method == "POST":
            donador_id = session["usuario_id"]
            categoria_id = request.form.get("categoria_id")
            cantidad = request.form.get("cantidad")
            descripcion = request.form.get("descripcion")


            if necesidad_prellenada:
                # Donación a una sola fundación (por necesidad)
                fundacion_ids = [str(necesidad_prellenada["fundacion_id"])]
            else:
                # Donación general: puede ser a varias fundaciones
                fundacion_ids = request.form.getlist("fundacion_ids")

            exito = modelo.registrar_donacion(
                donador_id,
                fundacion_ids,
                categoria_id,
                cantidad,
                descripcion
            )

            if exito:
                flash("🎉 ¡Gracias! Tu donación ha sido registrada.", "success")
                return redirect(url_for("home_donador"))
            else:
                flash("❌ Hubo un problema al registrar tu donación.", "danger")

        categorias = modelo.obtener_categorias()
        return render_template("donar.html", necesidad=necesidad_prellenada, categorias=categorias, fundaciones_activas=fundaciones_activas)

# Fin del Controlador DonacionController