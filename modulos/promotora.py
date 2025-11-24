import streamlit as st
import pandas as pd
from datetime import date
import sys
import os

# --- ARREGLO DE RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# --- IMPORTACIÓN CORRECTA DE LA CONEXIÓN ---
try:
    from config.conexion import obtener_conexion
except ImportError as e:
    st.error(f"Error al importar la conexión: {e}")
    st.stop()

# Importación del archivo distrito
try:
    import distrito
except ImportError:
    from modulos import distrito

# Importamos el módulo vecino
try:
    import distrito 
except ImportError:
    from modulos import distrito

# ... (El resto de tu código sigue igual) ...

# ... A PARTIR DE AQUÍ SIGUE TU CÓDIGO NORMAL (def registrar_nuevo_grupo...) ... 

# ------------------------------------------------------------------------------
# FUNCIONES DE BASE DE DATOS ESPECÍFICAS PARA ESTE PANEL
# ------------------------------------------------------------------------------

def registrar_nuevo_grupo(nombre, ubicacion, id_distrito):
    """Inserta un nuevo grupo asociado al distrito actual."""
    conn = obtener_conexion
    if conn:
        try:
            cursor = conn.cursor()
            # NOTA: Insertamos en la tabla GRUPO, vinculándolo con el id_distrito
            # Asumimos que la tabla tiene columnas: nombre_grupo, ubicacion_grupo, id_distrito, fecha_creacion
            query = """
                INSERT INTO Grupo (nombre_grupo, ubicacion_grupo, id_distrito, fecha_creacion) 
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
    """
    Genera un reporte uniendo tablas: 
    Distrito -> Grupo -> Miembro -> Prestamo
    """
    conn = create_connection()
    df = pd.DataFrame()
    if conn:
        try:
            # Este QUERY es clave: Une las tablas para ver quién debe qué y de qué grupo es.
            query = """
                SELECT 
                    m.nombre_miembro, 
                    m.apellido_miembro,
                    g.nombre_grupo, 
                    p.monto_prestamo, 
                    p.fecha_vencimiento,
                    p.estado_prestamo
                FROM Prestamo p
                JOIN Miembro m ON p.id_miembro = m.id_miembro
                JOIN Grupo g ON m.id_grupo = g.id_grupo
                WHERE g.id_distrito = %s 
                AND p.estado_prestamo IN ('Activo', 'Pendiente', 'Mora')
                ORDER BY p.fecha_vencimiento ASC
            """
            df = pd.read_sql(query, conn, params=(id_distrito,))
            conn.close()
        except Exception as e:
            st.error(f"Error generando reporte de préstamos: {e}")
    return df

def obtener_reporte_multas(id_distrito):
    """Obtiene multas activas en el distrito."""
    conn = create_connection()
    df = pd.DataFrame()
    if conn:
        try:
            query = """
                SELECT 
                    m.nombre_miembro, 
                    g.nombre_grupo, 
                    mu.monto_multa, 
                    mu.motivo_multa,
                    mu.estado_multa
                FROM Multa mu
                JOIN Miembro m ON mu.id_miembro = m.id_miembro
                JOIN Grupo g ON m.id_grupo = g.id_grupo
                WHERE g.id_distrito = %s AND mu.estado_multa = 'Pendiente'
            """
            df = pd.read_sql(query, conn, params=(id_distrito,))
            conn.close()
        except Exception as e:
            st.error(f"Error generando reporte de multas: {e}")
    return df

# ------------------------------------------------------------------------------
# INTERFAZ GRÁFICA PRINCIPAL
# ------------------------------------------------------------------------------

def app():
    # 1. VERIFICACIÓN DE SEGURIDAD
    if 'id_distrito_actual' not in st.session_state:
        st.error("Acceso no autorizado. Inicie sesión.")
        st.stop()
    
    id_distrito = st.session_state['id_distrito_actual']
    
    # 2. BARRA LATERAL (SIDEBAR)
    st.sidebar.title("👩‍🌾 Panel Promotora")
    st.sidebar.write(f"Distrito ID: {id_distrito}")
    
    opcion = st.sidebar.radio(
        "Menú de Opciones", 
        ["📊 Dashboard y Reportes", "📂 Gestión de Grupos (Detalles)", "➕ Agregar Nuevo Grupo"]
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

    # 3. LÓGICA DE LAS OPCIONES

    # --- OPCIÓN 1: REPORTES GENERALES ---
    if opcion == "📊 Dashboard y Reportes":
        st.title("Reportes Generales del Distrito")
        st.markdown("Resumen de actividad financiera de todos los grupos bajo su cargo.")
        
        # Métricas rápidas (KPIs)
        # Podrías hacer consultas count(*) aquí para llenar estos datos reales
        col1, col2, col3 = st.columns(3)
        
        df_prestamos = obtener_reporte_prestamos(id_distrito)
        df_multas = obtener_reporte_multas(id_distrito)
        
        col1.metric("Préstamos Activos", len(df_prestamos))
        col2.metric("Multas Pendientes", len(df_multas))
        # Total dinero en la calle (suma de préstamos)
        total_prestado = df_prestamos['monto_prestamo'].sum() if not df_prestamos.empty else 0
        col3.metric("Capital en Préstamos", f"${total_prestado:,.2f}")

        st.divider()

        st.subheader("⚠️ Estado de Préstamos (Activos/Mora)")
        if df_prestamos.empty:
            st.info("No hay préstamos activos en este momento.")
        else:
            # Mostramos la tabla con Nombre, Grupo y Estado
            st.dataframe(
                df_prestamos, 
                use_container_width=True,
                column_config={
                    "nombre_miembro": "Miembro",
                    "nombre_grupo": "Pertenece al Grupo",
                    "monto_prestamo": st.column_config.NumberColumn("Monto", format="$%.2f"),
                    "estado_prestamo": "Estado"
                }
            )

        st.subheader("🚨 Reporte de Multas e Infracciones")
        if df_multas.empty:
            st.success("¡Excelente! No hay multas pendientes en el distrito.")
        else:
            st.dataframe(df_multas, use_container_width=True)

    # --- OPCIÓN 2: GESTIÓN DE GRUPOS (Tu archivo distrito.py) ---
    elif opcion == "📂 Gestión de Grupos (Detalles)":
        # Aquí llamamos directamente a la función principal del archivo que creamos antes
        # Esto reutiliza toda la lógica de selectores en cascada
        distrito.app()

    # --- OPCIÓN 3: AGREGAR NUEVO GRUPO ---
    elif opcion == "➕ Agregar Nuevo Grupo":
        st.title("Registrar Nuevo Grupo")
        st.markdown("Utilice este formulario para dar de alta un nuevo grupo en su distrito.")
        
        with st.form("form_alta_grupo"):
            col_a, col_b = st.columns(2)
            with col_a:
                nombre_nuevo = st.text_input("Nombre del Grupo")
                ubicacion_nueva = st.text_input("Ubicación / Comunidad")
            with col_b:
                # El distrito es automático, no se pregunta
                st.text_input("Distrito Asignado (Automático)", value=f"ID: {id_distrito}", disabled=True)
                st.info("La fecha de creación se registrará como 'Hoy'.")
            
            submitted = st.form_submit_button("Guardar Nuevo Grupo")
            
            if submitted:
                if nombre_nuevo and ubicacion_nueva:
                    exito = registrar_nuevo_grupo(nombre_nuevo, ubicacion_nueva, id_distrito)
                    if exito:
                        st.success(f"¡El grupo '{nombre_nuevo}' ha sido creado exitosamente!")
                        # Opcional: st.rerun() para limpiar
                    else:
                        st.error("Hubo un problema al guardar en la base de datos.")
                else:
                    st.warning("Por favor complete el nombre y la ubicación.")

if __name__ == "__main__":
    # Solo para pruebas
    st.session_state['id_distrito_actual'] = 1 
    app()
