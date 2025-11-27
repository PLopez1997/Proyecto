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
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
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
    # --- CORRECCIÓN: SE ELIMINÓ LA INTERFAZ DE USUARIO DE AQUÍ ---
    conn = obtener_conexion()
    if not conn:
        st.warning("No hay conexión a BD; usando datos simulados.")
        return {
            "distritos": pd.DataFrame({"Id_distrito": [], "Nombre": []}),
            "ciclos": pd.DataFrame({"Id_ciclo": [], "Nombre": []}),
            "grupos": pd.DataFrame({"Id_grupo": [], "Nombre": []})
        }

    try:
        # Detectar nombres reales de tablas
        distrito_table = next((t for t in ["Distrito", "distrito", "Distritos", "distritos"] if table_columns(conn, t)), None)
        ciclo_table = next((t for t in ["Ciclo", "ciclo", "Ciclos", "ciclos"] if table_columns(conn, t)), None)
        grupo_table = next((t for t in ["Grupo", "grupo", "Grupos", "grupos"] if table_columns(conn, t)), None)

        ref = {}

        # Distritos
        if distrito_table:
            cols = table_columns(conn, distrito_table)
            id_col = pick_column(cols, ["Id_distrito", "id_distrito", "Id_distr", "Id"])
            label_col = pick_column(cols, ["Nombre", "nombre", "Descripcion", "descripcion", "Label", "label", "Nombre_distrito"])

            if id_col and label_col:
                ref["distritos"] = pd.read_sql(f"SELECT {id_col} AS Id_distrito, {label_col} AS Nombre FROM {distrito_table}", conn)
            elif id_col:
                ref["distritos"] = pd.read_sql(f"SELECT {id_col} AS Id_distrito FROM {distrito_table}", conn)
                ref["distritos"]["Nombre"] = ref["distritos"]["Id_distrito"].astype(str)
            else:
                ref["distritos"] = pd.DataFrame({"Id_distrito": [], "Nombre": []})
        else:
            ref["distritos"] = pd.DataFrame({"Id_distrito": [], "Nombre": []})

        # Ciclos
        if ciclo_table:
            cols = table_columns(conn, ciclo_table)
            id_col = pick_column(cols, ["Id_ciclo", "id_ciclo", "Id"])
            label_col = pick_column(cols, ["Nombre", "nombre", "Descripcion", "descripcion", "Periodo", "Ciclo", "Fecha_inicio"])

            if id_col and label_col:
                ref["ciclos"] = pd.read_sql(f"SELECT {id_col} AS Id_ciclo, {label_col} AS Nombre FROM {ciclo_table}", conn)
            elif id_col:
                ref["ciclos"] = pd.read_sql(f"SELECT {id_col} AS Id_ciclo FROM {ciclo_table}", conn)
                ref["ciclos"]["Nombre"] = "Ciclo " + ref["ciclos"]["Id_ciclo"].astype(str)
            else:
                ref["ciclos"] = pd.DataFrame({"Id_ciclo": [], "Nombre": []})
        else:
            ref["ciclos"] = pd.DataFrame({"Id_ciclo": [], "Nombre": []})

        # ================= GRUPOS ====================
        try:
            if grupo_table:
                cols = table_columns(conn, grupo_table)
                id_col = pick_column(cols, ["Id_grupo", "id_grupo", "Id_cliente", "Id", "Id_cliente"])
                label_col = pick_column(cols, ["Nombre", "nombre", "Descripcion", "descripcion", "Grupo"])

                # ---- LECTURA NORMAL DE GRUPOS ----
                if id_col and label_col:
                    ref["grupos"] = pd.read_sql(
                        f"SELECT {id_col} AS Id_grupo, {label_col} AS Nombre, Id_distrito FROM {grupo_table}",
                        conn
                    )
                elif id_col:
                    ref["grupos"] = pd.read_sql(
                        f"SELECT {id_col} AS Id_grupo, Id_distrito FROM {grupo_table}",
                        conn
                    )
                    ref["grupos"]["Nombre"] = ref["grupos"]["Id_grupo"].astype(str)
                else:
                    ref["grupos"] = pd.DataFrame({
                        "Id_grupo": [],
                        "Nombre": [],
                        "Id_distrito": []
                    })
            else:
                ref["grupos"] = pd.DataFrame({
                    "Id_grupo": [],
                    "Nombre": [],
                    "Id_distrito": []
                })
        except Exception:
            ref["grupos"] = pd.DataFrame({
                "Id_grupo": [],
                "Nombre": [],
                "Id_distrito": []
            })

        # --------------------
        # RETURN NORMAL
        # --------------------
        return ref

    # -------- EXCEPTION --------
    except Exception as e:
        st.warning(f"No se pudieron cargar datos de referencia. Error: {e}")
        return {
            "distritos": pd.DataFrame({"Id_distrito": [], "Nombre": []}),
            "ciclos": pd.DataFrame({"Id_ciclo": [], "Nombre": []}),
            "grupos": pd.DataFrame({"Id_grupo": [], "Nombre": []})
        }

    # -------- FINALLY --------
    finally:
        conn.close()


