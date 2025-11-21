import mysql.connector
from mysql.connector import Error
import streamlit as st

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host='bofs0tswlhkcaaow8a72-mysql.services.clever-cloud.com',
            user='unjjfykaw275rydj',
            password='7DzfZb9rZr3VIJdX92DP',
            database='bofs0tswlhkcaaow8a72',
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


def get_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="bofs0tswlhkcaaow8a72-mysql.services.clever-cloud.com",
            user="unjjfykaw275rydj",      
            password="7DzfZb9rZr3VIJdX92DP",      # Si tienes contraseña en XAMPP/MAMP, ponla aquí
            database="bofs0tswlhkcaaow8a72" # <--- ¡IMPORTANTE! CAMBIA ESTO SI TU BD SE LLAMA DIFERENTE
        )
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None
        
    return connection
