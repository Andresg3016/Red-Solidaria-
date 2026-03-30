from flask import Flask, render_template, request, redirect
from models.usuario_model import UsuarioModel, Usuario

app = Flask(__name__)

modelo = UsuarioModel()

@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template('login.html')


@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        password = request.form["password"]
        rol_id = int(request.form["rol"])

        usuario = Usuario(
            nombre=nombre,
            correo=correo,
            password=password,
            rol_id=rol_id
        )

        modelo.crear_usuario(usuario)

        return redirect("/login") 

    return render_template('registro.html')


if __name__ == "__main__":
    app.run(debug=True)