# -----------------------
# CREAR USUARIO (textbox para grupo y textbox para promotora->distrito)
# -----------------------

def menu_gestion_usuarios():
    st.header("👤 Gestión de Usuarios y Accesos")
    tab1, tab2 = st.tabs(["➕ Crear Usuario", "📋 Lista de Usuarios"])

    with tab1:
        create_user_form() 
    with tab2:
        listar_usuarios()

def create_user_form():
    st.subheader("Registrar Credenciales")
    st.info("Crea un usuario y contraseña para vincularlo a un perfil existente.")

    conn = obtener_conexion()
    if not conn:
        st.error("Sin conexión a BD")
        return

    df_miembros = pd.DataFrame()
    df_promotoras = pd.DataFrame() 

    try:
        # Cargar Miembros
        query_m = """
            SELECT m.Id_miembro, m.Nombre, m.`DUI/Identificación` as DUI, m.Id_grupo, g.Nombre as NombreGrupo
            FROM Miembro m
            JOIN Grupo g ON m.Id_grupo = g.Id_grupo
        """
        df_miembros = pd.read_sql(query_m, conn)
        
        # Cargar Promotoras (CORREGIDO: Sin JOIN a Distrito)
        query_p = "SELECT Id_promotora, Nombre, Id_distrito FROM Promotora"
        try: df_promotoras = pd.read_sql(query_p, conn)
        except: pass 

    except Exception as e:
        st.error(f"Error cargando datos: {e}")
    finally:
        conn.close()

    # --- FORMULARIO ---
    c1, c2 = st.columns(2)
    new_username = c1.text_input("Usuario (Login)")
    new_password = c2.text_input("Contraseña", type="password")
    new_rol = st.selectbox("Rol", ['miembro', 'junta directiva', 'promotora', 'administrador'])

    id_miembro_final = None
    id_grupo_final = None
    id_promotora_final = None
    id_distrito_final = None

    st.markdown("---")

    # CASO A: MIEMBRO O DIRECTIVA
    if new_rol in ("junta directiva", "miembro"):
        if not df_miembros.empty:
            st.write(f"👤 **Vincular a Miembro:**")
            lista_m = {
                row['Id_miembro']: f"{row['Nombre']} - {row['NombreGrupo']}"
                for i, row in df_miembros.iterrows()
            }
            id_sel = st.selectbox("Persona:", options=lista_m.keys(), format_func=lambda x: lista_m[x])
            
            if id_sel:
                id_miembro_final = id_sel
                fila = df_miembros[df_miembros['Id_miembro'] == id_sel].iloc[0]
                id_grupo_final = int(fila['Id_grupo'])
                st.info(f"✅ Se vinculará a: **{fila['Nombre']}** del grupo **{fila['NombreGrupo']}**")
        else:
            st.warning("No hay miembros registrados.")

    # CASO B: PROMOTORA
    elif new_rol == 'promotora':
        if not df_promotoras.empty:
            st.write(f"👩‍💼 **Vincular a Promotora:**")
            lista_p = {
                row['Id_promotora']: f"{row['Nombre']} (Distrito {row['Id_distrito']})"
                for i, row in df_promotoras.iterrows()
            }
            id_p_sel = st.selectbox("Seleccionar:", options=lista_p.keys(), format_func=lambda x: lista_p[x])
            
            if id_p_sel:
                id_promotora_final = id_p_sel
                fila = df_promotoras[df_promotoras['Id_promotora'] == id_p_sel].iloc[0]
                
                if pd.notna(fila['Id_distrito']):
                    id_distrito_final = int(fila['Id_distrito'])
                    st.info(f"✅ ID Promotora: {id_promotora_final} | Distrito: {id_distrito_final}")
                else:
                    st.warning("Esta promotora no tiene distrito asignado.")
        else:
            st.warning("⚠️ No hay promotoras registradas.")

    # CASO C: ADMIN
    elif new_rol == 'administrador':
        st.info("El administrador tiene acceso total.")

    st.markdown("---")

    if st.button("Crear Usuario", type="primary"):
        if new_username and new_password:
            guardar_usuario_bd(new_username, new_password, new_rol, id_miembro_final, id_grupo_final, id_promotora_final, id_distrito_final)
        else:
            st.error("Faltan datos.")

