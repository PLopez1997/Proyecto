import streamlit as st
import pandas as pd
from modulos.config.conexion import obtener_conexion

def miembro_page():
    st.title("👋 Bienvenid@ a tu Espacio Personal")
    st.markdown("---")
    
    # 1. RECUPERAR IDENTIDAD DEL MIEMBRO
    # Intentamos obtener el ID del miembro basado en la sesión.
    # Si tu login no guarda 'Id_miembro', necesitamos buscarlo por el nombre de usuario.
    usuario_nombre = st.session_state.get('Usuario')
    id_miembro = obtener_id_miembro_por_usuario(usuario_nombre)
    
    if not id_miembro:
        st.error(f"No se pudo vincular tu usuario ({usuario_nombre}) con un perfil de Miembro.")
        st.info("Contacta a la directiva para verificar tu registro.")
        return

    # 2. DASHBOARD DE RESUMEN
    col1, col2, col3 = st.columns(3)
    
    # Obtenemos totales
    total_ahorro = obtener_total_ahorro(id_miembro)
    deuda_prestamo = obtener_deuda_actual(id_miembro)
    multas_pendientes = obtener_multas_pendientes(id_miembro)
    
    col1.metric("💰 Mis Ahorros Totales", f"${total_ahorro:,.2f}")
    col2.metric("📉 Deuda Activa", f"${deuda_prestamo:,.2f}", delta_color="inverse")
    col3.metric("⚠️ Multas Pendientes", f"${multas_pendientes:,.2f}", delta_color="inverse")
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["🐷 Historial de Ahorro", "💸 Estado de Préstamos", "📋 Historial de Multas"])
    
    # --- PESTAÑA 1: AHORROS ---
    with tab1:
        st.subheader("Mi Evolución de Ahorro")
        df_ahorros = obtener_historial_ahorros(id_miembro)
        
        if not df_ahorros.empty:
            # Gráfico de línea temporal
            st.line_chart(df_ahorros, x="Fecha", y="Monto")
            
            # Tabla detallada
            with st.expander("Ver detalles de depósitos"):
                st.dataframe(df_ahorros, use_container_width=True)
        else:
            st.info("Aún no tienes registros de ahorro.")

    # --- PESTAÑA 2: PRÉSTAMOS ---
    with tab2:
        st.subheader("Mis Créditos")
        df_prestamos = obtener_historial_prestamos(id_miembro)
        
        if not df_prestamos.empty:
            for index, row in df_prestamos.iterrows():
                # Tarjeta visual por cada préstamo
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.write(f"**Fecha:** {row['Fecha_inicio']}")
                    c2.write(f"**Monto:** ${row['Monto']}")
                    c3.write(f"**Interés:** {row['Interes']}%")
                    
                    estado = row['Estado']
                    if estado == 'Activo':
                        c4.success(f"🟢 {estado}")
                    else:
                        c4.secondary(f"⚪ {estado}")
                    
                    # Barra de progreso de pago (Estimada)
                    pagado = obtener_pagado_por_prestamo(row['Id_prestamo'])
                    total_deuda = row['Monto'] + (row['Monto'] * row['Interes']/100 * row['Plazo'])
                    
                    progreso = min(pagado / total_deuda, 1.0) if total_deuda > 0 else 0
                    st.progress(progreso, text=f"Pagado: ${pagado:,.2f} / Total estimado: ${total_deuda:,.2f}")
        else:
            st.info("No has solicitado préstamos.")

    # --- PESTAÑA 3: MULTAS ---
    with tab3:
        st.subheader("Sanciones y Multas")
        df_multas = obtener_historial_multas(id_miembro)
        
        if not df_multas.empty:
            # Colorear fila según estado
            def color_estado(val):
                color = 'red' if val == 'Pendiente' else 'green'
                return f'color: {color}'

            st.dataframe(df_multas.style.map(color_estado, subset=['Estado']), use_container_width=True)
        else:
            st.success("¡Felicidades! Tienes un historial limpio sin multas.")

# ==========================================
# FUNCIONES SQL DE LECTURA (Solo lectura)
# ==========================================

