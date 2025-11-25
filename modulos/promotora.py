# ==============================================================================
# ARCHIVO: distrito.py
# DESCRIPCIÓN: Entorno de Promotora (Sidebar Menu).
# - Dashboard (KPIs y Reportes)
# - Gestión de Grupos (Detalle en cascada: Grupo -> Miembro -> Finanzas)
# - Agregar Nuevo Grupo
# ==============================================================================

import streamlit as st
import pandas as pd
from datetime import date

# --- IMPORTACIÓN SEGURA DE LA CONEXIÓN ---
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
# LÓGICA DE DETALLE DE GRUPOS (Simulación de distritos.py integrado)
# ==============================================================================

def mostrar_detalle_grupos(id_distrito):
    """
    Esta función contiene la lógica que solía estar en distritos.py.
    Permite navegar: Seleccionar Grupo -> Seleccionar Miembro -> Ver Finanzas.
    FILTRADO ESTRICTAMENTE POR EL ID_DISTRITO DE LA SESIÓN.
    """
    st.header(f"📂 Gestión de Grupos del Distrito {id_distrito}")
    conn = obtener_conexion()
    if not conn:
        st.error("Error de conexión.")
        return

    # 1. Selector de Grupo (Filtrado por Distrito)
    df_grupos = pd.DataFrame()
    try:
        # Ajusta nombres de columnas según tu BD (ej: Id_grupo, Nombre)
        query_grupos = "SELECT Id_grupo, Nombre FROM Grupo WHERE Id_distrito = %s"
        df_grupos = pd.read_sql(query_grupos, conn, params=(id_distrito,))
    except Exception as e:
        st.error(f"Error cargando grupos: {e}")
    
    if df_grupos.empty:
        st.info("No hay grupos registrados en este distrito.")
        conn.close()
        return

    grupos_dict = dict(zip(df_grupos['Nombre'], df_grupos['Id_grupo']))
    grupo_sel_nombre = st.selectbox("Seleccione un Grupo:", options=grupos_dict.keys())
    
    if grupo_sel_nombre:
        id_grupo = grupos_dict[grupo_sel_nombre]
        
        # 2. Selector de Miembro (Filtrado por Grupo)
        st.markdown("---")
        df_miembros = pd.DataFrame()
        try:
            # Ajusta nombres: Id_miembro, Nombre, Dni...
            query_miembros = "SELECT Id_miembro, Nombre, Dni FROM Miembro WHERE Id_grupo = %s"
            df_miembros = pd.read_sql(query_miembros, conn, params=(id_grupo,))
        except Exception as e:
            st.error(f"Error cargando miembros: {e}")

        if df_miembros.empty:
            st.warning(f"El grupo '{grupo_sel_nombre}' no tiene miembros.")
        else:
            miembros_dict = dict(zip(df_miembros['Nombre'] + " - " + df_miembros['Dni'].astype(str), df_miembros['Id_miembro']))
            miembro_sel_nombre = st.selectbox("Seleccione un Miembro:", options=miembros_dict.keys())

            if miembro_sel_nombre:
                id_miembro = miembros_dict[miembro_sel_nombre]
                
                # 3. Detalles Financieros del Miembro
                st.info(f"Detalles de: **{miembro_sel_nombre}**")
                
                tab1, tab2 = st.tabs(["💰 Préstamos", "⚠️ Multas"])
                
                with tab1:
                    try:
                        q_prest = "SELECT Monto, Fecha_inicio, Estado, Tasa_interes FROM Prestamo WHERE Id_miembro = %s"
                        df_p = pd.read_sql(q_prest, conn, params=(id_miembro,))
                        if not df_p.empty:
                            st.dataframe(df_p, use_container_width=True)
                        else:
                            st.write("Sin préstamos registrados.")
                    except:
                        st.write("Error cargando préstamos.")

                with tab2:
                    try:
                        q_multa = "SELECT Monto, Motivo, Estado FROM Multa WHERE Id_miembro = %s"
                        df_m = pd.read_sql(q_multa, conn, params=(id_miembro,))
                        if not df_m.empty:
                            st.dataframe(df_m, use_container_width=True)
                        else:
                            st.write("Sin multas registradas.")
                    except:
                        st.write("Error cargando multas.")
    
    conn.close()


# ==============================================================================
# FUNCIONES AUXILIARES (REGISTRO Y REPORTES)
# ==============================================================================

def registrar_nuevo_grupo(nombre, ubicacion, id_distrito):
    """Inserta un nuevo grupo asociado al distrito actual."""
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO Grupo (Nombre, Ubicacion, Id_distrito, Fecha_inicio) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (nombre, ubicacion, id_distrito, date.today()))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error al registrar el grupo: {e}")
            return False
    return False

