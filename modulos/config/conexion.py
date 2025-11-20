import mysql.connector
from mysql.connector import Error

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host='be5bmntqvmjb45dbc68h-mysql.services.clever-cloud.com',
            user='ufrsewvahgrdaghy',
            password='UxDnJbPxibZaLwBC6Xt1',
            database='be5bmntqvmjb45dbc68h',
            port=3306
        )
        if conexion.is_connected():
            print("✅ Conexión establecida")
            return conexion
        else:
            print("❌ Conexión fallida (is_connected = False)")
            return None
    except mysql.connector.Error as e:
        print(f"❌ Error al conectar: {e}")
        return None