def obtener_id_miembro_por_usuario(usuario_nombre):
    """
    Busca el Id_miembro en la tabla Miembro usando el nombre
    Suposición: El 'Nombre' en la tabla Miembro coincide con el 'Usuario' del login
    O hay una relación. Ajusta esto según tu realidad.
    """
    conn = obtener_conexion()
    id_m = None
    if conn:
        try:
            cursor = conn.cursor()
            # INTENTO 1: Buscar por coincidencia de nombre (Ajustar si tienes lógica distinta)
            # Lo ideal es que la tabla Login tenga Id_miembro. Si no, usamos el nombre.
            query = "SELECT Id_miembro FROM Miembro WHERE Nombre LIKE %s LIMIT 1"
            cursor.execute(query, (f"%{usuario_nombre}%",))
            res = cursor.fetchone()
            if res:
                id_m = res[0]
        finally:
            conn.close()
    return id_m

def obtener_total_ahorro(id_miembro):
    conn = obtener_conexion()
    total = 0.0
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(Monto) FROM Ahorro WHERE Id_miembro = %s", (id_miembro,))
            res = cursor.fetchone()
            if res and res[0]:
                total = res[0]
        finally:
            conn.close()
    return total

def obtener_deuda_actual(id_miembro):
    # Calcula deuda capital simple de préstamos activos
    conn = obtener_conexion()
    deuda = 0.0
    if conn:
        try:
            cursor = conn.cursor()
            # Suma de montos prestados activos
            cursor.execute("SELECT SUM(Monto) FROM Prestamo WHERE Id_miembro = %s AND Estado = 'Activo'", (id_miembro,))
            res = cursor.fetchone()
            prestado = res[0] if res and res[0] else 0.0
            
            # Restar lo pagado a capital en esos préstamos
            query_pagos = """
                SELECT SUM(pg.Monto_capital) 
                FROM Pago pg
                JOIN Prestamo p ON pg.Id_prestamo = p.Id_prestamo
                WHERE p.Id_miembro = %s AND p.Estado = 'Activo'
            """
            cursor.execute(query_pagos, (id_miembro,))
            res_pagos = cursor.fetchone()
            pagado = res_pagos[0] if res_pagos and res_pagos[0] else 0.0
            
            deuda = prestado - pagado
        finally:
            conn.close()
    return max(deuda, 0.0)

def obtener_multas_pendientes(id_miembro):
    conn = obtener_conexion()
    total = 0.0
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(Monto) FROM Multa WHERE Id_miembro = %s AND Estado = 'Pendiente'", (id_miembro,))
            res = cursor.fetchone()
            if res and res[0]:
                total = res[0]
        finally:
            conn.close()
    return total

def obtener_historial_ahorros(id_miembro):
    conn = obtener_conexion()
    df = pd.DataFrame()
    if conn:
        try:
            query = "SELECT Fecha, Monto FROM Ahorro WHERE Id_miembro = %s ORDER BY Fecha ASC"
            df = pd.read_sql(query, conn, params=(id_miembro,))
            if not df.empty and 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        finally:
            conn.close()
    return df

def obtener_historial_prestamos(id_miembro):
    conn = obtener_conexion()
    df = pd.DataFrame()
    if conn:
        try:
            # Id_cosa: Id_prestamo, Interes, Fecha_inicio
            query = "SELECT Id_prestamo, Monto, Interes, Plazo, Fecha_inicio, Estado FROM Prestamo WHERE Id_miembro = %s ORDER BY Fecha_inicio DESC"
            df = pd.read_sql(query, conn, params=(id_miembro,))
        finally:
            conn.close()
    return df

def obtener_pagado_por_prestamo(id_prestamo):
    conn = obtener_conexion()
    total = 0.0
    if conn:
        try:
            cursor = conn.cursor()
            # Sumamos Capital + Interes pagado
            cursor.execute("SELECT SUM(Monto_capital + Monto_interes) FROM Pago WHERE Id_prestamo = %s", (id_prestamo,))
            res = cursor.fetchone()
            if res and res[0]:
                total = res[0]
        finally:
            conn.close()
    return total

def obtener_historial_multas(id_miembro):
    conn = obtener_conexion()
    df = pd.DataFrame()
    if conn:
        try:
            query = "SELECT Fecha, Motivo, Monto, Estado FROM Multa WHERE Id_miembro = %s ORDER BY Fecha DESC"
            df = pd.read_sql(query, conn, params=(id_miembro,))
            if not df.empty and 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
        finally:
            conn.close()
    return df
