import streamlit as st
from modulos.config.conexion import obtener_conexion


def verificar_usuario(Usuario, Contraseña, Rol):
    con = obtener_conexion()
    if not con:
        st.error("⚠️ No se pudo conectar a la base de datos.")
        return None
    else:
        # ✅ Guardar en el estado que la conexión fue exitosa
        st.session_state["conexion_exitosa"] = True

    try:
        cursor = con.cursor()
        # Modificamos la consulta para incluir el rol
        query =  "SELECT Usuario, Contraseña, Rol FROM Login WHERE Usuario = %s AND Contraseña = %s AND Rol = %s"
        cursor.execute(query, (Usuario, Contraseña, Rol))
        result = cursor.fetchone()
        
        if result:
            # Si se encontró un resultado, el rol coincide
            return result[0]
        else:
            # Si no hay resultado, las credenciales o el rol son incorrectos.
            # Para diferenciar si es un rol incorrecto vs credenciales incorrectas,
            # podríamos hacer una consulta adicional, pero por simplicidad, 
            # si la consulta de 3 campos falla, se considera 'incorrecto'.
            # Si quisiéramos diferenciar, podríamos primero verificar usuario/contraseña
            # y luego el rol. Por ahora, si no coincide todo, es 'None'.
            return None 
    finally:
        con.close()


def login():
    st.title("Inicio de sesión")

    # 🟢 Mostrar mensaje persistente si ya hubo conexión exitosa
    if st.session_state.get("conexion_exitosa"):
        st.success("✅ Conexión a la base de datos establecida correctamente.")

    Usuario = st.text_input("Usuario", key="Usuario_input")
    Contraseña = st.text_input("Contraseña", type="password", key="Contraseña_input")
    
    # Nuevo campo desplegable para el rol
    roles_posibles = ["administrador", "promotora", "miembro", "junta directiva"]
    roles_posibles = st.selectbox("Rol", roles_posibles, key="rol_input")

    if st.button("Iniciar sesión"):
        tipo = verificar_usuario(Usuario, Contraseña, Rol)
        if tipo:
            st.session_state["Usuario"] = Usuario
            st.session_state["tipo_usuario"] = tipo
            st.success(f"Bienvenido {usuario} ({Usuario}) 👋")
            st.session_state["sesion_iniciada"] = True
            st.rerun()
        else:
            st.error("❌ Credenciales o rol incorrectos.")


