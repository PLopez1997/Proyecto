import streamlit as st
from modulos.config.conexion import obtener_conexion
import pandas as pd


# PANEL DEL ADMINISTRADOR

def administrador_page():
    st.title("Panel de Control - Administrador")

    tabs = st.tabs(["📍 Distritos (Grupos)", "👤 Registrar Usuarios"])

    with tabs[0]:
        panel_grupos()

    with tabs[1]:
        panel_usuarios()


# ============================================
# SECCIÓN 1: GESTIÓN DE GRUPOS
# ============================================

def panel_grupos():
    st.subheader("📌 Gestión de Distritos (Tabla: grupos)")

    con = obtener_conexion()
    cursor = con.cursor()

    # Mostrar datos existentes
    cursor.execute("SELECT * FROM grupos")
    data = cursor.fetchall()
    columnas = [i[0] for i in cursor.description]

    df = pd.DataFrame(data, columns=columnas)
    st.dataframe(df, use_container_width=True)

    st.divider()
    st.subheader("➕ Agregar nuevo distrito")

    nombre_nuevo = st.text_input("Nombre del distrito", key="add_nombre")
    fecha_inicio_nueva = st.date_input("Fecha de inicio", key="add_fecha_inicio")
    id_ciclo_nuevo = st.number_input("ID Ciclo", min_value=1, step=1, key="add_id_ciclo")
    tasa_interes_nueva = st.number_input("Tasa de interés (%)", key="add_tasa_interes")
    tipo_multa_nuevo = st.text_input("Tipo de multa", key="add_tipo_multa")
    regla_interna_nueva = st.text_area("Regla interna", key="add_regla_interna")

    if st.button("Registrar nuevo distrito"):
        query = """
            INSERT INTO grupos (Nombre, Fecha_inicio, Id_ciclo, Tasa_interes, Tipo_multa, Regla_interna)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (nombre_nuevo, fecha_inicio_nueva, id_ciclo_nuevo, tasa_interes_nueva, tipo_multa_nuevo, regla_interna_nueva))
        con.commit()
        st.success("Distrito registrado correctamente.")
        st.rerun()

    st.divider()
    st.subheader("✏️ Editar Distrito Existente")

    # Asegurarse de que df no esté vacío y contenga 'id_grupo'
    if not df.empty and "id_grupo" in df.columns:
        id_editar = st.selectbox("Selecciona un ID a editar", df["id_grupo"].tolist())
    else:
        id_editar = None
        st.info("No hay distritos disponibles para editar o la columna 'id_grupo' no existe.")

    if id_editar:
        # Cargar datos del distrito seleccionado
        cursor.execute("SELECT Nombre, Fecha_inicio, Id_ciclo, Tasa_interes, Tipo_multa, Regla_interna FROM grupos WHERE id_grupo = %s", (id_editar,))
        distrito_actual = cursor.fetchone()

        if distrito_actual:
            # Mostrar campos pre-rellenados para edición
            nombre_actual, fecha_inicio_actual, id_ciclo_actual, tasa_interes_actual, tipo_multa_actual, regla_interna_actual = distrito_actual

            st.write(f"Editando el distrito con ID: **{id_editar}**")

            # Convertir la fecha de inicio a datetime.date si es de otro tipo (ej. datetime.datetime)
            if isinstance(fecha_inicio_actual, pd.Timestamp):
                fecha_inicio_actual = fecha_inicio_actual.date()
            elif isinstance(fecha_inicio_actual, str):
                 fecha_inicio_actual = pd.to_datetime(fecha_inicio_actual).date()

            edited_nombre = st.text_input("Nombre del distrito", value=nombre_actual, key=f"edit_nombre_{id_editar}")
            edited_fecha_inicio = st.date_input("Fecha de inicio", value=fecha_inicio_actual, key=f"edit_fecha_inicio_{id_editar}")
            edited_id_ciclo = st.number_input("ID Ciclo", min_value=1, step=1, value=id_ciclo_actual, key=f"edit_id_ciclo_{id_editar}")
            edited_tasa_interes = st.number_input("Tasa de interés (%)", value=tasa_interes_actual, key=f"edit_tasa_interes_{id_editar}")
            edited_tipo_multa = st.text_input("Tipo de multa", value=tipo_multa_actual, key=f"edit_tipo_multa_{id_editar}")
            edited_regla_interna = st.text_area("Regla interna", value=regla_interna_actual, key=f"edit_regla_interna_{id_editar}")

            if st.button("Guardar cambios"):
                update_query = """
                    UPDATE grupos
                    SET Nombre = %s, Fecha_inicio = %s, Id_ciclo = %s, Tasa_interes = %s, Tipo_multa = %s, Regla_interna = %s
                    WHERE id_grupo = %s
                """
                cursor.execute(update_query, (
                    edited_nombre, edited_fecha_inicio, edited_id_ciclo,
                    edited_tasa_interes, edited_tipo_multa, edited_regla_interna,
                    id_editar
                ))
                con.commit()
                st.success(f"Distrito con ID {id_editar} actualizado correctamente.")
                st.rerun()

    con.close()
