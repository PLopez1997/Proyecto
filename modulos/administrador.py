import streamlit as st
import pandas as pd
# Asegúrate de que esta importación coincida con tu estructura de archivos
try:
    from config.conexion import obtener_conexion 
except ImportError:
    # Fallback para simulación en entornos como Colab sin la estructura completa
    st.error("Error: No se pudo importar obtener_conexion. Asegúrate de que el archivo config/conexion.py exista.")
    obtener_conexion = None 

# --- Funciones Auxiliares para Datos de Referencia (Simulación) ---

def fetch_referencia_data():
    """Función para obtener IDs de referencia (Distritos, Ciclos) para los selectbox."""
    if not obtener_conexion:
        # Datos simulados para que el formulario funcione si la DB no está conectada
        return {
            "distritos": pd.DataFrame({"Id_distrito": [1, 2], "Nombre": ["Central", "Norte"]}),
            "ciclos": pd.DataFrame({"Id_ciclo": [1, 2, 3], "Nombre": ["Ciclo 2025-I", "Ciclo 2025-II", "Ciclo 2026-I"]}),
            "grupos": pd.DataFrame({"Id_grupo": [101, 102], "Nombre": ["G-Paz", "G-Sol"]})
        }
    
    # Lógica para obtener datos reales de la DB (necesitas tener estas tablas)
    conn = obtener_conexion()
    if conn:
        try:
            # Asume que tienes una tabla Distrito y una tabla Ciclo
            distritos = pd.read_sql("SELECT Id_distrito, Nombre FROM Distrito", conn)
            ciclos = pd.read_sql("SELECT Id_ciclo, Nombre FROM Ciclo", conn)
            grupos = pd.read_sql("SELECT Id_grupo, Nombre FROM Grupo", conn)
            return {"distritos": distritos, "ciclos": ciclos, "grupos": grupos}
        except Exception as e:
            st.warning(f"No se pudieron cargar datos de referencia: {e}")
            return fetch_referencia_data() # Retorna datos simulados en caso de error de consulta
        finally:
            conn.close()
    return fetch_referencia_data() # Retorna datos simulados si la conexión falla

# --- Lógica Específica: Creación de Grupos y Miembros ---

def create_new_group(ref_data):
    """Formulario y lógica para registrar un nuevo grupo en la tabla Grupo."""
    st.header("➕ Crear Nuevo Grupo GAPC")

    # Mapear nombres a IDs para FKs
    distritos_map = dict(zip(ref_data["distritos"]["Nombre"], ref_data["distritos"]["Id_distrito"]))
    ciclos_map = dict(zip(ref_data["ciclos"]["Nombre"], ref_data["ciclos"]["Id_ciclo"]))

    with st.form("form_nuevo_grupo"):
        # Campos de tu tabla Grupo:
        nombre = st.text_input("Nombre del Grupo (Obligatorio)")
        fecha_inicio = st.date_input("Fecha de inicio (Ciclo)")
        
        # FKs
        distrito_nombre = st.selectbox("Asignar a Distrito", ref_data["distritos"]["Nombre"])
        ciclo_nombre = st.selectbox("Asignar a Ciclo", ref_data["ciclos"]["Nombre"])
        
        # Atributos de Reglas
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
            
            if not id_distrito or not id_ciclo:
                st.error("Error al obtener IDs de referencia. Revise la tabla Distrito y Ciclo.")
                return

            con = obtener_conexion()
            if con:
                try:
                    cursor = con.cursor()
                    # NOTA: Se asume que Id_grupo es AUTO_INCREMENT. 
                    # Se incluye Id_distrito (crucial para el filtrado)
                    # El campo Id_cliente se omite por ambigüedad.
                    
                    sql = """
                    INSERT INTO Grupo (Nombre, Fecha_inicio, Id_ciclo, Tasa_interes, Tipo_multa, Regla_interna, Id_distrito)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        nombre, str(fecha_inicio), id_ciclo, tasa_interes, tipo_multa, regla_interna, id_distrito
                    ))
                    con.commit()
                    st.success(f"✅ Grupo '{nombre}' registrado correctamente en el Distrito {distrito_nombre}.")
                    st.rerun()
                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al registrar el grupo: {e}")
                finally:
                    cursor.close()
                    con.close()
            else:
                st.error("No se pudo establecer conexión con la base de datos.")

def add_member_to_group(ref_data):
    """Formulario y lógica para agregar un miembro a un grupo existente."""
    st.header("👥 Agregar Nuevo Miembro a Grupo")

    grupos_map = dict(zip(ref_data["grupos"]["Nombre"], ref_data["grupos"]["Id_grupo"]))

    with st.form("form_nuevo_miembro"):
        # Campos de la tabla Miembro (ejemplo)
        nombre_miembro = st.text_input("Nombre Completo del Miembro")
        cedula = st.text_input("Cédula/DUI (Identificación)")
        grupo_nombre = st.selectbox("Asignar a Grupo", ref_data["grupos"]["Nombre"])

        enviar = st.form_submit_button("✅ Guardar Nuevo Miembro")

        if enviar:
            if not nombre_miembro or not cedula:
                st.warning("⚠️ Nombre y Cédula son obligatorios.")
                return

            id_grupo = grupos_map.get(grupo_nombre)
            if not id_grupo:
                st.error("Error: Grupo seleccionado no es válido.")
                return

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
                    st.error(f"❌ Error al registrar el miembro: {e}")
                finally:
                    cursor.close()
                    con.close()
            else:
                st.error("No se pudo establecer conexión con la base de datos.")


def pagina_grupos_admin():
    """ Contenido principal para la gestión de grupos y miembros. """
    ref_data = fetch_referencia_data()
    
    st.title("Administración de Unidades y Miembros")
    
    tab_grupo, tab_miembro = st.tabs(["Crear Nuevo Grupo", "Agregar Miembro"])
    
    with tab_grupo:
        create_new_group(ref_data)
        
    with tab_miembro:
        add_member_to_group(ref_data)


# --- Función Principal del Administrador (modificada para llamar a la nueva página) ---

def administrador_page():
    """
    Función principal que se ejecuta al iniciar sesión como Administrador.
    Define el menú lateral y el contenido de la página.
    """
    st.title("Panel de Administración Global")
    
    # 1. Mostrar el menú lateral con st.sidebar
    opciones = ["Gestión de Usuarios", "Grupos y Distritos", "Reportes Consolidados"] 
    seleccion = st.sidebar.selectbox("Selecciona una sección", opciones)
    
    # 2. Según la opción seleccionada, mostramos el contenido correspondiente
    if seleccion == "Gestión de Usuarios":
        st.header("👤 Gestión de Usuarios")
        st.write("Formulario para crear y editar roles de usuario.")
        # Aquí va la función create_user_form()
        
    elif seleccion == "Grupos y Distritos":
        # ¡Llamamos a la nueva función!
        pagina_grupos_admin()
        
    elif seleccion == "Reportes Consolidados":
        st.header("📊 Reportes Globales")
        st.write("Acceso irrestricto a todos los reportes (Caja, Mora, Utilidades).")
        # Aquí va la función show_reports()
