import streamlit as st
import pandas as pd
import mysql.connector
import hashlib
import uuid # Para generar IDs anónimos si fuera necesario

# Importación Confirmada por el Usuario: Asume que app.py carga el módulo correctamente
# Esta importación debe ser relativa si administrador.py está en una carpeta, pero la mantengo
# como la última que funcionó, asumiendo que el entorno de ejecución lo resuelve.
from .config.conexion import obtener_conexion 

# --- Funciones Auxiliares para Datos de Referencia ---

def fetch_referencia_data():
    """Función para obtener IDs de referencia (Distritos, Ciclos, Grupos) para los selectbox."""
    
    conn = obtener_conexion()
    if conn:
        try:
            # Trae todos los datos necesarios para las FKs y la asignación de usuarios
            distritos = pd.read_sql("SELECT Id_distrito, Nombre FROM Distrito", conn)
            ciclos = pd.read_sql("SELECT Id_ciclo FROM Ciclo", conn)
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

# --- 1. GESTIÓN DE USUARIOS ---

def create_user_form(ref_data):
    """Formulario para crear un nuevo usuario y asignar su rol/referencia."""
    st.subheader("➕ Registrar Nuevo Usuario")
    
    # Mapear nombres a IDs para el campo Id_referencia
    distritos_map = dict(zip(ref_data["distritos"]["Nombre"], ref_data["distritos"]["Id_distrito"]))
    grupos_map = dict(zip(ref_data["grupos"]["Nombre"], ref_data["grupos"]["Id_grupo"]))

    with st.form("form_new_user"):
        new_username = st.text_input("Nombre de Usuario (Login)", help="Será usado para iniciar sesión")
        new_password = st.text_input("Contraseña", type="password")
        new_rol = st.selectbox("Rol del Usuario", 
                               ['Administrador', 'Promotora', 'Directivo', 'Miembro Común'])
        
        id_ref_seleccionado = None
        
        # Lógica dinámica para el campo Id_referencia
        if new_rol == 'Promotora':
            st.info("La Promotora debe ser asignada a un Distrito. Su Id_referencia será el Id_distrito.")
            distrito_nombre = st.selectbox("Asignar Distrito de Referencia", ref_data["distritos"]["Nombre"])
            id_ref_seleccionado = distritos_map.get(distrito_nombre)
            
        elif new_rol in ['Directivo', 'Miembro Común']:
            st.info("El Directivo/Miembro debe ser asignado a un Grupo. Su Id_referencia será el Id_grupo.")
            grupo_nombre = st.selectbox("Asignar Grupo de Referencia", ref_data["grupos"]["Nombre"])
            id_ref_seleccionado = grupos_map.get(grupo_nombre)
            
        elif new_rol == 'Administrador':
             st.info("El Administrador tiene acceso total. Su Id_referencia será NULL.")
             id_ref_seleccionado = None


        submitted = st.form_submit_button("Crear Usuario en el Sistema de Login")
        
        if submitted:
            if not new_username or not new_password:
                st.error("El Usuario y la Contraseña son obligatorios.")
                return

            # Generar Hash de Contraseña (Recomendado: Usar un algoritmo más seguro como bcrypt)
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            
            # El administrador no tiene filtro, por lo que su Id_referencia es NULL
            final_id_referencia = id_ref_seleccionado
            
            con = obtener_conexion()
            if con:
                try:
                    cursor = con.cursor()
                    # ASUME que tienes una tabla llamada 'Login' o 'Usuario' con estas columnas
                    sql = """
                    INSERT INTO Login (Usuario, Contraseña, Rol, Id_referencia)
                    VALUES (%s, %s, %s, %s)
                    """
                    # Nota: Id_referencia puede ser NULL, por eso se pasa directamente
                    cursor.execute(sql, (new_username, password_hash, new_rol, final_id_referencia))
                    con.commit()
                    st.success(f"Usuario {new_username} ({new_rol}) creado con éxito!")
                    st.json({
                        "Usuario": new_username, 
                        "Rol": new_rol, 
                        "Id_referencia": final_id_referencia if final_id_referencia is not None else "NULL (Acceso Global)"
                    })
                    st.rerun()
                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al insertar el usuario: {e}. Revise si la tabla Login/Usuario existe y acepta NULLs en Id_referencia.")
                finally:
                    cursor.close()
                    con.close()
            else:
                st.error("No se pudo establecer conexión con la base de datos para la gestión de usuarios.")

# --- 2. GESTIÓN DE GRUPOS Y MIEMBROS (Código existente, movido aquí) ---

