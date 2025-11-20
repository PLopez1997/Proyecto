# Asumiendo que 'st' y 'obtener_conexion' están definidos en el entorno de Streamlit
import streamlit as st

# Mock para la función obtener_conexion si no está definida
def obtener_conexion():
    # En una aplicación real, esto conectaría a tu base de datos
    st.warning("⚠️ Simulación: Conectando a la base de datos...")
    # Aquí deberías tener tu lógica real de conexión a la base de datos, por ejemplo:
    # import mysql.connector
    # try:
    #     con = mysql.connector.connect(
    #         host="localhost",
    #         user="your_username",
    #         password="your_password",
    #         database="your_database"
    #     )
    #     return con
    # except mysql.connector.Error as err:
    #     st.error(f"Error al conectar a la base de datos: {err}")
    #     return None
    return True # Simula una conexión exitosa para el entorno de Colab

def verificar_usuario(usuario, contrasena):
    con = obtener_conexion()
    if not con:
        st.error("⚠️ No se pudo conectar a la base de datos.")
        return None # Retornar None si no hay conexión a la DB
    else:
        # ✅ Guardar en el estado que la conexión fue exitosa
        st.session_state["conexion_exitosa"] = True

    try:
        # Lógica de verificación de usuario original, asumiendo 'con' es un objeto de conexión real
        cursor = con.cursor()
        query = "SELECT Tipo_usuario FROM USUARIO WHERE usuario = %s AND contrasena = %s"
        cursor.execute(query, (usuario, contrasena))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        # Asegúrate de cerrar la conexión si es un objeto de conexión real
        if con and hasattr(con, 'close'):
            con.close()

