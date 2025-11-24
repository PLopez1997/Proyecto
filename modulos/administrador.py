import streamlit as st
import pandas as pd
import hashlib
from modulos.config.conexion import obtener_conexion

# -----------------------
# Helpers para inspección
# -----------------------
def table_columns(conn, table_name):
    try:
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        cols = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return cols
    except Exception:
        return []


def pick_column(cols, candidates):
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
            "distritos": pd.DataFrame({"Id_distrito":[],"Nombre":[]}),
            "ciclos": pd.DataFrame({"Id_ciclo":[],"Nombre":[]}),
            "grupos": pd.DataFrame({"Id_grupo":[],"Nombre":[]})
        }

    try:
        # Detectar nombres reales de tablas
        distrito_table = next((t for t in ["Distrito","distrito","Distritos","distritos"] if table_columns(conn, t)), None)
        ciclo_table = next((t for t in ["Ciclo","ciclo","Ciclos","ciclos"] if table_columns(conn, t)), None)
        grupo_table = next((t for t in ["Grupo","grupo","Grupos","grupos"] if table_columns(conn, t)), None)

        ref = {}

        # Distritos
        if distrito_table:
            cols = table_columns(conn, distrito_table)
            id_col = pick_column(cols, ["Id_distrito","id_distrito","Id_distr","Id"])
            label_col = pick_column(cols, ["Nombre","nombre","Descripcion","descripcion","Label","label","Nombre_distrito"]) 
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
            id_col = pick_column(cols, ["Id_ciclo","id_ciclo","Id"]) 
            label_col = pick_column(cols, ["Nombre","nombre","Descripcion","descripcion","Periodo","Ciclo","Fecha_inicio"]) 
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
            id_col = pick_column(cols, ["Id_grupo","id_grupo","Id_cliente","Id","Id_cliente"]) 
            label_col = pick_column(cols, ["Nombre","nombre","Descripcion","descripcion","Grupo"]) 
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
        return {"distritos":pd.DataFrame({"Id_distrito":[],"Nombre":[]}),"ciclos":pd.DataFrame({"Id_ciclo":[],"Nombre":[]}),"grupos":pd.DataFrame({"Id_grupo":[],"Nombre":[]})}
    finally:
        conn.close()

# -----------------------
# CREAR USUARIO (textbox para grupo y textbox para promotora->distrito)
# -----------------------

