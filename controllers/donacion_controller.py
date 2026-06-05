from flask import render_template, redirect, url_for, flash, request, session, current_app
from models.donacion_model import DonacionModel
import os
import requests
from werkzeug.utils import secure_filename
# IMPORTANTE: Asegúrate que esta ruta sea la correcta según tu estructura de carpetas
from database.db import get_connection 

class DonacionController:
    def __init__(self, modelo=None):
        self.modelo = modelo if modelo else DonacionModel()

    def cambiar_estado(self, donacion_id, accion):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        
        # Mapeo de la acción al ENUM de tu base de datos
        estado_db = 'recibido' if accion == 'aceptar' else 'rechazado'
        
        exito = self.modelo.cambiar_estado_donacion(donacion_id, estado_db)
        
        if exito:
            flash(f"✅ La donación ha sido marcada como {estado_db}", "success")
        else:
            flash("❌ No se pudo actualizar el estado de la donación", "danger")
            
        return redirect(url_for("home_fundacion"))

    def eliminar(self, donacion_id):
        """Elimina lógicamente una donación del panel de la fundación."""
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
            
        # Usamos el método unificado del modelo
        exito = self.modelo.cambiar_estado_donacion(donacion_id, 'eliminado')
        
        if exito:
            flash("🗑️ Donación eliminada del panel con éxito.", "success")
        else:
            flash("❌ Error al intentar eliminar la donación.", "danger")
        
        return redirect(url_for('home_fundacion'))
    
    # =========================================================================
    # GESTIÓN DE NECESIDADES (SOLICITUDES DE AYUDA)
    # =========================================================================
    
    def solicitar_ayuda_view(self, session):
        # Primero obtenemos el ID interno de la fundación desde la sesión
        from models.usuario_model import UsuarioModel
        user_model = UsuarioModel()
        fundacion = user_model.obtener_fundacion_por_usuario(session.get('usuario_id'))
        
        if not fundacion:
            return "Error: No se encontró la fundación asociada a este usuario."
            
        fundacion_id = fundacion['id']

        if request.method == 'POST':
            categoria_texto = request.form.get('categoria') # "Alimentos", "Ropa", etc. (Viene None si es monetario)
            cantidad = request.form.get('cantidad')
            urgencia = request.form.get('urgencia')
            telefono = request.form.get('telefono')
            descripcion = request.form.get('descripcion')
            fecha_vencimiento = request.form.get('fecha_vencimiento')
            tipo_recurso_especial = request.form.get('tipo_recurso_especial')

            # ── [NUEVO] DETECTOR DE PESTAÑA SELECCIONADA DESDE LA UI ──
            tipo_ayuda = request.form.get('tipo_ayuda', 'fisico')

            # ── DETECTOR DINÁMICO DE CATEGORÍAS REALES CON BLINDAJE PARA EVITAR NONE-STRIP ──
            lista_categorias = self.modelo.obtener_categorias()
            categoria_id = None

            if tipo_ayuda == 'monetario':
                # Si la pestaña es monetaria, forzamos directamente el ID 5 de la DB sin evaluar cadenas
                categoria_id = 5
            else:
                # Si es físico, buscamos de forma segura el ID cuyo nombre coincida con lo que viene de la UI
                if categoria_texto:
                    for cat in lista_categorias:
                        if cat['nombre'] and (cat['nombre'].strip().lower() in categoria_texto.strip().lower() or categoria_texto.strip().lower() in cat['nombre'].strip().lower()):
                            categoria_id = cat['id']
                            break

            # Si por alguna razón sigue sin encontrar coincidencia en físico, agarramos el primer ID que exista en tu DB
            if not categoria_id and lista_categorias:
                categoria_id = lista_categorias[0]['id']

            if not fecha_vencimiento: 
                fecha_vencimiento = None
                
            correo_usuario = session.get('correo') # Capturas el correo de quien crea la solicitud    

            # ── INSERCIÓN EN MODELO LIMPIO (Sincronizado con tus columnas reales de la DB) ──
            # ── INSERCIÓN EN MODELO (Sincronizado pasando None a los parámetros que pide tu modelo) ──
            exito = self.modelo.crear_necesidad(
                fundacion_id=fundacion_id, 
                categoria_id=categoria_id,
                cantidad=cantidad if tipo_ayuda == 'fisico' else 0, # Si es dinero, la cantidad física se inicializa en 0
                urgencia=urgencia,
                fecha_limite=None,          # <-- Se reincorpora porque tu modelo lo pide en la cabecera
                ubicacion=None,             # <-- Se reincorpora porque tu modelo lo pide en la cabecera
                telefono=telefono,
                descripcion=descripcion,
                contacto_correo=correo_usuario, 
                fecha_vencimiento=fecha_vencimiento,
                tipo_recurso_especial=tipo_recurso_especial,
                tipo=tipo_ayuda 
            )

            if exito:
                flash("✨ Solicitud de ayuda creada con éxito.", "success")
                return redirect(url_for('home_fundacion'))
            else:
                categorias = self.modelo.obtener_categorias()
                return render_template('solicitar_ayuda.html', error="No se pudo registrar la solicitud", categorias=categorias)

        categorias = self.modelo.obtener_categorias()
        return render_template('solicitar_ayuda.html', categories=categorias, fundacion=fundacion)
    
    
    def editar_necesidad_view(self, necesidad_id, session):
        """Renderiza y procesa el formulario de edición de una necesidad"""
        necesidad = self.modelo.obtener_necesidad_por_id(necesidad_id)
        if not necesidad:
            flash("❌ La solicitud de ayuda no existe.", "danger")
            return redirect(url_for('home_fundacion'))

        # Mapeo de Categorías
        mapeo_categories = {
            "Alimentos": 1, "Ropa": 2, "Higiene": 3,
            "Educación": 4, "Mobiliario": 5, "Otros": 6
        }

        if request.method == 'POST':
            categoria_texto = request.form.get('categoria')
            cantidad = request.form.get('cantidad')
            urgencia = request.form.get('urgencia')
            telefono = request.form.get('telefono')
            descripcion = request.form.get('descripcion')
            fecha_vencimiento = request.form.get('fecha_vencimiento')
            tipo_recurso_especial = request.form.get('tipo_recurso_especial')
            punto_entrega = request.form.get('punto_entrega')
            
            # ── [NUEVO] CAPTURA DEL TIPO EN LA EDICIÓN ──
            tipo_ayuda = request.form.get('tipo_ayuda', 'fisico')
            categoria_id = 5 if tipo_ayuda == 'monetario' else mapeo_categories.get(categoria_texto, 6)

            if not fecha_vencimiento: fecha_vencimiento = None

            # Actualización enviando el tipo correspondiente
            exito = self.modelo.actualizar_necesidad(
                necesidad_id=necesidad_id,
                categoria_id=categoria_id,
                cantidad=cantidad if tipo_ayuda == 'fisico' else 0,
                urgencia=urgencia,
                fecha_limite=None,
                ubicacion=None,
                telefono=telefono,
                descripcion=descripcion,
                fecha_vencimiento=fecha_vencimiento,
                tipo_recurso_especial=tipo_recurso_especial,
                tipo=tipo_ayuda # <-- NUEVO PARÁMETRO ENVIADO AL MODELO CORREGIDO
            )

            if exito:
                flash("✅ Solicitud de ayuda actualizada correctamente.", "success")
                return redirect(url_for('home_fundacion'))
            else:
                categorias = self.modelo.obtener_categorias()
                flash("❌ No se realizaron cambios o hubo un error al actualizar.", "warning")
                return render_template('solicitar_ayuda.html', necesidad=necesidad, categories=categorias)

        categorias = self.modelo.obtener_categorias()
        return render_template('solicitar_ayuda.html', necesidad=necesidad, categories=categorias)
    
    
    def eliminar(self, donacion_id):
        """Elimina lógicamente una donación del panel de la fundación."""
        # Validación de seguridad: Asegúrate que el usuario tenga sesión activa
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
            
        # El método cambiar_estado_donacion debe existir en tu modelo
        # y ejecutar el: UPDATE donaciones SET estado_donante = 'eliminado' WHERE id = ...
        exito = self.modelo.cambiar_estado_donacion(donacion_id, 'eliminado')
        
        if exito:
            flash("🗑️ Donación eliminada del panel con éxito.", "success")
        else:
            flash("❌ Error al intentar eliminar la donación.", "danger")
        
        return redirect(url_for('home_fundacion'))
    # =========================================================================
    # MÉTODOS DE DONACIONES PARA DONADORES
    # =========================================================================

    def publicar_donacion_view(self, request, necesidad_id=None, fundacion_id=None):
        print(f"DEBUG: Datos recibidos en POST: {request.form}")
        print(f"DEBUG: Archivos recibidos en POST: {request.files}")
        
        # 1. Seguridad
        if "usuario_id" not in session:
            return redirect(url_for("login"))
            
        usuario_id = session["usuario_id"]
        necesidad_prellenada = None
        if necesidad_id:
            necesidad_prellenada = self.modelo.obtener_necesidad_por_id(necesidad_id)

        # 2. Obtención de fundaciones activas y métodos de pago guardados
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

        # Obtenemos métodos de pago guardados del usuario (NUEVO)
        metodos_guardados = self.modelo.obtener_metodos_usuario(usuario_id)
        print(f"DEBUG: Buscando métodos para usuario_id: {usuario_id}")
        print(f"DEBUG: Resultados encontrados: {metodos_guardados}")

        # 3. Procesamiento del POST
        if request.method == "POST":
            donador_id = usuario_id
            tipo_donacion = request.form.get("tipo_donacion", "fisico")
            
            # Captura y validación estricta de la fundación
            f_id_final = request.form.get("fundacion_id") or fundacion_id
            
            print(f"DEBUG: Iniciando POST donación. Usuario: {donador_id}, Fundación capturada: {f_id_final}, Tipo: {tipo_donacion}")

            # BLINDAJE: Si la fundación es nula o vacía, bloqueamos el proceso aquí mismo
            if not f_id_final or f_id_final == "" or f_id_final == "0":
                print("DEBUG: ¡ERROR! Intento de donación sin fundación válida.")
                flash("❌ Debes seleccionar una fundación destino válida para continuar.", "danger")
                print(f"DEBUG: Métodos guardados: {metodos_guardados}")
                return render_template("donar.html", necesidad=necesidad_prellenada, 
                                       categorias=self.modelo.obtener_categorias(), 
                                       fundaciones_activas=fundaciones_activas,
                                       metodos=metodos_guardados)

            descripcion = request.form.get("descripcion")

           # ── FLUJO MONETARIO ──
            if tipo_donacion == "monetario":
                monto = request.form.get("monto", 0)
                referencia = request.form.get("referencia_pago", "")
                
                # Gestión de guardado de tarjeta
                if request.form.get("guardar_tarjeta") == "on":
                    token_pago = request.form.get("token_pago")
                    ultimos_4 = request.form.get("ultimos_4")
                    marca = request.form.get("marca")
                    if token_pago:
                        self.modelo.guardar_metodo_pago(donador_id, token_pago, ultimos_4, marca)
                
                # ID 5 es la categoría 'Monetaria'
                categoria_id = 5 
                
                exito = self.modelo.registrar_donacion(
                    donador_id, int(f_id_final), categoria_id, monto, descripcion, None, es_monetario=True
                )
                
                # ── [NUEVO BLINDAJE CON LOGICA DE ESTADOS] ──
                if exito and necesidad_prellenada:
                    # 1. Sumamos el dinero en la base de datos
                    self.modelo.actualizar_monto_recaudado(necesidad_prellenada["id"], monto)
                    
                    # 2. Consultamos cómo quedó la necesidad usando tu método actual
                    necesidad_act = self.modelo.obtener_necesidad_por_id(necesidad_prellenada["id"])
                    if necesidad_act:
                        recaudado = float(necesidad_act.get("monto_recaudado") or 0.00)
                        objetivo = float(necesidad_act.get("monto_objetivo") or 0.00)
                        
                        # 3. Si el dinero recaudado alcanzó o superó la meta, cambiamos el estado automáticamente
                        if recaudado >= objetivo:
                            self.modelo.cambiar_estado_necesidad(necesidad_prellenada["id"], "gestionada")
                
                if exito:
                    flash("💳 ¡Gracias! Tu donación monetaria ha sido registrada.", "success")
                    return redirect(url_for("home_donador"))
                else:
                    flash("❌ Error al procesar la donación monetaria.", "danger")
                    
                    
            # ── FLUJO FÍSICO ──
            else:
                categoria_id = request.form.get("categoria_id")
                cantidad = request.form.get("cantidad")
                fotos_lista = request.files.getlist("fotos")
                nombre_foto_bd = None

                if fotos_lista and fotos_lista[0].filename != '':
                    archivo = fotos_lista[0]
                    nombre_foto = secure_filename(archivo.filename)
                    carpeta_destino = os.path.join(current_app.root_path, 'static', 'img', 'donaciones')
                    os.makedirs(carpeta_destino, exist_ok=True)
                    archivo.save(os.path.join(carpeta_destino, nombre_foto))
                    nombre_foto_bd = nombre_foto

                if necesidad_prellenada:
                    exito = self.modelo.registrar_donacion_con_necesidad(
                        donador_id, int(f_id_final), categoria_id, cantidad, descripcion, necesidad_prellenada["id"], nombre_foto_bd
                    )
                    if exito:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE necesidades SET estado = 'gestionada' WHERE id = %s", (necesidad_prellenada["id"],))
                        conn.commit()
                        conn.close()
                else:
                    exito = self.modelo.registrar_donacion(donador_id, int(f_id_final), categoria_id, cantidad, descripcion, nombre_foto_bd)

                if exito:
                    flash("🎉 ¡Gracias! Tu donación ha sido registrada.", "success")
                    return redirect(url_for("home_donador"))
                else:
                    flash("❌ Error al registrar la donación.", "danger")

        return render_template("donar.html", necesidad=necesidad_prellenada, 
                               categorias=self.modelo.obtener_categorias(), 
                               fundaciones_activas=fundaciones_activas,
                               metodos=metodos_guardados)
        
        
    def home_donador_view(self, session, request):
        from flask import render_template, redirect, url_for
        
        if "usuario_id" not in session:
            return redirect(url_for("login"))

        usuario_id = session["usuario_id"]

        # 1. Datos del Donador (Necesarios para evitar el error 'donador is undefined')
        datos_donador = {
            "nombre":       session.get("nombre", "Usuario"),
            "foto_perfil":  session.get("foto_perfil"),
            "telefono":     session.get("telefono"),
            "estado":       session.get("estado") or "Activo"
        }

        # 2. Filtros
        q = request.args.get('q')
        categoria = request.args.get('cat')
        estado = request.args.get('est')
        fundacion = request.args.get('fundacion')

        # 3. Historial
        historial = self.modelo.obtener_donaciones_por_usuario_filtrado(
            usuario_id, q=q, categoria=categoria, estado=estado, fundacion=fundacion
        )
        
        # 4. Lógica de Contadores
        stats_base = self.modelo.obtener_estadisticas_donador(usuario_id)
        
        contadores = {
            'pendientes': stats_base.get('pendientes', 0) if stats_base else 0,
            'recibidas':  stats_base.get('recibidas', 0) if stats_base else 0,
            'rechazadas': stats_base.get('rechazadas', 0) if stats_base else 0,
            'monetarias': stats_base.get('monetarias', 0) if stats_base else 0
        }
        
        # 5. Otros datos
        necesidades = self.modelo.obtener_necesidades_activas(usuario_id=usuario_id, q=q, cat=categoria)
        categorias = self.modelo.obtener_categorias()

        print(f"DEBUG: Enviando total_pagos: {contadores.get('monetarias')}")

        return render_template("home_donador.html", 
                                historial=historial,
                                donador=datos_donador, 
                                categorias=categorias,
                                necesidades=necesidades,
                                contadores=contadores,
                                total_pagos=contadores.get('monetarias', 0))
        
    def gestionar_donacion_accion(self):
        import requests
        if "usuario_id" not in session:
            return redirect(url_for("login"))

        donacion_id = request.form.get('donacion_id')
        accion = request.form.get('accion')
        
        usuario_id = session.get('usuario_id') 

        # Esto mapea la acción a una cadena de texto para actualizar la BD
        # 'eliminar' pasará a ser el estado 'eliminado' en la tabla, no borra el registro.
        nuevo_estado = {
            'aceptar': 'recibido',
            'rechazar': 'rechazado',
            'eliminar': 'eliminado'
        }.get(accion)

        if not nuevo_estado:
            flash("❌ Acción no válida", "danger")
            return redirect(url_for('home_fundacion'))

        # 1. Obtenemos datos ANTES de actualizar
        donacion_info = self.modelo.obtener_donacion_por_id(donacion_id)

        # 2. Actualizamos el estado (ESTO DEBE SER UN UPDATE EN TU MODELO, NO UN DELETE)
        exito = self.modelo.cambiar_estado_donacion(donacion_id, nuevo_estado)

        if exito:
    # ── Sincronización con necesidad vinculada ──
            try:
                if donacion_info and donacion_info.get('necesidad_id'):
                    nec_id = donacion_info['necesidad_id']
                    if accion == 'rechazar':
                        # Vuelve al carrusel general
                        self.modelo.cambiar_estado_necesidad(nec_id, 'pendiente')
                    elif accion == 'aceptar':
                        self.modelo.cambiar_estado_necesidad(nec_id, 'completada')
            except Exception as e:
                print(f"⚠️ Error al sincronizar estado necesidad: {e}")

            # ── Notificación al donante ──
            if accion in ['aceptar', 'rechazar'] and donacion_info:
                try:
                    datos_correo = {
                        "destinatario":    donacion_info.get("donador_email", ""),
                        "nombreFundacion": session.get("nombre", "Fundación"),
                        "estado": "RECIBIDO" if accion == "aceptar" else "RECHAZADO_DONACION"
                    }
                    requests.post(
                        "http://localhost:8080/api/email/enviar",
                        json=datos_correo, timeout=5
                    )
                except Exception as e:
                    print(f"Error notificación: {e}")

            flash(f"✅ Donación actualizada correctamente.", "success")
        else:
            flash("❌ No se pudo actualizar la donación", "danger")

        return redirect(url_for('home_fundacion'))
    # =========================================================================
    # NUEVO: ACCIÓN PARA RECHAZAR/OCULTAR UNA NECESIDAD DESDE EL DONANTE
    # =========================================================================
    def rechazar_necesidad_accion(self, necesidad_id, session):
        """Registra que un donador específico ocultó una necesidad de su vista"""
        usuario_id = session.get("usuario_id")
        
        # Llamamos al modelo para insertar en la tabla pivote de exclusión/rechazo
        exito = self.modelo.guardar_rechazo_necesidad(usuario_id, necesidad_id)
        
        if exito:
            flash("👁️ Solicitud ocultada. No volverá a aparecer en tu carrusel.", "info")
        else:
            flash("❌ No se pudo ocultar la solicitud.", "danger")
            
        return redirect(url_for("home_donador"))