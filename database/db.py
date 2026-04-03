import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="donaciones_db"  # <--- Cambié "red_solidaria" por "donaciones_db"
    )