def create_user_form(ref_data):
    st.subheader("➕ Registrar Nuevo Usuario")

    grupos_list = list(ref_data["grupos"]["Nombre"]) if not ref_data["grupos"].empty else []
    distritos_list = list(ref_data["distritos"]["Nombre"]) if not ref_data["distritos"].empty else []

    with st.form("form_new_user"):
        new_username = st.text_input("Nombre de Usuario (Login)")
        new_password = st.text_input("Contraseña", type="password")
        new_rol = st.selectbox("Rol del Usuario", ['administrador','promotora','junta directiva','miembro'])

        asignar_grupo_text = None
        asignar_distrito_text = None

        if new_rol in ("junta directiva","miembro"):
            st.info("Escribe el **Nombre exacto** del grupo tal como aparece en la tabla 'grupos' (Capital inicial).")
            asignar_grupo_text = st.text_input("Nombre del Grupo (texto exacto)")

        if new_rol == 'promotora':
            st.info("Escribe el **Nombre exacto** del distrito para asignar la promotora (Capital inicial).")
            asignar_distrito_text = st.text_input("Nombre del Distrito (texto exacto)")

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
                # Detectar tabla de login
                login_table = next((t for t in ["Login","login","Usuario","usuario"] if table_columns(con, t)), None)
                if not login_table:
                    st.error("No se encontró tabla de Login/Usuario en la BD.")
                    return

                cols = table_columns(con, login_table)
                user_col = pick_column(cols, ["Usuario","usuario","user","User"])
                pass_col = pick_column(cols, ["Contraseña","Contrasena","Contrasena_Hash","Password","password"])
                rol_col = pick_column(cols, ["Rol","rol","Role"])
                id_ref_col = pick_column(cols, ["Id_referencia","Id_referencia","id_referencia"]) 
                id_grupo_col = pick_column(cols, ["Id_grupo","id_grupo"])
                id_distr_col = pick_column(cols, ["Id_distrito","id_distrito"]) 

                # Hash si la columna sugiere hash
                to_store_pass = new_password
                if pass_col and "hash" in (pass_col.lower() or ""):
                    to_store_pass = hashlib.sha256(new_password.encode()).hexdigest()

                # buscar id_grupo si el admin escribió nombre
                id_grupo_val = None
                if asignar_grupo_text:
                    # buscar en tabla grupos
                    grupo_table = next((t for t in ["grupos","Grupo","GrupoS","GRUPOS"] if table_columns(con, t)), None)
                    if grupo_table:
                        # buscar columna nombre
                        gcols = table_columns(con, grupo_table)
                        gname_col = pick_column(gcols, ["Nombre","nombre","Grupo","Descripcion","descripcion"]) 
                        gid_col = pick_column(gcols, ["Id_grupo","id_grupo","Id_cliente","Id"]) 
                        if gname_col and gid_col:
                            cur = con.cursor()
                            cur.execute(f"SELECT `{gid_col}` FROM `{grupo_table}` WHERE `{gname_col}` = %s LIMIT 1", (asignar_grupo_text,))
                            r = cur.fetchone()
                            cur.close()
                            if r:
                                id_grupo_val = r[0]
                            else:
                                st.error("No se encontró un grupo con ese nombre exacto.")
                                return
                        else:
                            st.error("Estructura de tabla grupos no reconocida para búsqueda por nombre.")
                            return
                    else:
                        st.error("No se encontró tabla de grupos en la BD.")
                        return

                # buscar id_distrito si el admin escribió nombre
                id_distr_val = None
                if asignar_distrito_text:
                    distrito_table = next((t for t in ["Distrito","distrito","Distritos","distritos"] if table_columns(con, t)), None)
                    if distrito_table:
                        dcols = table_columns(con, distrito_table)
                        dname_col = pick_column(dcols, ["Nombre","nombre","Descripcion","descripcion","Nombre_distrito"]) 
                        did_col = pick_column(dcols, ["Id_distrito","id_distrito","Id"]) 
                        if dname_col and did_col:
                            cur = con.cursor()
                            cur.execute(f"SELECT `{did_col}` FROM `{distrito_table}` WHERE `{dname_col}` = %s LIMIT 1", (asignar_distrito_text,))
                            r = cur.fetchone()
                            cur.close()
                            if r:
                                id_distr_val = r[0]
                            else:
                                st.error("No se encontró un distrito con ese nombre exacto.")
                                return
                        else:
                            st.error("Estructura de tabla distrito no reconocida para búsqueda por nombre.")
                            return
                    else:
                        st.error("No se encontró tabla de distrito en la BD.")
                        return

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
                if id_ref_col:
                    insert_cols.append(id_ref_col); insert_vals.append("%s"); params.append(None)
                if id_grupo_col and id_grupo_val is not None:
                    insert_cols.append(id_grupo_col); insert_vals.append("%s"); params.append(id_grupo_val)
                if id_distr_col and id_distr_val is not None:
                    insert_cols.append(id_distr_col); insert_vals.append("%s"); params.append(id_distr_val)

                sql = f"INSERT INTO `{login_table}` ({', '.join('`'+c+'`' for c in insert_cols)}) VALUES ({', '.join(insert_vals)})"
                cur = con.cursor()
                cur.execute(sql, tuple(params))
                con.commit()
                st.success("Usuario creado correctamente en la BD.")
                cur.close()
                st.rerun()

            except Exception as e:
                con.rollback()
                st.error(f"Error al insertar usuario: {e}")
            finally:
                con.close()

