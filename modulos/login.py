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
            st.error("❌ Error crítico: No se encuentra el archivo de conexión.")
            st.stop()


# ==============================================================================
# FUNCIÓN: CONSULTA A BASE DE DATOS
# ==============================================================================
def verificar_usuario(Usuario, Contraseña, Rol):
    con = obtener_conexion()
    if not con:
        st.error("⚠️ No se pudo conectar a la base de datos.")
        return None

    try:
        cursor = con.cursor(dictionary=True)

        query = """
            SELECT Usuario, Rol, Id_grupo, Id_distrito 
            FROM Login 
            WHERE Usuario = %s AND Contraseña = %s AND Rol = %s
        """
        cursor.execute(query, (Usuario, Contraseña, Rol))
        result = cursor.fetchone()
        return result

    except Exception as e:
        st.error(f"Error en la consulta: {e}")
        return None
    finally:
        if con.is_connected():
            con.close()


# ==============================================================================
# FUNCIÓN: PÁGINA DE LOGIN
# ==============================================================================
def login_page():
    st.title("Inicio de sesión - GAPC")
    st.markdown("---")

    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            Usuario = st.text_input("👤 Usuario")
        with col2:
            Contraseña = st.text_input("🔑 Contraseña", type="password")

        Roles = ["administrador", "promotora", "miembro", "junta directiva"]
        Rol = st.selectbox("Seleccione su Rol", Roles)

        # -----------------------------------------
        # SELECCIÓN DE DISTRITO PARA PROMOTORA
        # -----------------------------------------
        distrito_seleccionado = None
        if Rol == "promotora":
            distrito_seleccionado = st.selectbox(
                "Seleccione su distrito (1, 2 o 3):",
                [1, 2, 3],
                help="Debe coincidir con el distrito asignado en su usuario."
            )

        submitted = st.form_submit_button("Iniciar sesión", use_container_width=True)

    if submitted:
        if not Usuario or not Contraseña:
            st.warning("⚠️ Por favor ingrese usuario y contraseña.")
            return

        # Consultamos usuario
        user_data = verificar_usuario(Usuario, Contraseña, Rol)

        if user_data:

            # ============================================================
            # VALIDACIÓN DE DISTRITO EXCLUSIVA PARA PROMOTORA
            # ============================================================
            if Rol == "promotora":

                db_distrito_id = user_data.get("Id_distrito")

                # Caso 1: No tiene distrito asignado
                if db_distrito_id is None:
                    st.error("⛔ Error: Su usuario no tiene un distrito asignado en la base de datos.")
                    return

                # Caso 2: El distrito seleccionado NO coincide con el de BD
                if int(db_distrito_id) != int(distrito_seleccionado):
                    st.error(
                        f"🚫 Acceso Denegado:\n\n"
                        f"Usted seleccionó el Distrito {distrito_seleccionado}, "
                        f"pero su usuario solo tiene acceso al Distrito {db_distrito_id}."
                    )
                    return

            # GUARDAR SESIÓN
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = user_data['Rol']
            st.session_state['user_name'] = user_data['Usuario']
            st.session_state['grupo_id'] = user_data.get('Id_grupo')
            st.session_state['id_distrito_actual'] = user_data.get('Id_distrito')

            st.success(f"✅ Bienvenido/a {user_data['Usuario']}.")
            time.sleep(0.8)
            st.rerun()

        else:
            st.error("❌ Usuario, contraseña o rol incorrectos.")


if __name__ == "__main__":
    login_page()

