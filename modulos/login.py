import streamlit as st
from modulos.config.conexion import obtener_conexion

def verificar_usuario(Usuario, Contraseña, Rol):
    con = obtener_conexion()
    if not con:
        st.error("⚠️ No se pudo conectar a la base de datos.")
        return None

    try:
        # CAMBIO 1: Usamos dictionary=True para acceder a los datos por nombre
        cursor = con.cursor(dictionary=True)

        # CAMBIO 2: Pedimos también el Id_grupo y Id_distrito en la consulta
        # Nota: Asegúrate que tu tabla se llame 'Usuario' o 'Login' según corresponda en tu BD.
        # Aquí asumo que las columnas Id_grupo y Id_distrito YA EXISTEN en esa tabla.
        query = """
            SELECT Usuario, Rol, Id_grupo, Id_distrito 
            FROM Login 
            WHERE Usuario = %s AND Contraseña = %s AND Rol = %s
        """
        cursor.execute(query, (Usuario, Contraseña, Rol))
        result = cursor.fetchone()

        if result:
            return result  # Devolvemos TODA la fila (diccionario completo)
        else:
            return None

    except Exception as e:
        st.error(f"Error en la consulta: {e}")
        return None
    finally:
        if con.is_connected():
            con.close()

def login():
    st.title("Inicio de sesión")

    # Inputs del usuario
    Usuario = st.text_input("Usuario")
    Contraseña = st.text_input("Contraseña", type="password")
    Roles = ["administrador", "promotora", "miembro", "junta directiva"]
    Rol = st.selectbox("Rol", Roles)

    if st.button("Iniciar sesión"):
        # Llamamos a la función
        usuario_validado = verificar_usuario(Usuario, Contraseña, Rol)

        if usuario_validado:
            # --- CAMBIO 3: Aquí adentro va la lógica de sesión ---
            
            st.success(f"Bienvenido {usuario_validado['Usuario']}")
            
            # Guardamos las variables críticas en la sesión
            st.session_state["logged_in"] = True
            st.session_state["Usuario"] = usuario_validado['Usuario']
            st.session_state["user_role"] = usuario_validado['Rol']
            
            # Guardamos los IDs de alcance (Grupo o Distrito)
            # .get() evita errores si la columna viene vacía (None)
            st.session_state['grupo_id'] = usuario_validado.get('Id_grupo')
            st.session_state['distrito_id'] = usuario_validado.get('Id_distrito')
            
            st.rerun() # Recargamos para ir a la página principal
        else:
            st.error("❌ Credenciales o rol incorrectos.")

# Esta parte final ya no es necesaria aquí porque la metimos dentro del 'if st.button'
