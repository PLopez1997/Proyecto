# ==============================================================================
# ARCHIVO: distrito.py
# DESCRIPCIÓN: Entorno de Promotoras actualizado.
# - Dashboard con KPIs financieros del distrito (Incluyendo Ahorros).
# - Gráfico comparativo de Ingresos vs Egresos.
# - Visualización de grupos del distrito.
# - Gestión de Miembros (Buscador Global con Ahorros).
# ==============================================================================

import streamlit as st
import pandas as pd

# --- IMPORTACIÓN SEGURA DE LA CONEXIÓN ---
try:
    from modulos.config.conexion import obtener_conexion
except ImportError:
    try:
        from config.conexion import obtener_conexion
    except ImportError:
        try:
            from conexion import obtener_conexion
        except ImportError:
            st.error("❌ Error crítico: No se encuentra el archivo de conexión.")
            st.stop()

# ==============================================================================
# SECCIÓN 1: FUNCIONES BACKEND (CONSULTAS SQL)
# ==============================================================================

def obtener_info_distrito(id_distrito):
    """Obtiene nombre y datos del distrito."""
    conn = obtener_conexion()
    data = None
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Distrito WHERE id_distrito = %s", (id_distrito,))
            data = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception as e:
            pass
    return data

# --- NUEVAS FUNCIONES PARA EL DASHBOARD (Conexión Distrito -> Grupo -> Miembro ...) ---

def obtener_kpis_financieros(id_distrito):
    """
    Calcula:
    1. Total Prestamos Activos
    2. Cantidad de Multas Pendientes
    3. Capital Total Prestado (Suma de montos)
    4. Monto Total en Ahorros (NUEVO)
    Todo filtrado por los grupos que pertenecen al id_distrito.
    """
    conn = obtener_conexion()
    kpis = {"num_prestamos": 0, "num_multas": 0, "capital_total": 0.0, "total_ahorros": 0.0}
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # 1. Capital Total y Numero de Prestamos Activos
            sql_prestamos = """
                SELECT COUNT(p.Id_prestamo), SUM(p.Monto)
                FROM Prestamo p
                JOIN Miembro m ON p.Id_miembro = m.Id_miembro
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s AND p.Estado = 'Activo'
            """
            cursor.execute(sql_prestamos, (id_distrito,))
            res_prestamos = cursor.fetchone()
            if res_prestamos:
                kpis["num_prestamos"] = res_prestamos[0] if res_prestamos[0] else 0
                kpis["capital_total"] = res_prestamos[1] if res_prestamos[1] else 0.0

            # 2. Multas Pendientes
            sql_multas = """
                SELECT COUNT(mu.Id_multa)
                FROM Multa mu
                JOIN Miembro m ON mu.Id_miembro = m.Id_miembro
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s AND mu.Estado = 'Pendiente'
            """
            cursor.execute(sql_multas, (id_distrito,))
            res_multas = cursor.fetchone()
            if res_multas:
                kpis["num_multas"] = res_multas[0] if res_multas[0] else 0
            
            # 3. Monto Total en Ahorros (NUEVO KPI)
            # Logica: Distrito -> Grupo -> Miembro -> Ahorro
            # Usamos un try interno por si la tabla Ahorro aun no tiene datos o estructura
            try:
                sql_ahorros = """
                    SELECT SUM(a.Monto)
                    FROM Ahorro a
                    JOIN Miembro m ON a.Id_miembro = m.Id_miembro
                    JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                    WHERE g.Id_distrito = %s
                """
                cursor.execute(sql_ahorros, (id_distrito,))
                res_ahorros = cursor.fetchone()
                if res_ahorros:
                    kpis["total_ahorros"] = res_ahorros[0] if res_ahorros[0] else 0.0
            except Exception as e_ahorro:
                print(f"Advertencia: No se pudieron sumar ahorros ({e_ahorro})")
                kpis["total_ahorros"] = 0.0
            
            conn.close()
        except Exception as e:
            st.error(f"Error calculando KPIs: {e}")
    return kpis

def obtener_todos_prestamos_distrito(id_distrito):
    """Obtiene la lista detallada de prestamos de todo el distrito."""
    conn = obtener_conexion()
    df = pd.DataFrame()
    if conn:
        try:
            query = """
                SELECT 
                    m.Nombre AS Miembro,
                    g.Nombre AS Grupo,
                    p.Monto AS Monto,
                    p.Estado AS Estado,
                    p.Fecha_inicio AS Fecha_Inicio
                FROM Prestamo p
                JOIN Miembro m ON p.Id_miembro = m.Id_miembro
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s
                ORDER BY g.Nombre, m.Nombre
            """
            df = pd.read_sql(query, conn, params=(id_distrito,))
            conn.close()
        except Exception as e:
            st.error(f"Error listando préstamos: {e}")
    return df

