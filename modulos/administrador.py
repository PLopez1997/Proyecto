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

def create_user_form():
    st.subheader("➕ Registrar Nuevo Usuario del Sistema")
    st.info("Aquí creas las credenciales (Usuario/Clave) y las vinculas a una persona real.")

    # 1. CARGAMOS DATOS REALES DE LA BD (Para los selectores)
    conn = obtener_conexion()
    if not conn:
        st.error("Sin conexión a BD")
        return

    try:
        # Cargar Miembros (para vincular usuarios normales y directiva)
        # Traemos también el nombre del grupo para que sea fácil identificar
        query_miembros = """
            SELECT m.Id_miembro, m.Nombre, m.`DUI/Identificación` as DUI, m.Id_grupo, g.Nombre as NombreGrupo
            FROM Miembro m
            JOIN Grupo g ON m.Id_grupo = g.Id_grupo
        """
        df_miembros = pd.read_sql(query_miembros, conn)

        # Cargar Distritos (para promotoras)
        # Asumiendo que tienes tabla Distrito
        try:
            df_distritos = pd.read_sql("SELECT Id_distrito, Nombre FROM Distrito", conn)
        except:
            df_distritos = pd.DataFrame() # Por si no existe aún la tabla

    finally:
        conn.close()

    # 2. FORMULARIO DE REGISTRO
    with st.form("form_new_user"):
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            new_username = st.text_input("Nombre de Usuario (Login)")
        with col_u2:
            new_password = st.text_input("Contraseña", type="password")
        
        # Seleccionamos el rol
        roles_disponibles = ['miembro', 'junta directiva', 'promotora', 'administrador']
        new_rol = st.selectbox("Rol del Usuario", roles_disponibles)

        # VARIABLES PARA GUARDAR
        id_miembro_sel = None
        id_grupo_sel = None
        id_distrito_sel = None

        # --- LÓGICA DINÁMICA SEGÚN ROL ---
        
        # CASO A: SI ES MIEMBRO O DIRECTIVA -> VINCULAR A UN MIEMBRO EXISTENTE
        if new_rol in ("junta directiva", "miembro"):
            if not df_miembros.empty:
                st.markdown("---")
                st.write(f"👤 Vincular a un Miembro existente:")
                
                # Creamos un diccionario para el selector: {Id_miembro: "Nombre - Grupo"}
                lista_miembros = {
                    row['Id_miembro']: f"{row['Nombre']} (DUI: {row['DUI']}) - {row['NombreGrupo']}"
                    for index, row in df_miembros.iterrows()
                }
                
                id_seleccionado = st.selectbox(
                    "Seleccione la persona:", 
                    options=lista_miembros.keys(),
                    format_func=lambda x: lista_miembros[x]
                )
                
                # Guardamos los IDs automáticamente
                id_miembro_sel = id_seleccionado
                # Buscamos el ID Grupo correspondiente a ese miembro
                id_grupo_sel = df_miembros[df_miembros['Id_miembro'] == id_seleccionado]['Id_grupo'].values[0]
                
                st.caption(f"✅ Se asignará automáticamente al Grupo ID: {id_grupo_sel}")
            else:
                st.error("No hay miembros registrados en la tabla 'Miembro'. Registre miembros primero.")
                st.form_submit_button("Detener")
                return

        # CASO B: SI ES PROMOTORA -> VINCULAR A DISTRITO
        elif new_rol == 'promotora':
            if not df_distritos.empty:
                st.markdown("---")
                lista_distritos = {row['Id_distrito']: row['Nombre'] for i, row in df_distritos.iterrows()}
                
                id_dist_sel = st.selectbox(
                    "Asignar Distrito:",
                    options=lista_distritos.keys(),
                    format_func=lambda x: lista_distritos[x]
                )
                id_distrito_sel = id_dist_sel
            else:
                st.warning("No se encontraron distritos registrados.")

        # 3. BOTÓN DE GUARDADO
        st.markdown("---")
        submitted = st.form_submit_button("Crear Usuario")

        if submitted:
            if not new_username or not new_password:
                st.error("Usuario y contraseña son obligatorios.")
                return

            guardar_usuario_bd(new_username, new_password, new_rol, id_miembro_sel, id_grupo_sel, id_distrito_sel)