def create_new_group(ref_data):
    """Formulario y lógica para registrar un nuevo grupo en la tabla Grupo."""
    st.subheader("➕ Crear Nuevo Grupo GAPC")

    distritos_map = dict(zip(ref_data["distritos"]["Nombre"], ref_data["distritos"]["Id_distrito"]))
    ciclos_map = dict(zip(ref_data["ciclos"]["Nombre"], ref_data["ciclos"]["Id_ciclo"]))

    with st.form("form_nuevo_grupo"):
        nombre = st.text_input("Nombre del Grupo (Obligatorio)")
        fecha_inicio = st.date_input("Fecha de inicio del Ciclo")
        
        distrito_nombre = st.selectbox("Asignar a Distrito (FK)", ref_data["distritos"]["Nombre"])
        ciclo_nombre = st.selectbox("Asignar a Ciclo (FK)", ref_data["ciclos"]["Nombre"])
        
        tasa_interes = st.number_input("Tasa de Interés Anual (%)", min_value=1.0, max_value=100.0, value=12.0)
        tipo_multa = st.selectbox("Tipo de Multa", ["Monto Fijo", "Porcentaje de Aporte", "Sin Multa"])
        regla_interna = st.text_area("Regla Interna/Observaciones")

        enviar = st.form_submit_button("✅ Guardar Nuevo Grupo")

        if enviar:
            if not nombre:
                st.warning("⚠️ El nombre del grupo es obligatorio.")
                return

            id_distrito = distritos_map.get(distrito_nombre)
            id_ciclo = ciclos_map.get(ciclo_nombre)
            
            con = obtener_conexion()
            if con:
                try:
                    cursor = con.cursor()
                    # Se usa Id_distrito para el campo de referencia del grupo
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


# --- 3. REPORTES GLOBALES ---

def show_reports():
    """Muestra todos los reportes del sistema (sin filtros)."""
    st.header("📊 Reportes Consolidados (Acceso Global)")
    st.markdown("El Administrador puede ver el rendimiento financiero de todos los Distritos y Grupos.")
    
    # 1. Reporte de Caja Global
    st.subheader("1. Reporte de Caja Global")
    st.markdown("Consulta SQL: `SELECT Fecha, Monto, Tipo, Id_grupo FROM Transaccion`")
    
    # Simulación de consulta o placeholder real de DB
    data_caja = {
        'Fecha': ['2025-10-01', '2025-10-01', '2025-10-02', '2025-10-02'],
        'Grupo_ID': [101, 102, 101, 102],
        'Tipo': ['Aporte', 'Préstamo', 'Multa', 'Aporte'],
        'Monto': [50.00, -200.00, 5.00, 75.00]
    }
    df_caja = pd.DataFrame(data_caja)
    st.dataframe(df_caja, use_container_width=True)
    
    # 2. Resumen de Cartera y Mora
    st.subheader("2. Cartera de Préstamos y Mora")
    st.markdown("Consulta SQL: `SELECT COUNT(*), SUM(Monto_pendiente), AVG(Dias_mora) FROM Prestamo`")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Total Préstamos Activos", value="150", help="Conteo de todos los préstamos en curso.")
    col2.metric(label="Capital Prestado Total", value="$55,000.00", help="Monto total pendiente de pago.")
    col3.metric(label="Tasa de Mora Global", value="8.5%", delta_color="inverse", help="Porcentaje de préstamos con más de X días de retraso.")
    
    st.markdown("---")
    st.subheader("3. Utilidades Generadas (Simulación)")
    st.metric(label="Utilidad Bruta Acumulada", value="$4,520.00", help="Intereses y multas generadas en el ciclo actual.")


# --- Función Principal del Administrador (Punto de Entrada) ---

def administrador_page():
    """
    Función principal que se ejecuta al iniciar sesión como Administrador.
    Define el menú lateral y el contenido de la página.
    """
    
    # Obtener los datos de referencia una sola vez al inicio
    ref_data = fetch_referencia_data()
    
    st.title("Panel de Administración Global")
    
    # 1. Mostrar el menú lateral con st.sidebar
    opciones = ["Gestión de Usuarios", "Grupos y Distritos", "Reportes Consolidados"] 
    seleccion = st.sidebar.selectbox("Selecciona una sección", opciones)
    
    st.sidebar.markdown("---")
    # Agregamos la lógica de cerrar sesión simple
    if st.sidebar.button("Cerrar Sesión"):
        if 'rol' in st.session_state:
            del st.session_state['rol']
        if 'filtro_id' in st.session_state:
            del st.session_state['filtro_id']
        st.rerun()

    # 2. Según la opción seleccionada, mostramos el contenido correspondiente
    if seleccion == "Gestión de Usuarios":
        st.header("👤 Gestión de Usuarios")
        create_user_form(ref_data)
        
    elif seleccion == "Grupos y Distritos":
        st.header("🏘️ Gestión de Grupos y Miembros")
        pagina_grupos_admin()
        
    elif seleccion == "Reportes Consolidados":
        show_reports()