def obtener_todas_multas_distrito(id_distrito):
    conn = obtener_conexion()
    df = pd.DataFrame()
    if conn:
        try:
            query = """
                SELECT 
                    m.Nombre AS Miembro,
                    g.Nombre AS Grupo,
                    mu.Monto AS Monto_Multa,
                    mu.Motivo,
                    mu.Estado
                FROM Multa mu
                JOIN Miembro m ON mu.Id_miembro = m.Id_miembro
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s
            """
            df = pd.read_sql(query, conn, params=(id_distrito,))
            conn.close()
        except Exception:
            pass
    return df

def obtener_grupos_distrito(id_distrito):
    """Solo obtiene la info basica de los grupos de este distrito"""
    conn = obtener_conexion()
    df = pd.DataFrame()
    if conn:
        try:
            query = "SELECT * FROM Grupo WHERE Id_distrito = %s"
            df = pd.read_sql(query, conn, params=(id_distrito,))
            conn.close()
        except Exception:
            pass
    return df

# --- FUNCIÓN BUSCADOR DE MIEMBRO ---

def buscar_miembro_detalle(nombre_busqueda, id_distrito):
    """
    Busca un miembro por nombre (parcial) dentro del distrito.
    Devuelve sus datos, su grupo, si tiene prestamos, multas y AHORROS.
    """
    conn = obtener_conexion()
    resultados = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # Busqueda con LIKE
            term = f"%{nombre_busqueda}%"
            
            # 1. Buscar Miembros y sus Grupos en este distrito
            # Ajuste de robustez: Buscamos columnas basicas
            sql_miembro = """
                SELECT m.Id_miembro, m.Nombre, m.Telefono, g.Nombre as NombreGrupo
                FROM Miembro m
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s AND m.Nombre LIKE %s
            """
            cursor.execute(sql_miembro, (id_distrito, term))
            miembros = cursor.fetchall()
            
            for m in miembros:
                id_m = m['Id_miembro']
                
                # 2. Buscar Prestamo Activo/Pendiente
                cursor.execute("SELECT Monto, Estado FROM Prestamo WHERE Id_miembro = %s", (id_m,))
                prestamos = cursor.fetchall()
                info_prestamos = ", ".join([f"${p['Monto']} ({p['Estado']})" for p in prestamos]) if prestamos else "Sin préstamos"
                
                # 3. Buscar Multas
                cursor.execute("SELECT Monto, Estado FROM Multa WHERE Id_miembro = %s", (id_m,))
                multas = cursor.fetchall()
                info_multas = ", ".join([f"${mu['Monto']} ({mu['Estado']})" for mu in multas]) if multas else "Sin multas"
                
                # 4. Buscar Ahorros (NUEVO)
                cursor.execute("SELECT Monto FROM Ahorro WHERE Id_miembro = %s", (id_m,))
                ahorros = cursor.fetchall()
                # Mostramos los montos individuales
                info_ahorros = ", ".join([f"${a['Monto']}" for a in ahorros]) if ahorros else "Sin ahorros"
                
                # Opcional: Calcular total ahorrado por este miembro
                total_ahorrado = sum([float(a['Monto']) for a in ahorros])

                resultados.append({
                    "Nombre": m['Nombre'],
                    "Grupo": m['NombreGrupo'],
                    "Prestamos": info_prestamos,
                    "Multas": info_multas,
                    "Ahorros": info_ahorros,
                    "Total Ahorrado": f"${total_ahorrado:.2f}"
                })
                
            cursor.close()
            conn.close()
        except Exception as e:
            st.error(f"Error en búsqueda: {e}")
            
    return pd.DataFrame(resultados)

# ==============================================================================
# SECCIÓN 2: INTERFAZ GRÁFICA (FRONTEND)
# ==============================================================================