def login():
    st.title("Inicio de sesión")

    # Inicializar variables de estado de sesión si no existen
    if "logged_in_primary" not in st.session_state:
        st.session_state["logged_in_primary"] = False
    if "selected_role" not in st.session_state:
        st.session_state["selected_role"] = None
    if "selected_colab_role" not in st.session_state:
        st.session_state["selected_colab_role"] = None
    if "final_login_miembro" not in st.session_state:
        st.session_state["final_login_miembro"] = False
    if "final_login_colaborador" not in st.session_state:
        st.session_state["final_login_colaborador"] = False
    if "sesion_iniciada" not in st.session_state:
        st.session_state["sesion_iniciada"] = False
    if "usuario" not in st.session_state:
        st.session_state["usuario"] = None

    # 🟢 Mostrar mensaje persistente si ya hubo conexión exitosa
    if st.session_state.get("conexion_exitosa") and not st.session_state["sesion_iniciada"]:
        st.success("✅ Conexión a la base de datos establecida correctamente.")

    # --- Paso 1: Inicio de sesión primario ---
    if not st.session_state["logged_in_primary"]:
        usuario_input = st.text_input("Usuario", key="usuario_primary_input")
        contrasena_input = st.text_input("Contraseña", type="password", key="contrasena_primary_input")

        if st.button("Iniciar sesión"): 
            tipo = verificar_usuario(usuario_input, contrasena_input)
            if tipo:
                st.session_state["logged_in_primary"] = True
                st.session_state["usuario"] = usuario_input
                st.session_state["tipo_usuario_db"] = tipo # Guarda el tipo de usuario de la DB
                st.success(f"¡Bienvenido, {usuario_input}! Ahora selecciona tu rol.")
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas.")

    # --- Paso 2: Selección de rol general (Miembro o Colaborador) ---
    elif st.session_state["logged_in_primary"] and st.session_state["selected_role"] is None:
        st.subheader("Selecciona tu rol:")

        if st.button("Miembro"):
            st.session_state["selected_role"] = "miembro"
            st.session_state["final_login_miembro"] = True
            st.session_state["sesion_iniciada"] = True # Marca la sesión como iniciada para el miembro
            st.session_state["tipo_usuario"] = "miembro" # Establece el tipo de usuario para la sesión
            st.success(f"Bienvenido como Miembro ({st.session_state['usuario']}) 👋")
            st.rerun()

        if st.button("Colaborador"):
            st.session_state["selected_role"] = "colaborador"
            st.info("Para el rol de Colaborador, se requiere una selección de cargo y una contraseña adicional.")
            st.rerun()

    # --- Paso 3: Selección de cargo para Colaborador ---
    elif st.session_state["logged_in_primary"] and st.session_state["selected_role"] == "colaborador" and st.session_state["selected_colab_role"] is None:
        st.subheader("Selecciona tu cargo de Colaborador:")

        colaborador_roles = [
            "director de junta",
            "promotora",
            "tesorero",
            "secretario",
            "administrador"
        ]

        selected_colab_role = st.selectbox("Cargo", colaborador_roles, key="colab_role_selector")

        if st.button("Confirmar Cargo"):
            st.session_state["selected_colab_role"] = selected_colab_role
            st.rerun()

    # --- Paso 4: Contraseña adicional para el cargo de Colaborador seleccionado ---
    elif st.session_state["logged_in_primary"] and st.session_state["selected_role"] == "colaborador" and st.session_state["selected_colab_role"] is not None and not st.session_state["final_login_colaborador"]:
        st.subheader(f"Contraseña para {st.session_state['selected_colab_role']}")
        contrasena_cargo = st.text_input(f"Contraseña de {st.session_state['selected_colab_role']}", type="password", key="colab_cargo_pass_input")

        # Contraseñas de ejemplo para cada cargo de colaborador
        COLABORADOR_ROLES_PASSWORDS = {
            "director de junta": "junta123",
            "promotora": "promo123",
            "tesorero": "tesoro123",
            "secretario": "secre123",
            "administrador": "admin123"
        }

        if st.button("Verificar Contraseña de Cargo"):
            if contrasena_cargo == COLABORADOR_ROLES_PASSWORDS.get(st.session_state['selected_colab_role']):
                st.session_state["final_login_colaborador"] = True
                st.session_state["sesion_iniciada"] = True # Marca la sesión como iniciada para el colaborador
                st.session_state["tipo_usuario"] = st.session_state['selected_colab_role'] # Establece el tipo de usuario como el cargo
                st.success(f"Bienvenido a la página de {st.session_state['tipo_usuario']} ({st.session_state['usuario']}) 👋")
                st.rerun()
            else:
                st.error("❌ Contraseña de cargo incorrecta.")

    # --- Si la sesión ya está iniciada, no mostrar nada más de login ---
    elif st.session_state["sesion_iniciada"]:
        # Esto se encargará de que la función de inicio de sesión no muestre nada
        # si el usuario ya está autenticado y en el rol final.
        pass

# --- Ejemplo de cómo usar el login y la navegación de páginas (fuera de la función login) ---
# Este es un esquema conceptual de cómo podrías manejar las páginas en Streamlit
if __name__ == '__main__':
    # Para demostración, inicializa algunos estados si no existen
    if "sesion_iniciada" not in st.session_state:
        st.session_state["sesion_iniciada"] = False
    if "tipo_usuario" not in st.session_state:
        st.session_state["tipo_usuario"] = None

    if not st.session_state["sesion_iniciada"]:
        login() # Muestra el flujo de login completo
    else:
        st.sidebar.success(f"Sesión iniciada como: {st.session_state['tipo_usuario']}")
        if st.session_state["tipo_usuario"] == "miembro":
            st.write("¡Bienvenido a la página de Miembros!")
            st.write("Aquí va el contenido exclusivo para miembros.")
            if st.button("Cerrar Sesión (Miembro)"):
                st.session_state.clear()
                st.rerun()
        elif st.session_state["tipo_usuario"] in ["director de junta", "promotora", "tesorero", "secretario", "administrador"]:
            st.write(f"¡Bienvenido a la página de {st.session_state['tipo_usuario']}!")
            st.write(f"Aquí va el contenido exclusivo para {st.session_state['tipo_usuario']}.")
            if st.button(f"Cerrar Sesión ({st.session_state['tipo_usuario']})"):
                st.session_state.clear()
                st.rerun()
        else:
            st.error("Tipo de usuario desconocido. Por favor, inicia sesión de nuevo.")
            if st.button("Cerrar Sesión (Error)"):
                st.session_state.clear()
                st.rerun()


