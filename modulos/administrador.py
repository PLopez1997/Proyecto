# modulos/administrador.py
import streamlit as st
import pandas as pd
import mysql.connector

# IMPORT: ajusta según dónde esté app.py.
# Si ejecutas streamlit run app.py desde la raíz del proyecto, usa:
from modulos.config.conexion import obtener_conexion
# Si ejecutas desde dentro de modulos (raro), cambia a:
# from .config.conexion import obtener_conexion

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
            "distritos": pd.DataFrame({"Id_distrito":[1], "Label":["Distrito 1"]}),
            "ciclos": pd.DataFrame({"Id_ciclo":[1], "Label":["Ciclo 1"]}),
            "grupos": pd.DataFrame({"Id_grupo":[1], "Label":["Grupo 1"]})
        }

    try:
        # Intentaremos cargar tablas con nombres diversos y columnas alternativas
        # Distritos
        distrito_table = None
        for t in ["Distrito", "distrito", "Distritos", "distritos"]:
            if table_columns(conn, t):
                distrito_table = t
                break

        # Ciclos
        ciclo_table = None
        for t in ["Ciclo", "ciclo", "Ciclos", "ciclos"]:
            if table_columns(conn, t):
                ciclo_table = t
                break

        # Grupos
        grupo_table = None
        for t in ["Grupo", "grupo", "Grupos", "grupos"]:
            if table_columns(conn, t):
                grupo_table = t
                break

        ref = {}

        # Distritos: preferimos Id + alguna etiqueta
        if distrito_table:
            cols = table_columns(conn, distrito_table)
            id_col = pick_column(cols, ["Id_distrito", "id_distrito", "Id_distr", "Id"])
            label_col = pick_column(cols, ["Nombre", "nombre", "Descripcion", "descripcion", "Label", "label"])
            if id_col and label_col:
                ref["distritos"] = pd.read_sql(f"SELECT `{id_col}` AS Id_distrito, `{label_col}` AS Nombre FROM `{distrito_table}`", conn)
            elif id_col:
                ref["distritos"] = pd.read_sql(f"SELECT `{id_col}` AS Id_distrito FROM `{distrito_table}`", conn)
                ref["distritos"]["Nombre"] = ref["distritos"]["Id_distrito"].astype(str)
            else:
                ref["distritos"] = pd.DataFrame({"Id_distrito":[],"Nombre":[]})
        else:
            ref["distritos"] = pd.DataFrame({"Id_distrito":[],"Nombre":[]})

        # Ciclos
        if ciclo_table:
            cols = table_columns(conn, ciclo_table)
            id_col = pick_column(cols, ["Id_ciclo", "id_ciclo", "Id"])
            label_col = pick_column(cols, ["Nombre", "nombre", "Descripcion", "descripcion", "Periodo", "Ciclo"])
            if id_col and label_col:
                ref["ciclos"] = pd.read_sql(f"SELECT `{id_col}` AS Id_ciclo, `{label_col}` AS Nombre FROM `{ciclo_table}`", conn)
            elif id_col:
                ref["ciclos"] = pd.read_sql(f"SELECT `{id_col}` AS Id_ciclo FROM `{ciclo_table}`", conn)
                ref["ciclos"]["Nombre"] = "Ciclo " + ref["ciclos"]["Id_ciclo"].astype(str)
            else:
                ref["ciclos"] = pd.DataFrame({"Id_ciclo":[],"Nombre":[]})
        else:
            ref["ciclos"] = pd.DataFrame({"Id_ciclo":[],"Nombre":[]})

        # Grupos
        if grupo_table:
            cols = table_columns(conn, grupo_table)
            id_col = pick_column(cols, ["Id_grupo", "id_grupo", "Id_cliente", "Id"])
            label_col = pick_column(cols, ["Nombre", "nombre", "Descripcion", "descripcion", "Grupo"])
            if id_col and label_col:
                ref["grupos"] = pd.read_sql(f"SELECT `{id_col}` AS Id_grupo, `{label_col}` AS Nombre FROM `{grupo_table}`", conn)
            elif id_col:
                ref["grupos"] = pd.read_sql(f"SELECT `{id_col}` AS Id_grupo FROM `{grupo_table}`", conn)
                ref["grupos"]["Nombre"] = ref["grupos"]["Id_grupo"].astype(str)
            else:
                ref["grupos"] = pd.DataFrame({"Id_grupo":[],"Nombre":[]})
        else:
            ref["grupos"] = pd.DataFrame({"Id_grupo":[],"Nombre":[]})

        return ref

    except Exception as e:
        st.warning(f"No se pudieron cargar datos de referencia. Error: {e}")
        return {
            "distritos": pd.DataFrame({"Id_distrito":[],"Nombre":[]}),
            "ciclos": pd.DataFrame({"Id_ciclo":[],"Nombre":[]}),
            "grupos": pd.DataFrame({"Id_grupo":[],"Nombre":[]})
        }
    finally:
        conn.close()

