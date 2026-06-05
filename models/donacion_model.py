from database.db import get_connection
import mysql.connector

class DonacionModel:
    print("Cargando DonacionModel...")
    def __init__(self, mysql=None):
        self.mysql = mysql

    # =========================================================================
    # MÉTODOS DE DONACIONES (HISTORIAL Y REGISTRO)
    # =========================================================================

    def registrar_donacion(self, donador_id, fundacion_id, categoria_id, cantidad, descripcion, fotos_str=None, es_monetario=False):
        """Registra la donación determinando el estado inicial según el tipo."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            c_id = int(categoria_id) if categoria_id else 0
            f_id = int(fundacion_id[0]) if isinstance(fundacion_id, list) else int(fundacion_id or 0)
            
            # Lógica Senior: Si es monetario, el estado inicial es 'gestionada', si no, 'pendiente'
            estado_inicial = 'gestionada' if es_monetario else 'pendiente'
            tipo_donacion = 'monetario' if es_monetario else 'fisico'

            query = """
                INSERT INTO donaciones 
                (usuario_id, fundacion_id, categoria_id, cantidad, descripcion, tipo, estado_donante, fecha, fotos)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """
            cursor.execute(query, (donador_id, f_id, c_id, cantidad, descripcion, tipo_donacion, estado_inicial, fotos_str))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error CRÍTICO al registrar donación: {e}")
            return False
        finally:
            conn.close()

    def registrar_donacion_con_necesidad(self, donador_id, fundacion_id, categoria_id, cantidad, descripcion, necesidad_id, fotos_str=None, es_monetario=False, forzar_estado=None):
        """Registra asociando necesidad_id manejando tipos físicos y monetarios de forma dinámica."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            c_id = int(categoria_id) if categoria_id else 0
            n_id = int(necesidad_id) if necesidad_id else None
            f_id = int(fundacion_id[0]) if isinstance(fundacion_id, list) else int(fundacion_id or 0)
            
            tipo_donacion = 'monetario' if es_monetario else 'fisico'
            
            # ── AQUÍ ESTÁ EL TRUCO SENIOR: Si pasamos un estado forzado, usa ese. Si no, usa el comportamiento por defecto ──
            if forzar_estado:
                estado_inicial = forzar_estado
            else:
                estado_inicial = 'gestionada' if es_monetario else 'pendiente'
            
            query = """
                INSERT INTO donaciones 
                (usuario_id, fundacion_id, categoria_id, cantidad, descripcion, tipo, estado_donante, fecha, necesidad_id, fotos)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
            """
            cursor.execute(query, (donador_id, f_id, c_id, cantidad, descripcion, tipo_donacion, estado_inicial, n_id, fotos_str))
            
            # Si el registro es exitoso, marcamos la necesidad origen como 'gestionada' para cerrarla definitivamente
            if n_id:
                cursor.execute("UPDATE necesidades SET estado = 'gestionada' WHERE id = %s", (n_id,))
                
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al registrar donación con necesidad_id {necesidad_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            
            
    def obtener_fundacion_por_usuario(self, usuario_id):
        from database.db import get_connection
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            # CORRECCIÓN: Quitamos f.foto_perfil que no existe en la tabla fundaciones
            query = """
                SELECT f.id, f.usuario_id, f.nit, f.telefono, f.descripcion,
                    f.nombre AS nombre_fundacion, 
                    u.nombre AS nombre_encargado, 
                    u.correo, u.estado AS estado_usuario, f.estado_validacion
                FROM fundaciones f
                INNER JOIN usuarios u ON f.usuario_id = u.id
                WHERE f.usuario_id = %s
            """
            cursor.execute(query, (usuario_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"❌ Error en obtener_fundacion_por_usuario: {e}")
            return None
        finally:
            if conn:
                conn.close()
                
    def buscar_reporte_admin(self, filtros):
        """Método para el panel de administración que resuelve el error 1054"""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            # Usamos d.estado_donante para que coincida con tu base de datos
            query = """
                SELECT 
                    d.id, d.cantidad, d.fecha, d.descripcion,
                    u.nombre AS donante_nombre,
                    f.nombre AS fundacion_nombre,
                    c.nombre AS categoria_nombre,
                    d.estado_donante  -- CAMBIA 'd.estado' POR 'd.estado_donante'
                FROM donaciones d
                JOIN usuarios u ON d.usuario_id = u.id
                JOIN fundaciones f ON d.fundacion_id = f.id
                JOIN categorias c ON d.categoria_id = c.id
                WHERE 1=1
            """
            params = []

            if filtros.get('estado'):
                query += " AND d.estado_donante = %s"
                params.append(filtros.get('estado'))
            
            if filtros.get('donante'):
                query += " AND u.nombre LIKE %s"
                params.append(f"%{filtros.get('donante')}%")

            query += " ORDER BY d.fecha DESC"
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en buscar_reporte_admin: {e}")
            return []
        finally:
            conn.close()

    def obtener_donaciones_por_fundacion(self, fundacion_id, q='', categoria='', estado='', donante=''):
        from database.db import get_connection
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            
            # 1. Base de la consulta: Ya incluye el filtro para ocultar los 'eliminado'
            query = """
                SELECT d.*, 
                       c.nombre as nombre_categoria, 
                       u.nombre as nombre_donante,
                       u.telefono,
                       u.correo
                FROM donaciones d
                JOIN categorias c ON d.categoria_id = c.id
                JOIN usuarios u ON d.usuario_id = u.id
                WHERE d.fundacion_id = %s 
                AND d.estado_donante != 'eliminado'
            """
            params = [fundacion_id]

            # 2. Filtro por descripción
            if q:
                query += " AND LOWER(d.descripcion) LIKE %s"
                params.append(f"%{q.lower().strip()}%")

            # 3. Filtro por categoría
            if categoria and categoria.lower() != 'todas' and categoria.strip() != '':
                query += " AND LOWER(c.nombre) = %s"
                params.append(categoria.lower().strip())

            # 4. Filtro por estado
            if estado and estado.lower() != 'todos' and estado.strip() != '':
                query += " AND LOWER(d.estado_donante) = %s"
                params.append(estado.lower().strip())
            
            # 5. Filtro por nombre del donante
            if donante:
                query += " AND LOWER(u.nombre) LIKE %s"
                params.append(f"%{donante.lower().strip()}%")

            # 6. Orden
            query += " ORDER BY d.fecha DESC"

            cursor.execute(query, params)
            return cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Error al obtener donaciones para fundación {fundacion_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()
                
    def obtener_necesidades_por_fundacion(self, fundacion_id):
        from database.db import get_connection
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            # LOGICA SENIOR: Cambiamos n.estado != 'eliminado' por n.estado = 'pendiente'
            # para que al pasar a 'gestionada' desaparezca del carrusel de la fundación automáticamente.
            query = """
                SELECT 
                    n.id, n.fundacion_id, n.categoria_id, n.cantidad, n.tipo_urgencia,
                    n.fecha_limite, n.ubicacion, n.telefono, n.descripcion, n.fecha_vencimiento,
                    n.tipo_recurso_especial, n.tipo, n.fecha, -- Agregamos n.fecha aquí para asegurar que viaje al HTML
                    c.nombre AS nombre_categoria,
                    COALESCE(d.estado_donante, n.estado) AS estado
                FROM necesidades n
                LEFT JOIN categorias c ON n.categoria_id = c.id
                LEFT JOIN donaciones d ON d.necesidad_id = n.id
                WHERE n.fundacion_id = %s AND n.estado = 'pendiente'
                ORDER BY n.id DESC
            """
            cursor.execute(query, (int(fundacion_id),))
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error en obtener_necesidades_por_fundacion: {e}")
            return []
        finally:
            if conn:
                conn.close()
                
    def obtener_donaciones_por_usuario_filtrado(self, usuario_id, q=None, categoria=None, estado=None, fundacion=None):
        """Filtros multicriterio para el historial personal del Donador."""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            # Seleccionamos explícitamente todo de donaciones
            query = """
                SELECT d.*, c.nombre AS categoria_nombre, fun.nombre AS fundacion_nombre
                FROM donaciones d
                LEFT JOIN categorias c ON d.categoria_id = c.id
                LEFT JOIN fundaciones fun ON d.fundacion_id = fun.id
                WHERE d.usuario_id = %s
            """
            params = [usuario_id]
            
            if q:
                query += " AND d.descripcion LIKE %s"; params.append(f"%{q}%")
            if categoria:
                query += " AND d.categoria_id = %s"; params.append(categoria)
            if fundacion:
                query += " AND fun.nombre LIKE %s"; params.append(f"%{fundacion}%")
            
            query += " ORDER BY d.fecha DESC"
            cursor.execute(query, tuple(params))
            donaciones = cursor.fetchall()

            for d in donaciones:
                # Obtenemos los estados actuales
                e_don = d.get('estado_donante')
                
                # NOTA: En tu tabla no existe 'estado_fundacion'. 
                # Si ese valor viene de otra tabla, deberías unirla en el JOIN arriba.
                # Por ahora, mantenemos la lógica de 'gestionada' y 'pendiente'.
                
                if d.get('tipo') == 'monetario':
                    d['estado_donante'] = 'gestionada'
                elif not e_don or e_don == '':
                    d['estado_donante'] = 'pendiente'
                else:
                    d['estado_donante'] = e_don
            
            # Filtro final por estado en memoria (como ya tenías)
            if estado:
                return [d for d in donaciones if d['estado_donante'] == estado]
            return donaciones

        except Exception as e:
            print(f"❌ ERROR en obtener_donaciones_por_usuario_filtrado: {e}")
            return []
        finally:
            if conn: conn.close()
    # =========================================================================
    # MÉTODOS DE NECESIDADES
    # =========================================================================

    def crear_necesidad(self, fundacion_id, categoria_id, cantidad, urgencia, fecha_limite, ubicacion, telefono, descripcion, contacto_correo, fecha_vencimiento, tipo_recurso_especial, tipo='fisico'):
        """Inserta una nueva solicitud de ayuda sin la columna punto_entrega."""
        try:
            from database.db import get_connection # O como tengas tu import de conexión
            conn = get_connection()
            cursor = conn.cursor()
            
            # Removido 'punto_entrega' del INSERT y de los VALUES
            query = """
                INSERT INTO necesidades (
                    fundacion_id, categoria_id, descripcion, tipo, tipo_recurso_especial, 
                    cantidad, fecha, estado, tipo_urgencia, 
                    fecha_limite, fecha_vencimiento, ubicacion, telefono, contacto_correo
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), 'pendiente', %s, %s, %s, %s, %s, %s)
            """
            valores = (
                fundacion_id, categoria_id, descripcion, tipo, tipo_recurso_especial,
                cantidad, urgencia, fecha_limite, fecha_vencimiento,
                ubicacion, telefono, contacto_correo
            )
            cursor.execute(query, valores)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error al crear necesidad en el modelo: {e}")
            return False
            
    def obtener_necesidades_activas(self, usuario_id, q=None, cat=None):
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            # Lógica Senior: Filtrar estrictamente por n.estado = 'disponible' 
            # Esto hace que si cambia a 'en_proceso' o 'gestionada' desaparezca de inmediato de los carruseles.
            query = """
                SELECT n.*, f.nombre AS nombre_fundacion, 
                       n.contacto_correo AS fundacion_correo, 
                       n.telefono AS fundacion_telefono, 
                       c.nombre AS nombre_categoria,
                       d.estado_donante AS interaccion_estado
                FROM necesidades n
                LEFT JOIN fundaciones f ON n.fundacion_id = f.id
                LEFT JOIN categorias c ON n.categoria_id = c.id
                LEFT JOIN donaciones d ON n.id = d.necesidad_id AND d.usuario_id = %s
                WHERE n.estado = 'pendiente'
                AND n.id NOT IN (
                    SELECT necesidad_id FROM necesidades_rechazadas WHERE usuario_id = %s
                )
            """
            params = [usuario_id, usuario_id]

            if q:
                query += " AND (n.descripcion LIKE %s OR f.nombre LIKE %s)"
                params.extend([f"%{q}%", f"%{q}%"])
            
            if cat:
                query += " AND c.nombre = %s"
                params.append(cat)

            query += " ORDER BY n.id DESC"
            
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error al obtener necesidades activas: {e}")
            return []
        finally:
            conn.close()
            
    def obtener_necesidad_por_id(self, necesidad_id):
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT n.*, f.nombre AS nombre_fundacion, f.id AS fundacion_id
                FROM necesidades n
                JOIN fundaciones f ON n.fundacion_id = f.id
                WHERE n.id = %s
            """
            cursor.execute(query, (necesidad_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error en obtener_necesidad_por_id: {e}")
            return None
        finally:
            conn.close()

    def actualizar_necesidad(self, necesidad_id, categoria_id, cantidad, urgencia, fecha_limite, ubicacion, telefono, descripcion, fecha_vencimiento=None, tipo_recurso_especial=None, punto_entrega=None):
        """Actualiza todos los campos de una necesidad específica, incluyendo las nuevas columnas de la interfaz."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            query = """
                UPDATE necesidades 
                SET categoria_id = %s, cantidad = %s, tipo_urgencia = %s, 
                    fecha_limite = %s, ubicacion = %s, telefono = %s, 
                    descripcion = %s, fecha_vencimiento = %s,
                    tipo_recurso_especial = %s, punto_entrega = %s
                WHERE id = %s
            """
            cursor.execute(query, (categoria_id, cantidad, urgencia, fecha_limite, ubicacion, telefono, descripcion, fecha_vencimiento, tipo_recurso_especial, punto_entrega, necesidad_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Error al actualizar necesidad {necesidad_id}: {e}")
            return False
        finally:
            conn.close()

    def cambiar_estado_necesidad(self, necesidad_id, nuevo_estado):
        """Permite cambiar el estado de una necesidad (ej. 'eliminado' para borrado lógico)."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            query = "UPDATE necesidades SET estado = %s WHERE id = %s"
            cursor.execute(query, (nuevo_estado, necesidad_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Error al cambiar estado de la necesidad {necesidad_id}: {e}")
            return False
        finally:
            conn.close()

    # =========================================================================
    # NUEVO: REGISTRO DE RECHAZO DE NECESIDADES
    # =========================================================================
    def guardar_rechazo_necesidad(self, usuario_id, necesidad_id):
        """Inserta el registro de exclusión para que el donante no vuelva a ver la solicitud."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            query = "INSERT IGNORE INTO necesidades_rechazadas (usuario_id, necesidad_id, fecha_rechazo) VALUES (%s, %s, NOW())"
            cursor.execute(query, (usuario_id, necesidad_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al guardar rechazo en DB: {e}")
            return False
        finally:
            conn.close()
            
    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================

    def obtener_categorias(self):
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener categorías: {e}")
            return []
        finally:
            conn.close()

    def actualizar_estado_donacion(self, donacion_id, nuevo_estado, fundacion_id=None):
        """Actualiza el estado de la donación validando que pertenezca a la fundación"""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            if fundacion_id:
                query = "UPDATE donaciones SET estado_donante = %s WHERE id = %s AND fundacion_id = %s"
                cursor.execute(query, (nuevo_estado, donacion_id, fundacion_id))
            else:
                query = "UPDATE donaciones SET estado_donante = %s WHERE id = %s"
                cursor.execute(query, (nuevo_estado, donacion_id))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error al actualizar estado en DB: {e}")
            return False
        finally:
            conn.close()
            
   # Ejemplo para contar monetarias de un donador
    def obtener_estadisticas_donador(self, usuario_id):
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            u_id = int(usuario_id)
            query = """
                SELECT 
                    SUM(CASE WHEN tipo = 'fisico' AND estado_donante = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
                    SUM(CASE WHEN tipo = 'fisico' AND estado_donante = 'recibido' THEN 1 ELSE 0 END) as recibidas,
                    SUM(CASE WHEN tipo = 'fisico' AND estado_donante = 'rechazado' THEN 1 ELSE 0 END) as rechazadas,
                    SUM(CASE WHEN tipo = 'monetario' THEN 1 ELSE 0 END) as monetarias
                FROM donaciones 
                WHERE usuario_id = %s
            """
            cursor.execute(query, (u_id,))
            resultado = cursor.fetchone()
            
            # --- CORRECCIÓN AQUÍ: Convertimos todo a int para evitar problemas de formato ---
            if resultado:
                stats_limpias = {
                    'pendientes': int(resultado.get('pendientes') or 0),
                    'recibidas':  int(resultado.get('recibidas') or 0),
                    'rechazadas': int(resultado.get('rechazadas') or 0),
                    'monetarias': int(resultado.get('monetarias') or 0)
                }
            else:
                stats_limpias = {'pendientes': 0, 'recibidas': 0, 'rechazadas': 0, 'monetarias': 0}
            
            print(f"DEBUG: Resultado limpio del modelo: {stats_limpias}")
            return stats_limpias

        except Exception as e:
            print(f"Error en estadísticas: {e}")
            return {'pendientes': 0, 'recibidas': 0, 'rechazadas': 0, 'monetarias': 0}
        finally:
            conn.close()
            
    def obtener_estadisticas_fundacion(self, fundacion_id):
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN estado_donante = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
                    SUM(CASE WHEN estado_donante = 'recibido' THEN 1 ELSE 0 END) as recibidas,
                    SUM(CASE WHEN estado_donante = 'rechazado' THEN 1 ELSE 0 END) as rechazadas,
                    SUM(CASE WHEN categoria_id = 1 THEN 1 ELSE 0 END) as alimentos,
                    SUM(CASE WHEN categoria_id = 2 THEN 1 ELSE 0 END) as ropa,
                    SUM(CASE WHEN categoria_id NOT IN (1, 2) THEN 1 ELSE 0 END) as otros
                FROM donaciones 
                WHERE fundacion_id = %s
            """
            cursor.execute(query, (fundacion_id,))
            resultado = cursor.fetchone()

            if not resultado or resultado['total'] is None:
                return {
                    'pendientes': 0, 'recibidas': 0, 'rechazadas': 0,
                    'alimentos': 0, 'ropa': 0, 'otros': 0, 'total': 0
                }
            
            return {k: (v if v is not None else 0) for k, v in resultado.items()}

        except Exception as e:
            print(f"Error en estadísticas: {e}")
            return {
                'pendientes': 0, 'recibidas': 0, 'rechazadas': 0,
                'alimentos': 0, 'ropa': 0, 'otros': 0, 'total': 0
            }
        finally:
            conn.close()
            
    def obtener_donacion_por_id(self, donacion_id):
        """NUEVO: Obtiene una donación específica para conocer su necesidad_id vinculada."""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM donaciones WHERE id = %s"
            cursor.execute(query, (donacion_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"❌ Error en obtener_donacion_por_id: {e}")
            return None
        finally:
            conn.close()        
            

    def cambiar_estado_donacion(self, id, nuevo_estado):
        """
        Este es el método que tu controlador llamará para:
        1. Aceptar (estado='recibido')
        2. Rechazar (estado='rechazado')
        3. Eliminar (estado='eliminado')
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            sql = "UPDATE donaciones SET estado_donante = %s WHERE id = %s"
            cursor.execute(sql, (nuevo_estado, id))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"❌ Error al actualizar estado de donación {id}: {e}")
            return False
        finally:
            conn.close()
            
# =========================================================================
    # DONACIONES MONETARIAS (POR IMPLEMENTAR)
# =========================================================================   

    def registrar_donacion_monetaria(self, donador_id, fundacion_id, categoria_id, monto, descripcion, referencia=None):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # Ahora usa el categoria_id que viene del controlador (el 5)
            cursor.execute("""
                INSERT INTO donaciones 
                (usuario_id, fundacion_id, categoria_id, cantidad, descripcion,
                tipo, estado_donante, fecha)
                VALUES (%s, %s, %s, %s, %s, 'monetario', 'gestionada', NOW())
            """, (donador_id, fundacion_id, categoria_id, monto, descripcion))
            
            donacion_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO transacciones
                (donacion_id, usuario_id, fundacion_id, monto, referencia, estado, fecha)
                VALUES (%s, %s, %s, %s, %s, 'aprobado', NOW())
            """, (donacion_id, donador_id, fundacion_id, monto, referencia or ''))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al registrar donación monetaria: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_historial_monetario(self, usuario_id_o_fundacion_id, es_fundacion=False):
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            if es_fundacion:
                # Para fundación: busca por fundacion_id
                cursor.execute("""
                    SELECT d.id, d.descripcion, d.fecha, d.cantidad AS monto,
                        u.nombre AS nombre_donante,
                        t.referencia, t.estado AS estado_transaccion,
                        t.monto AS monto_real
                    FROM donaciones d
                    LEFT JOIN usuarios u    ON d.usuario_id  = u.id
                    LEFT JOIN transacciones t ON t.donacion_id = d.id
                    WHERE d.fundacion_id = %s AND d.tipo = 'monetario'
                    ORDER BY d.fecha DESC
                """, (usuario_id_o_fundacion_id,))
            else:
                # Para donante: busca por usuario_id
                cursor.execute("""
                    SELECT d.id, d.descripcion, d.fecha, d.cantidad AS monto,
                        fun.nombre AS fundacion_nombre,
                        t.referencia, t.estado AS estado_transaccion,
                        t.monto AS monto_real
                    FROM donaciones d
                    LEFT JOIN fundaciones fun ON d.fundacion_id = fun.id
                    LEFT JOIN transacciones t  ON t.donacion_id  = d.id
                    WHERE d.usuario_id = %s AND d.tipo = 'monetario'
                    ORDER BY d.fecha DESC
                """, (usuario_id_o_fundacion_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error en get_historial_monetario: {e}")
            return []
        finally:
            if conn: conn.close()
            
    # ... (Tus otros métodos existentes como registrar_donacion_monetaria y get_historial_monetario)

    def get_historial_monetario_detallado(self, fundacion_id):
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            # Agregamos 'c.nombre AS nombre_categoria' y el JOIN
            query = """
                SELECT d.id, d.descripcion, d.fecha, d.cantidad AS monto,
                       u.nombre AS nombre_donante, t.referencia, 
                       t.estado AS estado_transaccion,
                       c.nombre AS nombre_categoria
                FROM donaciones d
                LEFT JOIN usuarios u ON d.usuario_id = u.id
                LEFT JOIN transacciones t ON t.donacion_id = d.id
                LEFT JOIN categorias c ON d.categoria_id = c.id
                WHERE d.fundacion_id = %s AND d.tipo = 'monetario'
                ORDER BY d.fecha DESC
            """
            cursor.execute(query, (fundacion_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
        finally:
            if conn: conn.close()
            
    # En models/donacion_model.py

    def guardar_metodo_pago(self, usuario_id, token, ultimos_4, marca):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            query = "INSERT INTO metodos_pago (usuario_id, token_pasarela, ultimos_4, marca) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (usuario_id, token, ultimos_4, marca))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar tarjeta: {e}")
            return False
        finally:
            conn.close()

    def obtener_metodos_usuario(self, usuario_id):
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            # Agregué 'token_pasarela' a la lista de campos
            cursor.execute("""
                SELECT id, token_pasarela, ultimos_4, marca 
                FROM metodos_pago 
                WHERE usuario_id = %s
            """, (usuario_id,))
            return cursor.fetchall()
        finally:
            conn.close()
            
    def obtener_datos_completos_donador(self, usuario_id):
        """
        Centraliza la obtención de estadísticas.
        """
        stats = self.obtener_estadisticas_donador(usuario_id) or {}
        return {
            'pendientes': stats.get('pendientes', 0) or 0,
            'recibidas':  stats.get('recibidas', 0) or 0,
            'rechazadas': stats.get('rechazadas', 0) or 0,
            'monetarias': stats.get('monetarias', 0) or 0
        }   
        
    # =========================================================================
    #  - GESTIÓN DE EXCLUSIÓN MUTUA EN PASARELA DE PAGO -
    # =========================================================================

    def apartar_necesidad_en_pasarela(self, necesidad_id):
        """Cambia el estado temporalmente a 'en_proceso' para que desaparezca del carrusel de otros usuarios."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            query = "UPDATE necesidades SET estado = 'en_proceso' WHERE id = %s AND estado = 'disponible'"
            cursor.execute(query, (necesidad_id,))
            conn.commit()
            return cursor.rowcount > 0  # True si logró apartarla exitosamente
        except Exception as e:
            print(f"❌ Error al apartar necesidad {necesidad_id}: {e}")
            return False
        finally:
            conn.close()

    def liberar_necesidad_pasarela(self, necesidad_id):
        """Si el donante cancela la transacción en la pasarela, vuelve a poner la solicitud 'disponible'."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            query = "UPDATE necesidades SET estado = 'disponible' WHERE id = %s AND estado = 'en_proceso'"
            cursor.execute(query, (necesidad_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al liberar necesidad {necesidad_id}: {e}")
            return False
        finally:
            conn.close()  
            
    def actualizar_monto_recaudado(self, necesidad_id, monto):
        """Suma el monto de la donación monetaria actual al acumulado de la necesidad."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            # 🚀 CORRECCIÓN SENIOR: Usando 'monto_recaudado' según la estructura de tu DB
            query = """
                UPDATE necesidades 
                SET monto_recaudado = COALESCE(monto_recaudado, 0.00) + %s 
                WHERE id = %s
            """
            cursor.execute(query, (float(monto), int(necesidad_id)))
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al actualizar monto recaudado en necesidad {necesidad_id}: {e}")
            return False
        finally:
            conn.close()
             