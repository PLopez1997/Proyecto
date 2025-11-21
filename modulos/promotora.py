import streamlit as st

def promotora_page():
    st.title("Panel de Promotora")
    st.write("Contenido exclusivo para PROMOTORAS.")

# modulos/promotora.py

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.db_manager import (
    fetch_data, 
    get_promotora_districts, get_groups_by_district, 
    get_group_financial_summary, get_members_summary_by_group 
) # Importa tus funciones de MySQL

# --- 1. Funciones de Vistas (Detalle del Contenido) ---

def show_group_summary(group_id):
    """Muestra el resumen financiero y métricas clave del grupo."""
    st.header("📊 Resumen Financiero y Métricas Clave")
    st.write("Validación rápida de la salud financiera del grupo.")

    try:
        summary = get_group_financial_summary(group_id)
    except Exception as e:
        st.error(f"Error al cargar el resumen financiero: {e}")
        return

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Caja Actual (Efectivo)", value=f"${summary.get('Caja_Actual', 0.0):,.2f}")
    with col2:
        st.metric(label="Ahorro Total Acumulado", value=f"${summary.get('Ahorro_Total_Miembros', 0.0):,.2f}")
    with col3:
        st.metric(label="Préstamos Activos", value=summary.get('Préstamos_Activos', 0))

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(label="Utilidades Acumuladas", value=f"${summary.get('Utilidades_Ciclo_Actual', 0.0):,.2f}")
    
    with col5:
        mora_pct = summary.get('Mora_Actual_Porcentaje', 0.0)
        mora_color = "red" if mora_pct > 10 else ("orange" if mora_pct > 5 else "green")
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; border-left: 5px solid {mora_color};">
            <p style='font-size: small; color: gray; margin: 0;'>% de Mora (Riesgo)</p>
            <h3 style='margin: 0; color: {mora_color};'>{mora_pct:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)
        st.warning("El porcentaje de mora es un indicador clave de validación.")


def show_members_detail(group_id):
    """Muestra la tabla de miembros con métricas clave (Asistencia y Préstamos/Mora)."""
    st.header("📋 Detalle de Miembros y Validación Técnica")
    st.write("Revisión de la participación individual, ausencias y estado de la cartera por miembro.")

    try:
        members_df = get_members_summary_by_group(group_id)
    except Exception as e:
        st.error(f"Error al cargar el detalle de miembros: {e}")
        return

    if not members_df.empty:
        # Estilizado para resaltar Ausencias y Mora (Validación técnica)
        def style_mora(val):
            return 'background-color: red' if val > 0 else 'background-color: lightgreen'

        def style_ausencia(val):
            return 'background-color: orange' if val >= 3 else ''
        
        st.dataframe(
            members_df.style.applymap(style_mora, subset=['Mora_Cuotas'])
                            .applymap(style_ausencia, subset=['Ausencias_Total']),
            use_container_width=True,
            column_config={
                "Ahorro_Acumulado": st.column_config.NumberColumn("Ahorro Acumulado", format="$%.2f"),
                "Préstamo_Vigente": st.column_config.CheckboxColumn("Préstamo Vigente")
            }
        )
        
        # Alertas de Ausencia (Control del número de ausencias permitidas [cite: 20])
        members_with_high_absences = members_df[members_df['Ausencias_Total'] >= 3] # Asumiendo 3 es el límite
        if not members_with_high_absences.empty:
            st.error("⚠️ Alerta: Algunos miembros tienen un alto nivel de ausencias.")
    else:
        st.info("No hay miembros registrados en este grupo.")


def show_report_downloads(group_id, group_name):
    """Permite la descarga de reportes consolidados."""
    st.header("📥 Descargar Reportes Consolidados")

    report_type = st.radio("Seleccione el Tipo de Reporte:", 
                           [
                            "Reporte de Caja (Ingresos/Egresos)", 
                            "Estado de Ahorros y Préstamos por Miembro", 
                            "Cartera de Préstamos y Mora", 
                            "Acta de Cierre de Ciclo"
                           ])

    if st.button("Generar y Descargar Reporte"):
        # La Promotora puede descargar reportes consolidados 
        st.info(f"Generando {report_type} para {group_name}...")
        
        # Lógica para generar datos (usando funciones de db_manager)
        if report_type == "Reporte de Caja (Ingresos/Egresos)":
            report_data = fetch_data(f"SELECT * FROM Caja WHERE ID_Grupo = {group_id} LIMIT 10") # Simulación
            report_title = "Reporte_Caja"
        # Agrega más condiciones para otros reportes...
        else:
            report_data = get_members_summary_by_group(group_id) # Usamos este como fallback
            report_title = report_type.replace(" ", "_")
        
        if not report_data.empty:
            csv = report_data.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="Descargar archivo CSV",
                data=csv,
                file_name=f"{report_title}_{group_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv',
            )
            st.success("Descarga lista.")
        else:
            st.warning("No hay datos disponibles para el reporte seleccionado.")


# --- 2. Función Principal del Módulo (Llamada desde app.py) ---

def promotora_page():
    """
    Función principal para el rol de Promotora.
    Incluye la selección de grupo y el menú lateral de supervisión.
    """
    st.title("🤝 Panel de Supervisión de Promotora")

    # --- 1. Inicialización y Obtención de Grupos Asignados ---
    # SIMULACIÓN DE ID (Reemplazar con el ID real de la promotora logueada)
    promotora_id = st.session_state.get('user_id', 1) 
    promotora_name = st.session_state.get('username', 'Promotora X')

    try:
        district_ids = get_promotora_districts(promotora_id)
        # Filtra grupos por los distritos asignados
        groups_df = get_groups_by_district(district_ids) 
    except Exception as e:
        st.error(f"Error al cargar los grupos supervisados: {e}")
        groups_df = pd.DataFrame()

    if groups_df.empty:
        st.warning("No hay grupos asignados a su supervisión en este momento.")
        return

    # --- 2. Menú Lateral y Selector de Grupo ---
    with st.sidebar:
        st.header(f"Hola, {promotora_name}")
        st.subheader("🔍 Grupos Asignados")
        
        group_options_map = dict(zip(groups_df['ID_Grupo'], groups_df['Nombre_Grupo'] + " (" + groups_df['Distrito'] + ")"))
        
        selected_group_id = st.selectbox(
            "Seleccione el Grupo a Supervisar:",
            options=groups_df['ID_Grupo'].tolist(),
            format_func=lambda x: group_options_map.get(x),
            key='promotora_group_selector'
        )
        
        if selected_group_id:
            st.markdown("---")
            st.subheader("Opciones de Supervisión")
            
            promotora_selection = st.radio(
                "Navegación",
                ["Resumen Financiero", "Detalle de Miembros", "Descargar Reportes"],
                key='promotora_menu'
            )
        else:
            st.stop() # Detiene la ejecución si no hay grupo seleccionado

    # --- 3. Contenido Principal Basado en la Selección ---
    
    st.header(f"Supervisando: {group_options_map.get(selected_group_id)}")
    st.markdown("---")

    if promotora_selection == "Resumen Financiero":
        show_group_summary(selected_group_id)
    
    elif promotora_selection == "Detalle de Miembros":
        show_members_detail(selected_group_id)
    
    elif promotora_selection == "Descargar Reportes":
        group_name = groups_df[groups_df['ID_Grupo'] == selected_group_id]['Nombre_Grupo'].iloc[0]
        show_report_downloads(selected_group_id, group_name)

# Alias para la función que se llama desde app.py
promotora_page = promotora_page
