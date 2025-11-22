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
        gestionar_reuniones()
        
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
                        row['Id_miembro']: f"{row['Nombre']} - {row['Rol']}" 
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




def gestionar_reuniones():
    st.header("Gestión de Reuniones y Asistencia")
    tab1, tab2 = st.tabs(["📅 Programar Nueva Reunión", "📝 Tomar Asistencia"])

    # --- PESTAÑA 1: CREAR REUNIÓN ---
    with tab1:
        st.subheader("Crear registro de reunión")
        with st.form("form_reunion"):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha de la reunión")
            with col2:
                # Nota: El usuario pidió atributo 'tema' en minúscula
                tema_reunion = st.text_input("Tema principal")
            
            submit = st.form_submit_button("Crear Reunión")
            
            if submit:
                if tema_reunion:
                    crear_reunion_bd(fecha, tema_reunion)
                else:
                    st.warning("El tema es obligatorio.")

    # --- PESTAÑA 2: ASISTENCIA ---
    with tab2:
        st.subheader("Registro de Asistencia")
        
        # 1. Obtener reuniones disponibles del grupo
        reuniones = obtener_reuniones_del_grupo()
        
        if reuniones:
            # Selector de reunión: Muestra "Fecha - Tema" pero devuelve el ID
            reunion_seleccionada = st.selectbox(
                "Seleccione la reunión:",
                options=reuniones, # Lista de diccionarios
                format_func=lambda x: f"{x['Fecha']} - {x['tema']}"
            )
            
            if reunion_seleccionada:
                st.markdown(f"**Pasando lista para:** {reunion_seleccionada['tema']}")
                st.markdown("---")
                
                # 2. Obtener miembros para armar la lista
                miembros = obtener_lista_miembros_simple()
                
                if miembros:
                    with st.form("form_asistencia"):
                        datos_asistencia = {} # Diccionario para guardar el estado de cada uno
                        
                        # Creamos una fila por miembro
                        for m in miembros:
                            c1, c2 = st.columns([3, 2])
                            with c1:
                                st.write(f"👤 **{m['Nombre']}")
                            with c2:
                                # Radio button para seleccionar estado
                                estado = st.radio(
                                    f"Estado {m['Id_miembro']}", 
                                    ["Presente", "Ausente", "Excusado"], 
                                    key=f"radio_{m['Id_miembro']}",
                                    horizontal=True,
                                    label_visibility="collapsed"
                                )
                                datos_asistencia[m['Id_miembro']] = estado
                        
                        st.markdown("---")
                        guardar_btn = st.form_submit_button("💾 Guardar Asistencia")
                        
                        if guardar_btn:
                            guardar_asistencia_bd(reunion_seleccionada['Id_reunion'], datos_asistencia)
                else:
                    st.warning("No hay miembros registrados para tomar asistencia.")
        else:
            st.info("No hay reuniones registradas. Ve a la pestaña 'Programar Nueva Reunión' primero.")


def crear_reunion_bd(fecha, tema):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id')
            
            # Insertamos en tabla Reunion (respetando 'tema' y 'Id_grupo')
            query = "INSERT INTO Reunion (Fecha, tema, Id_grupo) VALUES (%s, %s, %s)"
            cursor.execute(query, (fecha, tema, grupo_id))
            conn.commit()
            
            st.success(f"Reunión del {fecha} creada exitosamente.")
            st.rerun() # Recargar para que aparezca en la otra pestaña
        except Exception as e:
            st.error(f"Error al crear reunión: {e}")
        finally:
            conn.close()

def obtener_reuniones_del_grupo():
    conn = obtener_conexion()
    data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True) # Importante: dictionary=True
            grupo_id = st.session_state.get('grupo_id')
            
            # Ordenamos por fecha descendente (las más nuevas primero)
            query = "SELECT Id_reunion, Fecha, tema FROM Reunion WHERE Id_grupo = %s ORDER BY Fecha DESC"
            cursor.execute(query, (grupo_id,))
            data = cursor.fetchall()
        except Exception as e:
            st.error(f"Error al cargar reuniones: {e}")
        finally:
            conn.close()
    return data

def obtener_lista_miembros_simple():
    # Función auxiliar ligera solo para obtener ID y Nombres
    conn = obtener_conexion()
    data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            grupo_id = st.session_state.get('grupo_id')
            query = "SELECT Id_miembro, Nombre, `DUI/Identificación` FROM Miembro WHERE Id_grupo = %s"
            cursor.execute(query, (grupo_id,))
            data = cursor.fetchall()
        finally:
            conn.close()
    return data

def guardar_asistencia_bd(id_reunion, diccionario_asistencia):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Preparamos la query de inserción
            query = "INSERT INTO Asistencia (Id_reunion, Id_miembro, Estado) VALUES (%s, %s, %s)"
            
            # Convertimos el diccionario en una lista de tuplas para insertar masivamente
            valores = []
            for id_miembro, estado in diccionario_asistencia.items():
                valores.append((id_reunion, id_miembro, estado))
            
            # executemany es más eficiente para guardar varios registros a la vez
            cursor.executemany(query, valores)
            conn.commit()
            
            st.toast("✅ Asistencia guardada correctamente.")
        except Exception as e:
            # Si intentas guardar asistencia dos veces para la misma reunión, podría dar error duplicate
            st.error(f"Error al guardar asistencia (¿quizás ya la tomaste?): {e}")
        finally:
            conn.close()
