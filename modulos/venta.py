# administrador.py

import streamlit as st
import pandas as pd
from utils.db_manager import (
    get_global_kpis, 
    get_all_districts, add_district, delete_district,
    get_all_promotoras, add_promotora, delete_promotora
)

def show_administrador_dashboard():
    """
    Muestra el panel de control y las funcionalidades para el Administrador.
    """
    st.title("🛡️ Panel de Control General del Sistema SGI")
    st.write("Vista de alto nivel y gestión de la estructura organizativa (Distritos y Promotoras).")

    st.markdown("---")

    # --- 1. Key Performance Indicators (KPIs) Globales ---
    st.header("Estadísticas Globales")
    
    kpis = get_global_kpis()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Total Grupos Activos", value=kpis['total_grupos'])
    with col2:
        st.metric(label="Miembros Registrados", value=kpis['total_miembros'])
    with col3:
        st.metric(label="Préstamos en Cartera", value=kpis['prestamos_activos'])
    with col4:
        st.metric(label="Utilidades Totales Históricas", value=f"${kpis['utilidades_totales']:,.2f}")
    
    st.markdown("---")

    # --- 2. Funcionalidades de Gestión ---
    tab1, tab2 = st.tabs(["🗺️ Gestión de Distritos", "👤 Gestión de Promotoras"])

    with tab1:
        manage_districts_view()
    
    with tab2:
        manage_promotoras_view()


def manage_districts_view():
    """Vista para la gestión de la tabla Distrito."""
    st.subheader("Administración de Distritos")

    # Mostrar todos los distritos
    districts_df = get_all_districts()
    if not districts_df.empty:
        st.dataframe(districts_df, use_container_width=True)
    else:
        st.info("No hay distritos registrados.")

    # Formulario para Añadir Distrito
    st.markdown("#### Añadir Nuevo Distrito")
    with st.form("add_district_form", clear_on_submit=True):
        new_district_name = st.text_input("Nombre del Nuevo Distrito", max_chars=100)
        submitted = st.form_submit_button("Registrar Distrito")
        
        if submitted and new_district_name:
            if add_district(new_district_name):
                st.success(f"Distrito '{new_district_name}' registrado con éxito.")
                st.experimental_rerun()
            else:
                st.error("Fallo al registrar el distrito.")

    # Formulario para Eliminar Distrito
    st.markdown("#### Eliminar Distrito")
    if not districts_df.empty:
        district_ids = districts_df['ID_Distrito'].tolist()
        district_to_delete = st.selectbox("Seleccione el ID del Distrito a eliminar:", district_ids)
        if st.button("Eliminar Distrito Seleccionado", help="¡Precaución! Esto debe ser manejado con cuidado debido a las relaciones con Grupo y Promotora."):
            # Una eliminación en cascada o una verificación de dependencias es necesaria aquí.
            if delete_district(district_to_delete):
                st.success(f"Distrito ID {district_to_delete} eliminado con éxito.")
                st.experimental_rerun()
            else:
                st.error("Fallo al eliminar el distrito. Revise si hay grupos o promotoras asignadas.")


def manage_promotoras_view():
    """Vista para la gestión de la tabla Promotora."""
    st.subheader("Administración de Promotoras")

    # Obtener listado de Promotoras con su Distrito
    promotoras_df = get_all_promotoras()
    if not promotoras_df.empty:
        st.dataframe(promotoras_df, use_container_width=True)
    else:
        st.info("No hay promotoras registradas.")

    # Obtener distritos para el selector
    districts_df = get_all_districts()
    district_options = dict(zip(districts_df['ID_Distrito'], districts_df['Nombre']))
    
    # Formulario para Añadir Promotora
    st.markdown("#### Añadir Nueva Promotora")
    with st.form("add_promotora_form", clear_on_submit=True):
        p_nombre = st.text_input("Nombre de la Promotora")
        p_contacto = st.text_input("Información de Contacto")
        p_distrito_id = st.selectbox("Distrito Asignado", options=district_options.keys(), format_func=lambda x: district_options[x] if x in district_options else "Seleccione Distrito")
        
        submitted = st.form_submit_button("Registrar Promotora")

        if submitted and p_nombre and p_distrito_id:
            if add_promotora(p_nombre, p_contacto, p_distrito_id):
                st.success(f"Promotora '{p_nombre}' registrada y asignada a {district_options[p_distrito_id]}.")
                st.experimental_rerun()
            else:
                st.error("Fallo al registrar la promotora.")

    # Formulario para Eliminar Promotora
    st.markdown("#### Eliminar Promotora")
    if not promotoras_df.empty:
        promotora_ids = promotoras_df['ID_Promotora'].tolist()
        promotora_to_delete = st.selectbox("Seleccione el ID de la Promotora a eliminar:", promotora_ids)
        if st.button("Eliminar Promotora Seleccionada"):
            if delete_promotora(promotora_to_delete):
                st.success(f"Promotora ID {promotora_to_delete} eliminada con éxito.")
                st.experimental_rerun()
            else:
                st.error("Fallo al eliminar la promotora.")
        con.close()

        st.success("Usuario registrado correctamente.")
        st.rerun()