# -----------------------
# CREAR CICLO (vinculado a un grupo)
# -----------------------

def create_cycle_form(ref_data):
    st.subheader("➕ Crear Nuevo Ciclo (vinculado a un Grupo)")

    grupos_df = ref_data["grupos"]
    if grupos_df.empty:
        st.error("No hay grupos disponibles. Crea primero un grupo en la sección correspondiente.")
        return

    with st.form("form_nuevo_ciclo"):
        grupo_sel = st.selectbox("Selecciona Grupo para el Ciclo", grupos_df["Nombre"].tolist())
        fecha_inicio = st.date_input("Fecha Inicio")
        fecha_cierre = st.date_input("Fecha Cierre")
        utilidades = st.number_input("Utilidades estimadas", min_value=0.0, value=0.0)
        estado = st.selectbox("Estado", ["activo","inactivo","planificado"]) 
        duracion = st.number_input("Duración (días)", min_value=1, value=30)

        submitted = st.form_submit_button("Crear Ciclo")
        if submitted:
            id_grupo = int(grupos_df.loc[grupos_df["Nombre"]==grupo_sel, "Id_grupo"].iloc[0])
            con = obtener_conexion()
            if not con:
                st.error("No hay conexión a BD")
                return
            try:
                ciclo_table = next((t for t in ["Ciclo","ciclo","Ciclos","ciclos"] if table_columns(con, t)), None)
                if not ciclo_table:
                    st.error("No se encontró la tabla Ciclo en la BD.")
                    return

                cols = table_columns(con, ciclo_table)
                insert_cols = []
                params = []
                placeholders = []

                def maybe_add(colname, value):
                    if colname in cols:
                        insert_cols.append(colname)
                        placeholders.append("%s")
                        params.append(value)

                maybe_add("Id_grupo", id_grupo)
                maybe_add("Fecha_inicio", str(fecha_inicio))
                maybe_add("Fecha_cierre", str(fecha_cierre))
                maybe_add("Utilidades", utilidades)
                maybe_add("Estado", estado)
                # aceptar variantes con y sin tilde
                maybe_add("Duración", duracion)
                maybe_add("Duracion", duracion)

                if not insert_cols:
                    st.error("La tabla Ciclo no tiene columnas reconocibles para insertar.")
                    return

                sql = f"INSERT INTO `{ciclo_table}` ({', '.join('`'+c+'`' for c in insert_cols)}) VALUES ({', '.join(placeholders)})"
                cur = con.cursor()
                cur.execute(sql, tuple(params))
                con.commit()
                st.success("Ciclo creado correctamente.")
                cur.close()
                st.rerun()
            except Exception as e:
                con.rollback()
                st.error(f"Error al crear ciclo: {e}")
            finally:
                con.close()

# -----------------------
# GESTIÓN DE GRUPOS (creación vinculada a tabla real)
# -----------------------

def create_new_group(ref_data):
    st.subheader("➕ Crear Nuevo Grupo")
    grupos_df = ref_data["grupos"]
    ciclos_df = ref_data["ciclos"]

    with st.form("form_nuevo_grupo"):
        nombre = st.text_input("Nombre del Grupo")
        fecha_inicio = st.date_input("Fecha inicio")
        id_ciclo = None
        if not ciclos_df.empty:
            ciclo_sel = st.selectbox("Ciclo (opcional)", ciclos_df["Nombre"].tolist())
            id_ciclo = int(ciclos_df.loc[ciclos_df["Nombre"]==ciclo_sel, "Id_ciclo"].iloc[0])
        else:
            id_ciclo = None

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
                grupo_table = next((t for t in ["grupos","Grupo","GrupoS","GRUPOS"] if table_columns(con, t)), None)
                if not grupo_table:
                    st.error("No se encontró tabla de grupos en la BD.")
                    return

                cols = table_columns(con, grupo_table)
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

                if not insert_cols:
                    st.error("Estructura de tabla grupos no reconocida.")
                    return

                sql = f"INSERT INTO `{grupo_table}` ({', '.join('`'+c+'`' for c in insert_cols)}) VALUES ({', '.join(placeholders)})"
                cur = con.cursor()
                cur.execute(sql, tuple(params))
                con.commit()
                st.success("Grupo creado correctamente en la BD.")
                cur.close()
                st.rerun()
            except Exception as e:
                con.rollback()
                st.error(f"Error al crear grupo: {e}")
            finally:
                con.close()

