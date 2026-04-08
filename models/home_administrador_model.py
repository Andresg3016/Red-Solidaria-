from database.db import get_connection

class HomeAdminModel:

    @classmethod
    def obtener_fundaciones_pendientes(cls):
        # Incluimos estado_validacion para mostrar el estado real de la fundación
        query = """
            SELECT 
                f.id, 
                f.nombre, 
                f.nit, 
                f.estado_validacion,
                u.correo, 
                u.fecha_registro, 
                u.estado
            FROM fundaciones f
            INNER JOIN usuarios u ON f.usuario_id = u.id
            ORDER BY u.fecha_registro DESC
        """
        connection = get_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as ex:
            print(f"Error en obtener: {ex}")
            return []
        finally:
            if connection:
                connection.close()
    @classmethod
    def aprobar_fundacion(cls, fundacion_id):
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                # 1. Obtener usuario_id desde la fundación
                sql_get = "SELECT usuario_id FROM fundaciones WHERE id = %s"
                cursor.execute(sql_get, (fundacion_id,))
                resultado = cursor.fetchone()

                if not resultado:
                    return False

                usuario_id = resultado[0]

                # 2. Activar usuario y poner en 'aprobado'
                sql_user = "UPDATE usuarios SET estado = 'aprobado' WHERE id = %s"
                cursor.execute(sql_user, (usuario_id,))

                # 3. Aprobar fundación
                sql_fund = "UPDATE fundaciones SET estado_validacion = 'aprobado' WHERE id = %s"
                cursor.execute(sql_fund, (fundacion_id,))

                connection.commit()
                return True
        except Exception as ex:
            print(f"Error al aprobar: {ex}")
            return False
        finally:
            if connection:
                connection.close()

    @classmethod
    def rechazar_fundacion(cls, fundacion_id):
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                # Obtener usuario_id
                sql_get = "SELECT usuario_id FROM fundaciones WHERE id = %s"
                cursor.execute(sql_get, (fundacion_id,))
                resultado = cursor.fetchone()

                if not resultado:
                    return False

                usuario_id = resultado[0]

                # Rechazar usuario
                sql_user = "UPDATE usuarios SET estado = 'rechazado' WHERE id = %s"
                cursor.execute(sql_user, (usuario_id,))

                # Rechazar fundación
                sql_fund = "UPDATE fundaciones SET estado_validacion = 'rechazado' WHERE id = %s"
                cursor.execute(sql_fund, (fundacion_id,))

                connection.commit()
                return True
        except Exception as ex:
            print(f"Error al rechazar: {ex}")
            return False
        finally:
            if connection:
                connection.close()

    @classmethod
    def registrar_fundacion_completo(cls, nombre, correo, password, rol_id, nit, organizacion):
        import mysql.connector
        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="donaciones_db"
            )
            cursor = connection.cursor()

            sql_user = """
                INSERT INTO usuarios (nombre, correo, password, rol_id, estado, fecha_registro)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(sql_user, (nombre, correo, password, rol_id, 'pendiente'))
            nuevo_usuario_id = cursor.lastrowid

            sql_fund = """
                INSERT INTO fundaciones (usuario_id, nombre, nit, estado_validacion) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_fund, (nuevo_usuario_id, organizacion, nit, 'pendiente'))

            connection.commit()
            return True
        except Exception as ex:
            print(f"¡ERROR CRÍTICO!: {ex}")
            return False
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    @classmethod
    def contar_pendientes(cls):
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                # Contamos usuarios con rol 3 (Fundación) que estén pendientes
                cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol_id = 3 AND estado = 'pendiente'")
                resultado = cursor.fetchone()
                return resultado[0] if resultado else 0
        except Exception as ex:
            print(f"Error en contador: {ex}")
            return 0
        finally:
            if connection:
                connection.close()

    @staticmethod
    def obtener_datos_fundacion(id_usuario):
        import mysql.connector
        conn = mysql.connector.connect(host='localhost', user='root', password='', database='donaciones_db')
        cursor = conn.cursor(dictionary=True)
        # Buscamos el correo (tabla usuarios) y el nombre (tabla fundaciones)
        sql = """
            SELECT u.correo, f.nombre 
            FROM usuarios u 
            JOIN fundaciones f ON u.id = f.usuario_id 
            WHERE u.id = %s
        """
        cursor.execute(sql, (id_usuario,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        return resultado            