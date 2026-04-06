from database.db import get_connection
import mysql.connector

class DonacionModel:
    
    # =========================================================================
    # MÉTODOS DE DONACIONES (HISTORIAL Y REGISTRO)
    # =========================================================================

    def registrar_donacion(self, donador_id, fundacion_id, categoria_id, cantidad, descripcion):
        """Registra una nueva donación asegurando que los IDs sean enteros para evitar NULLs"""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            # CORRECCIÓN DE SEGURIDAD: Evita que entren NULLs accidentales
            f_id = int(fundacion_id) if fundacion_id else 0
            c_id = int(categoria_id) if categoria_id else 0
            
            query = """INSERT INTO donaciones 
                        (usuario_id, fundacion_id, categoria_id, cantidad, descripcion, estado, fecha) 
                        VALUES (%s, %s, %s, %s, %s, 'pendiente', NOW())"""
            
            cursor.execute(query, (donador_id, f_id, c_id, cantidad, descripcion))
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
            # CORRECCIÓN: LEFT JOIN en categorias para que se vean registros aunque tengan categoria_id NULL o 0
            query = """SELECT d.*, u.nombre as nombre_donante, c.nombre as nombre_categoria 
                       FROM donaciones d
                       JOIN usuarios u ON d.usuario_id = u.id
                       LEFT JOIN categorias c ON d.categoria_id = c.id
                       WHERE d.fundacion_id = %s"""
            params = [fundacion_id]

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
                query += " AND d.estado = %s"
                params.append(estado)

            query += " ORDER BY d.fecha DESC"
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en filtros fundacion: {e}")
            return []
        finally:
            conn.close()

    def obtener_donaciones_por_usuario_filtrado(self, usuario_id, q=None, categoria=None, estado=None):
        """Filtros multicriterio para el historial personal del Donador"""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT d.*, c.nombre as categoria_nombre, u.nombre as fundacion_nombre 
                FROM donaciones d
                LEFT JOIN categorias c ON d.categoria_id = c.id
                LEFT JOIN usuarios u ON d.fundacion_id = u.id
                WHERE d.usuario_id = %s
            """
            params = [usuario_id]

            if q:
                query += " AND d.descripcion LIKE %s"
                params.append(f"%{q}%")
            if categoria:
                query += " AND d.categoria_id = %s"
                params.append(categoria)
            if estado:
                query += " AND d.estado = %s"
                params.append(estado)

            query += " ORDER BY d.fecha DESC"
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
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

    def obtener_todas_las_necesidades(self):
        """Trae todas las solicitudes activas para el Muro del Donador"""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """SELECT n.*, u.nombre as nombre_fundacion 
                        FROM necesidades n 
                        JOIN usuarios u ON n.fundacion_id = u.id 
                        WHERE n.estado = 'pendiente' 
                        ORDER BY n.fecha_creacion DESC"""
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en obtener_todas_las_necesidades: {e}")
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