import streamlit as st
import pandas as pd
from datetime import date

# --- IMPORTACIÓN CORRECTA DE LA CONEXIÓN ---
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

# --- IMPORTACIÓN CORRECTA DEL MÓDULO DISTRITO ---
# Intentamos importar con manejo de errores por si la ruta cambia
try:
    from modulos.distritos import app as distritos_page
except ImportError:
    try:
        import distritos
        distritos_page = distritos.app
    except ImportError:
        # Si el archivo se llama 'distrito.py' (singular) en lugar de 'distritos.py'
        try:
             from modulos.distrito import app as distritos_page
        except ImportError:
             st.warning("⚠️ No se pudo cargar el módulo de distritos. Verifique el nombre del archivo (distrito.py vs distritos.py).")
             def distritos_page(): st.write("Módulo distritos no encontrado.")

# ----------------------------------------------------------------------
# FUNCIÓN: REGISTRAR GRUPO
# ----------------------------------------------------------------------
def registrar_nuevo_grupo(nombre, ubicacion, id_distrito):
    """Inserta un nuevo grupo asociado al distrito actual."""
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            # Ajusta los nombres de columnas según tu BD real (ej: nombre_grupo vs Nombre)
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

# ----------------------------------------------------------------------
# FUNCIÓN: REPORTE DE PRÉSTAMOS
# ----------------------------------------------------------------------
def obtener_reporte_prestamos(id_distrito):
    conn = obtener_conexion()
    df = pd.DataFrame()
    if conn:
        try:
            query = """
                SELECT 
                    m.Nombre AS nombre_miembro, 
                    g.Nombre AS nombre_grupo, 
                    p.Monto AS monto_prestamo, 
                    p.Fecha_vencimiento,
                    p.Estado
                FROM Prestamo p
                JOIN Miembro m ON p.Id_miembro = m.Id_miembro
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s 
                  AND p.Estado IN ('Activo', 'Pendiente', 'Mora')
                ORDER BY p.Fecha_vencimiento ASC
            """
            df = pd.read_sql(query, conn, params=(id_distrito,))
            conn.close()
        except Exception as e:
            st.error(f"Error generando reporte de préstamos: {e}")
    return df

# ----------------------------------------------------------------------
# FUNCIÓN: REPORTE DE MULTAS
# ----------------------------------------------------------------------
def obtener_reporte_multas(id_distrito):
    conn = obtener_conexion()
    df = pd.DataFrame()
    if conn:
        try:
            query = """
                SELECT 
                    m.Nombre AS nombre_miembro, 
                    g.Nombre AS nombre_grupo, 
                    mu.Monto AS monto_multa, 
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

# ----------------------------------------------------------------------
# INTERFAZ PRINCIPAL DEL PANEL PROMOTORA
# ----------------------------------------------------------------------
def app():
    # --- 1. VERIFICACIÓN DE SESIÓN ---
    if 'id_distrito_actual' not in st.session_state:
        st.error("Acceso no autorizado. Inicie sesión.")
        st.stop()
    
    id_distrito = st.session_state['id_distrito_actual']
    
    # --- SIDEBAR ---
    st.sidebar.title("👩‍🌾 Panel Promotora")
    st.sidebar.write(f"Distrito ID: {id_distrito}")
    
    opcion = st.sidebar.radio(
        "Menú de Opciones", 
        ["📊 Dashboard y Reportes", "📂 Gestión de Grupos (Detalles)", "➕ Agregar Nuevo Grupo"]
    )
    
    st.sidebar.markdown("---")
    
    # --- CORRECCIÓN DEL ERROR ---
    # Se agrega key='btn_logout_promotora' para evitar duplicidad de IDs
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
        
        total_prestado = df_prestamos['monto_prestamo'].sum() if not df_prestamos.empty else 0
        col3.metric("Capital Prestado", f"${total_prestado:,.2f}")

        st.divider()

        st.subheader("📌 Préstamos en el Distrito")
        if df_prestamos.empty:
            st.info("No hay préstamos activos.")
        else:
            st.dataframe(df_prestamos, use_container_width=True)

        st.subheader("🚨 Multas Pendientes")
        if df_multas.empty:
            st.success("Sin multas.")
        else:
            st.dataframe(df_multas, use_container_width=True)

    # --- OPCIÓN 2: GESTIÓN DE GRUPOS ---
    elif opcion == "📂 Gestión de Grupos (Detalles)":
        # Llamamos a la función importada de distritos.py
        distritos_page()

    # --- OPCIÓN 3: AGREGAR GRUPO ---
    elif opcion == "➕ Agregar Nuevo Grupo":
        st.title("Nuevo Grupo")
        
        with st.form("form_alta_grupo"):
            nombre = st.text_input("Nombre del Grupo")
            ubicacion = st.text_input("Ubicación / Comunidad")
            
            # Campo informativo, no editable
            st.text_input("Distrito", value=f"ID: {id_distrito}", disabled=True)
            
            submitted = st.form_submit_button("Guardar")
            
            if submitted:
                if nombre and ubicacion:
                    if registrar_nuevo_grupo(nombre, ubicacion, id_distrito):
                        st.success(f"Grupo '{nombre}' creado correctamente.")
                    else:
                        st.error("Error al guardar el grupo en la base de datos.")
                else:
                    st.warning("Complete todos los campos.")

# Para pruebas locales
if __name__ == "__main__":
    st.session_state['id_distrito_actual'] = 1 
    app()

