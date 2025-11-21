import streamlit as st
import pandas as pd
import mysql.connector

# Importación Confirmada por el Usuario: Asume que app.py carga el módulo correctamente
from config.conexion import obtener_conexion 

# --- Funciones Auxiliares para Datos de Referencia ---

def fetch_referencia_data():
    """Función para obtener IDs de referencia (Distritos, Ciclos, Grupos) para los selectbox."""
    
    # ⚠️ Nota: Esta lógica depende de que tus tablas 'Distrito' y 'Ciclo' existan.
    
    conn = obtener_conexion()
    if conn:
        try:
            distritos = pd.read_sql("SELECT Id_distrito, Nombre FROM Distrito", conn)
            ciclos = pd.read_sql("SELECT Id_ciclo, Nombre FROM Ciclo", conn)
            grupos = pd.read_sql("SELECT Id_grupo, Nombre FROM Grupo", conn)
            return {"distritos": distritos, "ciclos": ciclos, "grupos": grupos}
        except Exception as e:
            st.warning(f"No se pudieron cargar datos de referencia (Distrito/Ciclo/Grupo). Error: {e}")
        finally:
            conn.close()
            
    # Datos simulados en caso de fallo de conexión o tablas no existentes
    return {
        "distritos": pd.DataFrame({"Id_distrito": [1, 2], "Nombre": ["Central", "Norte"]}),
        "ciclos": pd.DataFrame({"Id_ciclo": [1, 2, 3], "Nombre": ["Ciclo 2025-I", "Ciclo 2025-II", "Ciclo 2026-I"]}),
        "grupos": pd.DataFrame({"Id_grupo": [101, 102], "Nombre": ["G-Paz", "G-Sol"]})
    }

# --- Lógica Específica: Creación de Grupos y Miembros ---

