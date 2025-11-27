# ==============================================================================
# ARCHIVO: distrito.py
# DESCRIPCIÓN: Entorno de Promotoras actualizado.
# ==============================================================================

import streamlit as st
import pandas as pd
from datetime import datetime

# --- IMPORTACIÓN SEGURA DE LA CONEXIÓN ---
try:
    from modulos.config.conexion import obtener_conexion
except ImportError:
    # Fallback para pruebas locales si la estructura de carpetas cambia
    try:
        from config.conexion import obtener_conexion
    except ImportError:
        st.error("❌ Error crítico: No se encuentra el archivo de conexión (modulos.config.conexion).")
        st.stop()

# ==============================================================================
# SECCIÓN 1: FUNCIONES BACKEND (CONSULTAS SQL)
# ==============================================================================

def obtener_conexion_safe():
    return obtener_conexion()

def obtener_info_distrito(id_distrito):
    """Obtiene nombre y datos del distrito."""
    conn = obtener_conexion_safe()
    data = None
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Distrito WHERE id_distrito = %s", (id_distrito,))
            data = cursor.fetchone()
        except Exception:
            pass
        finally:
            conn.close()
    return data

# --- KPIs FINANCIEROS ---

def obtener_kpis_financieros(id_distrito):
    """
    Calcula KPIs financieros agregando datos de todos los grupos del distrito.
    """
    conn = obtener_conexion_safe()
    kpis = {"num_prestamos": 0, "num_multas": 0, "capital_total": 0.0, "total_ahorros": 0.0}
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # 1. Préstamos Activos y Capital en calle
            sql_prestamos = """
                SELECT COUNT(p.Id_prestamo), SUM(p.Monto)
                FROM Prestamo p
                JOIN Miembro m ON p.Id_miembro = m.Id_miembro
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s AND p.Estado = 'Activo'
            """
            cursor.execute(sql_prestamos, (id_distrito,))
            res_p = cursor.fetchone()
            if res_p:
                kpis["num_prestamos"] = res_p[0] if res_p[0] else 0
                kpis["capital_total"] = float(res_p[1]) if res_p[1] else 0.0

            # 2. Multas Pendientes
            sql_multas = """
                SELECT COUNT(mu.Id_multa)
                FROM Multa mu
                JOIN Miembro m ON mu.Id_miembro = m.Id_miembro
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s AND mu.Estado = 'Pendiente'
            """
            cursor.execute(sql_multas, (id_distrito,))
            res_m = cursor.fetchone()
            if res_m:
                kpis["num_multas"] = res_m[0] if res_m[0] else 0
            
            # 3. Ahorros Totales
            sql_ahorros = """
                SELECT SUM(a.Monto)
                FROM Ahorro a
                JOIN Miembro m ON a.Id_miembro = m.Id_miembro
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s
            """
            cursor.execute(sql_ahorros, (id_distrito,))
            res_a = cursor.fetchone()
            if res_a:
                kpis["total_ahorros"] = float(res_a[0]) if res_a[0] else 0.0
            
        except Exception as e:
            st.error(f"Error calculando KPIs: {e}")
        finally:
            conn.close()
            
    return kpis

def obtener_todos_prestamos_distrito(id_distrito):
    conn = obtener_conexion_safe()
    df = pd.DataFrame()
    if conn:
        try:
            query = """
                SELECT m.Nombre AS Miembro, g.Nombre AS Grupo, p.Monto, p.Estado, p.Fecha_inicio
                FROM Prestamo p
                JOIN Miembro m ON p.Id_miembro = m.Id_miembro
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s
                ORDER BY g.Nombre, m.Nombre
            """
            df = pd.read_sql(query, conn, params=(id_distrito,))
        except Exception: pass
        finally: conn.close()
    return df

def obtener_todas_multas_distrito(id_distrito):
    conn = obtener_conexion_safe()
    df = pd.DataFrame()
    if conn:
        try:
            query = """
                SELECT m.Nombre AS Miembro, g.Nombre AS Grupo, mu.Monto, mu.Motivo, mu.Estado
                FROM Multa mu
                JOIN Miembro m ON mu.Id_miembro = m.Id_miembro
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s AND mu.Estado = 'Pendiente'
            """
            df = pd.read_sql(query, conn, params=(id_distrito,))
        except Exception: pass
        finally: conn.close()
    return df

def obtener_grupos_distrito(id_distrito):
    conn = obtener_conexion_safe()
    df = pd.DataFrame()
    if conn:
        try:
            # Seleccionamos explícitamente las columnas para evitar errores si la tabla cambia
            query = "SELECT Id_grupo, Nombre, Fecha_inicio, Tasa_interes FROM Grupo WHERE Id_distrito = %s"
            df = pd.read_sql(query, conn, params=(id_distrito,))
        except Exception: pass
        finally: conn.close()
    return df