def app():
    # 1. VALIDACIÓN DE SESIÓN
    if 'id_distrito_actual' not in st.session_state or st.session_state['id_distrito_actual'] is None:
        st.warning("⚠️ No se ha detectado un distrito. Inicie sesión nuevamente.")
        return

    id_distrito = st.session_state['id_distrito_actual']
    
    # 2. HEADER
    info = obtener_info_distrito(id_distrito)
    nombre_distrito = info.get('Nombre', f'Distrito {id_distrito}') if info else f'Distrito {id_distrito}'
    
    st.title(f"🏡 Panel del {nombre_distrito}")
    st.markdown("---")

    # 3. PESTAÑAS PRINCIPALES
    tab_dashboard, tab_gestion = st.tabs(["📊 Reportes & Dashboard", "👥 Gestión de Miembros y Grupos"])

    # -----------------------------------------------------------
    # TAB 1: DASHBOARD Y REPORTES
    # -----------------------------------------------------------
    with tab_dashboard:
        st.subheader("Resumen Financiero del Distrito")
        
        # A) KPIs (Tarjetas)
        kpis = obtener_kpis_financieros(id_distrito)
        
        # Agregamos una columna más para el nuevo KPI de Ahorros
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Capital Prestado", f"${kpis['capital_total']:,.2f}", help="Dinero que ha salido de caja en préstamos")
        c2.metric("🐷 Ahorros Totales", f"${kpis['total_ahorros']:,.2f}", delta_color="normal", help="Dinero ingresado por ahorros de miembros")
        c3.metric("📈 Préstamos Activos", kpis['num_prestamos'])
        c4.metric("⚠️ Multas Pendientes", kpis['num_multas'], delta_color="inverse")
        
        st.divider()

        # --- NUEVO GRÁFICO DE BARRAS (INGRESOS vs EGRESOS) ---
        st.subheader("📊 Ingresos y Egresos totales")
        
        # Creamos el DataFrame formateado para que el gráfico sea claro
        # Nota: Usamos una estructura que Streamlit entiende bien (Categoría en eje X, Monto en eje Y)
        df_grafico = pd.DataFrame({
            "Tipo": ["Egresos", "Ingresos"],
            "Monto": [float(kpis['capital_total']), float(kpis['total_ahorros'])]
        })
        
        # Renderizamos el gráfico usando la columna 'Tipo' para el color también
        try:
            st.bar_chart(
                df_grafico,
                x="Tipo",
                y="Monto",
                color="Tipo"  # Esto asigna un color distinto a cada barra automáticamente
            )
        except Exception:
            # Fallback para versiones antiguas de Streamlit
            st.bar_chart(df_grafico.set_index("Tipo"))
        
        st.divider()
        
        # B) Tablas Detalladas
        col_izq, col_der = st.columns([2, 1])
        
        with col_izq:
            st.markdown("##### 📋 Detalle de Préstamos (Distrito Completo)")
            df_prestamos = obtener_todos_prestamos_distrito(id_distrito)
            if not df_prestamos.empty:
                st.dataframe(df_prestamos, use_container_width=True, hide_index=True)
            else:
                st.info("No hay préstamos registrados en los grupos de este distrito.")
                
        with col_der:
            st.markdown("##### 🚨 Reporte de Multas")
            df_multas = obtener_todas_multas_distrito(id_distrito)
            if not df_multas.empty:
                st.dataframe(df_multas, use_container_width=True, hide_index=True)
            else:
                st.success("¡Excelente! No hay multas registradas.")

    # -----------------------------------------------------------
    # TAB 2: GESTIÓN (Grupos y Buscador de Miembros)
    # -----------------------------------------------------------
    with tab_gestion:
        
        # A) VISUALIZACIÓN DE GRUPOS (Lectura)
        st.subheader(f"📂 Grupos del {nombre_distrito}")
        df_grupos = obtener_grupos_distrito(id_distrito)
        
        if not df_grupos.empty:
            # Mostramos columnas relevantes
            cols_mostrar = [c for c in ['Nombre', 'Fecha_inicio', 'Id_ciclo', 'Tasa_interes'] if c in df_grupos.columns]
            st.dataframe(df_grupos[cols_mostrar], use_container_width=True)
        else:
            st.warning("Este distrito aún no tiene grupos asignados.")
            
        st.markdown("---")
        
        # B) GESTIÓN DE MIEMBROS (Buscador Inteligente)
        
        st.subheader("🔍 Gestión y Búsqueda de Miembros")
        st.caption("Busque un miembro para ver su Grupo, Préstamos, Multas y Ahorros.")
        
        busqueda = st.text_input("Escriba el nombre del miembro:", placeholder="Ej: Maria Perez...")
        
        if busqueda:
            if len(busqueda) < 3:
                st.warning("Ingrese al menos 3 letras para buscar.")
            else:
                with st.spinner("Buscando en la base de datos..."):
                    df_resultados = buscar_miembro_detalle(busqueda, id_distrito)
                
                if not df_resultados.empty:
                    st.success(f"Se encontraron {len(df_resultados)} coincidencia(s).")
                    st.dataframe(df_resultados, use_container_width=True)
                else:
                    st.error("No se encontró ningún miembro con ese nombre en este distrito.")

# Bloque para pruebas locales
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    # Simulamos un distrito para probar
    if 'id_distrito_actual' not in st.session_state:
        st.session_state['id_distrito_actual'] = 1 
    app()

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
