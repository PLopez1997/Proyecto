import streamlit as st
from modulos.config.conexion import obtener_conexion

def verificar_usuario(Usuario, Contraseña, Rol):
    con = obtener_conexion()
    if not con:
        st.error("⚠️ No se pudo conectar a la base de datos.")
        return None

    try:
        # Usamos dictionary=True para manejar los datos ordenadamente
        cursor = con.cursor(dictionary=True)

        # IMPORTANTE: Pedimos las columnas Id_grupo y Id_distrito
        query = """
            SELECT Usuario, Rol, Id_grupo, Id_distrito 
            FROM Login 
            WHERE Usuario = %s AND Contraseña = %s AND Rol = %s
        """
        cursor.execute(query, (Usuario, Contraseña, Rol))
        result = cursor.fetchone()

        # Retornamos TODA la fila (el diccionario completo)
        return result 

    except Exception as e:
        st.error(f"Error en la consulta: {e}")
        return None
    finally:
        if con.is_connected():
            con.close()

def login_page():
    st.title("Inicio de sesión - GAPC")

    Usuario = st.text_input("Usuario")
    Contraseña = st.text_input("Contraseña", type="password")
    Roles = ["administrador", "promotora", "miembro", "junta directiva"] # Asegúrate que coincidan con tu BD
    Rol = st.selectbox("Rol", Roles)

    if st.button("Iniciar sesión"):
        user_data = verificar_usuario(Usuario, Contraseña, Rol)

        if user_data:
            # --- GUARDAR SESIÓN (Llave maestra: 'logged_in') ---
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = user_data['Rol']
            st.session_state['user_name'] = user_data['Usuario']
            
            # Guardamos el alcance (Grupo o Distrito) usando .get() para evitar errores si es nulo
            st.session_state['grupo_id'] = user_data.get('Id_grupo')
            st.session_state['distrito_id'] = user_data.get('Id_distrito')
            
            st.success("¡Bienvenido! Redirigiendo...")
            st.rerun() # Recarga la página para que app.py tome el control
        else:
            st.error("❌ Credenciales incorrectas o rol no coincide.")
