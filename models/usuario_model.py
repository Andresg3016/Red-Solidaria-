from database.db import get_connection

class Usuario:
    def __init__(self, id = None, nombre = None, correo = None, password = None, rol_id = None, estado = None, fecha_registro = None):
        self.id = id
        self.nombre = nombre
        self.correo = correo
        self.password = password
        self.rol_id = rol_id
        self.estado = estado
        self.fecha_registro = fecha_registro

class UsuarioModel:
    def crear_usuario(self, usuario):
        
        conn = get_connection()
        cursor = conn.cursor()
        
        if usuario.rol_id == 2:
            estado = 'pendiente'
        else:
            estado = 'aprobado'
        
        query = """INSERT INTO usuarios (nombre, correo, password, rol_id, estado)
        VALUES (%s,%s,%s,%s,%s)
        """
        
        cursor.execute(query,(
            usuario.nombre,
            usuario.correo,
            usuario.password,
            usuario.rol_id,
            estado
        ))
        
        conn.commit()
        conn.close()
        
def obtener_usuario_por_correo(self, correo):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM usuarios WHERE correo = %s"
    cursor.execute(query, (correo,))

    data = cursor.fetchone()

    conn.close()

    if data:
        return Usuario(**data)
    return None