def guardar_usuario_bd(usuario, password, rol, id_miembro, id_grupo, id_promotora, id_distrito):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT Usuario FROM Login WHERE Usuario = %s", (usuario,))
            if cursor.fetchone():
                st.error("El usuario ya existe.")
                return

            query = """
                INSERT INTO Login (Usuario, Contraseña, Rol, Id_miembro, Id_grupo, Id_promotora, Id_distrito) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            id_m = int(id_miembro) if id_miembro else None
            id_g = int(id_grupo) if id_grupo else None
            id_p = int(id_promotora) if id_promotora else None
            id_d = int(id_distrito) if id_distrito else None

            cursor.execute(query, (usuario, password, rol, id_m, id_g, id_p, id_d))
            conn.commit()
            st.success("Usuario creado exitosamente.")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()

def listar_usuarios():
    conn = obtener_conexion()
    if conn:
        try:
            st.subheader("Lista de Usuarios")
            df = pd.read_sql("SELECT Id_usuario, Usuario, Rol, Id_miembro, Id_promotora, Id_grupo FROM Login", conn)
            st.dataframe(df, use_container_width=True)
        finally:
            conn.close()

# -----------------------
# CREAR CICLO (ya SIN vínculo a grupo)
# ------------------------------------

# ==========================================
# SECCIÓN 4: GESTIÓN DE CICLOS Y CIERRE
# ==========================================
def create_cycle_form(ref_data):
    # Redirigimos a la nueva función completa
    menu_gestion_ciclos(ref_data)

def menu_gestion_ciclos(ref_data):
    st.header("🔄 Gestión del Ciclo Operativo")
    
    tab_crear, tab_cerrar = st.tabs(["➕ Iniciar Nuevo Ciclo", "🏁 Cerrar Ciclo Actual"])
    
    # --- PESTAÑA 1: CREAR ---
    with tab_crear:
        st.subheader("Configuración de Nuevo Ciclo")
        with st.form("form_nuevo_ciclo"):
            c1, c2 = st.columns(2)
            fecha_inicio = c1.date_input("Fecha Inicio")
            fecha_cierre = c2.date_input("Fecha Cierre Estimada")
            
            duracion = st.number_input("Duración (meses)", min_value=6, max_value=12, value=12)
            meta_ahorro = st.number_input("Meta de Ahorro Grupal ($)", min_value=0.0)
            estado = st.selectbox("Estado Inicial", ["Activo", "Planificado"])
            
            if st.form_submit_button("Registrar Inicio de Ciclo"):
                guardar_ciclo_bd(fecha_inicio, fecha_cierre, estado)
        
        if "ciclos" in ref_data and not ref_data["ciclos"].empty:
            st.markdown("### Historial de Ciclos")
            st.dataframe(ref_data["ciclos"], use_container_width=True)

    # --- PESTAÑA 2: CIERRE DE CICLO ---
    with tab_cerrar:
        vista_cierre_ciclo()

def guardar_ciclo_bd(inicio, cierre, estado):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            # CORRECCIÓN: Cambiado 'Fecha_fin' por 'Fecha_cierre'
            query = "INSERT INTO Ciclo (Fecha_inicio, Fecha_cierre, Estado) VALUES (%s, %s, %s)"
            cursor.execute(query, (inicio, cierre, estado))
            conn.commit()
            st.success("✅ Nuevo ciclo registrado.")
            st.rerun()
        except Exception as e:
            # Manejo de error inteligente: Si falla por columna, sugerir el nombre alternativo
            if "Unknown column" in str(e):
                st.error(f"Error de base de datos: {e}. (Verifica si la columna se llama 'Fecha_cierre' o 'Fecha_fin' en phpMyAdmin)")
            else:
                st.error(f"Error al guardar ciclo: {e}")
        finally:
            conn.close()

def vista_cierre_ciclo():
    st.subheader("🏁 Auditoría y Cierre de Ciclo")
    st.info("Este proceso calculará las utilidades y generará el acta final.")
    
    conn = obtener_conexion()
    if not conn: return

    try:
        # Validaciones
        errores = []
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Prestamo WHERE Estado = 'Activo'")
        if cur.fetchone()[0] > 0: errores.append("❌ Hay préstamos activos.")
            
        cur.execute("SELECT COUNT(*) FROM Multa WHERE Estado = 'Pendiente'")
        if cur.fetchone()[0] > 0: errores.append("❌ Hay multas sin pagar.")

        if errores:
            for e in errores: st.error(e)
            st.warning("⛔ El cierre está bloqueado.")
            return 

        # Cálculos
        st.success("✅ Validaciones pasadas.")
        
        # Calcular Saldo Caja
        cur.execute("SELECT Tipo_transaccion, Monto FROM Caja")
        movs = cur.fetchall()
        ing = sum(m[1] for m in movs if m[0] == 'Ingreso')
        egr = sum(m[1] for m in movs if m[0] == 'Egreso')
        saldo_caja = ing - egr
        
        # Calcular Ahorros
        cur.execute("SELECT SUM(Monto) FROM Ahorro")
        res = cur.fetchone()
        total_ahorros = float(res[0]) if res and res[0] else 0.0
        
        utilidad_neta = saldo_caja - total_ahorros
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Dinero en Caja", f"${saldo_caja:,.2f}")
        c2.metric("Capital Ahorrado", f"${total_ahorros:,.2f}")
        c3.metric("Utilidad a Repartir", f"${utilidad_neta:,.2f}")
        
        st.markdown("---")
        st.subheader("💰 Distribución de Utilidades")
        
        query_dist = """
            SELECT m.Nombre, SUM(a.Monto) as AhorroIndividual
            FROM Ahorro a
            JOIN Miembro m ON a.Id_miembro = m.Id_miembro
            GROUP BY m.Id_miembro, m.Nombre
        """
        df_reparto = pd.read_sql(query_dist, conn)
        
        if not df_reparto.empty and total_ahorros > 0:
            df_reparto['Participación %'] = (df_reparto['AhorroIndividual'] / total_ahorros) * 100
            df_reparto['Ganancia'] = (df_reparto['Participación %'] / 100) * utilidad_neta
            df_reparto['Total'] = df_reparto['AhorroIndividual'] + df_reparto['Ganancia']
            
            st.dataframe(df_reparto, use_container_width=True)
            
            if st.button("📝 Generar Acta", type="primary"):
                st.balloons()
                st.success("Acta generada (Simulación).")
        else:
            st.info("No hay datos para distribuir.")

    except Exception as e:
        st.error(f"Error en cierre: {e}")
    finally:
        conn.close()            
# -----------------------
# GESTIÓN DE GRUPOS (creación vinculada a tabla real)
# -----------------------

def asignar_distrito_a_grupo_existente():
    """
    Función que SOLO aparece en Grupos y Distritos para asignar
    un distrito a un grupo existente mediante UPDATE.
    """
    st.markdown("---")
    st.subheader("➕ Asignar grupo a distrito")
    st.caption("Escriba el nombre exacto del grupo existente para vincularlo a un distrito.")

    nuevo_nombre = st.text_input("Nombre del Grupo (existente):")
    nuevo_distrito = st.selectbox("Seleccione el distrito del grupo:", [1, 2, 3])

    if st.button("Guardar/Vincular Grupo"):
        if nuevo_nombre.strip() == "":
            st.error("Debe ingresar un nombre para buscar el grupo.")
        else:
            conn = obtener_conexion()
            if conn:
                try:
                    cur = conn.cursor()
                    # LÓGICA PEDIDA: BUSCAR NOMBRE -> UPDATE COLUMNA ID_DISTRITO
                    update_query = """
                        UPDATE Grupo 
                        SET Id_distrito = %s 
                        WHERE Nombre = %s
                    """
                    cur.execute(update_query, (nuevo_distrito, nuevo_nombre))
                    
                    if cur.rowcount > 0:
                        conn.commit()
                        st.success(f"✅ Se asignó el Distrito {nuevo_distrito} al grupo '{nuevo_nombre}'.")
                    else:
                        st.warning(f"No se encontró ningún grupo llamado '{nuevo_nombre}'. Verifique el nombre.")
                        
                except Exception as e:
                    st.error(f"Error al actualizar el grupo: {e}")
                finally:
                    conn.close()

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
            id_ciclo = int(ciclos_df.loc[ciclos_df["Nombre"] == ciclo_sel, "Id_ciclo"].iloc[0])
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
                grupo_table = next((t for t in ["grupos", "Grupo", "GrupoS", "GRUPOS"] if table_columns(con, t)), None)
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

                sql = f"INSERT INTO {grupo_table} ({', '.join('' + c + '' for c in insert_cols)}) VALUES ({', '.join(placeholders)})"
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
        grupos_dict = {0: "👁 Ver Todos los Grupos"}  # Opción por defecto
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

    # --- MENÚ LATERAL ---
    opciones = ["Gestión de Usuarios", "Grupos y Distritos", "Ciclos", "Reportes Consolidados", "Gestión de Promotoras"]
    seleccion = st.sidebar.selectbox("Sección", opciones)

    st.sidebar.markdown("---")

    # --- RUTEO DE PÁGINAS ---
    if seleccion == "Gestión de Usuarios":
        menu_gestion_usuarios()

    elif seleccion == "Grupos y Distritos":
        # AQUÍ LLAMAMOS A LAS DOS FUNCIONES DE GRUPO
        create_new_group(ref_data)
        # ESTA ES LA FUNCIÓN NUEVA QUE SOLO APARECE AQUÍ:
        asignar_distrito_a_grupo_existente()

    elif seleccion == "Ciclos":
        create_cycle_form(ref_data)

    elif seleccion == "Reportes Consolidados":
        show_admin_reports()

    elif seleccion == "Gestión de Promotoras":
        menu_gestion_promotoras()


# ==========================================
# FORMULARIO DE REGISTRO 1
# ==========================================

# ==========================================
# 3. GESTIÓN DE PROMOTORAS (CORREGIDO)
# ==========================================

def menu_gestion_promotoras():
    st.header("👩‍💼 Gestión de Promotoras")
    tab1, tab2 = st.tabs(["➕ Registrar Nueva", "📋 Directorio"])
    
    with tab1:
        registrar_promotora_form()
    with tab2:
        listar_promotoras()

def registrar_promotora_form():
    st.subheader("Alta de Nueva Promotora")
    
    # --- CORRECCIÓN: Distritos Fijos (Ya no se leen de BD) ---
    distritos_fijos = {
        1: "Distrito 1 - Zona Norte",
        2: "Distrito 2 - Zona Centro",
        3: "Distrito 3 - Zona Sur"
    }
    
    with st.form("form_promotora"):
        c1, c2 = st.columns(2)
        with c1:
            nombre = st.text_input("Nombre Completo")
        with c2:
            contacto = st.text_input("Contacto (Teléfono/Email)")
        
        # Selector usando el diccionario fijo
        id_distrito = st.selectbox(
            "Asignar Distrito:", 
            options=distritos_fijos.keys(), 
            format_func=lambda x: distritos_fijos[x]
        )
            
        if st.form_submit_button("Guardar Promotora"):
            if nombre:
                guardar_promotora_bd(nombre, id_distrito, contacto)
            else:
                st.error("El nombre es obligatorio.")

def guardar_promotora_bd(nombre, id_distrito, contacto):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            # Guardamos directamente el número de distrito (1, 2 o 3)
            query = "INSERT INTO Promotora (Nombre, Id_distrito, Contacto) VALUES (%s, %s, %s)"
            cursor.execute(query, (nombre, id_distrito, contacto))
            conn.commit()
            st.success(f"✅ Promotora '{nombre}' registrada en Distrito {id_distrito}.")
        except Exception as e:
            st.error(f"Error al guardar: {e}")
        finally:
            conn.close()

def listar_promotoras():
    conn = obtener_conexion()
    if conn:
        try:
            # CORRECCIÓN: Consulta simple sin JOIN a tabla Distrito
            query = "SELECT Id_promotora, Nombre, Contacto, Id_distrito FROM Promotora"
            df = pd.read_sql(query, conn)
            
            if not df.empty:
                # Agregamos columna visual
                df['Zona'] = df['Id_distrito'].apply(lambda x: f"Distrito {x}")
                st.dataframe(df[['Id_promotora', 'Nombre', 'Zona', 'Contacto']], use_container_width=True)
            else:
                st.info("No hay promotoras registradas.")
        except Exception as e:
            st.error(f"Error al listar: {e}")
        finally:
            conn.close()
