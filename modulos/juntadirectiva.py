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
    st.header("Gestión Operativa de Reuniones")
    
    # AHORA TENEMOS 3 PESTAÑAS
    tab1, tab2, tab3 = st.tabs(["📅 1. Programar", "📝 2. Asistencia", "💰 3. Registrar Ahorros"])

    # --- PESTAÑA 1: CREAR (Igual que antes) ---
    with tab1:
        st.subheader("Crear nueva reunión")
        with st.form("form_reunion"):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha")
            with col2:
                tema = st.text_input("Tema")
            
            if st.form_submit_button("Crear Reunión"):
                crear_reunion_bd(fecha, tema)

    # --- PESTAÑA 2: ASISTENCIA (Igual que antes) ---
    with tab2:
        st.subheader("Tomar Asistencia")
        reuniones = obtener_reuniones_del_grupo()
        if reuniones:
            reunion_sel = st.selectbox("Seleccione Reunión para Asistencia:", options=reuniones, format_func=lambda x: f"{x['Fecha']} - {x['tema']}", key="sel_asist")
            
            if reunion_sel:
                miembros = obtener_lista_miembros_simple()
                if miembros:
                    with st.form("form_asistencia"):
                        datos_asistencia = {}
                        st.write("Marque el estado de los miembros:")
                        for m in miembros:
                            c1, c2 = st.columns([3, 2])
                            with c1:
                                st.write(f"👤 {m['Nombre']}")
                            with c2:
                                estado = st.radio("Estado", ["Presente", "Ausente", "Excusado"], key=f"asist_{m['Id_miembro']}", label_visibility="collapsed", horizontal=True)
                                datos_asistencia[m['Id_miembro']] = estado
                        
                        if st.form_submit_button("Guardar Asistencia"):
                            guardar_asistencia_bd(reunion_sel['Id_reunion'], datos_asistencia)
        else:
            st.info("No hay reuniones creadas.")

    # --- PESTAÑA 3: AHORROS (NUEVO) ---
    with tab3:
        st.subheader("Registro de Ahorros por Reunión")
        
        reuniones_ahorro = obtener_reuniones_del_grupo()
        
        if reuniones_ahorro:
            # Seleccionamos la reunión donde está entrando el dinero
            reunion_ahorro_sel = st.selectbox("Seleccione Reunión:", options=reuniones_ahorro, format_func=lambda x: f"{x['Fecha']} - {x['tema']}", key="sel_ahorro")
            
            st.markdown("---")
            
            # Formulario para registrar ahorro INDIVIDUAL
            # (Hacerlo uno por uno es más seguro para manejar dinero)
            col_izq, col_der = st.columns(2)
            
            with col_izq:
                miembros = obtener_lista_miembros_simple()
                # Diccionario para buscar fácil
                dict_miembros = {m['Id_miembro']: m['Nombre'] for m in miembros}
                
                miembro_ahorrador = st.selectbox("Miembro que ahorra:", options=dict_miembros.keys(), format_func=lambda x: dict_miembros[x])
                
            with col_der:
                monto = st.number_input("Monto a Ahorrar ($)", min_value=0.0, step=0.01)
            
            if st.button("Registrar Ahorro", type="primary"):
                guardar_ahorro_bd(reunion_ahorro_sel['Id_reunion'], miembro_ahorrador, monto)
                
            # --- VISTA RÁPIDA DE LO AHORRADO EN ESTA REUNIÓN ---
            st.markdown("#### 📊 Resumen de esta reunión")
            ver_ahorros_reunion(reunion_ahorro_sel['Id_reunion'])
            
        else:
            st.info("Primero debe crear una reunión.")

# --- AGREGAR ESTAS FUNCIONES AL FINAL (SECCIÓN SQL) ---

def guardar_ahorro_bd(id_reunion, id_miembro, monto):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            # Insertamos el ahorro vinculándolo a la reunión
            query = "INSERT INTO Ahorro (Id_reunion, Id_miembro, Monto, Fecha) VALUES (%s, %s, %s, NOW())"
            cursor.execute(query, (id_reunion, id_miembro, monto))
            conn.commit()
            st.success(f"Ahorro de ${monto} registrado correctamente.")
        except Exception as e:
            st.error(f"Error al guardar ahorro: {e}")
        finally:
            conn.close()

def ver_ahorros_reunion(id_reunion):
    conn = obtener_conexion()
    if conn:
        try:
            # Consulta con JOIN para ver el nombre del miembro
            query = """
                SELECT m.Nombre, a.Monto, a.Fecha 
                FROM Ahorro a
                JOIN Miembro m ON a.Id_miembro = m.Id_miembro
                WHERE a.Id_reunion = %s
                ORDER BY a.id_ahorro DESC
            """
            df = pd.read_sql(query, conn, params=(id_reunion,))
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                total = df['Monto'].sum()
                st.metric("Total Recaudado hoy", f"${total:,.2f}")
            else:
                st.info("Aún no hay ahorros registrados en esta sesión.")
        finally:
            conn.close()


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
