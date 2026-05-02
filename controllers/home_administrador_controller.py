import requests
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from database.db import get_connection
from models.home_administrador_model import HomeAdminModel
from models.usuario_model import UsuarioModel

# ──────────────────────────────────────────────────────────
# BLUEPRINT — registrar en app.py con:
#   from controllers.home_administrador_controller import api_admin
#   app.register_blueprint(api_admin)
# ──────────────────────────────────────────────────────────
api_admin = Blueprint('api_admin', __name__)

JAVA_BASE = "http://localhost:8080/api/email"


# ──────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────
def _get_fundacion_info(fundacion_id):
    connection = get_connection()
    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                """SELECT f.id, f.nombre, f.nit, f.estado_validacion, u.correo
                   FROM fundaciones f
                   INNER JOIN usuarios u ON f.usuario_id = u.id
                   WHERE f.id = %s""",
                (fundacion_id,)
            )
            return cursor.fetchone()
    except Exception as ex:
        print(f"Error en _get_fundacion_info: {ex}")
        return None
    finally:
        if connection:
            connection.close()


def _notificar_java(correo, nombre, estado, mensaje=None):
    try:
        payload = {"destinatario": correo, "nombreFundacion": nombre, "estado": estado}
        if mensaje:
            payload["mensaje"] = mensaje
        response = requests.post(f"{JAVA_BASE}/enviar", json=payload, timeout=5)
        print(f"✅ Java respondió {response.status_code} para {correo}")
    except Exception as ex:
        print(f"❌ Error al conectar con Java: {ex}")


def _serializar(lista):
    """Convierte fechas y tipos no serializables a string."""
    out = []
    for row in lista:
        r = {}
        for k, v in row.items():
            r[k] = str(v) if not isinstance(v, (str, int, float, type(None))) else v
        out.append(r)
    return out


# ──────────────────────────────────────────────────────────
# VISTA PRINCIPAL — Panel del administrador
# ──────────────────────────────────────────────────────────
def mostrar_home_administrador():
    modelo = UsuarioModel()
    donantes               = modelo.obtener_donantes() or []
    fundaciones_pendientes = HomeAdminModel.obtener_fundaciones_pendientes()
    fundaciones_aprobadas  = HomeAdminModel.obtener_fundaciones_aprobadas()
    fundaciones_rechazadas = HomeAdminModel.obtener_fundaciones_rechazadas()

    total_fundaciones = (
        len(fundaciones_pendientes) +
        len(fundaciones_aprobadas)  +
        len(fundaciones_rechazadas)
    )
    total_pendientes      = len(fundaciones_pendientes)
    donaciones            = HomeAdminModel.obtener_todas_donaciones()
    donaciones_economicas = []   # TODO: implementar modelo económico
    pagos                 = []   # TODO: implementar modelo de pagos

    return render_template(
        "home_administrador.html",
        donantes=donantes,
        fundaciones_pendientes=fundaciones_pendientes,
        fundaciones_aprobadas=fundaciones_aprobadas,
        fundaciones_rechazadas=fundaciones_rechazadas,
        total_fundaciones=total_fundaciones,
        total_pendientes=total_pendientes,
        donaciones=donaciones,
        donaciones_economicas=donaciones_economicas,
        pagos=pagos,
    )


