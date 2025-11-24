import streamlit as st
import time

# --- GESTIÓN DE IMPORTACIONES DE CONEXIÓN ---
# Esto maneja el problema de las rutas (modulos vs raiz)
try:
    from modulos.config.conexion import obtener_conexion
except ImportError:
    try:
        from config.conexion import obtener_conexion
    except ImportError:
        # Último intento: importar desde la raíz si el archivo está ahí
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

        # NOTA: Aquí asumimos que la tabla 'Login' o 'Promotora' tiene la columna 'Id_distrito'.
        # Si tienes una tabla separada 'Promotora', el query debería hacer un JOIN, 
        # pero basándonos en tu imagen anterior, 'Login' ya tiene el 'Id_distrito'.
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

    # Contenedor para el formulario
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            Usuario = st.text_input("👤 Usuario")
        with col2:
            Contraseña = st.text_input("🔑 Contraseña", type="password")
        
        Roles = ["administrador", "promotora", "miembro", "junta directiva"]
        Rol = st.selectbox("Seleccione su Rol", Roles)
        
        # --- LÓGICA ESPECÍFICA PARA PROMOTORA ---
        distrito_seleccionado = None
        
        if Rol == "promotora":
            st.info("📍 Verificación de Zona")
            # El usuario pidió seleccionar entre 1, 2 o 3 (o los distritos que existan)
            # Nota: Idealmente esto vendría de BD, pero respetamos la lista fija solicitada
            distrito_seleccionado = st.selectbox(
                "Seleccione el Número de Distrito asignado:",
                options=[1, 2, 3],
                help="Seleccione el distrito que le corresponde administrar."
            )

        submitted = st.form_submit_button("Iniciar sesión", use_container_width=True)

    if submitted:
        if not Usuario or not Contraseña:
            st.warning("⚠️ Por favor ingrese usuario y contraseña.")
            return

        # 1. Verificamos credenciales en la Base de Datos
        # Ahora pasamos el Rol también para filtrar desde la consulta
        user_data = verificar_usuario(Usuario, Contraseña, Rol)

        if user_data:
            # -----------------------------------------------------------
            # 2. VALIDACIÓN DE DISTRITO (Solo para Promotora)
            # -----------------------------------------------------------
            if Rol == "promotora":
                # Obtenemos el ID real que está guardado en la Base de Datos
                db_distrito_id = user_data.get('Id_distrito')
                
                # Caso A: El usuario en la BD no tiene distrito asignado (es NULL)
                if db_distrito_id is None:
                    st.error("⛔ Error de cuenta: Este usuario 'Promotora' no tiene un distrito asignado en la base de datos.")
                    return

                # Caso B: El distrito que seleccionó NO coincide con el de la BD
                if int(db_distrito_id) != distrito_seleccionado:
                    st.error(f"🚫 Acceso Denegado: Usted intentó acceder al Distrito {distrito_seleccionado}, pero su usuario está registrado únicamente en el Distrito {db_distrito_id}.")
                    return 

            # -----------------------------------------------------------
            # 3. ÉXITO: GUARDAR SESIÓN Y REDIRIGIR
            # -----------------------------------------------------------
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = user_data['Rol']
            st.session_state['user_name'] = user_data['Usuario']
            
            # --- IMPORTANTE: Variables críticas para que funcionen los otros módulos ---
            st.session_state['Usuario'] = user_data['Usuario'] # Necesario para Modulo Miembro
            st.session_state['user_id_miembro'] = user_data.get('Id_miembro') # Optimización
            
            # Guardamos IDs importantes para el resto del sistema
            st.session_state['grupo_id'] = user_data.get('Id_grupo')
            st.session_state['distrito_id'] = user_data.get('Id_distrito') # Estándar del sistema
            
            # Guardamos el distrito validado (variable específica de tu compañera)
            st.session_state['id_distrito_actual'] = user_data.get('Id_distrito')
            
            st.success(f"✅ Credenciales correctas. Bienvenido/a {user_data['Usuario']}.")
            time.sleep(1) 
            st.rerun()    
            
        else:
            st.error("❌ Error: Usuario, contraseña o rol incorrectos.")