def buscar_miembro_detalle(nombre_busqueda, id_distrito):
    conn = obtener_conexion_safe()
    resultados = []
    
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            term = f"%{nombre_busqueda}%"
            
            # Buscar miembro + Grupo
            sql = """
                SELECT m.Id_miembro, m.Nombre, m.Telefono, g.Nombre as NombreGrupo
                FROM Miembro m
                JOIN Grupo g ON m.Id_grupo = g.Id_grupo
                WHERE g.Id_distrito = %s AND m.Nombre LIKE %s
            """
            cursor.execute(sql, (id_distrito, term))
            miembros = cursor.fetchall()
            
            for m in miembros:
                id_m = m['Id_miembro']
                
                # Prestamos
                cursor.execute("SELECT Monto, Estado FROM Prestamo WHERE Id_miembro = %s", (id_m,))
                prestamos = cursor.fetchall()
                txt_prestamos = ", ".join([f"${p['Monto']} ({p['Estado']})" for p in prestamos]) if prestamos else "---"
                
                # Ahorros (Suma)
                cursor.execute("SELECT SUM(Monto) as Total FROM Ahorro WHERE Id_miembro = %s", (id_m,))
                res_ahorro = cursor.fetchone()
                total_ahorro = float(res_ahorro['Total']) if res_ahorro and res_ahorro['Total'] else 0.0
                
                resultados.append({
                    "Nombre": m['Nombre'],
                    "Grupo": m['NombreGrupo'],
                    "Préstamos Activos/Hist": txt_prestamos,
                    "Total Ahorrado": f"${total_ahorro:,.2f}"
                })
        except Exception as e:
            st.error(f"Error búsqueda: {e}")
        finally:
            conn.close()
            
    return pd.DataFrame(resultados)

# --- FUNCIONES DE CREACIÓN / EDICIÓN ---