# -----------------------
# CREAR USUARIO (insert dinámico según columnas reales)
# -----------------------
def create_user_form(ref_data):
    st.subheader("➕ Registrar Nuevo Usuario")

    # Mapas
    distritos = list(ref_data["distritos"]["Nombre"]) if not ref_data["distritos"].empty else []
    grupos = list(ref_data["grupos"]["Nombre"]) if not ref_data["grupos"].empty else []

    with st.form("form_new_user"):
        new_username = st.text_input("Nombre de Usuario (Login)")
        new_password = st.text_input("Contraseña", type="password")
        new_rol = st.selectbox("Rol del Usuario", ['administrador','promotora','junta directiva','miembro'])

        id_ref = None
        id_grupo = None
        id_distrito = None

        if new_rol == "promotora":
            if distritos:
                distrito_sel = st.selectbox("Asignar Distrito", distritos)
                # buscar id por nombre
                id_ref = ref_data["distritos"].loc[ref_data["distritos"]["Nombre"]==distrito_sel, "Id_distrito"].iloc[0]
            else:
                st.info("No hay distritos cargados en la BD.")

        elif new_rol in ("junta directiva","miembro"):
            if grupos:
                grupo_sel = st.selectbox("Asignar Grupo", grupos)
                id_grupo = ref_data["grupos"].loc[ref_data["grupos"]["Nombre"]==grupo_sel, "Id_grupo"].iloc[0]
            else:
                st.info("No hay grupos cargados en la BD.")

        submitted = st.form_submit_button("Crear Usuario")
        if submitted:
            if not new_username or not new_password:
                st.error("Usuario y contraseña obligatorios.")
                return

            con = obtener_conexion()
            if not con:
                st.error("No se pudo conectar a la base de datos.")
                return

            try:
                cols = table_columns(con, "Login") or table_columns(con, "login") or table_columns(con, "Usuario") or table_columns(con, "usuario")
                # Detectar columnas posibles
                user_col = pick_column(cols, ["Usuario","usuario","user","User"])
                pass_col = pick_column(cols, ["Contraseña","Contrasena","Contrasena_Hash","Password","password"])
                rol_col = pick_column(cols, ["Rol","rol","Role"])
                id_ref_col = pick_column(cols, ["Id_referencia","Id_referencia","id_referencia"])
                id_grupo_col = pick_column(cols, ["Id_grupo","id_grupo"])
                id_distr_col = pick_column(cols, ["Id_distrito","id_distrito"])

                cursor = con.cursor()

                # Si la tabla usa hash o no: aquí guardamos la contraseña tal cual si la columna se llama 'Contraseña'
                # RECOMENDACIÓN: cambiar a hashed en BD; aquí hacemos hashing SHA256 si la columna sugiere 'Contrasena_Hash'
                to_store_pass = new_password
                if pass_col and "hash" in (pass_col.lower() or ""):
                    import hashlib
                    to_store_pass = hashlib.sha256(new_password.encode()).hexdigest()

                # Construir INSERT dinámico
                insert_cols = []
                insert_vals = []
                params = []

                if user_col:
                    insert_cols.append(user_col); insert_vals.append("%s"); params.append(new_username)
                if pass_col:
                    insert_cols.append(pass_col); insert_vals.append("%s"); params.append(to_store_pass)
                if rol_col:
                    insert_cols.append(rol_col); insert_vals.append("%s"); params.append(new_rol)
                # referencia/grupo/distrito si existen
                if id_ref_col:
                    insert_cols.append(id_ref_col); insert_vals.append("%s"); params.append(id_ref)
                if id_grupo_col:
                    insert_cols.append(id_grupo_col); insert_vals.append("%s"); params.append(id_grupo)
                if id_distr_col:
                    insert_cols.append(id_distr_col); insert_vals.append("%s"); params.append(id_distrito)

                if not insert_cols:
                    st.error("No se pudo detectar columnas de la tabla de usuarios en la BD.")
                    return

                sql = f"INSERT INTO Login ({', '.join('`'+c+'`' for c in insert_cols)}) VALUES ({', '.join(insert_vals)})"
                cursor.execute(sql, tuple(params))
                con.commit()
                st.success("Usuario creado correctamente en la BD.")
                st.rerun()
            except Exception as e:
                con.rollback()
                st.error(f"Error al insertar usuario: {e}")
            finally:
                cursor.close()
                con.close()

