import streamlit as st
import pandas as pd
from .config.conexion import obtener_conexion 

def junta_directiva_page():
    st.title("Panel de Control - Directiva")
    st.markdown("---")

    menu = ["Gestionar Miembros", "Gestionar Reuniones", "Caja y Préstamos", "Reportes"]
    choice = st.sidebar.selectbox("Menú Directiva", menu)

    if choice == "Gestionar Miembros":
        gestionar_miembros()
    
    elif choice == "Gestionar Reuniones":
        st.info("Módulo de Reuniones en construcción.")
        
    elif choice == "Caja y Préstamos":
        st.info("Módulo de Caja en construcción.")

    elif choice == "Reportes":
        st.info("Módulo de Reportes en construcción.")

# --- SUB-FUNCIONES ---

def gestionar_miembros():
    st.header("Gestión de Miembros del Grupo")
    tab1, tab2 = st.tabs(["Registrar Nuevo Miembro", "Ver Lista de Miembros"])

    # --- PESTAÑA 1: REGISTRO ---
    with tab1:
        st.subheader("Afiliación de Nuevo Miembro")
        with st.form("form_nuevo_miembro"):
            col1, col2 = st.columns(2)
            with col1:
                # Mantenemos inputs separados para mejor experiencia de usuario
                nombre = st.text_input("Nombre")
                apellido = st.text_input("Apellido")
                dui = st.text_input("DUI (Documento Único)")
            with col2:
                telefono = st.text_input("Teléfono")
                direccion = st.text_input("Dirección")
                
               # Definimos los roles claramente: 1:Pres, 2:Tes, 3:Miembro, 4:Sec
            rol_id = st.selectbox(
                "Asignar Rol", 
                options=[1, 2, 4, 3], # El orden aquí define el orden en la lista desplegable
                format_func=lambda x: {
                    1: "Presidente", 
                    2: "Tesorero", 
                    3: "Miembro", 
                        4: "Secretario"
                    }.get(x, "Desconocido"))
            
            submitted = st.form_submit_button("Guardar Miembro")
            
            if submitted:
                if nombre and apellido and dui:
                    # AQUI CONCATENAMOS NOMBRE Y APELLIDO
                    nombre_completo = f"{nombre} {apellido}"
                    guardar_miembro_bd(nombre_completo, dui, telefono, direccion, rol_id)
                else:
                    st.error("Por favor llene los campos obligatorios.")

    # --- PESTAÑA 2: LISTADO ---
    with tab2:
        st.subheader("Directorio de Miembros")
        listar_miembros()

# --- FUNCIONES SQL ---

def guardar_miembro_bd(nombre_completo, dui, telefono, direccion, rol_id):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id', 1) 
            
            # CAMBIOS REALIZADOS:
            # 1. Tabla: Miembro (singular)
            # 2. Columna `DUI/Identificación` con comillas invertidas (backticks) por tener el símbolo "/"
            # 3. Solo pasamos 'Nombre', ya no 'Apellido'
            query = """
                INSERT INTO Miembro (Nombre, `DUI/Identificación`, Telefono, Direccion, Rol, Id_grupo)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            valores = (nombre_completo, dui, telefono, direccion, rol_id, grupo_id)
            
            cursor.execute(query, valores)
            conn.commit()
            st.success(f"Miembro {nombre_completo} registrado exitosamente.")
        except Exception as e:
            st.error(f"Error al guardar en BD: {e}")
        finally:
            cursor.close()
            conn.close()

def listar_miembros():
    conn = obtener_conexion()
    if conn:
        try:
            # Usamos .get() por seguridad
            grupo_id = st.session_state.get('grupo_id')
            
            # CORRECCIÓN DE NOMBRES DE COLUMNAS AQUÍ:
            # Usamos Id_miembro, Rol y Id_grupo
            query = "SELECT Id_miembro, Nombre, `DUI/Identificación`, Telefono, Rol FROM Miembro WHERE Id_grupo = %s"
            
            df = pd.read_sql(query, conn, params=(grupo_id,))
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                st.markdown("---")
                
                # SECCIÓN DE ELIMINAR
                with st.expander("🗑️ Eliminar Miembro", expanded=False):
                    st.warning("⚠️ Cuidado: Esta acción no se puede deshacer.")
                    
                    # CORRECCIÓN AQUÍ TAMBIÉN:
                    # Python debe buscar 'Id_miembro' (tal como viene del SQL)
                    lista_miembros = {
                        row['Id_miembro']: f"{row['Nombre']} - {row["Rol"]}" 
                        for index, row in df.iterrows()
                    }
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        id_a_eliminar = st.selectbox(
                            "Seleccione el miembro a eliminar:", 
                            options=lista_miembros.keys(),
                            format_func=lambda x: lista_miembros[x]
                        )
                    
                    with col2:
                        st.write("") 
                        st.write("") 
                        if st.button("Eliminar Permanentemente", type="primary"):
                            eliminar_miembro_bd(id_a_eliminar)
                            st.rerun()
                            
            else:
                st.info("No hay miembros registrados en este grupo aún.")
                
        except Exception as e:
            st.error(f"Error al cargar miembros: {e}")
        finally:
            conn.close()

def eliminar_miembro_bd(id_miembro):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            
            # CORRECCIÓN AQUÍ: Id_miembro
            query = "DELETE FROM Miembro WHERE Id_miembro = %s"
            cursor.execute(query, (id_miembro,))
            conn.commit()
            
            st.toast("✅ Miembro eliminado correctamente.")
            
        except Exception as e:
            if "1451" in str(e): 
                st.error("⛔ No puedes eliminar a este miembro porque ya tiene registros asociados.")
            else:
                st.error(f"Error al eliminar: {e}")
        finally:
            cursor.close()
            conn.close()
