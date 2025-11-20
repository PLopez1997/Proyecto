import streamlit as st
from modulos.config.conexion import obtener_conexion
from modulos.Venta          import mostrar_venta

def verificar_usuario(Usuario, Contraseña, Rol):
    con = obtener_conexion()
    if not con:
        st.error("⚠️ No se pudo conectar a la base de datos.")
        return None
    else:
        st.session_state["conexion_exitosa"] = True

    try:
        cursor = con.cursor()

        query = (
            "SELECT Usuario, Contraseña, Rol "
            "FROM Login WHERE Usuario = %s AND Contraseña = %s AND Rol = %s"
        )
        cursor.execute(query, (Usuario, Contraseña, Rol))
        result = cursor.fetchone()

        if result:
            # devolver el rol del usuario
            return result[2]
        else:
            return None

    finally:
        con.close()


def login():
    st.title("Inicio de sesión")

    if st.session_state.get("conexion_exitosa"):
        st.success("✅ Conexión a la base de datos establecida correctamente.")

    Usuario = st.text_input("Usuario", key="Usuario_input")
    Contraseña = st.text_input("Contraseña", type="password", key="Contraseña_input")

    # ahora sí creamos la variable Rol
    Roles = ["administrador", "promotora", "miembro", "junta directiva"]
    Rol = st.selectbox("Rol", Roles, key="rol_input")

    if st.button("Iniciar sesión"):
        tipo = verificar_usuario(Usuario, Contraseña, Rol)

        if tipo:
            st.session_state["Usuario"] = Usuario
            st.session_state["tipo_usuario"] = tipo
            st.session_state["sesion_iniciada"] = True

            st.success(f"Bienvenido {Usuario} ({tipo}) 👋")
            st.rerun()
        else:
            st.error("❌ Credenciales o rol incorrectos.")


