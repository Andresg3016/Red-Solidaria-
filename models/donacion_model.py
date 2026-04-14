from database.db import get_connection
import mysql.connector

class DonacionModel:
    
    # =========================================================================
    # MÉTODOS DE DONACIONES (HISTORIAL Y REGISTRO)
    # =========================================================================

    def registrar_donacion(self, donador_id, fundacion_ids, categoria_id, cantidad, descripcion):
        """Registra una nueva donación y la asocia a varias fundaciones en donaciones_fundaciones"""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            c_id = int(categoria_id) if categoria_id else 0
            # Insertar en donaciones (solo una vez)
            query = """INSERT INTO donaciones 
                        (usuario_id, categoria_id, cantidad, descripcion, estado, fecha) 
                        VALUES (%s, %s, %s, %s, 'pendiente', NOW())"""
            cursor.execute(query, (donador_id, c_id, cantidad, descripcion))
            donacion_id = cursor.lastrowid
            # Insertar en donaciones_fundaciones para cada fundación
            query_df = "INSERT INTO donaciones_fundaciones (donacion_id, fundacion_id, estado) VALUES (%s, %s, 'pendiente')"
            for f_id in fundacion_ids:
                if f_id and str(f_id).isdigit():
                    cursor.execute(query_df, (donacion_id, int(f_id)))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error CRÍTICO al registrar donación: {e}")
            return False
        finally:
            conn.close()

    def donaciones_por_usuario(self, usuario_id):
        """Historial para el Panel del Donador (Lista simple)"""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            # LEFT JOIN: Para que si falta categoría, la donación no desaparezca del historial
            query = """SELECT d.id, c.nombre as categoria, d.descripcion, d.cantidad, d.estado, d.fecha 
                        FROM donaciones d 
                        LEFT JOIN categorias c ON d.categoria_id = c.id 
                        WHERE d.usuario_id = %s 
                        ORDER BY d.fecha DESC"""
            cursor.execute(query, (usuario_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en donaciones_por_usuario: {e}")
            return []
        finally:
            conn.close()

    def obtener_donaciones_por_fundacion(self, fundacion_id, q=None, donante=None, categoria=None, estado=None):
        """Filtros multicriterio para el Panel de la Fundación (Visible para Camila Gonzales)"""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT d.*, u.nombre as nombre_donante, c.nombre as nombre_categoria, df.estado as estado_fundacion
                FROM donaciones d
                JOIN usuarios u ON d.usuario_id = u.id
                LEFT JOIN categorias c ON d.categoria_id = c.id
                LEFT JOIN donaciones_fundaciones df ON d.id = df.donacion_id
                WHERE df.fundacion_id = %s
            """
            params = [fundacion_id]

            print(f"[PY-DEBUG] Valor recibido para estado: '{estado}'")

            if q:
                query += " AND d.descripcion LIKE %s"
                params.append(f"%{q}%")
            if donante:
                query += " AND u.nombre LIKE %s"
                params.append(f"%{donante}%")
            if categoria:
                query += " AND c.nombre = %s"
                params.append(categoria)
            if estado:
                query += " AND df.estado = %s"
                params.append(estado)

            print(f"[PY-DEBUG] Consulta SQL final: {query}")
            print(f"[PY-DEBUG] Parámetros: {params}")

            query += " ORDER BY d.fecha DESC"
            cursor.execute(query, tuple(params))
            resultados = cursor.fetchall()
            print(f"[PY-DEBUG] Resultados encontrados: {len(resultados)}")
            return resultados
        except Exception as e:
            print(f"Error en filtros fundacion: {e}")
            return []
        finally:
            conn.close()

    def obtener_donaciones_por_usuario_filtrado(self, usuario_id, q=None, categoria=None, estado=None):
        """Filtros multicriterio para el historial personal del Donador, mostrando el estado real por fundación"""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT d.*, c.nombre as categoria_nombre, f.nombre as fundacion_nombre,
                       GROUP_CONCAT(df.estado) as estados_fundaciones
                FROM donaciones d
                LEFT JOIN categorias c ON d.categoria_id = c.id
                LEFT JOIN donaciones_fundaciones df ON d.id = df.donacion_id
                LEFT JOIN fundaciones fun ON df.fundacion_id = fun.id
                LEFT JOIN usuarios f ON fun.usuario_id = f.id
                WHERE d.usuario_id = %s
            """
            params = [usuario_id]

            if q:
                query += " AND d.descripcion LIKE %s"
                params.append(f"%{q}%")
            if categoria:
                query += " AND d.categoria_id = %s"
                params.append(categoria)

            query += " GROUP BY d.id ORDER BY d.fecha DESC"
            cursor.execute(query, tuple(params))
            donaciones = cursor.fetchall()

            # Determinar el estado global de la donación para el donante
            for d in donaciones:
                estados = (d.get('estados_fundaciones') or '').split(',')
                if not estados or estados == ['']:
                    d['estado_donante'] = 'pendiente'
                elif all(e == 'aceptada' for e in estados):
                    d['estado_donante'] = 'recibido'
                elif all(e == 'rechazada' for e in estados):
                    d['estado_donante'] = 'rechazado'
                elif 'pendiente' in estados:
                    d['estado_donante'] = 'pendiente'
                elif 'aceptada' in estados:
                    d['estado_donante'] = 'recibido'
                elif 'rechazada' in estados:
                    d['estado_donante'] = 'rechazado'
                else:
                    d['estado_donante'] = 'pendiente'
            # Filtro por estado si se solicita
            if estado:
                donaciones = [d for d in donaciones if d['estado_donante'] == estado]
            return donaciones
        except Exception as e:
            print(f"Error en historial filtrado donador: {e}")
            return []
        finally:
            conn.close()

    # =========================================================================
    # MÉTODOS DE NECESIDADES (MURO DE AYUDA - RED SOLIDARIA)
    # =========================================================================

    def crear_necesidad(self, fundacion_id, categoria_id, cantidad, urgencia, fecha_limite, ubicacion, telefono, descripcion):
        """Crea una solicitud de ayuda urgente para las fundaciones"""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            query = """INSERT INTO necesidades 
                        (fundacion_id, categoria_id, cantidad, tipo_urgencia, fecha_limite, ubicacion, telefono, descripcion, estado) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pendiente')"""
            cursor.execute(query, (int(fundacion_id), categoria_id, cantidad, urgencia, fecha_limite, ubicacion, telefono, descripcion))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al crear necesidad: {e}")
            return False
        finally:
            conn.close()

    def obtener_necesidades_activas(self, q=None, cat=None):
        """Trae solicitudes activas filtradas para el Muro del Donador"""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """SELECT n.*, u.nombre as nombre_fundacion 
                        FROM necesidades n 
                        JOIN usuarios u ON n.fundacion_id = u.id 
                        WHERE n.estado = 'pendiente' AND u.estado = 'aprobado'"""
            params = []
            if q:
                query += " AND n.descripcion LIKE %s"
                params.append(f"%{q}%")
            if cat:
                query += " AND n.categoria_id = %s"
                params.append(cat)
            query += " ORDER BY n.fecha DESC"
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en obtener_necesidades_activas: {e}")
            return []
        finally:
            conn.close()

    def obtener_necesidad_por_id(self, necesidad_id):
        """Obtiene una necesidad específica para pre-llenar el formulario de donación"""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """SELECT n.*, u.nombre as nombre_fundacion, u.id as fundacion_id
                        FROM necesidades n
                        JOIN usuarios u ON n.fundacion_id = u.id
                        WHERE n.id = %s"""
            cursor.execute(query, (necesidad_id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error en obtener_necesidad_por_id: {e}")
            return None
        finally:
            conn.close()

    # =========================================================================
    # MÉTODOS AUXILIARES Y CATEGORÍAS
    # =========================================================================

    def obtener_categorias(self):
        """Lista de categorías para los select de los formularios"""
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

    def actualizar_estado_donacion(self, donacion_id, nuevo_estado):
        """Permite a la fundación marcar donaciones como recibidas o rechazadas"""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            query = "UPDATE donaciones SET estado = %s WHERE id = %s"
            cursor.execute(query, (nuevo_estado, donacion_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar estado: {e}")
            return False
        finally:
            conn.close()

# Fin del archivo DonacionModel - Red Solidaria