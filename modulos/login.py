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
# FUNCIÓN 1: VERIFICAR CREDENCIALES (TABLA LOGIN)
# ==============================================================================
def verificar_usuario(Usuario, Contraseña, Rol):
    con = obtener_conexion()
    if not con:
        st.error("⚠️ No se pudo conectar a la base de datos.")
        return None

    try:
        cursor = con.cursor(dictionary=True)
        # Verificamos credenciales básicas
        query = """
            SELECT Usuario, Rol, Id_grupo, Id_distrito 
            FROM Login 
            WHERE Usuario = %s AND Contraseña = %s AND Rol = %s
        """
        cursor.execute(query, (Usuario, Contraseña, Rol))
        result = cursor.fetchone()
        return result 
    except Exception as e:
        st.error(f"Error en Login: {e}")
        return None
    finally:
        if con.is_connected():
            con.close()

# ==============================================================================
# FUNCIÓN 2 (NUEVA): VERIFICAR IDENTIDAD EN TABLA PROMOTORA
# ==============================================================================
def validar_identidad_promotora(nombre_usuario, id_distrito):
    """
    Busca en la tabla 'Promotora' si existe alguien con ese nombre en ese distrito.
    """
    con = obtener_conexion()
    existe = False
    
    if con:
        try:
            cursor = con.cursor()
            # ⚠️ IMPORTANTE: Ajusta 'nombre_promotora' si tu columna se llama solo 'Nombre'
            # Esta consulta busca que el nombre coincida Y que pertenezca al distrito seleccionado.
            query = """
                SELECT COUNT(*) 
                FROM Promotora 
                WHERE nombre_promotora = %s AND id_distrito = %s
            """
            cursor.execute(query, (nombre_usuario, id_distrito))
            
            # Obtenemos el conteo (si es 1 o más, existe)
            resultado = cursor.fetchone()
            if resultado[0] > 0:
                existe = True
                
            cursor.close()
            con.close()
        except Exception as e:
            # Si falla (ej: la tabla Promotora no existe), mostramos error pero asumimos falso
            st.error(f"Error verificando tabla Promotora: {e}")
    
    return existe

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
        
        # --- SELECTOR DE DISTRITO ---
        distrito_seleccionado = None
        if Rol == "promotora":
            st.info("📍 Verificación de Zona")
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

        # PASO 1: Verificar Credenciales en Tabla LOGIN
        user_data = verificar_usuario(Usuario, Contraseña, Rol)

        if user_data:
            
            # --- VALIDACIONES EXCLUSIVAS PARA PROMOTORA ---
            if Rol == "promotora":
                
                # A) Validación Cruzada Login vs Selección
                # ----------------------------------------
                db_distrito_id = user_data.get('Id_distrito')
                
                if db_distrito_id is None:
                    st.error("⛔ Error de cuenta: Usuario sin distrito asignado en tabla Login.")
                    return

                if int(db_distrito_id) != distrito_seleccionado:
                    st.error(f"🚫 Error de Zona: Su usuario pertenece al Distrito {db_distrito_id}, no al {distrito_seleccionado}.")
                    return 

                # B) Validación de Identidad en Tabla PROMOTORA (TU REQUERIMIENTO)
                # ---------------------------------------------------------------
                # Verificamos que el Usuario exista en la columna Nombre de la tabla Promotora
                es_promotora_valida = validar_identidad_promotora(Usuario, distrito_seleccionado)
                
                if not es_promotora_valida:
                    st.error(f"❌ Acceso Denegado: El usuario '{Usuario}' no aparece registrado en la lista oficial de la tabla 'Promotora' para el Distrito {distrito_seleccionado}.")
                    st.info("Nota: Asegúrese de que su Nombre de Usuario coincida exactamente con su Nombre registrado en la tabla Promotora.")
                    return

            # --- SI PASA TODAS LAS VALIDACIONES ---
            st.session_state['logged_in'] = True
            st.session_state['user_role'] = user_data['Rol']
            st.session_state['user_name'] = user_data['Usuario']
            st.session_state['grupo_id'] = user_data.get('Id_grupo')
            st.session_state['id_distrito_actual'] = user_data.get('Id_distrito')
            
            st.success(f"✅ Identidad verificada. Bienvenido/a {user_data['Usuario']}.")
            time.sleep(1)
            st.rerun()
            
        else:
            st.error("❌ Credenciales incorrectas.")

if __name__ == "__main__":
    login_page()
```

### ⚠️ Requisito Importante para que funcione

En la función `validar_identidad_promotora` (línea 46), he usado esta consulta:

```sql
SELECT COUNT(*) FROM Promotora WHERE nombre_promotora = %s AND id_distrito = %s
