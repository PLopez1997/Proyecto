import streamlit as st
import pandas as pd
# Ajusta este import si tu carpeta de configuración tiene otro nombre, 
# pero esta es la ruta estándar sugerida.
from modulos.config.conexion import obtener_conexion 

def junta_directiva_page():
    st.title("Panel de Control - Directiva")
    st.markdown("---")

    menu = ["Gestionar Miembros", "Gestionar Reuniones", "Caja y Préstamos", "Reportes"]
    choice = st.sidebar.selectbox("Menú Directiva", menu)

    if choice == "Gestionar Miembros":
        gestionar_miembros()

    elif choice == "Gestionar Reuniones":
        gestionar_reuniones()
        
    elif choice == "Caja y Préstamos":
        gestionar_caja_prestamos()

    elif choice == "Reportes":
        show_reports()

# ==========================================
# SECCIÓN 1: MIEMBROS
# ==========================================

def gestionar_miembros():
    st.header("Gestión de Miembros del Grupo")
    tab1, tab2 = st.tabs(["Registrar Nuevo Miembro", "Ver Lista de Miembros"])

    # --- PESTAÑA 1: REGISTRO ---
    with tab1:
        st.subheader("Afiliación de Nuevo Miembro")
        with st.form("form_nuevo_miembro"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre")
                apellido = st.text_input("Apellido")
                dui = st.text_input("DUI (Documento Único)")
            with col2:
                telefono = st.text_input("Teléfono")
                direccion = st.text_input("Dirección")
                
                # Roles: 1:Pres, 2:Tes, 3:Miembro, 4:Sec
                rol_id = st.selectbox(
                    "Asignar Rol", 
                    options=[1, 2, 4, 3], 
                    format_func=lambda x: {
                        1: "Presidente", 
                        2: "Tesorero", 
                        3: "Miembro", 
                        4: "Secretario"
                    }.get(x, "Desconocido")
                )
            
            submitted = st.form_submit_button("Guardar Miembro")
            
            if submitted:
                if nombre and apellido and dui:
                    nombre_completo = f"{nombre} {apellido}"
                    guardar_miembro_bd(nombre_completo, dui, telefono, direccion, rol_id)
                else:
                    st.error("Por favor llene los campos obligatorios.")

    # --- PESTAÑA 2: LISTADO ---
    with tab2:
        st.subheader("Directorio de Miembros")
        listar_miembros()

# ==========================================
# SECCIÓN 2: REUNIONES
# ==========================================

def gestionar_reuniones():
    st.header("Gestión Operativa de Reuniones")
    
    tab1, tab2, tab3 = st.tabs(["📅 1. Programar", "📝 2. Asistencia", "💰 3. Registrar Ahorros"])

    # --- PESTAÑA 1: CREAR ---
    with tab1:
        st.subheader("Crear nueva reunión")
        with st.form("form_reunion"):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha")
            with col2:
                tema = st.text_input("Tema")
            
            if st.form_submit_button("Crear Reunión"):
                crear_reunion_bd(fecha, tema)

    # --- PESTAÑA 2: ASISTENCIA ---
    with tab2:
        st.subheader("Tomar Asistencia")
        reuniones = obtener_reuniones_del_grupo()
        if reuniones:
            reunion_sel = st.selectbox("Seleccione Reunión para Asistencia:", options=reuniones, format_func=lambda x: f"{x['Fecha']} - {x['tema']}", key="sel_asist")
            
            if reunion_sel:
                miembros = obtener_lista_miembros_simple()
                if miembros:
                    with st.form("form_asistencia"):
                        datos_asistencia = {}
                        st.write("Marque el estado de los miembros:")
                        for m in miembros:
                            c1, c2 = st.columns([3, 2])
                            with c1:
                                st.write(f"👤 {m['Nombre']}")
                            with c2:
                                estado = st.radio("Estado", ["Presente", "Ausente", "Excusado"], key=f"asist_{m['Id_miembro']}", label_visibility="collapsed", horizontal=True)
                                datos_asistencia[m['Id_miembro']] = estado
                        
                        if st.form_submit_button("Guardar Asistencia"):
                            guardar_asistencia_bd(reunion_sel['Id_reunion'], datos_asistencia)
                else:
                    st.info("No hay miembros registrados.")
        else:
            st.info("No hay reuniones creadas.")

    # --- PESTAÑA 3: AHORROS ---
    with tab3:
        st.subheader("Registro de Ahorros por Reunión")
        reuniones_ahorro = obtener_reuniones_del_grupo()
        
        if reuniones_ahorro:
            reunion_ahorro_sel = st.selectbox("Seleccione Reunión:", options=reuniones_ahorro, format_func=lambda x: f"{x['Fecha']} - {x['tema']}", key="sel_ahorro")
            
            st.markdown("---")
            col_izq, col_der = st.columns(2)
            
            with col_izq:
                miembros = obtener_lista_miembros_simple()
                if miembros:
                    dict_miembros = {m['Id_miembro']: m['Nombre'] for m in miembros}
                    miembro_ahorrador = st.selectbox("Miembro que ahorra:", options=dict_miembros.keys(), format_func=lambda x: dict_miembros[x])
                else:
                    miembro_ahorrador = None
                    st.warning("No hay miembros.")
                
            with col_der:
                monto = st.number_input("Monto a Ahorrar ($)", min_value=0.0, step=0.01)
            
            if st.button("Registrar Ahorro", type="primary"):
                if miembro_ahorrador:
                    guardar_ahorro_bd(reunion_ahorro_sel['Id_reunion'], miembro_ahorrador, monto)
                
            st.markdown("#### 📊 Resumen de esta reunión")
            ver_ahorros_reunion(reunion_ahorro_sel['Id_reunion'])
        else:
            st.info("Primero debe crear una reunión.")

# ==========================================
# SECCIÓN 3: CAJA Y PRÉSTAMOS
# ==========================================

def gestionar_caja_prestamos():
    st.header("💰 Gestión Financiera: Caja y Créditos")
    
    # Calculamos saldo con manejo de error para que no bloquee la página
    try:
        saldo_actual = calcular_saldo_disponible()
        st.metric(label="💵 EFECTIVO DISPONIBLE EN CAJA (GLOBAL)", value=f"${saldo_actual:,.2f}")
    except Exception as e:
        st.error(f"Error calculando saldo (Verifique BD): {e}")
        saldo_actual = 0.0
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Nuevo Préstamo", "📥 Registrar Pago", "⚠️ Multas", "📜 Movimientos de Caja"])

    # --- PESTAÑA 1: NUEVO PRÉSTAMO ---
    with tab1:
        st.subheader("Otorgar Nuevo Préstamo")
        with st.form("form_prestamo"):
            col1, col2 = st.columns(2)
            
            # Cargamos miembros
            miembros = obtener_lista_miembros_simple()
            if miembros:
                dict_miembros = {m['Id_miembro']: m['Nombre'] for m in miembros}
                
                with col1:
                    id_miembro = st.selectbox("Solicitante", options=dict_miembros.keys(), format_func=lambda x: dict_miembros[x])
                    monto = st.number_input("Monto Solicitado ($)", min_value=0.0, step=5.0)
                with col2:
                    tasa = st.number_input("Tasa de Interés (%)", min_value=0.0, value=5.0)
                    plazo = st.number_input("Plazo (meses)", min_value=1, value=6)
                
                fecha_inicio = st.date_input("Fecha de desembolso")
                
                interes_est = monto * (tasa / 100) * plazo
                st.info(f"Total a pagar estimado: ${monto + interes_est:.2f}")

                if st.form_submit_button("Aprobar y Desembolsar"):
                    if monto > saldo_actual:
                        st.error(f"⛔ Fondos insuficientes (${saldo_actual}).")
                    elif monto <= 0:
                        st.error("El monto debe ser positivo.")
                    else:
                        crear_prestamo_bd(id_miembro, monto, tasa, plazo, fecha_inicio)
            else:
                st.warning("No hay miembros registrados para dar préstamos.")

    # --- PESTAÑA 2: REGISTRAR PAGO ---
    with tab2:
        st.subheader("Cobro de Cuotas")
        prestamos = obtener_prestamos_activos()
        
        if prestamos:
            prestamo_sel = st.selectbox(
                "Seleccione Préstamo:", 
                options=prestamos,
                format_func=lambda x: f"{x['Nombre_Miembro']} - ${x['Monto']} (Fecha: {x['Fecha_inicio']})"
            )
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            c1.metric("Monto Original", f"${prestamo_sel['Monto']}")
            # Ajuste visual para coincidir con BD 'Interes'
            c2.metric("Tasa Interés", f"{prestamo_sel['Interes']}%")
            
            with st.form("form_pago"):
                col_cap, col_int = st.columns(2)
                with col_cap:
                    abono_capital = st.number_input("Abono a Capital ($)", min_value=0.0)
                with col_int:
                    pago_interes = st.number_input("Pago de Interés ($)", min_value=0.0)
                
                fecha_pago = st.date_input("Fecha de pago")
                
                if st.form_submit_button("Registrar Pago"):
                    registrar_pago_bd(prestamo_sel['Id_prestamo'], abono_capital, pago_interes, fecha_pago, prestamo_sel['Id_grupo'])
        else:
            st.info("No hay préstamos activos.")

    # --- PESTAÑA 3: MULTAS ---
    with tab3:
        st.subheader("Gestión de Multas")
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.markdown("#### 😡 Multa Manual")
            with st.form("form_multa_manual"):
                if miembros:
                    miembro_m = st.selectbox("Miembro", options=dict_miembros.keys(), format_func=lambda x: dict_miembros[x], key="sel_mul")
                    monto_m = st.number_input("Monto ($)", min_value=0.50, step=0.25)
                    motivo_m = st.text_input("Motivo", "Mora / Otros")
                    
                    if st.form_submit_button("Aplicar Multa"):
                        aplicar_multa_bd(miembro_m, monto_m, motivo_m)
                else:
                    st.warning("Sin miembros.")

        with col_m2:
            st.markdown("#### 📋 Pendientes de Pago")
            listar_multas_pendientes()

    # --- PESTAÑA 4: CAJA ---
    with tab4:
        st.subheader("Movimientos de Caja")
        ver_movimientos_caja()


# ==========================================
# SECCIÓN 4: REPORTES
# ==========================================

def show_reports():
    st.header("📊 Reportes Consolidados")
    
    conn = obtener_conexion()
    if not conn:
        st.error("No hay conexión con la base de datos.")
        return

    try:
        grupo_id = st.session_state.get('grupo_id')
        
        # 1. CONSULTA GLOBAL (Saldo Caja Común)
        df_global = pd.read_sql("SELECT Tipo_transaccion, Monto FROM Caja", conn)
        
        saldo_global = 0.0
        if not df_global.empty:
            ing = df_global[df_global['Tipo_transaccion'] == 'Ingreso']['Monto'].sum()
            egr = df_global[df_global['Tipo_transaccion'] == 'Egreso']['Monto'].sum()
            saldo_global = ing - egr

        # 2. CONSULTA LOCAL (Historial del Grupo)
        query_local = """
            SELECT Fecha, Detalle, Tipo_transaccion, Monto 
            FROM Caja 
            WHERE Id_grupo = %s 
            ORDER BY Fecha DESC
        """
        df_local = pd.read_sql(query_local, conn, params=(grupo_id,))

        # --- VISUALIZACIÓN ---
        st.metric("💰 SALDO DISPONIBLE (Fondo Común)", f"${saldo_global:,.2f}")
        st.markdown("---")

        if not df_local.empty:
            st.subheader("📜 Historial de Movimientos de MI GRUPO")
            
            if 'Fecha' in df_local.columns:
                df_local['Fecha'] = pd.to_datetime(df_local['Fecha']).dt.date
            
            # Flujo visual
            df_local['Flujo'] = df_local.apply(lambda x: x['Monto'] if x['Tipo_transaccion'] == 'Ingreso' else -x['Monto'], axis=1)
            
            st.dataframe(df_local[['Fecha', 'Detalle', 'Tipo_transaccion', 'Monto']], use_container_width=True)
            st.bar_chart(df_local, x="Fecha", y="Flujo", color="Tipo_transaccion")
            
        else:
            st.info("Este grupo aún no ha registrado movimientos.")

    except Exception as e:
        st.error(f"Error cargando reportes: {e}")
    finally:
        conn.close()

# ==========================================
# FUNCIONES SQL (BACKEND)
# ==========================================

def obtener_conexion_safe():
    return obtener_conexion()

# --- MIEMBROS ---

def guardar_miembro_bd(nombre_completo, dui, telefono, direccion, rol_id):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id', 1) 
            query = "INSERT INTO Miembro (Nombre, `DUI/Identificación`, Telefono, Direccion, Rol, Id_grupo) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (nombre_completo, dui, telefono, direccion, rol_id, grupo_id))
            conn.commit()
            st.success(f"Miembro {nombre_completo} registrado.")
        except Exception as e:
            st.error(f"Error BD: {e}")
        finally:
            conn.close()

def listar_miembros():
    conn = obtener_conexion_safe()
    if conn:
        try:
            grupo_id = st.session_state.get('grupo_id')
            query = "SELECT Id_miembro, Nombre, `DUI/Identificación`, Rol FROM Miembro WHERE Id_grupo = %s"
            df = pd.read_sql(query, conn, params=(grupo_id,))
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                with st.expander("🗑️ Eliminar Miembro"):
                    lista = {row['Id_miembro']: f"{row['Nombre']}" for i, row in df.iterrows()}
                    id_elim = st.selectbox("Seleccione:", options=lista.keys(), format_func=lambda x: lista[x])
                    if st.button("Eliminar Permanentemente"):
                        eliminar_miembro_bd(id_elim)
            else:
                st.info("Sin miembros.")
        except Exception as e:
            st.error(f"Error listando: {e}")
        finally:
            conn.close()

def eliminar_miembro_bd(id_miembro):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Miembro WHERE Id_miembro = %s", (id_miembro,))
            conn.commit()
            st.toast("Miembro eliminado.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()

def obtener_lista_miembros_simple():
    conn = obtener_conexion_safe()
    data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            grupo_id = st.session_state.get('grupo_id')
            cursor.execute("SELECT Id_miembro, Nombre, `DUI/Identificación` FROM Miembro WHERE Id_grupo = %s", (grupo_id,))
            data = cursor.fetchall()
        finally:
            conn.close()
    return data

# --- REUNIONES ---

def crear_reunion_bd(fecha, tema):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id')
            cursor.execute("INSERT INTO Reunion (Fecha, tema, Id_grupo) VALUES (%s, %s, %s)", (fecha, tema, grupo_id))
            conn.commit()
            st.success("Reunión creada.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()

def obtener_reuniones_del_grupo():
    conn = obtener_conexion_safe()
    data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            grupo_id = st.session_state.get('grupo_id')
            cursor.execute("SELECT Id_reunion, Fecha, tema FROM Reunion WHERE Id_grupo = %s ORDER BY Fecha DESC", (grupo_id,))
            data = cursor.fetchall()
        finally:
            conn.close()
    return data

def guardar_asistencia_bd(id_reunion, dict_asistencia):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            query = "INSERT INTO Asistencia (Id_reunion, Id_miembro, Estado) VALUES (%s, %s, %s)"
            vals = []
            multas = []
            
            for id_m, est in dict_asistencia.items():
                vals.append((id_reunion, id_m, est))
                if est == "Ausente":
                    multas.append((id_m, 1.00, "Inasistencia Auto", "Pendiente"))
                elif est == "Excusado":
                    multas.append((id_m, 0.50, "Excusa Auto", "Pendiente"))
            
            cursor.executemany(query, vals)
            if multas:
                cursor.executemany("INSERT INTO Multa (Id_miembro, Monto, Motivo, Estado) VALUES (%s, %s, %s, %s)", multas)
            
            conn.commit()
            st.toast("Asistencia guardada.")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()

def guardar_ahorro_bd(id_reunion, id_miembro, monto):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            # Asegúrate que la columna en BD se llame 'Fecha' o 'Fecha de registro' (recomendado 'Fecha')
            query = "INSERT INTO Ahorro (Id_reunion, Id_miembro, Monto, Fecha) VALUES (%s, %s, %s, NOW())"
            cursor.execute(query, (id_reunion, id_miembro, monto))
            conn.commit()
            st.success(f"Ahorro ${monto} registrado.")
        except Exception as e:
            st.error(f"Error ahorro: {e}")
        finally:
            conn.close()

def ver_ahorros_reunion(id_reunion):
    conn = obtener_conexion_safe()
    if conn:
        try:
            query = """
                SELECT m.Nombre, a.Monto, a.Fecha 
                FROM Ahorro a
                JOIN Miembro m ON a.Id_miembro = m.Id_miembro
                WHERE a.Id_reunion = %s
                ORDER BY a.Id_ahorro DESC
            """
            df = pd.read_sql(query, conn, params=(id_reunion,))
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.metric("Total", f"${df['Monto'].sum():,.2f}")
            else:
                st.info("Sin ahorros.")
        except Exception as e:
            st.error(f"Error SQL: {e}")
        finally:
            conn.close()

# --- CAJA Y CRÉDITOS ---

def calcular_saldo_disponible():
    conn = obtener_conexion_safe()
    saldo = 0.0
    if conn:
        try:
            cursor = conn.cursor()
            
            # Ahorros Totales
            cursor.execute("SELECT SUM(Monto) FROM Ahorro")
            res = cursor.fetchone()
            ahorros = res[0] if res and res[0] else 0.0

            # Caja Común (Ingreso - Egreso)
            cursor.execute("SELECT Tipo_transaccion, Monto FROM Caja")
            movs = cursor.fetchall()
            
            ingresos = sum(m[1] for m in movs if m[0] == 'Ingreso')
            egresos = sum(m[1] for m in movs if m[0] == 'Egreso')
            
            saldo_caja = ingresos - egresos
            
            # Si no hay caja, usamos ahorros como base
            if not movs and ahorros > 0:
                saldo = ahorros
            else:
                saldo = saldo_caja # O saldo_caja + ahorros iniciales si no se migraron
                
        finally:
            conn.close()
    return saldo

def crear_prestamo_bd(id_miembro, monto, tasa, plazo, fecha):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id')
            
            # Insertar Préstamo
            q_p = "INSERT INTO Prestamo (Id_miembro, Monto, Interes, Plazo, Fecha_inicio, Estado) VALUES (%s, %s, %s, %s, %s, 'Activo')"
            cursor.execute(q_p, (id_miembro, monto, tasa, plazo, fecha))
            
            # Egreso Caja
            q_c = "INSERT INTO Caja (Id_grupo, Tipo_transaccion, Monto, Fecha, Detalle) VALUES (%s, 'Egreso', %s, %s, %s)"
            cursor.execute(q_c, (grupo_id, monto, fecha, f"Préstamo ID_M {id_miembro}"))
            
            conn.commit()
            st.success("Préstamo creado.")
            st.rerun()
        except Exception as e:
            st.error(f"Error prestamo: {e}")
        finally:
            conn.close()

def registrar_pago_bd(id_prestamo, capital, interes, fecha, id_grupo):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Registrar Pago
            q_p = "INSERT INTO Pago (Id_prestamo, Monto_capital, Monto_interes, Fecha) VALUES (%s, %s, %s, %s)"
            cursor.execute(q_p, (id_prestamo, capital, interes, fecha))
            
            # Ingreso Caja
            total = capital + interes
            q_c = "INSERT INTO Caja (Id_grupo, Tipo_transaccion, Monto, Fecha, Detalle) VALUES (%s, 'Ingreso', %s, %s, %s)"
            cursor.execute(q_c, (id_grupo, total, fecha, f"Pago Préstamo {id_prestamo}"))
            
            conn.commit()
            st.success("Pago registrado.")
            st.rerun()
        except Exception as e:
            st.error(f"Error pago: {e}")
        finally:
            conn.close()

def obtener_prestamos_activos():
    conn = obtener_conexion_safe()
    data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            grupo_id = st.session_state.get('grupo_id')
            query = """
                SELECT p.Id_prestamo, p.Monto, p.Interes, p.Fecha_inicio, 
                       m.Nombre as Nombre_Miembro, p.Id_miembro, m.Id_grupo
                FROM Prestamo p
                JOIN Miembro m ON p.Id_miembro = m.Id_miembro
                WHERE m.Id_grupo = %s AND p.Estado = 'Activo'
            """
            cursor.execute(query, (grupo_id,))
            data = cursor.fetchall()
        finally:
            conn.close()
    return data

def aplicar_multa_bd(id_miembro, monto, motivo):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Multa (Id_miembro, Monto, Motivo, Estado) VALUES (%s, %s, %s, 'Pendiente')", (id_miembro, monto, motivo))
            conn.commit()
            st.toast("Multa creada.")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()

def listar_multas_pendientes():
    conn = obtener_conexion_safe()
    if conn:
        try:
            grupo_id = st.session_state.get('grupo_id')
            query = """
                SELECT mu.Id_multa, m.Nombre, mu.Monto, mu.Motivo 
                FROM Multa mu
                JOIN Miembro m ON mu.Id_miembro = m.Id_miembro
                WHERE m.Id_grupo = %s AND mu.Estado = 'Pendiente'
            """
            df = pd.read_sql(query, conn, params=(grupo_id,))
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                id_pagar = st.selectbox("Pagar Multa ID:", df['Id_multa'])
                if st.button("Pagar Multa"):
                    pagar_multa_bd(id_pagar)
            else:
                st.info("Sin multas pendientes.")
        except Exception as e:
            st.error(f"Error multas: {e}")
        finally:
            conn.close()

def pagar_multa_bd(id_multa):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id')
            
            cursor.execute("SELECT Monto FROM Multa WHERE Id_multa = %s", (id_multa,))
            res = cursor.fetchone()
            if res:
                monto = res[0]
                cursor.execute("UPDATE Multa SET Estado = 'Pagado' WHERE Id_multa = %s", (id_multa,))
                cursor.execute("INSERT INTO Caja (Id_grupo, Tipo_transaccion, Monto, Fecha, Detalle) VALUES (%s, 'Ingreso', %s, NOW(), 'Pago Multa')", (grupo_id, monto))
                conn.commit()
                st.success("Multa pagada.")
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()

def ver_movimientos_caja():
    conn = obtener_conexion_safe()
    if conn:
        try:
            grupo_id = st.session_state.get('grupo_id')
            df = pd.read_sql("SELECT Fecha, Tipo_transaccion, Monto, Detalle FROM Caja WHERE Id_grupo = %s ORDER BY Fecha DESC", conn, params=(grupo_id,))
            st.dataframe(df, use_container_width=True)
        finally:
            conn.close()

