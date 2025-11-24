import streamlit as st
import pandas as pd
from datetime import date

# --- IMPORTACIÓN CORRECTA DE LA CONEXIÓN ---
try:
    from modulos.config.conexion import obtener_conexion
except ImportError as e:
    st.error(f"Error al importar la conexión: {e}")
    st.stop()

# --- IMPORTACIÓN CORRECTA DEL MÓDULO DISTRITO ---
try:
    from modulos.distrito import app as distrito_page
except ImportError as e:
    st.error(f"Error al importar el módulo distrito: {e}")
    st.stop()


# ----------------------------------------------------------------------
# FUNCIÓN: REGISTRAR GRUPO
# ----------------------------------------------------------------------
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
                WHERE g.Id_distrito = %s
                  AND mu.Estado = 'Pendiente'
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
        ["📊 Dashboard y Reportes",
         "📂 Gestión de Grupos (Detalles)",
         "➕ Agregar Nuevo Grupo"]
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar Sesión"):
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
        col3.metric(
            "Capital Prestado",
            f"${df_prestamos['monto_prestamo'].sum():,.2f}" if not df_prestamos.empty else "$0.00"
        )

        st.divider()

        st.subheader("📌 Préstamos en el Distrito")
        st.dataframe(df_prestamos, use_container_width=True) if not df_prestamos.empty else st.info("No hay préstamos.")

        st.subheader("🚨 Multas Pendientes")
        st.dataframe(df_multas, use_container_width=True) if not df_multas.empty else st.success("Sin multas.")

    # --- OPCIÓN 2: GESTIÓN DE GRUPOS ---
    elif opcion == "📂 Gestión de Grupos (Detalles)":
        distrito_page()

    # --- OPCIÓN 3: AGREGAR GRUPO ---
    elif opcion == "➕ Agregar Nuevo Grupo":
        st.title("Nuevo Grupo")

        with st.form("form_alta_grupo"):
            nombre = st.text_input("Nombre del Grupo")
            ubicacion = st.text_input("Ubicación / Comunidad")

            submitted = st.form_submit_button("Guardar")

            if submitted:
                if nombre and ubicacion:
                    if registrar_nuevo_grupo(nombre, ubicacion, id_distrito):
                        st.success("Grupo creado correctamente.")
                    else:
                        st.error("Error al guardar el grupo.")
                else:
                    st.warning("Complete todos los campos.")


# PARA PRUEBAS
if __name__ == "__main__":
    st.session_state['id_distrito_actual'] = 1
    app()