# -----------------------
# REPORTES: leer tabla caja si existe
# -----------------------

def show_reports():
    st.header("📊 Reportes de los Grupos y Caja Común")
    
    conn = obtener_conexion()
    if not conn:
        st.error("No hay conexión.")
        return

    try:
        grupo_id = st.session_state.get('grupo_id')
        
        # --- PARTE A: DATOS GLOBALES (LA CAJA COMÚN) ---
        # Calculamos el saldo de TODA la organización
        query_global = "SELECT Tipo_transaccion, Monto FROM Caja"
        df_global = pd.read_sql(query_global, conn)
        
        saldo_global = 0.0
        if not df_global.empty:
            ingresos_totales = df_global[df_global['Tipo_transaccion'] == 'Ingreso']['Monto'].sum()
            egresos_totales = df_global[df_global['Tipo_transaccion'] == 'Egreso']['Monto'].sum()
            saldo_global = ingresos_totales - egresos_totales
        
        # --- PARTE B: DATOS LOCALES (SOLO DE ESTE GRUPO) ---
        # Para el historial, solo mostramos lo que ESTE grupo ha aportado/gastado
        query_local = """
            SELECT Fecha, Detalle, Tipo_transaccion, Monto 
            FROM Caja 
            WHERE Id_grupo = %s 
            ORDER BY Fecha DESC
        """
        df_local = pd.read_sql(query_local, conn, params=(grupo_id,))

        # --- VISUALIZACIÓN ---
        
        # 1. KPI PRINCIPAL (GLOBAL)
        st.info("ℹ️ Nota: El saldo mostrado pertenece a la Caja Común de todos los grupos.")
        st.metric("💰 SALDO DISPONIBLE (Fondo Común)", f"${saldo_global:,.2f}")
        
        st.markdown("---")

        if not df_local.empty:
            st.subheader("📜 Historial de Movimientos de MI GRUPO")
            
            # Métricas locales (solo informativas)
            local_ing = df_local[df_local['Tipo_transaccion'] == 'Ingreso']['Monto'].sum()
            local_egr = df_local[df_local['Tipo_transaccion'] == 'Egreso']['Monto'].sum()
            
            c1, c2 = st.columns(2)
            c1.metric("Aportes de este Grupo", f"${local_ing:,.2f}")
            c2.metric("Retiros de este Grupo", f"${local_egr:,.2f}")

            # Formato de fecha
            if 'Fecha' in df_local.columns:
                df_local['Fecha'] = pd.to_datetime(df_local['Fecha']).dt.date
            
            # Tabla
            st.dataframe(df_local, use_container_width=True)

            # Gráfico
            st.caption("Tendencia de aportes y retiros de este grupo")
            st.bar_chart(df_local, x="Fecha", y="Monto", color="Tipo_transaccion")
            
        else:
            st.info("Este grupo aún no ha registrado movimientos en la caja común.")

    except Exception as e:
        st.error(f"Error cargando reportes: {e}")
    finally:
        conn.close()

# -----------------------
# Página principal del admin
# -----------------------

def administrador_page():
    ref_data = fetch_referencia_data()
    st.title("Panel de Administración")
    opciones = ["Gestión de Usuarios", "Grupos y Distritos", "Ciclos", "Reportes Consolidados"]
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
    elif seleccion == "Ciclos":
        create_cycle_form(ref_data)
    elif seleccion == "Reportes Consolidados":
        show_reports()


