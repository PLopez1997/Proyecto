# Asumiendo que 'st' y 'obtener_conexion' están definidos en el entorno de Streamlit
import streamlit as st

# Mock para la función obtener_conexion si no está definida
def obtener_conexion():
    # En una aplicación real, esto conectaría a tu base de datos
    st.warning("⚠️ Simulación: Conectando a la base de datos...")
    return True # Simula una conexión exitosa

def verificar_usuario(usuario, contrasena):
    con = obtener_conexion()
    if not con:
        st.error("⚠️ No se pudo conectar a la base de datos.")
        return None
    else:
        # ✅ Guardar en el estado que la conexión fue exitosa
        st.session_state["conexion_exitosa"] = True

    try:
        # Simulación de verificación de usuario
        if usuario == "admin" and contrasena == "123":
            return "admin_role" # Un rol que necesita selección posterior
        elif usuario == "miembro" and contrasena == "miembro_pass":
            return "miembro"
        elif usuario == "colab" and contrasena == "colab_pass":
            return "colaborador"
        else:
            return None
    finally:
        # con.close() # Descomentar en una aplicación real
        pass

def login():
    st.title("Inicio de sesión")

    # Inicializar variables de estado de sesión si no existen
    if "logged_in_primary" not in st.session_state:
        st.session_state["logged_in_primary"] = False
    if "selected_role" not in st.session_state:
        st.session_state["selected_role"] = None
    if "final_login_miembro" not in st.session_state:
        st.session_state["final_login_miembro"] = False
    if "final_login_colaborador" not in st.session_state:
        st.session_state["final_login_colaborador"] = False
    if "sesion_iniciada" not in st.session_state:
        st.session_state["sesion_iniciada"] = False
    if "usuario" not in st.session_state:
        st.session_state["usuario"] = None
    if "tipo_usuario_db" not in st.session_state:
        st.session_state["tipo_usuario_db"] = None # Almacena el tipo de la DB

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

    # --- Paso 2: Selección de rol (si el inicio primario fue exitoso) ---
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
            st.info("Para el rol de Colaborador, se requiere una contraseña adicional.")
            st.rerun()

    # --- Paso 3: Contraseña adicional para Colaborador (si se seleccionó Colaborador) ---
    elif st.session_state["logged_in_primary"] and st.session_state["selected_role"] == "colaborador" and not st.session_state["final_login_colaborador"]:
        st.subheader("Contraseña adicional para Colaborador")
        contrasena_adicional = st.text_input("Contraseña de Colaborador", type="password", key="colaborador_pass_input")

        # Contraseña de ejemplo para el rol de colaborador
        COLABORADOR_PASSWORD = "segunda_clave"

        if st.button("Verificar Contraseña"): # Asumo un botón para verificar la segunda contraseña
            if contrasena_adicional == COLABORADOR_PASSWORD:
                st.session_state["final_login_colaborador"] = True
                st.session_state["sesion_iniciada"] = True # Marca la sesión como iniciada para el colaborador
                st.session_state["tipo_usuario"] = "colaborador" # Establece el tipo de usuario para la sesión
                st.success(f"Bienvenido como Colaborador ({st.session_state['usuario']}) 👋")
                st.rerun()
            else:
                st.error("❌ Contraseña adicional incorrecta.")

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
        elif st.session_state["tipo_usuario"] == "colaborador":
            st.write("¡Bienvenido a la página de Colaboradores!")
            st.write("Aquí va el contenido exclusivo para colaboradores.")
            if st.button("Cerrar Sesión (Colaborador)"):
                st.session_state.clear()
                st.rerun()
        else:
            st.error("Tipo de usuario desconocido. Por favor, inicia sesión de nuevo.")
            if st.button("Cerrar Sesión (Error)"):
                st.session_state.clear()
                st.rerun()

