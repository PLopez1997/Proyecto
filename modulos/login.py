import streamlit as st
import time

# --- GESTIÓN DE IMPORTACIONES DE CONEXIÓN ---
try:
    from modulos.config.conexion import obtener_conexion
except ImportError:
    try:
        from config.conexion import obtener_conexion
    except ImportError:
        try:
            from conexion import obtener_conexion
        except ImportError:
            st.error("❌ Error crítico: No se encuentra la conexión.")
            st.stop()

# ==============================================================================
# 1️⃣ VERIFICAR USUARIO NORMAL (TABLA LOGIN)
# ==============================================================================
def verificar_usuario_login(usuario, contrasena, rol):
    con = obtener_conexion()
    if not con:
        return None

    try:
        cursor = con.cursor(dictionary=True)

        query = """
            SELECT Usuario, Contraseña, Rol, Id_grupo, Id_distrito
            FROM Login 
            WHERE Usuario = %s AND Contraseña = %s AND Rol = %s
        """

        cursor.execute(query, (usuario, contrasena, rol))
        return cursor.fetchone()

    finally:
        con.close()

# ==============================================================================
# 2️⃣ OBTENER DISTRITO REAL DESDE TABLA PROMOTORA
# ==============================================================================
def obtener_distrito_promotora(usuario):
    con = obtener_conexion()
    if not con:
        return None

    try:
        cursor = con.cursor(dictionary=True)

        query = """

