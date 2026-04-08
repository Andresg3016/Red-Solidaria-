import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='donaciones_db',
        port=3307  # <--- Aquí va el puerto
    )