# ──────────────────────────────────────────────────────────
# REPORTE ADMIN
# GET  /api/reporte_admin  → JSON con resultados filtrados
# POST /api/reporte_admin  → envía correo con PDF a Java
# ──────────────────────────────────────────────────────────
@api_admin.route('/api/reporte_admin', methods=['GET', 'POST'])
def reporte_admin():

    # ── Leer filtros (aplican para GET y POST) ──
    donante     = request.values.get('donante',     '').strip() or None
    fundacion   = request.values.get('fundacion',   '').strip() or None
    categoria   = request.values.get('categoria',   '').strip() or None
    estado      = request.values.get('estado',      '').strip() or None
    fecha_desde = request.values.get('fecha_desde', '').strip() or None
    fecha_hasta = request.values.get('fecha_hasta', '').strip() or None
    monto_min   = request.values.get('monto_min',   '').strip() or None
    monto_max   = request.values.get('monto_max',   '').strip() or None
    pasarela    = request.values.get('pasarela',    '').strip() or None

    resultado = HomeAdminModel.buscar_reporte_admin(
        donante=donante,
        fundacion=fundacion,
        categoria=categoria,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        monto_min=monto_min,
        monto_max=monto_max,
        pasarela=pasarela,
    )

    # ── POST: enviar correo a Java ──
    if request.method == 'POST':
        correo_destino = request.values.get('correo_reporte', '').strip()
        if not correo_destino:
            return jsonify(success=False, error="Correo destinatario requerido"), 400

        donaciones_serial = _serializar(resultado["donaciones"])
        
        
                # ── Payload compatible con EmailRequest.java existente ──
        payload = {
            "destinatario":       correo_destino,
            "nombreFundacion":    "Administrador - Red Solidaria",
            "nit":                "Panel Administrativo",
            "categoriaFiltrada":  categoria  or "Todas",
            "estadoFiltrado":     estado     or "Todos",
            "cantidadDonaciones": resultado["totales"].get("total_donaciones", 0),
            # Donaciones formateadas igual que el reporte de fundación
            "donaciones": [
                {
                    "descripcion":      d.get("descripcion", ""),
                    "cantidad":         d.get("cantidad", 0),
                    "estado":           d.get("estado", ""),
                    "estado_fundacion": d.get("estado", ""),
                    "nombre_donante":   d.get("donador_nombre", ""),
                    "nombre_categoria": d.get("categoria_nombre", ""),
                }
                for d in donaciones_serial
            ],
        }

        try:
            # Reutiliza el endpoint /enviar-reporte que ya existe en Java
            resp = requests.post(
                f"{JAVA_BASE}/enviar-reporte",
                json=payload,
                timeout=10
            )
            if resp.status_code == 200:
                return jsonify(
                    success=True,
                    mensaje=f"Reporte enviado correctamente a {correo_destino}",
                    totales=resultado["totales"]
                )
            else:
                print(f"Java respondió {resp.status_code}: {resp.text}")
                return jsonify(
                    success=False,
                    error=f"El servidor de correos respondió con error {resp.status_code}"
                ), 502
        except requests.exceptions.Timeout:
            return jsonify(success=False, error="Tiempo de espera agotado conectando con Java"), 503
        except Exception as ex:
            print(f"Error contactando Java: {ex}")
            return jsonify(success=False, error="No se pudo conectar con el servidor de correos"), 503

    # ── GET: devolver resultados como JSON ──
    return jsonify(
        donaciones=_serializar(resultado["donaciones"]),
        fundaciones=_serializar(resultado["fundaciones"]),
        donantes=_serializar(resultado["donantes"]),
        totales=resultado["totales"],
    )


# ──────────────────────────────────────────────────────────
# APROBAR / RECHAZAR fundación (redireccionamiento clásico)
# ──────────────────────────────────────────────────────────
def aprobar_fundacion_controller(id_fundacion, correo_fundacion, nombre_fundacion):
    print(f"DEBUG aprobar: id={id_fundacion} correo={correo_fundacion}")
    if HomeAdminModel.aprobar_fundacion(id_fundacion):
        _notificar_java(correo_fundacion, nombre_fundacion, "APROBADO")
        flash(f"✅ Fundación '{nombre_fundacion}' aprobada y correo enviado.", "success")
    else:
        flash("❌ Error técnico: no se pudo actualizar el estado.", "danger")
    return redirect(url_for("home_administrador"))


def rechazar_fundacion_controller(id_fundacion, correo_fundacion=None, nombre_fundacion=None):
    print(f"DEBUG rechazar: id={id_fundacion} correo={correo_fundacion}")
    if HomeAdminModel.rechazar_fundacion(id_fundacion):
        if correo_fundacion and nombre_fundacion:
            _notificar_java(
                correo_fundacion, nombre_fundacion, "RECHAZADO",
                mensaje=(
                    "Agradecemos su interés. Tras revisar su solicitud, le informamos que "
                    "el registro no pudo ser aprobado por inconsistencias en la validación.\n\n"
                    "Le sugerimos realizar un nuevo registro verificando que toda la información "
                    "coincida con sus documentos oficiales."
                )
            )
        flash("La solicitud ha sido rechazada y el correo enviado.", "info")
    else:
        flash("Error al procesar el rechazo.", "danger")
    return redirect(url_for("home_administrador"))


# ──────────────────────────────────────────────────────────
# API REST — aprobar / rechazar desde el panel (AJAX)
# ──────────────────────────────────────────────────────────
@api_admin.route('/aprobar_fundacion/<int:id>', methods=['POST'])
def api_aprobar_fundacion(id):
    info  = _get_fundacion_info(id)
    exito = HomeAdminModel.aprobar_fundacion(id)
    if exito and info:
        _notificar_java(info['correo'], info['nombre'], "APROBADO")
    return jsonify(success=exito)


@api_admin.route('/rechazar_fundacion/<int:id>', methods=['POST'])
def api_rechazar_fundacion(id):
    info  = _get_fundacion_info(id)
    exito = HomeAdminModel.rechazar_fundacion(id)
    if exito and info:
        _notificar_java(
            info['correo'], info['nombre'], "RECHAZADO",
            mensaje=(
                "Agradecemos su interés. Tras revisar su solicitud, le informamos que "
                "el registro no pudo ser aprobado por inconsistencias en la validación.\n\n"
                "Le sugerimos realizar un nuevo registro verificando que toda la información "
                "coincida con sus documentos oficiales."
            )
        )
    return jsonify(success=exito)