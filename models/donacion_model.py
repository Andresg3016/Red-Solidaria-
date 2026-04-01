from database.db import get_connection

class DonacionModel:
    def crear_donacion(self, usuario_id, categoria_id, descripcion, cantidad):
        conn = get_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO donaciones (usuario_id, categoria_id, descripcion, cantidad)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (usuario_id, categoria_id, descripcion, cantidad))
        conn.commit()
        conn.close()

    def obtener_categorias(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM categorias")
        categorias = cursor.fetchall()
        conn.close()
        return categorias

    def donaciones_por_usuario(self, usuario_id):
        conn = get_connection()
        cursor = conn.cursor()
        query = """
        SELECT d.id, c.nombre, d.descripcion, d.cantidad, d.estado, d.fecha
        FROM donaciones d
        JOIN categorias c ON d.categoria_id = c.id
        WHERE d.usuario_id = %s
        ORDER BY d.fecha DESC
        """
        cursor.execute(query, (usuario_id,))
        donaciones = cursor.fetchall()
        conn.close()
        return donaciones
