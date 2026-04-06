from flask import render_template, redirect, url_for, flash, request

class DonacionController:
    # --- MÉTODO YA EXISTENTE ---
    def solicitar_ayuda_view(self, session):
        from flask import request, redirect, url_for, flash, render_template
        from models.donacion_model import DonacionModel

        # 1. Seguridad
        if "usuario_id" not in session or int(session.get("rol")) != 3:
            return redirect(url_for("login"))

        if request.method == "POST":
            # 2. Captura EXACTA de los campos del formulario HTML
            fundacion_id = session["usuario_id"]
            categoria_id = request.form.get("categoria")
            cantidad = request.form.get("cantidad")
            urgencia = request.form.get("urgencia")
            fecha_limite = request.form.get("fecha_limite")
            ubicacion = request.form.get("ubicacion")
            telefono = request.form.get("telefono")
            descripcion = request.form.get("descripcion")

            modelo = DonacionModel()
            
            # 3. Llamada al modelo con los 8 argumentos que vimos en tu archivo
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

    # --- NUEVO MÉTODO PARA EL DONADOR ---
    def publicar_donacion_view(self, request, session, necesidad_id=None):
        from models.donacion_model import DonacionModel
        
        if "usuario_id" not in session:
            return redirect(url_for("login"))
            
        modelo = DonacionModel()
        necesidad_prellenada = None

        # Si viene de una necesidad específica, traemos los datos de la fundación
        if necesidad_id:
            necesidad_prellenada = modelo.obtener_necesidad_por_id(necesidad_id)

        if request.method == "POST":
            # Aquí capturamos los datos del formulario de donación
            # (Lo que el donador está enviando físicamente)
            donador_id = session["usuario_id"]
            fundacion_id = request.form.get("fundacion_id")
            categoria = request.form.get("categoria")
            cantidad = request.form.get("cantidad")
            descripcion = request.form.get("descripcion")

            exito = modelo.registrar_donacion(donador_id, fundacion_id, categoria, cantidad, descripcion)

            if exito:
                flash("🎉 ¡Gracias! Tu donación ha sido registrada.", "success")
                return redirect(url_for("home_donador"))
            else:
                flash("❌ Hubo un problema al registrar tu donación.", "danger")

        return render_template("donar.html", necesidad=necesidad_prellenada)