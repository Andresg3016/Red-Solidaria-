from flask import render_template, redirect, url_for, flash, request # Asegúrate de importar request aquí

class DonacionController:
    def solicitar_ayuda_view(self, session): # Quitamos 'request' de los parámetros porque flask lo maneja global
        from flask import request
        from models.donacion_model import DonacionModel
        
        # 1. Verificamos sesión
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        
        if request.method == "POST":
            # 2. Capturamos los datos
            usuario_id = session["usuario_id"]
            tipo_urgencia = request.form.get("tipo_urgencia")
            meta = request.form.get("meta")
            descripcion = request.form.get("descripcion")
            fecha_limite = request.form.get("fecha_limite")

            print(f"DEBUG: Intentando guardar necesidad para usuario {usuario_id}")

            # 3. Llamamos al modelo
            modelo = DonacionModel()
            exito = modelo.crear_necesidad(
                usuario_id, tipo_urgencia, meta, descripcion, fecha_limite
            )

            if exito:
                flash("✅ Solicitud publicada con éxito", "success")
                return redirect(url_for("home_fundacion"))
            else:
                flash("❌ Error al procesar la solicitud", "danger")
        
        # 4. Si es GET, mostramos el formulario
        return render_template("solicitar_ayuda.html")