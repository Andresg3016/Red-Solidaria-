from database.db import get_connection

class DonacionModel:
    
    # ================= MÉTODOS DE DONACIONES (HISTORIAL Y REGISTRO) =================

    def registrar_donacion(self, donador_id, fundacion_id, categoria_id, cantidad, descripcion):
        """Registra una nueva donación en la base de datos"""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            query = """INSERT INTO donaciones 
                        (usuario_id, fundacion_id, categoria_id, cantidad, descripcion, estado, fecha) 
                        VALUES (%s, %s, %s, %s, %s, 'pendiente', NOW())"""
            cursor.execute(query, (donador_id, fundacion_id, categoria_id, cantidad, descripcion))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al registrar donación: {e}")
            return False
        finally:
            conn.close()

    def donaciones_por_usuario(self, usuario_id):
        """Historial de donaciones para el Panel del Donador (Versión Simple)"""
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """SELECT d.id, c.nombre as categoria, d.descripcion, d.cantidad, d.estado, d.fecha 
                    FROM donaciones d JOIN categorias c ON d.categoria_id = c.id 
                    WHERE d.usuario_id = %s ORDER BY d.fecha DESC"""
        cursor.execute(query, (usuario_id,))
        donaciones = cursor.fetchall()
        conn.close()
        return donaciones

    def obtener_donaciones_por_fundacion(self, fundacion_id, q=None, donante=None, categoria=None, estado=None):
        """Filtros multicriterio para el Panel de la Fundación"""
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            # Cambiamos a fundacion_id y añadimos JOINS para nombres reales
            query = """SELECT d.*, u.nombre as nombre_donante, c.nombre as nombre_categoria 
                       FROM donaciones d
                       JOIN usuarios u ON d.usuario_id = u.id
                       JOIN categorias c ON d.categoria_id = c.id
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
            print(f"Error multicriterio fundacion: {e}")
            return []
        finally:
            conn.close()

    # ================= MÉTODOS DE NECESIDADES (MURO DE AYUDA) =================

    def crear_necesidad(self, fundacion_id, categoria_id, cantidad, urgencia, fecha_limite, ubicacion, telefono, descripcion):
        """Crea una solicitud de ayuda urgente (Mantiene todos tus parámetros originales)"""
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
            print(f"Error al obtener necesidades: {e}")
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
            print(f"Error al obtener necesidad por ID: {e}")
            return None
        finally:
            conn.close()

    # ================= MÉTODOS AUXILIARES =================

    def obtener_categorias(self):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre FROM categorias")
        categorias = cursor.fetchall()
        conn.close()
        return categorias
    
    # ================= MÉTODOS DE FILTRADO (MULTICRITERIO ADICIONALES) =================

    def obtener_donaciones_por_usuario_filtrado(self, usuario_id, q=None, categoria=None, estado=None):
        """Filtros multicriterio para el historial personal del Donador"""
        conn = get_connection()
        print(f"DEBUG: Filtrando historial para donador ID: {usuario_id}")
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT d.*, c.nombre as categoria_nombre, u.nombre as fundacion_nombre 
                FROM donaciones d
                JOIN categorias c ON d.categoria_id = c.id
                JOIN usuarios u ON d.fundacion_id = u.id
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
            resultado = cursor.fetchall()
            print(f"DEBUG: Se encontraron {len(resultado)} donaciones")
            return resultado
        except Exception as e:
            print(f"ERROR en obtener_donaciones_por_usuario_filtrado: {e}")
            return []
        finally:
            if conn:
                conn.close()

    # Fin del archivo DonacionModel - Red Solidaria