# -----------------------
# GESTIÓN DE GRUPOS (usando la tabla real 'grupos' o 'Grupo')
# -----------------------
def create_new_group(ref_data):
    st.subheader("➕ Crear Nuevo Grupo")
    grupos_df = ref_data["grupos"]
    ciclos_df = ref_data["ciclos"]

    with st.form("form_nuevo_grupo"):
        nombre = st.text_input("Nombre del Grupo")
        fecha_inicio = st.date_input("Fecha inicio")
        ciclo_sel = None
        if not ciclos_df.empty:
            ciclo_sel = st.selectbox("Ciclo", ciclos_df["Nombre"])
            id_ciclo = int(ciclos_df.loc[ciclos_df["Nombre"]==ciclo_sel, "Id_ciclo"].iloc[0])
        else:
            id_ciclo = None

        distrito_sel = None
        if not ref_data["distritos"].empty:
            distrito_sel = st.selectbox("Distrito", ref_data["distritos"]["Nombre"])
            id_distrito = int(ref_data["distritos"].loc[ref_data["distritos"]["Nombre"]==distrito_sel, "Id_distrito"].iloc[0])
        else:
            id_distrito = None

        tasa = st.number_input("Tasa de interés", min_value=0.0, value=0.1)
        tipo_multa = st.text_input("Tipo de multa", value="")
        regla = st.text_area("Regla interna", value="")

        submitted = st.form_submit_button("Crear Grupo")
        if submitted:
            if not nombre:
                st.error("Nombre obligatorio")
                return

            con = obtener_conexion()
            if not con:
                st.error("No hay conexión a BD")
                return
            try:
                # Detectar nombre real de tabla grupos
                grupo_table = None
                for t in ["grupos","Grupo","GrupoS","GRUPOS"]:
                    if table_columns(con, t):
                        grupo_table = t
                        break
                if not grupo_table:
                    st.error("No se encontró tabla de grupos en la BD.")
                    return

                cols = table_columns(con, grupo_table)
                # columnas esperadas: Nombre, Fecha_inicio, Id_ciclo, Tasa_interes, Tipo_multa, Regla_interna, Id_distrito
                insert_cols = []
                params = []
                placeholders = []

                def maybe_add(colname, value):
                    if colname in cols:
                        insert_cols.append(colname)
                        placeholders.append("%s")
                        params.append(value)

                maybe_add("Nombre", nombre)
                maybe_add("Fecha_inicio", str(fecha_inicio))
                maybe_add("Id_ciclo", id_ciclo)
                maybe_add("Tasa_interes", tasa)
                maybe_add("Tipo_multa", tipo_multa)
                maybe_add("Regla_interna", regla)
                maybe_add("Id_distrito", id_distrito)

                if not insert_cols:
                    st.error("Estructura de tabla grupos no reconocida.")
                    return

                sql = f"INSERT INTO `{grupo_table}` ({', '.join('`'+c+'`' for c in insert_cols)}) VALUES ({', '.join(placeholders)})"
                cur = con.cursor()
                cur.execute(sql, tuple(params))
                con.commit()
                st.success("Grupo creado correctamente en la BD.")
                st.rerun()
            except Exception as e:
                con.rollback()
                st.error(f"Error al crear grupo: {e}")
            finally:
                cur.close()
                con.close()

# -----------------------
# REPORTES: leer tabla caja si existe
# -----------------------
def show_reports():
    st.header("📊 Reportes Consolidados")
    con = obtener_conexion()
    if not con:
        st.error("No hay conexión.")
        return
    try:
        # Detectar tabla caja (varios nombres posibles)
        caja_table = None
        for t in ["Caja","caja","Cajas"]:
            if table_columns(con, t):
                caja_table = t
                break
        if not caja_table:
            st.info("No se encontró tabla Caja en la BD. Mostrar datos simulados.")
            st.dataframe(pd.DataFrame({"msg":["Tabla Caja no encontrada"]}))
            return

        cols = table_columns(con, caja_table)
        # Pedimos algunas columnas comunes para mostrar: Fecha, Id_grupo, Ingresos, Egresos, Saldo actual
        want_cols = ["Fecha","fecha","Id_grupo","Id_grupo","Ingresos","Egresos","Saldo actual","Saldo_actual","Saldo"]
        to_select = []
        for c in want_cols:
            if c in cols and c not in to_select:
                to_select.append(c)

        if not to_select:
            # si no hay columnas conocidas, seleccionamos todas
            df = pd.read_sql(f"SELECT * FROM `{caja_table}` LIMIT 200", con)
        else:
            # formatear columnas entre backticks
            sel = ", ".join(f"`{c}`" for c in to_select)
            df = pd.read_sql(f"SELECT {sel} FROM `{caja_table}` LIMIT 200", con)

        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error cargando reportes: {e}")
    finally:
        con.close()


# -----------------------
# Página principal del admin
# -----------------------
def administrador_page():
    ref_data = fetch_referencia_data()
    st.title("Panel de Administración")
    opciones = ["Gestión de Usuarios", "Grupos y Distritos", "Reportes Consolidados"]
    seleccion = st.sidebar.selectbox("Sección", opciones)
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar sesión"):
        for k in ["sesion_iniciada","Usuario","tipo_usuario","rol"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

    if seleccion == "Gestión de Usuarios":
        create_user_form(ref_data)
    elif seleccion == "Grupos y Distritos":
        create_new_group(ref_data)
    elif seleccion == "Reportes Consolidados":
        show_reports()
