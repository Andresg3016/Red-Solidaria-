from flask import render_template, redirect, url_for
from models.donacion_model import DonacionModel

class DonacionController:
	def publicar_donacion_view(self, request, session):
		if "usuario_id" not in session:
			return redirect(url_for("login"))
		if request.method == "POST":
			descripcion = request.form["descripcion"]
			categoria_id = int(request.form["categoria_id"])
			cantidad = int(request.form["cantidad"])
			usuario_id = session["usuario_id"]
			DonacionModel().crear_donacion(usuario_id, categoria_id, descripcion, cantidad)
			return redirect(url_for("home_donador"))
		categorias = DonacionModel().obtener_categorias()
		return render_template("donar.html", categorias=categorias)