def obtener_reporte_prestamos(id_distrito):
    conn = obtener_conexion()
    df = pd.DataFrame()
    if conn:
        try:
            # Se usa JOIN para asegurar que solo traiga datos del distrito correcto
            query = """
                SELECT 
                    m.Nombre AS Miembro, 
                    g.Nombre AS Grupo, 
                    p.Monto AS Monto, 
                    p.Fecha_inicio AS Fecha_Inicio,
                    p.Estado
                FROM Prestamo p
                JOIN Miembro m ON p.Id_miembro = m.Id_miembro
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s 
                  AND p.Estado IN ('Activo', 'Pendiente', 'Mora')
                ORDER BY p.Fecha_inicio ASC
            """
            df = pd.read_sql(query, conn, params=(id_distrito,))
            conn.close()
        except Exception as e:
            st.error(f"Error generando reporte de préstamos: {e}")
    return df

def obtener_reporte_multas(id_distrito):
    conn = obtener_conexion()
    df = pd.DataFrame()
    if conn:
        try:
            query = """
                SELECT 
                    m.Nombre AS Miembro, 
                    g.Nombre AS Grupo, 
                    mu.Monto AS Monto, 
                    mu.Motivo,
                    mu.Estado
                FROM Multa mu
                JOIN Miembro m ON mu.Id_miembro = m.Id_miembro
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s AND mu.Estado = 'Pendiente'
            """
            df = pd.read_sql(query, conn, params=(id_distrito,))
            conn.close()
        except Exception as e:
            st.error(f"Error generando reporte de multas: {e}")
    return df


# ==============================================================================
# INTERFAZ PRINCIPAL (APP)
# ==============================================================================

def app():
    # --- 1. VERIFICACIÓN DE SESIÓN ---
    if 'id_distrito_actual' not in st.session_state:
        st.warning("⚠️ Acceso no autorizado o sesión expirada. Por favor inicie sesión.")
        st.stop()
    
    id_distrito = st.session_state['id_distrito_actual']
    
    # --- SIDEBAR ---
    st.sidebar.title("👩‍🌾 Panel Promotora")
    st.sidebar.caption(f"Distrito ID: {id_distrito}")
    
    opcion = st.sidebar.radio(
        "Menú de Opciones", 
        ["📊 Dashboard y Reportes", "📂 Gestión de Grupos (Detalles)", "➕ Agregar Nuevo Grupo"]
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar Sesión", key="btn_logout_promotora"):
        st.session_state.clear()
        st.rerun()

    # --- OPCIÓN 1: DASHBOARD ---
    if opcion == "📊 Dashboard y Reportes":
        st.title("Reportes del Distrito")
        
        df_prestamos = obtener_reporte_prestamos(id_distrito)
        df_multas = obtener_reporte_multas(id_distrito)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Préstamos Activos", len(df_prestamos))
        col2.metric("Multas Pendientes", len(df_multas))
        
        # Validar columna Monto para suma
        total_prestado = df_prestamos['Monto'].sum() if not df_prestamos.empty and 'Monto' in df_prestamos.columns else 0
        col3.metric("Capital Prestado", f"${total_prestado:,.2f}")

        st.divider()

        col_izq, col_der = st.columns([2, 1])
        with col_izq:
            st.subheader("📌 Préstamos Activos")
            if df_prestamos.empty:
                st.info("No hay préstamos activos.")
            else:
                st.dataframe(df_prestamos, use_container_width=True)

        with col_der:
            st.subheader("🚨 Multas")
            if df_multas.empty:
                st.success("Sin multas.")
            else:
                st.dataframe(df_multas, use_container_width=True)

    # --- OPCIÓN 2: GESTIÓN DE GRUPOS (INTEGRACIÓN DISTRITOS.PY) ---
    elif opcion == "📂 Gestión de Grupos (Detalles)":
        # Aquí llamamos a la función interna que reemplaza la llamada externa
        mostrar_detalle_grupos(id_distrito)

    # --- OPCIÓN 3: AGREGAR GRUPO ---
    elif opcion == "➕ Agregar Nuevo Grupo":
        st.title("Nuevo Grupo")
        st.info(f"Registrando grupo para el Distrito {id_distrito}")
        
        with st.form("form_alta_grupo"):
            nombre = st.text_input("Nombre del Grupo")
            ubicacion = st.text_input("Ubicación / Comunidad")
            
            # Campo informativo visual
            st.text_input("ID Distrito Asignado", value=id_distrito, disabled=True)
            
            submitted = st.form_submit_button("Guardar Grupo")
            
            if submitted:
                if nombre and ubicacion:
                    if registrar_nuevo_grupo(nombre, ubicacion, id_distrito):
                        st.success(f"Grupo '{nombre}' creado correctamente.")
                    else:
                        st.error("Error al guardar en la base de datos.")
                else:
                    st.warning("El nombre y la ubicación son obligatorios.")

# Para pruebas locales
if __name__ == "__main__":
    if 'id_distrito_actual' not in st.session_state:
        st.session_state['id_distrito_actual'] = 1 
    app()
