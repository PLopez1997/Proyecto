import streamlit as st
from modulos.config.conexion import obtener_conexion

def verificar_usuario(Usuario, Contraseña, Rol):
    con = obtener_conexion()
    if not con:
        st.error("⚠️ No se pudo conectar a la base de datos.")
        return None
    else:
        st.session_state["conexion_exitosa"] = True

    try:
        cursor = con.cursor()

        query = """
            SELECT Usuario, Contraseña, Rol 
            FROM Login WHERE Usuario = %s AND Contraseña = %s AND Rol = %s
        """
        cursor.execute(query, (Usuario, Contraseña, Rol))
        result = cursor.fetchone()

        if result:
            return result[2]  # rol
        else:
            return None

    finally:
        con.close()


def login():
    st.title("Inicio de sesión")

    if st.session_state.get("conexion_exitosa"):
        st.success("✅ Conexión a la base de datos establecida correctamente.")

    Usuario = st.text_input("Usuario")
    Contraseña = st.text_input("Contraseña", type="password")
    Roles = ["administrador", "promotora", "miembro", "junta directiva"]
    Rol = st.selectbox("Rol", Roles)

    if st.button("Iniciar sesión"):
        tipo = verificar_usuario(Usuario, Contraseña, Rol)

        if tipo:
            st.session_state["Usuario"] = Usuario
            st.session_state["tipo_usuario"] = tipo
            st.session_state["sesion_iniciada"] = True
              
           
# AQUÍ ESTÁ LA MAGIA DEL FILTRO POR GRUPO
            st.session_state['grupo_id'] = usuario_validado['Id_grupo'] 
    
            st.success("Login exitoso")
        
#CODIGOS EXTRA


            
            st.rerun()
        else:
            st.error("❌ Credenciales o rol incorrectos.")