def crear_grupo_bd(nombre, fecha, id_ciclo, tasa, tipo_multa, regla, id_distrito):
    """
    Crea un grupo insertando explícitamente en las columnas definidas en el Excel.
    """
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            # NOTA: Se agrega Id_distrito al insert para que el grupo nazca vinculado
            query = """
                INSERT INTO Grupo 
                (Nombre, Fecha_inicio, Id_ciclo, Tasa_interes, Tipo_multa, `Regla interna`, Id_distrito) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (nombre, fecha, id_ciclo, tasa, tipo_multa, regla, id_distrito))
            conn.commit()
            st.success(f"✅ Grupo '{nombre}' creado exitosamente en este distrito.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al crear grupo: {e}")
        finally:
            conn.close()

def asignar_distrito_existente_bd(nombre_grupo, id_distrito):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            # Verificar si existe primero
            cursor.execute("SELECT Id_grupo FROM Grupo WHERE Nombre = %s", (nombre_grupo,))
            if not cursor.fetchone():
                st.warning("No se encontró un grupo con ese nombre exacto.")
                return

            cursor.execute("UPDATE Grupo SET Id_distrito = %s WHERE Nombre = %s", (id_distrito, nombre_grupo))
            conn.commit()
            st.success(f"Grupo '{nombre_grupo}' vinculado a este distrito.")
            st.rerun()
        except Exception as e:
            st.error(f"Error update: {e}")
        finally:
            conn.close()

def obtener_ciclos_disponibles():
    """Para llenar el dropdown de ciclos al crear grupo"""
    conn = obtener_conexion_safe()
    lista = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # Asumiendo tabla Ciclo con Id_ciclo y algun descriptor
            cursor.execute("SELECT * FROM Ciclo ORDER BY Id_ciclo DESC")
            lista = cursor.fetchall()
        except: pass
        finally: conn.close()
    return lista

# ==============================================================================
# SECCIÓN 2: INTERFAZ GRÁFICA (FRONTEND)
# ==============================================================================

def app():
    # 1. VALIDACIÓN DE SESIÓN
    if 'id_distrito_actual' not in st.session_state or st.session_state['id_distrito_actual'] is None:
        st.warning("⚠️ No se ha detectado un distrito. Inicie sesión nuevamente.")
        # Para pruebas, descomentar siguiente linea:
        # st.session_state['id_distrito_actual'] = 1 
        return

    id_distrito = st.session_state['id_distrito_actual']
    
    # 2. HEADER
    info = obtener_info_distrito(id_distrito)
    # Si info es None, usamos un fallback
    nombre_distrito = info.get('Nombre', f'Distrito {id_distrito}') if info else f"Distrito ID {id_distrito}"
    
    st.title(f"🏡 Panel del {nombre_distrito}")
    st.markdown("---")

    # 3. PESTAÑAS (Ahora son 4 para mayor claridad)
    tab_dashboard, tab_gestion, tab_grupos, tab_crear = st.tabs([
        "📊 Dashboard Financiero", 
        "🔍 Miembros", 
        "📂 Grupos del Distrito", 
        "➕ Crear Nuevo Grupo"
    ])

    # -----------------------------------------------------------
    # TAB 1: DASHBOARD
    # -----------------------------------------------------------
    with tab_dashboard:
        st.subheader("Resumen Financiero")
        kpis = obtener_kpis_financieros(id_distrito)
        
        # Tarjetas KPI
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Capital Prestado", f"${kpis['capital_total']:,.2f}")
        c2.metric("🐷 Ahorros Totales", f"${kpis['total_ahorros']:,.2f}")
        c3.metric("📈 Préstamos Activos", kpis['num_prestamos'])
        c4.metric("⚠️ Multas Pendientes", kpis['num_multas'], delta_color="inverse")
        
        st.divider()

        # Gráfico simple
        col_g1, col_g2 = st.columns([2,1])
        with col_g1:
            st.subheader("Flujo de Capital (Ingresos vs Egresos)")
            # Datos para gráfico
            data_chart = pd.DataFrame({
                "Concepto": ["Salidas (Préstamos)", "Entradas (Ahorros)"],
                "Monto": [kpis['capital_total'], kpis['total_ahorros']]
            })
            st.bar_chart(data_chart, x="Concepto", y="Monto", color="Concepto")
        
        with col_g2:
            st.markdown("##### 🚨 Multas Pendientes")
            df_multas = obtener_todas_multas_distrito(id_distrito)
            if not df_multas.empty:
                st.dataframe(df_multas[['Miembro', 'Monto_Multa', 'Motivo']], use_container_width=True, hide_index=True)
            else:
                st.info("Sin multas pendientes.")

        st.subheader("📋 Detalle de Préstamos")
        df_prestamos = obtener_todos_prestamos_distrito(id_distrito)
        if not df_prestamos.empty:
            st.dataframe(df_prestamos, use_container_width=True, hide_index=True)
        else:
            st.info("No hay préstamos activos.")

    # -----------------------------------------------------------
    # TAB 2: MIEMBROS
    # -----------------------------------------------------------
    with tab_gestion:
        st.subheader("Buscador Global de Miembros")
        busqueda = st.text_input("Buscar por nombre:", placeholder="Ej: Juan Perez...")
        
        if busqueda:
            if len(busqueda) >= 3:
                df_res = buscar_miembro_detalle(busqueda, id_distrito)
                if not df_res.empty:
                    st.dataframe(df_res, use_container_width=True)
                else:
                    st.warning("No se encontraron resultados.")
            else:
                st.caption("Ingrese al menos 3 caracteres.")

    # -----------------------------------------------------------
    # TAB 3: LISTADO Y VINCULACIÓN DE GRUPOS
    # -----------------------------------------------------------
    with tab_grupos:
        st.subheader(f"📂 Grupos en {nombre_distrito}")
        df_grupos = obtener_grupos_distrito(id_distrito)
        if not df_grupos.empty:
            st.dataframe(df_grupos, use_container_width=True)
        else:
            st.info("No hay grupos asignados a este distrito.")
            
        st.markdown("---")
        with st.expander("🔗 Vincular Grupo Existente (Avanzado)"):
            st.caption("Si un grupo ya existe pero no tiene distrito, asígnelo aquí.")
            with st.form("form_vincular"):
                nombre_existente = st.text_input("Nombre exacto del grupo:")
                if st.form_submit_button("Vincular al Distrito"):
                    if nombre_existente:
                        asignar_distrito_existente_bd(nombre_existente, id_distrito)
                    else:
                        st.error("Escriba el nombre.")

    # -----------------------------------------------------------
    # TAB 4: CREAR NUEVO GRUPO (Ahora en su propia pestaña)
    # -----------------------------------------------------------
    with tab_crear:
        st.subheader("➕ Crear Nuevo Grupo")
        st.info(f"El grupo que cree aquí se asignará automáticamente al **{nombre_distrito}**.")
        
        ciclos = obtener_ciclos_disponibles()
        
        with st.form("form_crear_grupo"):
            c1, c2 = st.columns(2)
            with c1:
                nombre_nuevo = st.text_input("Nombre del Grupo")
                fecha_inicio = st.date_input("Fecha de Inicio")
                
                # Selector de Ciclo (Manejo seguro si no hay ciclos)
                id_ciclo_sel = None
                if ciclos:
                    opciones_ciclo = {c['Id_ciclo']: f"Ciclo {c['Id_ciclo']} ({c.get('Duracion', '')})" for c in ciclos}
                    id_ciclo_sel = st.selectbox("Ciclo", options=opciones_ciclo.keys(), format_func=lambda x: opciones_ciclo[x])
                else:
                    # st.warning("No hay ciclos registrados en BD. Se usará valor 1 por defecto.")
                    id_ciclo_sel = 1 # Fallback
            
            with c2:
                tasa = st.number_input("Tasa de Interés (%)", min_value=0.0, value=5.0, step=0.1)
                tipo_multa = st.text_input("Tipo de Multa (Ej: Fija, %)", value="Fija")
                regla = st.text_area("Reglas Internas", placeholder="Describa brevemente...")
            
            if st.form_submit_button("Crear Grupo", type="primary"):
                if nombre_nuevo:
                    crear_grupo_bd(nombre_nuevo, fecha_inicio, id_ciclo_sel, tasa, tipo_multa, regla, id_distrito)
                else:
                    st.error("El nombre del grupo es obligatorio.")

if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Distrito")
    # Simulación para desarrollo local
    if 'id_distrito_actual' not in st.session_state:
        st.session_state['id_distrito_actual'] = 1
    app()
