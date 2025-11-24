import streamlit as st
import time

# --- IMPORTAR CONEXIÓN ---
try:
    from modulos.config.conexion import obtener_conexion
except ImportError:
    try:
        from config.conexion import obtener_conexion
    except ImportError:
        try:
            from conexion import obtener_conexion
        except ImportError:
            st.error("❌ No se encontró el archivo de conexión.")
            st.stop()

# ==============================================================================
# VERIFICAR USUARIO DESDE TABLA PROMOTORA
# ==============================================================================
def verificar_usuario_promotora(usuario, contrasena):
    con = obtener_conexion()
    if not con:
        return None

    try:
        cursor = con.cursor(dictionary=True)

        # AHORA BUSCA EN TABLA PROMOTORA
        query = """
            SELECT 
                p.Usuario,
                p.Contraseña,
                p.Id_distrito
            FROM Promotora p
            WHERE p.Usuario = %s AND p.Contraseña = %s
        """

        cursor.execute(query, (usuario, contrasena))
        result = cursor.fetchone()
        return result

    except Exception as e:
        st.error(f"Error en la consulta: {e}")
        return None
    finally:
        con.close()

# ==============================================================================
# LOGIN PAGE
# ==============================================================================
def login_page():
    st.title("Inicio de sesión - GAPC")
    st.markdown("---")

    with st.form("login_form"):
        usuario = st.text_input("👤 Usuario")
        contrasena = st.text_input("🔑 Contraseña", type="password")

        rol = st.selectbox(
            "Seleccione su Rol",
            ["administrador", "promotora", "miembro", "junta directiva"]
        )

        distrito_seleccionado = None
        
        if rol == "promotora":
            st.info("📍 Verificación de Distrito")
            distrito_seleccionado = st.selectbox(
                "Seleccione el distrito:",
                [1, 2, 3]
            )

        submitted = st.form_submit_button("Iniciar sesión")

    if submitted:

        if rol != "promotora":
            st.error("⚠️ En este código solo estamos corrigiendo la parte de promotora.")
            return

        # -----------------------------
        # 1. VERIFICAR EN TABLA PROMOTORA
        # -----------------------------
        user_data = verificar_usuario_promotora(usuario, contrasena)

        if not user_data:
            st.error("❌ Usuario o contraseña incorrectos.")
            return

        # -----------------------------
        # 2. VALIDAR DISTRITO
        # -----------------------------
        distrito_db = user_data["Id_distrito"]

        if distrito_db is None:
            st.error("⛔ Error: Esta promotora no tiene distrito asignado en la base de datos.")
            return

        if int(distrito_db) != int(distrito_seleccionado):
            st.error(
                f"🚫 Acceso Denegado:\n"
                f"El usuario '{usuario}' está asignado al distrito {distrito_db}, "
                f"pero intentó acceder al distrito {distrito_seleccionado}."
            )
            return

        # -----------------------------
        # 3. LOGIN CORRECTO
        # -----------------------------
        st.success(f"✅ Bienvenida {usuario}. Acceso autorizado al Distrito {distrito_db}.")

        st.session_state["logged_in"] = True
        st.session_state["user_role"] = rol
        st.session_state["user_name"] = usuario
        st.session_state["id_distrito_actual"] = distrito_db

        time.sleep(1)
        st.rerun()


if __name__ == "__main__":
    login_page()