# --- FUNCIÓN SQL PARA GUARDAR ---
def guardar_usuario_bd(usuario, password, rol, id_miembro, id_grupo, id_distrito):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Verificamos si el usuario ya existe
            cursor.execute("SELECT Usuario FROM Login WHERE Usuario = %s", (usuario,))
            if cursor.fetchone():
                st.error(f"El usuario '{usuario}' ya existe. Elija otro.")
                return

            # Insertamos con todos los datos vinculados
            # Asegúrate que tu tabla se llama 'Login' o 'Usuario'
            query = """
                INSERT INTO Login (Usuario, Contraseña, Rol, Id_miembro, Id_grupo, Id_distrito) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            # Pasamos None si no aplica (MySQL lo convierte a NULL)
            valores = (usuario, password, rol, id_miembro, id_grupo, id_distrito)
            
            cursor.execute(query, valores)
            conn.commit()
            
            st.success(f"✅ Usuario '{usuario}' creado exitosamente.")
            if id_miembro:
                st.info("🔗 Vinculado correctamente al perfil del miembro.")
                
        except Exception as e:
            st.error(f"Error al guardar usuario: {e}")
        finally:
            conn.close()

# -----------------------
# CREAR CICLO (ya SIN vínculo a grupo)
# ------------------------------------

def create_cycle_form(ref_data):
    st.subheader("➕ Crear Nuevo Ciclo")

    with st.form("form_nuevo_ciclo"):

        fecha_inicio = st.date_input("Fecha Inicio")
        fecha_cierre = st.date_input("Fecha Cierre")
        utilidades = st.number_input("Utilidades estimadas", min_value=0.0, value=0.0)
        estado = st.selectbox("Estado", ["activo","inactivo","planificado"]) 
        duracion = st.number_input("Duración (días)", min_value=1, value=30)

        submitted = st.form_submit_button("Crear Ciclo")

        if submitted:

            con = obtener_conexion()
            if not con:
                st.error("No hay conexión a BD")
                return

            try:
                # Detectar tabla ciclo en la BD
                ciclo_table = next(
                    (t for t in ["Ciclo", "ciclo", "Ciclos", "ciclos"] if table_columns(con, t)),
                    None
                )
                if not ciclo_table:
                    st.error("No se encontró la tabla Ciclo en la BD.")
                    return

                cols = table_columns(con, ciclo_table)

                insert_cols = []
                placeholders = []
                params = []

                # Función para agregar columnas solo si existen
                def maybe_add(colname, value):
                    if colname in cols:
                        insert_cols.append(colname)
                        placeholders.append("%s")
                        params.append(value)

                # Campos reconocidos en la tabla Ciclo
                maybe_add("Fecha_inicio", str(fecha_inicio))
                maybe_add("Fecha_cierre", str(fecha_cierre))
                maybe_add("Utilidades", utilidades)
                maybe_add("Estado", estado)
                maybe_add("Duracion", duracion)
                maybe_add("Duración", duracion)  # si existe con tilde

                if not insert_cols:
                    st.error("La tabla Ciclo no tiene columnas reconocibles para insertar.")
                    return

                sql = (
                    f"INSERT INTO `{ciclo_table}` "
                    f"({', '.join('`' + c + '`' for c in insert_cols)}) "
                    f"VALUES ({', '.join(placeholders)})"
                )

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

def show_admin_reports():
    st.header("📊 Tablero Financiero Maestro (Admin)")
    
    conn = obtener_conexion()
    if not conn:
        st.error("Error de conexión.")
        return

    try:
        # 1. OBTENER LISTA DE GRUPOS PARA EL FILTRO
        grupos_dict = {0: "👁️ Ver Todos los Grupos"} # Opción por defecto
        try:
            # Asumo que tu tabla se llama 'Grupo' y tiene 'Id_grupo' y 'Nombre'
            # Si se llama 'Grupos', ajusta el FROM.
            cursor = conn.cursor()
            cursor.execute("SELECT Id_grupo, Nombre FROM Grupo") 
            for id_g, nom in cursor.fetchall():
                grupos_dict[id_g] = f"Grupo {id_g}: {nom}"
        except Exception as e:
            st.warning(f"No se pudo cargar la lista de grupos (¿Tabla 'Grupo' existe?): {e}")

        # --- FILTRO SUPERIOR ---
        col_filtro, col_vacio = st.columns([1, 2])
        with col_filtro:
            grupo_seleccionado = st.selectbox(
                "Filtrar Movimientos:", 
                options=grupos_dict.keys(), 
                format_func=lambda x: grupos_dict[x]
            )

        st.markdown("---")

        # 2. LÓGICA DE CONSULTA (Dinámica según el filtro)
        # Usamos LEFT JOIN para traer el nombre del grupo junto con el movimiento
        if grupo_seleccionado == 0:
            # CASO A: VER TODO
            query = """
                SELECT c.Fecha, g.Nombre as Grupo, c.Detalle, c.Tipo_transaccion, c.Monto 
                FROM Caja c
                LEFT JOIN Grupo g ON c.Id_grupo = g.Id_grupo
                ORDER BY c.Fecha DESC
            """
            params = ()
        else:
            # CASO B: FILTRAR UN GRUPO
            query = """
                SELECT c.Fecha, g.Nombre as Grupo, c.Detalle, c.Tipo_transaccion, c.Monto 
                FROM Caja c
                LEFT JOIN Grupo g ON c.Id_grupo = g.Id_grupo
                WHERE c.Id_grupo = %s
                ORDER BY c.Fecha DESC
            """
            params = (grupo_seleccionado,)

        df = pd.read_sql(query, conn, params=params)

        # 3. CÁLCULO DE TOTALES (KPIs)
        # Calculamos sobre lo que se está viendo en pantalla (Filtrado o Total)
        if not df.empty:
            ingresos = df[df['Tipo_transaccion'] == 'Ingreso']['Monto'].sum()
            egresos = df[df['Tipo_transaccion'] == 'Egreso']['Monto'].sum()
            balance = ingresos - egresos

            # Tarjetas de colores
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Ingresos (Vista Actual)", f"${ingresos:,.2f}")
            kpi2.metric("Egresos (Vista Actual)", f"${egresos:,.2f}")
            kpi3.metric("Balance Neto", f"${balance:,.2f}", delta_color="normal")

            # 4. TABLA DETALLADA
            st.subheader("📜 Detalle de Transacciones")
            
            # Limpieza de fecha
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date

            st.dataframe(df, use_container_width=True)

            # 5. GRÁFICO COMPARATIVO
            st.subheader("Tendencia Visual")
            
            if grupo_seleccionado == 0:
                # Si vemos todo, un gráfico interesante es ver "Monto por Grupo"
                # Agrupamos por nombre de grupo y tipo
                st.caption("Comparativa de volumen por Grupo")
                chart_data = df.groupby(['Grupo', 'Tipo_transaccion'])['Monto'].sum().reset_index()
                st.bar_chart(chart_data, x="Grupo", y="Monto", color="Tipo_transaccion")
            else:
                # Si vemos uno solo, mostramos su historial en el tiempo
                st.caption("Evolución temporal del grupo")
                st.bar_chart(df, x="Fecha", y="Monto", color="Tipo_transaccion")

        else:
            st.info("No se encontraron movimientos para los criterios seleccionados.")

    except Exception as e:
        st.error(f"Error en reporte de admin: {e}")
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
        show_admin_reports()


