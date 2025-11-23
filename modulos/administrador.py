import streamlit as st
import pandas as pd
import mysql.connector
import hashlib
import uuid  # Para generar IDs anónimos si fuera necesario

# IMPORT: ajusta según dónde esté app.py.
# Si ejecutas streamlit run app.py desde la raíz del proyecto, usa:
from .config.conexion import obtener_conexion

# -----------------------
# Helpers para inspección
# -----------------------
def table_columns(conn, table_name):
    """Devuelve una lista de columnas existentes de table_name (sin fallo)."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        cols = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return cols
    except Exception:
        return []

def pick_column(cols, candidates):
    """Devuelve la primera columna de candidates que exista en cols o None."""
    for c in candidates:
        if c in cols:
            return c
    return None

# -----------------------
# Lectura flexible (referencias)
# -----------------------
def fetch_referencia_data():
    conn = obtener_conexion()
    if not conn:
        st.warning("No hay conexión a BD; usando datos simulados.")
        return {
            "distritos": pd.DataFrame({"Id_distrito": [1, 2], "Nombre": ["Central", "Norte"]}),
            "ciclos": pd.DataFrame({"Id_ciclo": [1, 2], "Nombre": ["Ciclo 2025-I", "Ciclo 2025-II"]}),
            "grupos": pd.DataFrame({"Id_grupo": [101, 102], "Nombre": ["G-Paz", "G-Sol"]})
        }

    try:
        # 1. Traer datos de Distritos
        distrito_table = None
        for t in ["Distrito", "distrito", "Distritos", "distritos"]:
            if table_columns(conn, t):
                distrito_table = t
                break

        ref_distritos = pd.DataFrame({"Id_distrito": [], "Nombre": []})
        if distrito_table:
            cols = table_columns(conn, distrito_table)
            id_col = pick_column(cols, ["Id_distrito", "id_distrito", "Id_distr", "Id"])
            label_col = pick_column(cols, ["Nombre", "nombre", "Descripcion", "descripcion", "Label", "label"])
            if id_col and label_col:
                ref_distritos = pd.read_sql(f"SELECT `{id_col}` AS Id_distrito, `{label_col}` AS Nombre FROM `{distrito_table}`", conn)
            elif id_col:
                ref_distritos = pd.read_sql(f"SELECT `{id_col}` AS Id_distrito FROM `{distrito_table}`", conn)
                ref_distritos["Nombre"] = "Distrito " + ref_distritos["Id_distrito"].astype(str)

        # 2. Traer datos de Ciclos
        ciclo_table = None
        for t in ["Ciclo", "ciclo", "Ciclos", "ciclos"]:
            if table_columns(conn, t):
                ciclo_table = t
                break

        ref_ciclos = pd.DataFrame({"Id_ciclo": [], "Nombre": []})
        if ciclo_table:
            cols = table_columns(conn, ciclo_table)
            id_col = pick_column(cols, ["Id_ciclo", "id_ciclo", "Id"])
            # Usaremos una combinación de columnas para formar el nombre del ciclo si no hay columna Nombre
            label_col = pick_column(cols, ["Nombre", "nombre", "Descripcion", "Periodo", "Ciclo"])
            if id_col and label_col:
                ref_ciclos = pd.read_sql(f"SELECT `{id_col}` AS Id_ciclo, `{label_col}` AS Nombre FROM `{ciclo_table}`", conn)
            elif id_col:
                # Si no hay columna Nombre, usaremos Id_ciclo o Fecha_inicio si existe
                if 'Fecha_inicio' in cols:
                    df = pd.read_sql(f"SELECT `{id_col}` AS Id_ciclo, Fecha_inicio FROM `{ciclo_table}`", conn)
                    ref_ciclos = df.assign(Nombre=df['Id_ciclo'].astype(str) + " (" + df['Fecha_inicio'].astype(str) + ")")
                else:
                    ref_ciclos = pd.read_sql(f"SELECT `{id_col}` AS Id_ciclo FROM `{ciclo_table}`", conn)
                    ref_ciclos["Nombre"] = "Ciclo " + ref_ciclos["Id_ciclo"].astype(str)

        # 3. Traer datos de Grupos
        grupo_table = None
        for t in ["Grupo", "grupo", "Grupos", "grupos"]:
            if table_columns(conn, t):
                grupo_table = t
                break

        ref_grupos = pd.DataFrame({"Id_grupo": [], "Nombre": []})
        if grupo_table:
            cols = table_columns(conn, grupo_table)
            id_col = pick_column(cols, ["Id_grupo", "id_grupo", "Id"])
            label_col = pick_column(cols, ["Nombre", "nombre", "Grupo"])
            if id_col and label_col:
                ref_grupos = pd.read_sql(f"SELECT `{id_col}` AS Id_grupo, `{label_col}` AS Nombre FROM `{grupo_table}`", conn)
            elif id_col:
                ref_grupos = pd.read_sql(f"SELECT `{id_col}` AS Id_grupo FROM `{grupo_table}`", conn)
                ref_grupos["Nombre"] = "Grupo " + ref_grupos["Id_grupo"].astype(str)

        return {
            "distritos": ref_distritos,
            "ciclos": ref_ciclos,
            "grupos": ref_grupos
        }

    except Exception as e:
        st.warning(f"No se pudieron cargar datos de referencia. Error: {e}")
        return {
            "distritos": pd.DataFrame({"Id_distrito": [], "Nombre": []}),
            "ciclos": pd.DataFrame({"Id_ciclo": [], "Nombre": []}),
            "grupos": pd.DataFrame({"Id_grupo": [], "Nombre": []})
        }
    finally:
        try:
            conn.close()
        except Exception:
            pass

# --- 1. GESTIÓN DE USUARIOS ---

def create_user_form(ref_data):
    """Formulario para crear un nuevo usuario y asignar su rol/referencia."""
    st.subheader("➕ Registrar Nuevo Usuario")

    # Mapas para obtener IDs a partir de Nombres
    distritos_map = dict(zip(ref_data["distritos"]["Nombre"], ref_data["distritos"]["Id_distrito"]))
    grupos_map = dict(zip(ref_data["grupos"]["Nombre"], ref_data["grupos"]["Id_grupo"]))

    # form key único para evitar duplicados con otras páginas
    with st.form(key="form_new_user_admin"):
        new_username = st.text_input("Nombre de Usuario (Login)", help="Será usado para iniciar sesión", key="input_new_username_admin")
        new_password = st.text_input("Contraseña", type="password", key="input_new_password_admin")
        # Roles en minúscula para estandarizar con la base de datos (si usa minúsculas)
        new_rol = st.selectbox("Rol del Usuario", ['administrador', 'promotora', 'directivo', 'miembro común'], key="select_new_rol_admin")

        # Valor a insertar en la columna Id_referencia
        id_ref_seleccionado = None

        # Lógica dinámica para el campo Id_referencia basado en el rol
        if new_rol == 'promotora':
            if ref_data["distritos"].empty:
                st.warning("No hay distritos para asignar a la Promotora.")
                distrito_nombre = None
            else:
                st.info("La Promotora debe ser asignada a un Distrito. Su Id_referencia será el Id_distrito.")
                distrito_nombre = st.selectbox("Asignar Distrito de Referencia", ref_data["distritos"]["Nombre"], key="select_distrito_promotora")
                id_ref_seleccionado = distritos_map.get(distrito_nombre)

        elif new_rol in ['directivo', 'miembro común']:
            if ref_data["grupos"].empty:
                st.warning("No hay grupos para asignar al Directivo/Miembro.")
                grupo_nombre = None
            else:
                st.info("El Directivo/Miembro debe ser asignado a un Grupo. Su Id_referencia será el Id_grupo.")
                grupo_nombre = st.selectbox("Asignar Grupo de Referencia (Nombre del Grupo)", ref_data["grupos"]["Nombre"], key="select_grupo_directivo")
                id_ref_seleccionado = grupos_map.get(grupo_nombre)

        elif new_rol == 'administrador':
            st.info("El Administrador tiene acceso total. Su Id_referencia será NULL.")
            id_ref_seleccionado = None

        submitted = st.form_submit_button("Crear Usuario en el Sistema de Login", key="submit_new_user_admin")

        if submitted:
            if not new_username or not new_password:
                st.error("El Usuario y la Contraseña son obligatorios.")
                return

            # Generar Hash de Contraseña (usando SHA256 como en la versión anterior)
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()

            con = obtener_conexion()
            if con:
                cursor = None
                try:
                    # Detección de columnas flexibles para Login (Usuario/login)
                    table_name = "Login"
                    cols = table_columns(con, table_name)
                    if not cols:
                        table_name = "Usuario"
                        cols = table_columns(con, table_name)
                    if not cols:
                        st.error("No se encontró la tabla 'Login' o 'Usuario'.")
                        return

                    user_col = pick_column(cols, ["Usuario", "user", "User"])
                    pass_col = pick_column(cols, ["Contrasena_Hash", "Contrasena", "Password"])
                    rol_col = pick_column(cols, ["Rol", "rol", "Role"])
                    id_ref_col = pick_column(cols, ["Id_referencia", "id_referencia"])

                    # Si la columna se llama 'Contrasena', se guarda sin hash
                    # defensiva: pass_col puede ser None
                    pass_col_lower = (pass_col or "").lower()
                    pass_value = password_hash if "hash" in pass_col_lower else new_password

                    insert_cols = []
                    insert_vals = []
                    params = []

                    # Construir INSERT dinámico
                    if user_col:
                        insert_cols.append(user_col); insert_vals.append("%s"); params.append(new_username)
                    if pass_col:
                        insert_cols.append(pass_col); insert_vals.append("%s"); params.append(pass_value)
                    if rol_col:
                        insert_cols.append(rol_col); insert_vals.append("%s"); params.append(new_rol)
                    if id_ref_col:
                        insert_cols.append(id_ref_col); insert_vals.append("%s"); params.append(id_ref_seleccionado)

                    if not insert_cols:
                        st.error("No se pudo detectar columnas de la tabla de usuarios en la BD.")
                        return

                    cursor = con.cursor()
                    sql = f"INSERT INTO `{table_name}` ({', '.join('`'+c+'`' for c in insert_cols)}) VALUES ({', '.join(insert_vals)})"
                    cursor.execute(sql, tuple(params))
                    con.commit()
                    st.success(f"Usuario {new_username} ({new_rol}) creado con éxito!")
                    st.json({
                        "Usuario": new_username,
                        "Rol": new_rol,
                        "Id_referencia": id_ref_seleccionado if id_ref_seleccionado is not None else "NULL (Acceso Global)"
                    })
                    # rerun para actualizar state / listados si corresponde
                    st.experimental_rerun()
                except Exception as e:
                    try:
                        con.rollback()
                    except Exception:
                        pass
                    st.error(f"❌ Error al insertar el usuario: {e}. Revise si la tabla {table_name} existe y si las columnas de referencia aceptan NULLs.")
                finally:
                    try:
                        if cursor:
                            cursor.close()
                    except Exception:
                        pass
                    try:
                        con.close()
                    except Exception:
                        pass
            else:
                st.error("No se pudo establecer conexión con la base de datos para la gestión de usuarios.")

# --- 2. GESTIÓN DE GRUPOS ---

def create_new_group(ref_data):
    """Formulario y lógica para registrar un nuevo grupo en la tabla Grupo."""
    st.subheader("➕ Crear Nuevo Grupo GAPC")

    grupos_df = ref_data["grupos"]
    ciclos_df = ref_data["ciclos"]
    distritos_df = ref_data["distritos"]

    # Key del form único
    with st.form(key="form_nuevo_grupo_admin"):
        nombre = st.text_input("Nombre del Grupo (Obligatorio)", key="input_nombre_grupo_admin")

        # Ahora seleccionamos un ciclo existente (FK)
        if ciclos_df.empty:
            st.warning("⚠️ No hay ciclos registrados. Debe registrar un ciclo primero.")
            id_ciclo = None
            ciclo_nombre = "N/A"
        else:
            ciclo_nombre = st.selectbox("Asignar Ciclo Activo (FK)", ciclos_df["Nombre"], key="select_ciclo_grupo_admin")
            id_ciclo = int(ciclos_df.loc[ciclos_df["Nombre"] == ciclo_nombre, "Id_ciclo"].iloc[0])

        # Asignar a Distrito (FK)
        if distritos_df.empty:
            st.info("No hay distritos cargados. Se intentará insertar con Id_distrito NULL.")
            id_distrito = None
        else:
            distrito_nombre = st.selectbox("Asignar a Distrito (FK)", distritos_df["Nombre"], key="select_distrito_grupo_admin")
            id_distrito = int(distritos_df.loc[distritos_df["Nombre"] == distrito_nombre, "Id_distrito"].iloc[0])

        # Estos campos son parte del Grupo/Reglas Internas
        tasa_interes = st.number_input("Tasa de Interés Anual (%)", min_value=1.0, max_value=100.0, value=12.0, key="num_tasa_interes_grupo_admin")
        tipo_multa = st.selectbox("Tipo de Multa", ["Monto Fijo", "Porcentaje de Aporte", "Sin Multa"], key="select_tipo_multa_grupo_admin")
        regla_interna = st.text_area("Regla Interna/Observaciones", key="ta_regla_interna_grupo_admin")

        enviar = st.form_submit_button("✅ Guardar Nuevo Grupo", key="submit_new_grupo_admin")

        if enviar:
            if not nombre:
                st.warning("⚠️ El nombre del grupo es obligatorio.")
                return
            if id_ciclo is None:
                st.error("No se puede crear el grupo sin un Ciclo ID válido. Registre un ciclo.")
                return

            con = obtener_conexion()
            if con:
                cursor = None
                try:
                    grupo_table = "Grupo"
                    cols = table_columns(con, grupo_table)
                    if not cols:
                        grupo_table = "GrupoS"
                        cols = table_columns(con, grupo_table)
                    if not cols:
                        st.error("No se encontró la tabla 'Grupo'.")
                        return

                    cursor = con.cursor()

                    insert_cols = []
                    params = []
                    placeholders = []

                    # Función para agregar columnas si existen
                    def maybe_add(colname, value):
                        if colname in cols:
                            insert_cols.append(colname)
                            placeholders.append("%s")
                            params.append(value)

                    # Ajustado a las columnas más comunes de Grupo
                    maybe_add("Nombre", nombre)
                    maybe_add("Id_ciclo", id_ciclo)
                    maybe_add("Tasa_interes", tasa_interes)
                    maybe_add("Tipo_multa", tipo_multa)
                    maybe_add("Regla_interna", regla_interna)
                    maybe_add("Id_distrito", id_distrito)  # Conexión a Distrito

                    if not insert_cols:
                        st.error("Estructura de tabla grupos no reconocida para inserción.")
                        return

                    sql = f"INSERT INTO `{grupo_table}` ({', '.join('`' + c + '`' for c in insert_cols)}) VALUES ({', '.join(placeholders)})"
                    cursor.execute(sql, tuple(params))
                    con.commit()
                    st.success(f"✅ Grupo '{nombre}' registrado correctamente.")
                    st.balloons()
                    st.experimental_rerun()
                except Exception as e:
                    try:
                        con.rollback()
                    except Exception:
                        pass
                    st.error(f"❌ Error al registrar el grupo. Revise la estructura de la tabla Grupo. Error: {e}")
                finally:
                    try:
                        if cursor:
                            cursor.close()
                    except Exception:
                        pass
                    try:
                        con.close()
                    except Exception:
                        pass
            else:
                st.error("No se pudo establecer conexión con la base de datos.")

# --- 3. GESTIÓN DE CICLOS ---

def pagina_ciclos_admin(ref_data):
    """ Contenido principal para registrar un nuevo ciclo. """
    st.subheader("📅 Registrar Nuevo Ciclo Operativo")

    # Mapas para obtener IDs a partir de Nombres de Grupos
    grupos_map = dict(zip(ref_data["grupos"]["Nombre"], ref_data["grupos"]["Id_grupo"]))

    with st.form(key="form_nuevo_ciclo_admin"):
        # La tabla Ciclo tiene Id_grupo como FK
        if ref_data["grupos"].empty:
            st.warning("⚠️ No hay grupos registrados. No se puede asignar el ciclo.")
            id_grupo = None
            grupo_nombre = "N/A"
        else:
            grupo_nombre = st.selectbox("Grupo al que pertenece el Ciclo", ref_data["grupos"]["Nombre"], key="select_grupo_para_ciclo_admin")
            id_grupo = grupos_map.get(grupo_nombre)

        # Columnas de la tabla Ciclo
        fecha_inicio = st.date_input("Fecha de inicio del Ciclo", key="date_inicio_ciclo_admin")
        fecha_cierre = st.date_input("Fecha de cierre (estimada)", key="date_cierre_ciclo_admin")
        duracion = st.selectbox("Duración (meses)", [6, 12, 18], index=1, key="select_duracion_ciclo_admin")

        # Columnas opcionales que se llenan al cierre
        estado = st.selectbox("Estado del Ciclo", ["Activo", "Cerrado", "Pendiente"], index=0, key="select_estado_ciclo_admin")

        enviar = st.form_submit_button("✅ Guardar Ciclo", key="submit_nuevo_ciclo_admin")

        if enviar:
            if id_grupo is None:
                st.error("Debe haber un grupo seleccionado para asignar el ciclo.")
                return

            con = obtener_conexion()
            if con:
                cursor = None
                try:
                    ciclo_table = "Ciclo"
                    cols = table_columns(con, ciclo_table)
                    if not cols:
                        ciclo_table = "CicloS"
                        cols = table_columns(con, ciclo_table)
                    if not cols:
                        st.error("No se encontró la tabla 'Ciclo'.")
                        return

                    cursor = con.cursor()

                    insert_cols = []
                    params = []
                    placeholders = []

                    def maybe_add_ciclo(colname, value):
                        if colname in cols:
                            insert_cols.append(colname)
                            placeholders.append("%s")
                            params.append(value)

                    # Columnas de la tabla Ciclo: Id_grupo, Fecha_inicio, Fecha_cierre, Duración, Estado, (Utilidades)
                    maybe_add_ciclo("Id_grupo", id_grupo)
                    maybe_add_ciclo("Fecha_inicio", str(fecha_inicio))
                    maybe_add_ciclo("Fecha_cierre", str(fecha_cierre))
                    # la columna puede llamarse "Duración" o "Duracion" - pickear ya se hace al leer columnas
                    maybe_add_ciclo("Duración", duracion)
                    maybe_add_ciclo("Duracion", duracion)
                    maybe_add_ciclo("Estado", estado)
                    maybe_add_ciclo("Utilidades", 0.0)  # Se inicializa en 0

                    if not insert_cols:
                        st.error("Estructura de tabla Ciclo no reconocida para inserción.")
                        return

                    sql = f"INSERT INTO `{ciclo_table}` ({', '.join('`' + c + '`' for c in insert_cols)}) VALUES ({', '.join(placeholders)})"
                    cursor.execute(sql, tuple(params))
                    con.commit()
                    st.success(f"✅ Nuevo Ciclo para el grupo '{grupo_nombre}' registrado correctamente.")
                    st.experimental_rerun()
                except Exception as e:
                    try:
                        con.rollback()
                    except Exception:
                        pass
                    st.error(f"❌ Error al registrar el ciclo. Revise la estructura de la tabla Ciclo. Error: {e}")
                finally:
                    try:
                        if cursor:
                            cursor.close()
                    except Exception:
                        pass
                    try:
                        con.close()
                    except Exception:
                        pass
            else:
                st.error("No se pudo establecer conexión con la base de datos.")


def pagina_grupos_admin():
    """ Contenido principal para la gestión de grupos y ciclos. """
    ref_data = fetch_referencia_data()

    tab_ciclo, tab_grupo = st.tabs(["Registrar Ciclo", "Crear Nuevo Grupo"])

    with tab_ciclo:
        pagina_ciclos_admin(ref_data)

    with tab_grupo:
        # Se necesita que el ciclo exista antes de crear el grupo.
        if ref_data["ciclos"].empty:
            st.warning("⚠️ Por favor, registre un ciclo en la pestaña 'Registrar Ciclo' antes de crear un grupo.")
        else:
            create_new_group(ref_data)

# --- 4. REPORTES GLOBALES ---

def show_reports():
    """Muestra todos los reportes del sistema (sin filtros)."""
    st.header("📊 Reportes Consolidados (Acceso Global)")
    st.markdown("El Administrador puede ver el rendimiento financiero de todos los Distritos y Grupos.")

    # 1. Reporte de Caja Global
    st.subheader("1. Reporte de Caja Global")

    # Intenta leer datos reales de la tabla Caja
    con = obtener_conexion()
    if con:
        try:
            caja_table = None
            for t in ["Caja", "caja", "Cajas"]:
                if table_columns(con, t):
                    caja_table = t
                    break

            if caja_table:
                st.info(f"Mostrando datos de la tabla real: `{caja_table}`")
                df_caja = pd.read_sql(f"SELECT * FROM `{caja_table}` LIMIT 200", con)
                st.dataframe(df_caja, use_container_width=True)
            else:
                st.warning("No se encontró la tabla 'Caja'. Mostrando datos simulados.")
                data_caja = {
                    'Fecha': ['2025-10-01', '2025-10-01', '2025-10-02', '2025-10-02'],
                    'Grupo_ID': [101, 102, 101, 102],
                    'Tipo': ['Aporte', 'Préstamo', 'Multa', 'Aporte'],
                    'Monto': [50.00, -200.00, 5.00, 75.00]
                }
                df_caja = pd.DataFrame(data_caja)
                st.dataframe(df_caja, use_container_width=True)

        except Exception as e:
            st.error(f"Error cargando reportes de caja: {e}")
        finally:
            try:
                con.close()
            except Exception:
                pass
    else:
        st.error("No se pudo conectar a la base de datos para cargar reportes.")

    st.markdown("---")

    # 2. Resumen de Cartera y Mora (Simulación)
    st.subheader("2. Cartera de Préstamos y Mora (Simulación)")

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
    opciones = ["Gestión de Usuarios", "Grupos y Ciclos", "Reportes Consolidados"]
    seleccion = st.sidebar.selectbox("Selecciona una sección", opciones, key="select_seccion_admin")

    st.sidebar.markdown("---")
    # Agregamos la lógica de cerrar sesión simple con key único para evitar duplicados
    if st.sidebar.button("Cerrar Sesión", key="cerrar_sesion_admin"):
        # limpiar estado de sesión de manera segura
        for k in list(st.session_state.keys()):
            # opcional: preservar algunas keys si lo deseas
            if k not in ("_auth",):
                del st.session_state[k]
        st.experimental_rerun()

    # 2. Según la opción seleccionada, mostramos el contenido correspondiente
    if seleccion == "Gestión de Usuarios":
        st.header("👤 Gestión de Usuarios")
        create_user_form(ref_data)

    elif seleccion == "Grupos y Ciclos":
        st.header("🏘️ Gestión de Grupos y Ciclos")
        pagina_grupos_admin()

    elif seleccion == "Reportes Consolidados":
        show_reports()

