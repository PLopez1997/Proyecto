import streamlit as st

def junta_directiva_page():
    st.title("Panel de Junta Directiva")
    st.write("Contenido exclusivo para Junta Directiva.")

#COMIENZA EL CODIGO
import pandas as pd
from conexion import conexion  # Importamos tu función de conexión existente

def show_directiva_dashboard():
    st.title("Panel de Control - Directiva")
    st.markdown("---")

    # Menú de navegación interno para la Directiva
    menu = ["Gestionar Miembros", "Gestionar Reuniones", "Caja y Préstamos", "Reportes"]
    choice = st.sidebar.selectbox("Menú Directiva", menu)

    if choice == "Gestionar Miembros":
        gestionar_miembros()
    
    elif choice == "Gestionar Reuniones":
        st.info("Módulo de Reuniones en construcción. Aquí registrarás asistencias y ahorros.")
        # Aquí irá la lógica de Reuniones (Fase 3 del PDF)
        
    elif choice == "Caja y Préstamos":
        st.info("Módulo de Caja en construcción. Aquí autorizarás préstamos.")
        # Aquí irá la lógica de Préstamos (Fase 4 del PDF)

    elif choice == "Reportes":
        st.info("Módulo de Reportes en construcción.")

# --- SUB-FUNCIONES ---

def gestionar_miembros():
    st.header("Gestión de Miembros del Grupo")
    
    # Pestañas para separar el registro de la visualización
    tab1, tab2 = st.tabs(["Registrar Nuevo Miembro", "Ver Lista de Miembros"])

    # --- PESTAÑA 1: REGISTRO ---
    with tab1:
        st.subheader("Afiliación de Nuevo Miembro")
        
        # Formulario para evitar recargas constantes
        with st.form("form_nuevo_miembro"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre")
                apellido = st.text_input("Apellido")
                dui = st.text_input("DUI (Documento Único)")
            
            with col2:
                telefono = st.text_input("Teléfono")
                direccion = st.text_input("Dirección")
                # Nota: Aquí deberíamos cargar los roles desde la BD, por ahora lo dejo estático
                rol_id = st.selectbox("Asignar Rol", [1, 2, 3], format_func=lambda x: "Miembro" if x==3 else ("Presidente" if x==1 else "Tesorero"))
            
            submitted = st.form_submit_button("Guardar Miembro")
            
            if submitted:
                if nombre and apellido and dui:
                    guardar_miembro_bd(nombre, apellido, dui, telefono, direccion, rol_id)
                else:
                    st.error("Por favor llene los campos obligatorios (Nombre, Apellido, DUI).")

    # --- PESTAÑA 2: LISTADO ---
    with tab2:
        st.subheader("Directorio de Miembros")
        listar_miembros()

# --- FUNCIONES SQL ---

def guardar_miembro_bd(nombre, apellido, dui, telefono, direccion, rol_id):
    conn = conexion ()
    if conn:
        try:
            cursor = conn.cursor()
            # ASUMIMOS: Que tenemos el ID_Grupo en la sesión del usuario logueado.
            # Si no está en session_state, necesitaremos consultarlo primero.
            grupo_id = st.session_state.get('grupo_id', 1) # Default 1 para pruebas
            
            query = """
                INSERT INTO Miembros (Nombre, Apellido, DUI, Telefono, Direccion, ID_Rol, ID_Grupo)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            valores = (nombre, apellido, dui, telefono, direccion, rol_id, grupo_id)
            
            cursor.execute(query, valores)
            conn.commit()
            st.success(f"Miembro {nombre} {apellido} registrado exitosamente.")
        except Exception as e:
            st.error(f"Error al guardar en BD: {e}")
        finally:
            cursor.close()
            conn.close()

def listar_miembros():
    conn = conexion ()
    if conn:
        try:
            # Consultamos los miembros del grupo actual
            grupo_id = st.session_state.get('grupo_id', 1)
            query = "SELECT ID_Miembro, Nombre, Apellido, DUI, Telefono, ID_Rol FROM Miembros WHERE ID_Grupo = %s"
            
            df = pd.read_sql(query, conn, params=(grupo_id,))
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No hay miembros registrados en este grupo aún.")
        except Exception as e:
            st.error(f"Error al cargar miembros: {e}")
        finally:
            conn.close()

#connector.connect
#create_connection
