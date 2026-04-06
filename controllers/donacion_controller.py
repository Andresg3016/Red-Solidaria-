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
            fundacion_id = session["usuario_id"]
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

        if request.method == "POST":
            # 3. CAPTURA DE DATOS (CORREGIDO: categoria_id coincide con el HTML)
            donador_id = session["usuario_id"]
            fundacion_id = request.form.get("fundacion_id")
            categoria_id = request.form.get("categoria_id") # <-- Corregido de 'categoria' a 'categoria_id'
            cantidad = request.form.get("cantidad")
            descripcion = request.form.get("descripcion")

            # 4. Registro en la base de datos
            exito = modelo.registrar_donacion(
                donador_id, 
                fundacion_id, 
                categoria_id, 
                cantidad, 
                descripcion
            )

            if exito:
                flash("🎉 ¡Gracias! Tu donación ha sido registrada.", "success")
                return redirect(url_for("home_donador"))
            else:
                flash("❌ Hubo un problema al registrar tu donación.", "danger")

        # 5. Cargar categorías por si es una donación general (sin necesidad_id)
        categorias = modelo.obtener_categorias()
        return render_template("donar.html", necesidad=necesidad_prellenada, categorias=categorias)

# Fin del Controlador DonacionController