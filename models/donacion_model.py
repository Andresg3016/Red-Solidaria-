from database.db import get_connection

class DonacionModel:
    def crear_donacion(self, usuario_id, categoria_id, descripcion, cantidad):
        conn = get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO donaciones (usuario_id, categoria_id, descripcion, cantidad) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (usuario_id, categoria_id, descripcion, cantidad))
        conn.commit()
        conn.close()

    def obtener_categorias(self):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre FROM categorias")
        categorias = cursor.fetchall()
        conn.close()
        return categorias

    def donaciones_por_usuario(self, usuario_id):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """SELECT d.id, c.nombre, d.descripcion, d.cantidad, d.estado, d.fecha 
                   FROM donaciones d JOIN categorias c ON d.categoria_id = c.id 
                   WHERE d.usuario_id = %s ORDER BY d.fecha DESC"""
        cursor.execute(query, (usuario_id,))
        donaciones = cursor.fetchall()
        conn.close()
        return donaciones

    def obtener_donaciones_por_fundacion(self, usuario_id):
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            # Cambiamos fundacion_id por usuario_id para que no de error 1054
            query = "SELECT * FROM donaciones WHERE usuario_id = %s ORDER BY fecha DESC"
            cursor.execute(query, (usuario_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error home fundacion: {e}")
            return []
        finally:
            conn.close()

    def crear_necesidad(self, fundacion_id, tipo, meta, desc, fecha):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            query = """INSERT INTO necesidades (fundacion_id, tipo_urgencia, meta, descripcion, fecha_limite, estado) 
                       VALUES (%s, %s, %s, %s, %s, 'pendiente')"""
            cursor.execute(query, (int(fundacion_id), tipo, meta, desc, fecha))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error necesidad: {e}")
            return False
        finally:
            conn.close()