def create_new_group(ref_data):
    """Formulario y lógica para registrar un nuevo grupo en la tabla Grupo."""
    st.subheader("➕ Crear Nuevo Grupo GAPC")

    # Mapear nombres a IDs para FKs
    distritos_map = dict(zip(ref_data["distritos"]["Nombre"], ref_data["distritos"]["Id_distrito"]))
    ciclos_map = dict(zip(ref_data["ciclos"]["Nombre"], ref_data["ciclos"]["Id_ciclo"]))

    with st.form("form_nuevo_grupo"):
        # 1. Atributos Principales
        nombre = st.text_input("Nombre del Grupo (Obligatorio)")
        fecha_inicio = st.date_input("Fecha de inicio del Ciclo")
        
        # 2. Claves Foráneas (FKs)
        distrito_nombre = st.selectbox("Asignar a Distrito (FK)", ref_data["distritos"]["Nombre"])
        ciclo_nombre = st.selectbox("Asignar a Ciclo (FK)", ref_data["ciclos"]["Nombre"])
        
        # 3. Atributos de Reglas
        tasa_interes = st.number_input("Tasa de Interés Anual (%)", min_value=1.0, max_value=100.0, value=12.0)
        tipo_multa = st.selectbox("Tipo de Multa", ["Monto Fijo", "Porcentaje de Aporte", "Sin Multa"])
        regla_interna = st.text_area("Regla Interna/Observaciones")

        enviar = st.form_submit_button("✅ Guardar Nuevo Grupo")

        if enviar:
            if not nombre:
                st.warning("⚠️ El nombre del grupo es obligatorio.")
                return

            # Obtener IDs de referencia
            id_distrito = distritos_map.get(distrito_nombre)
            id_ciclo = ciclos_map.get(ciclo_nombre)
            
            con = obtener_conexion()
            if con:
                try:
                    cursor = con.cursor()
                    # Se asume que 'Id_cliente' que tienes en tu tabla Grupo es realmente el 'Id_distrito' para el filtrado.
                    # Asumimos que 'Regla interna' es 'Regla_interna' sin espacios.
                    sql = """
                    INSERT INTO Grupo (Nombre, Fecha_inicio, Id_ciclo, Tasa_interes, Tipo_multa, Regla_interna, Id_distrito)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        nombre, str(fecha_inicio), id_ciclo, tasa_interes, tipo_multa, regla_interna, id_distrito
                    ))
                    con.commit()
                    st.success(f"✅ Grupo '{nombre}' registrado correctamente.")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al registrar el grupo. Revise la estructura de la tabla Grupo. Error: {e}")
                finally:
                    cursor.close()
                    con.close()
            else:
                st.error("No se pudo establecer conexión con la base de datos.")

def add_member_to_group(ref_data):
    """Formulario y lógica para agregar un miembro a un grupo existente."""
    st.subheader("👥 Agregar Nuevo Miembro a Grupo")

    grupos_map = dict(zip(ref_data["grupos"]["Nombre"], ref_data["grupos"]["Id_grupo"]))

    with st.form("form_nuevo_miembro"):
        # Campos de la tabla Miembro (ejemplo)
        nombre_miembro = st.text_input("Nombre Completo del Miembro")
        cedula = st.text_input("Cédula/DUI (Identificación)")
        grupo_nombre = st.selectbox("Asignar a Grupo (FK)", ref_data["grupos"]["Nombre"])

        enviar = st.form_submit_button("✅ Guardar Nuevo Miembro")

        if enviar:
            if not nombre_miembro or not cedula:
                st.warning("⚠️ Nombre y Cédula son obligatorios.")
                return

            id_grupo = grupos_map.get(grupo_nombre)
            
            con = obtener_conexion()
            if con:
                try:
                    cursor = con.cursor()
                    # Asume que la tabla Miembro tiene columnas: Id_miembro (PK), Nombre, Cedula, Id_grupo (FK)
                    sql = """
                    INSERT INTO Miembro (Nombre, Cedula, Id_grupo)
                    VALUES (%s, %s, %s)
                    """
                    cursor.execute(sql, (nombre_miembro, cedula, id_grupo))
                    con.commit()
                    st.success(f"✅ Miembro '{nombre_miembro}' agregado al grupo {grupo_nombre}.")
                    st.rerun()
                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al registrar el miembro. Revise la estructura de la tabla Miembro. Error: {e}")
                finally:
                    cursor.close()
                    con.close()
            else:
                st.error("No se pudo establecer conexión con la base de datos.")


def pagina_grupos_admin():
    """ Contenido principal para la gestión de grupos y miembros. """
    ref_data = fetch_referencia_data()
    
    tab_grupo, tab_miembro = st.tabs(["Crear Nuevo Grupo", "Agregar Miembro"])
    
    with tab_grupo:
        create_new_group(ref_data)
        
    with tab_miembro:
        add_member_to_group(ref_data)

# --- Función Principal del Administrador (Punto de Entrada) ---

def administrador_page():
    """
    Función principal que se ejecuta al iniciar sesión como Administrador.
    Define el menú lateral y el contenido de la página.
    """
    st.title("Panel de Administración Global")
    
    # 1. Mostrar el menú lateral con st.sidebar
    opciones = ["Gestión de Usuarios", "Grupos y Distritos", "Reportes Consolidados"] 
    seleccion = st.sidebar.selectbox("Selecciona una sección", opciones)
    
    st.sidebar.markdown("---")
    st.sidebar.button("Cerrar Sesión")
    
    # 2. Según la opción seleccionada, mostramos el contenido correspondiente
    if seleccion == "Gestión de Usuarios":
        st.header("👤 Gestión de Usuarios")
        st.write("Formulario para crear y editar roles de usuario.")
        # Aquí va la función create_user_form()
        
    elif seleccion == "Grupos y Distritos":
        pagina_grupos_admin()
        
    elif seleccion == "Reportes Consolidados":
        st.header("📊 Reportes Globales")
        st.write("Acceso irrestricto a todos los reportes (Caja, Mora, Utilidades).")
        # Aquí va la función show_reports()
