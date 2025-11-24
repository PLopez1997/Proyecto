import streamlit as st
# Asegúrate de que esta ruta sea correcta según tu estructura de carpetas
try:
    from modulos.config.conexion import obtener_conexion
except ImportError:
    # Intento alternativo por si cambió la ruta
    from conexion import obtener_conexion

def verificar_usuario(Usuario, Contraseña, Rol):
    con = obtener_conexion()
    if not con:
        st.error("⚠️ No se pudo conectar a la base de datos.")
        return None

    try:
        cursor = con.cursor(dictionary=True)

        # Seleccionamos también el Id_distrito para validar
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

def login_page():
    st.title("Inicio de sesión - GAPC")

    # Contenedor para el formulario
    with st.form("login_form"):
        Usuario = st.text_input("Usuario")
        Contraseña = st.text_input("Contraseña", type="password")
        
        Roles = ["administrador", "promotora", "miembro", "junta directiva"]
        Rol = st.selectbox("Seleccione su Rol", Roles)
        
        # --- NUEVA LÓGICA: SELECTOR DE DISTRITO ---
        distrito_seleccionado = None
        
        if Rol == "promotora":
            st.info("👤 Como Promotora, confirme su zona de trabajo.")
            # Aquí el usuario selecciona el ID del distrito (ej: 1, 2, 3...)
            distrito_seleccionado = st.number_input(
                "Ingrese el Número de Distrito asignado", 
                min_value=1, 
                step=1,
                help="Debe coincidir con el distrito registrado en su usuario."
            )

        submitted = st.form_submit_button("Iniciar sesión")

    if submitted:
        if not Usuario or not Contraseña:
            st.warning("Por favor ingrese usuario y contraseña.")
            return

        # 1. Verificamos credenciales en la Base de Datos
        user_data = verificar_usuario(Usuario, Contraseña, Rol)

        if user_data:
            # 2. VALIDACIÓN EXTRA PARA PROMOTORA
            # Verificamos si el distrito que escribió coincide con el de la BD
            if Rol == "promotora":
                db_distrito = user_data.get('Id_distrito')
                
                # Si en la BD no tiene distrito o no coincide con el seleccionado:
                if db_distrito != distrito_seleccionado:
                    st.error(f"⛔ Error de Seguridad: El usuario '{Usuario}' no está autorizado para acceder al Distrito {distrito_seleccionado}. Su distrito registrado es el {db_distrito}.")
                    return # Detenemos el login aquí

            # --- SI PASA LAS VALIDACIONES, GUARDAMOS SESIÓN ---
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = user_data['Rol']
            st.session_state['user_name'] = user_data['Usuario']
            
            # Guardamos los IDs clave para usar en los otros archivos
            st.session_state['grupo_id'] = user_data.get('Id_grupo')
            
            # Aquí guardamos el distrito validado (ya sea el seleccionado o el de la BD)
            # Nota: Usamos 'id_distrito_actual' porque así lo llamamos en los archivos anteriores (distrito.py y promotora.py)
            st.session_state['id_distrito_actual'] = user_data.get('Id_distrito')
            
            st.success(f"¡Bienvenido! Accediendo al entorno de {Rol}...")
            st.rerun()
            
        else:
            st.error("❌ Credenciales incorrectas o el rol seleccionado no coincide con el usuario.")

# Para probarlo localmente si ejecutas este archivo solo
if __name__ == "__main__":
    login_page()
