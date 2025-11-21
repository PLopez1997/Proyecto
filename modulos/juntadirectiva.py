import streamlit as st

def junta_directiva_page():
    st.title("Panel de Junta Directiva")
    st.write("Contenido exclusivo para Junta Directiva.")

import streamlit as st
import pandas as pd
import sys
import os

# Aseguramos que Python encuentre el archivo conexion.py en la carpeta principal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# --- AQUÍ ESTABA EL ERROR: Usamos el nombre real de tu función ---
from conexion import get_connection 

def show_directiva_dashboard():
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
                nombre = st.text_input("Nombre")
                apellido = st.text_input("Apellido")
                dui = st.text_input("DUI (Documento Único)")
            with col2:
                telefono = st.text_input("Teléfono")
                direccion = st.text_input("Dirección")
                # Ajusta los IDs de rol según tu tabla Roles en la BD
                rol_id = st.selectbox("Asignar Rol", [1, 2, 3], format_func=lambda x: "Miembro" if x==3 else ("Presidente" if x==1 else "Tesorero"))
            
            submitted = st.form_submit_button("Guardar Miembro")
            
            if submitted:
                if nombre and apellido and dui:
                    guardar_miembro_bd(nombre, apellido, dui, telefono, direccion, rol_id)
                else:
                    st.error("Por favor llene los campos obligatorios.")

    # --- PESTAÑA 2: LISTADO ---
    with tab2:
        st.subheader("Directorio de Miembros")
        listar_miembros()

# --- FUNCIONES SQL ---

def guardar_miembro_bd(nombre, apellido, dui, telefono, direccion, rol_id):
    # Usamos get_connection() aquí
    conn = get_connection() 
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id', 1) 
            
            query = """
                INSERT INTO Miembros (Nombre, Apellido, DUI, Telefono, Direccion, ID_Rol, ID_Grupo)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            valores = (nombre, apellido, dui, telefono, direccion, rol_id, grupo_id)
            
            cursor.execute(query, valores)
            conn.commit()
            st.success(f"Miembro {nombre} {apellido} registrado exitosamente.")
        except Exception as e:
            st.error(f"Error al guardar en BD: {e}")
        finally:
            cursor.close()
            conn.close()

def listar_miembros():
    # Usamos get_connection() aquí también
    conn = get_connection()
    if conn:
        try:
            grupo_id = st.session_state.get('grupo_id', 1)
            query = "SELECT ID_Miembro, Nombre, Apellido, DUI, Telefono, ID_Rol FROM Miembros WHERE ID_Grupo = %s"
            
            df = pd.read_sql(query, conn, params=(grupo_id,))
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No hay miembros registrados en este grupo aún.")
        except Exception as e:
            st.error(f"Error al cargar miembros: {e}")
        finally:
            conn.close()
