import streamlit as st
import pandas as pd
from datetime import datetime
from modulos.config.conexion import obtener_conexion

# Función segura para obtener conexión
def obtener_conexion_safe():
    return obtener_conexion()

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
                rol_id = st.selectbox(
                    "Asignar Rol", 
                    options=[1, 2, 4, 3], 
                    format_func=lambda x: {1: "Presidente", 2: "Tesorero", 3: "Miembro", 4: "Secretario"}.get(x, "Desconocido")
                )
            
            if st.form_submit_button("Guardar Miembro"):
                if nombre and apellido and dui:
                    guardar_miembro_bd(f"{nombre} {apellido}", dui, telefono, direccion, rol_id)
                else:
                    st.error("Llene los campos obligatorios.")

    with tab2:
        st.subheader("Directorio de Miembros")
        listar_miembros()

# ==========================================
# SECCIÓN 2: REUNIONES
# ==========================================

def gestionar_reuniones():
    st.header("Gestión Operativa de Reuniones")
    tab1, tab2, tab3 = st.tabs(["📅 1. Programar", "📝 2. Asistencia", "💰 3. Registrar Ahorros"])

    with tab1:
        st.subheader("Crear nueva reunión")
        with st.form("form_reunion"):
            c1, c2 = st.columns(2)
            fecha = c1.date_input("Fecha")
            tema = c2.text_input("Tema")
            if st.form_submit_button("Crear Reunión"):
                crear_reunion_bd(fecha, tema)

    with tab2:
        st.subheader("Tomar Asistencia")
        reuniones = obtener_reuniones_del_grupo()
        if reuniones:
            reunion_sel = st.selectbox("Seleccione Reunión:", options=reuniones, format_func=lambda x: f"{x['Fecha']} - {x['tema']}", key="sel_asist")
            if reunion_sel:
                miembros = obtener_lista_miembros_simple()
                if miembros:
                    with st.form("form_asistencia"):
                        datos_asistencia = {}
                        st.write("Marque el estado de los miembros:")
                        for m in miembros:
                            c1, c2 = st.columns([3, 2])
                            c1.write(f"👤 {m['Nombre']}")
                            estado = c2.radio("Estado", ["Presente", "Ausente", "Excusado"], key=f"asist_{m['Id_miembro']}", horizontal=True, label_visibility="collapsed")
                            datos_asistencia[m['Id_miembro']] = estado
                        
                        if st.form_submit_button("Guardar Asistencia"):
                            guardar_asistencia_bd(reunion_sel['Id_reunion'], datos_asistencia)
                else:
                    st.warning("No hay miembros registrados.")
        else:
            st.info("No hay reuniones creadas.")

    with tab3:
        st.subheader("Registro de Ahorros")
        reuniones_ahorro = obtener_reuniones_del_grupo()
        if reuniones_ahorro:
            reunion_ahorro_sel = st.selectbox("Seleccione Reunión:", options=reuniones_ahorro, format_func=lambda x: f"{x['Fecha']} - {x['tema']}", key="sel_ahorro")
            miembros = obtener_lista_miembros_simple()
            if miembros:
                c1, c2 = st.columns(2)
                dict_miembros = {m['Id_miembro']: m['Nombre'] for m in miembros}
                miembro_ahorrador = c1.selectbox("Miembro:", options=dict_miembros.keys(), format_func=lambda x: dict_miembros[x])
                monto = c2.number_input("Monto ($)", min_value=0.0, step=0.01)
                
                if st.button("Registrar Ahorro", type="primary"):
                    guardar_ahorro_bd(reunion_ahorro_sel['Id_reunion'], miembro_ahorrador, monto)
                
                ver_ahorros_reunion(reunion_ahorro_sel['Id_reunion'])
            else:
                st.warning("Sin miembros.")
        else:
            st.info("Cree una reunión primero.")

# ==========================================
# SECCIÓN 3: CAJA Y PRÉSTAMOS
# ==========================================

def gestionar_caja_prestamos():
    st.header("💰 Gestión Financiera: Caja y Créditos")
    
    try:
        saldo_actual = calcular_saldo_disponible()
        st.metric(label="💵 EFECTIVO DISPONIBLE EN CAJA", value=f"${saldo_actual:,.2f}")
    except Exception as e:
        st.error(f"Error saldo: {e}")
        saldo_actual = 0.0
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Nuevo Préstamo", "📥 Registrar Pago", "⚠️ Multas", "📜 Movimientos"])

    # --- NUEVO PRÉSTAMO ---
    with tab1:
        st.subheader("Otorgar Nuevo Préstamo")
        with st.form("form_prestamo"):
            miembros = obtener_lista_miembros_simple()
            if miembros:
                dict_miembros = {m['Id_miembro']: m['Nombre'] for m in miembros}
                col1, col2 = st.columns(2)
                id_miembro = col1.selectbox("Solicitante", options=dict_miembros.keys(), format_func=lambda x: dict_miembros[x])
                monto = col1.number_input("Monto Solicitado ($)", min_value=0.0, step=5.0)
                tasa = col2.number_input("Tasa Interés (%)", min_value=0.0, value=5.0)
                plazo = col2.number_input("Plazo (meses)", min_value=1, value=6)
                fecha_inicio = st.date_input("Fecha desembolso")

                if st.form_submit_button("Aprobar Préstamo"):
                    if monto > saldo_actual:
                        st.error(f"Fondos insuficientes (Disp: ${saldo_actual:,.2f}).")
                    elif monto <= 0:
                        st.error("El monto debe ser positivo.")
                    else:
                        crear_prestamo_bd(id_miembro, monto, tasa, plazo, fecha_inicio)
            else:
                st.warning("No hay miembros.")

    # --- REGISTRAR PAGO ---
    with tab2:
        st.subheader("Cobro de Cuotas")
        prestamos = obtener_prestamos_activos() 
        
        if prestamos:
            prestamo_sel = st.selectbox(
                "Seleccione Préstamo:", 
                options=prestamos,
                format_func=lambda x: f"{x['Nombre_Miembro']} - Restan: ${x['Saldo_Pendiente']:,.2f} (Orig: ${x['Monto']})"
            )
            
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            col1.metric("Monto Original", f"${prestamo_sel['Monto']:,.2f}")
            col2.metric("Saldo Pendiente", f"${prestamo_sel['Saldo_Pendiente']:,.2f}", delta_color="inverse")
            col3.metric("Tasa Interés", f"{prestamo_sel['Interes']}%")

            st.info(f"💡 Para liquidar este préstamo se requiere un abono a capital de: **${prestamo_sel['Saldo_Pendiente']:,.2f}**")

            with st.form("form_pago"):
                c1, c2 = st.columns(2)
                abono_capital = c1.number_input(
                    "Abono a Capital ($)", 
                    min_value=0.0, 
                    max_value=float(prestamo_sel['Saldo_Pendiente']), 
                    step=5.0,
                    help="No puede ser mayor al saldo pendiente"
                )
                pago_interes = c2.number_input("Pago de Interés ($)", min_value=0.0)
                fecha_pago_input = st.date_input("Fecha de pago")
                
                if st.form_submit_button("Registrar Pago"):
                    try:
                        registrar_pago_bd(
                            id_prestamo=prestamo_sel['Id_prestamo'], 
                            capital=abono_capital, 
                            interes=pago_interes, 
                            fecha=fecha_pago_input, 
                            id_grupo=prestamo_sel['Id_grupo'],
                            monto_original=prestamo_sel['Monto'],
                            id_multa=0
                        )
                        if abono_capital >= float(prestamo_sel['Saldo_Pendiente']):
                            st.balloons()
                            st.success("¡Pago registrado y PRÉSTAMO LIQUIDADO exitosamente!")
                        else:
                            st.success("Pago parcial registrado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al registrar: {e}")
        else:
            st.info("✅ No hay préstamos pendientes de cobro.")

    # --- MULTAS (MEJORADO) ---
    with tab3:
        st.subheader("Gestión de Multas")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 😡 Multa Manual")
            with st.form("form_multa"):
                if miembros:
                    dict_miembros = {m['Id_miembro']: m['Nombre'] for m in miembros}
                    m_sel = st.selectbox("Miembro", options=dict_miembros.keys(), format_func=lambda x: dict_miembros[x])
                    monto_m = st.number_input("Monto ($)", min_value=0.50)
                    motivo_m = st.text_input("Motivo")
                    if st.form_submit_button("Aplicar"):
                        aplicar_multa_bd(m_sel, monto_m, motivo_m)
        with c2:
            st.markdown("#### 📋 Pendientes")
            # Llamamos a la función actualizada que incluye el botón de pago
            listar_multas_pendientes()

    # --- CAJA ---
    with tab4:
        st.subheader("Movimientos de Caja")
        ver_movimientos_caja()

# ==========================================
# FUNCIONES SQL (BACKEND)
# ==========================================

# ... FUNCIONES BASE (Iguales a la versión anterior) ...
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
        except Exception as e: st.error(f"Error BD: {e}")
        finally: conn.close()

def listar_miembros():
    conn = obtener_conexion_safe()
    if conn:
        try:
            grupo_id = st.session_state.get('grupo_id')
            query = "SELECT Id_miembro, Nombre, `DUI/Identificación`, Rol FROM Miembro WHERE Id_grupo = %s"
            df = pd.read_sql(query, conn, params=(grupo_id,))
            if not df.empty: st.dataframe(df, use_container_width=True)
            else: st.info("Sin miembros.")
        except: pass
        finally: conn.close()

def obtener_lista_miembros_simple():
    conn = obtener_conexion_safe()
    data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            grupo_id = st.session_state.get('grupo_id')
            cursor.execute("SELECT Id_miembro, Nombre, `DUI/Identificación` FROM Miembro WHERE Id_grupo = %s", (grupo_id,))
            data = cursor.fetchall()
        finally: conn.close()
    return data

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
        except Exception as e: st.error(f"Error: {e}")
        finally: conn.close()

def obtener_reuniones_del_grupo():
    conn = obtener_conexion_safe()
    data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            grupo_id = st.session_state.get('grupo_id')
            cursor.execute("SELECT Id_reunion, Fecha, tema FROM Reunion WHERE Id_grupo = %s ORDER BY Fecha DESC", (grupo_id,))
            data = cursor.fetchall()
        finally: conn.close()
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
                if est == "Ausente": multas.append((id_m, 1.00, "Inasistencia Auto", "Pendiente"))
                elif est == "Excusado": multas.append((id_m, 0.50, "Excusa Auto", "Pendiente"))
            cursor.executemany(query, vals)
            if multas: cursor.executemany("INSERT INTO Multa (Id_miembro, Monto, Motivo, Estado, Fecha) VALUES (%s, %s, %s, %s, NOW())", multas)
            conn.commit()
            st.toast("Asistencia guardada.")
        except Exception as e: st.error(f"Error: {e}")
        finally: conn.close()

def guardar_ahorro_bd(id_reunion, id_miembro, monto):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Ahorro (Id_reunion, Id_miembro, Monto, Fecha) VALUES (%s, %s, %s, NOW())", (id_reunion, id_miembro, monto))
            conn.commit()
            st.success(f"Ahorro registrado.")
        except: pass
        finally: conn.close()

def ver_ahorros_reunion(id_reunion):
    conn = obtener_conexion_safe()
    if conn:
        try:
            df = pd.read_sql("SELECT m.Nombre, a.Monto FROM Ahorro a JOIN Miembro m ON a.Id_miembro=m.Id_miembro WHERE a.Id_reunion=%s", conn, params=(id_reunion,))
            if not df.empty: st.dataframe(df, use_container_width=True)
        except: pass
        finally: conn.close()

def calcular_saldo_disponible():
    conn = obtener_conexion_safe()
    saldo = 0.0
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(Monto) FROM Ahorro")
            res = cursor.fetchone()
            ahorros = float(res[0]) if res and res[0] else 0.0
            cursor.execute("SELECT Tipo_transaccion, Monto FROM Caja")
            movs = cursor.fetchall()
            caja = 0.0
            for t, m in movs:
                if t == 'Ingreso': caja += float(m)
                elif t == 'Egreso': caja -= float(m)
            saldo = ahorros + caja
        finally: conn.close()
    return saldo

def crear_prestamo_bd(id_miembro, monto, tasa, plazo, fecha):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id')
            cursor.execute("INSERT INTO Prestamo (Id_miembro, Monto, Interes, Plazo, Fecha_inicio, Estado) VALUES (%s, %s, %s, %s, %s, 'Activo')", (id_miembro, monto, tasa, plazo, fecha))
            cursor.execute("INSERT INTO Caja (Id_grupo, Tipo_transaccion, Monto, Fecha, Detalle) VALUES (%s, 'Egreso', %s, %s, %s)", (grupo_id, monto, fecha, f"Prestamo {id_miembro}"))
            conn.commit()
            st.success("Préstamo creado.")
            st.rerun()
        except Exception as e: st.error(f"Error: {e}")
        finally: conn.close()

def aplicar_multa_bd(id_miembro, monto, motivo):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Multa (Id_miembro, Monto, Motivo, Estado, Fecha) VALUES (%s, %s, %s, 'Pendiente', NOW())", (id_miembro, monto, motivo))
            conn.commit()
            st.toast("Multa creada.")
        except: pass
        finally: conn.close()

# --- AQUÍ ESTÁ LA ACTUALIZACIÓN CLAVE ---

def listar_multas_pendientes():
    conn = obtener_conexion_safe()
    if conn:
        try:
            grupo_id = st.session_state.get('grupo_id')
            # Traemos ID, Nombre, Monto y Motivo de las pendientes
            query = """
                SELECT mu.Id_multa, m.Nombre, mu.Monto, mu.Motivo 
                FROM Multa mu 
                JOIN Miembro m ON mu.Id_miembro=m.Id_miembro 
                WHERE m.Id_grupo=%s AND mu.Estado='Pendiente'
            """
            df = pd.read_sql(query, conn, params=(grupo_id,))
            
            if not df.empty:
                # Mostramos la tabla solo con datos relevantes
                st.dataframe(df[['Nombre', 'Monto', 'Motivo']], use_container_width=True)
                
                # --- ZONA DE PAGO ---
                st.markdown("##### 💸 Pagar Multa")
                col_pay1, col_pay2 = st.columns([3, 1])
                
                # Convertimos a diccionario para facilitar la selección
                opciones = df.to_dict('records')
                
                with col_pay1:
                    multa_a_pagar = st.selectbox(
                        "Seleccione multa a liquidar:",
                        options=opciones,
                        format_func=lambda x: f"{x['Nombre']} - ${x['Monto']} ({x['Motivo']})",
                        label_visibility="collapsed"
                    )
                
                with col_pay2:
                    if st.button("Pagar", type="primary", use_container_width=True):
                        pagar_multa_bd(multa_a_pagar['Id_multa'])
            else:
                st.info("👏 No hay multas pendientes.")
        except Exception as e:
            st.error(f"Error listando multas: {e}")
        finally:
            conn.close()

def pagar_multa_bd(id_multa):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id')
            
            # 1. Obtener el monto antes de actualizar
            cursor.execute("SELECT Monto FROM Multa WHERE Id_multa = %s", (id_multa,))
            res = cursor.fetchone()
            if res:
                monto = res[0]
                
                # 2. Actualizar estado a 'Pagado'
                cursor.execute("UPDATE Multa SET Estado = 'Pagado' WHERE Id_multa = %s", (id_multa,))
                
                # 3. Registrar Ingreso en Caja
                cursor.execute("INSERT INTO Caja (Id_grupo, Tipo_transaccion, Monto, Fecha, Detalle) VALUES (%s, 'Ingreso', %s, NOW(), 'Pago Multa')", (grupo_id, monto))
                
                conn.commit()
                st.success("Multa pagada y registrada en caja.")
                st.rerun() # Recarga la página para quitarla de la lista pendiente
        except Exception as e:
            st.error(f"Error al pagar multa: {e}")
        finally:
            conn.close()

def ver_movimientos_caja():
    conn = obtener_conexion_safe()
    if conn:
        try:
            grupo_id = st.session_state.get('grupo_id')
            df = pd.read_sql("SELECT Fecha, Tipo_transaccion, Monto, Detalle FROM Caja WHERE Id_grupo=%s ORDER BY Fecha DESC", conn, params=(grupo_id,))
            st.dataframe(df, use_container_width=True)
        finally: conn.close()

def show_reports():
    st.info("Módulo de reportes")

def obtener_prestamos_activos():
    conn = obtener_conexion_safe()
    data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            grupo_id = st.session_state.get('grupo_id')
            
            query = """
                SELECT 
                    p.Id_prestamo, 
                    p.Monto, 
                    p.Interes, 
                    p.Fecha_inicio, 
                    m.Nombre as Nombre_Miembro, 
                    p.Id_miembro, 
                    m.Id_grupo,
                    (p.Monto - COALESCE(SUM(pg.Monto_capital), 0)) AS Saldo_Pendiente
                FROM Prestamo p
                JOIN Miembro m ON p.Id_miembro = m.Id_miembro
                LEFT JOIN Pagos pg ON p.Id_prestamo = pg.Id_prestamo
                WHERE m.Id_grupo = %s AND p.Estado = 'Activo'
                GROUP BY p.Id_prestamo, p.Monto, p.Interes, p.Fecha_inicio, m.Nombre, p.Id_miembro, m.Id_grupo
            """
            cursor.execute(query, (grupo_id,))
            data = cursor.fetchall()
        finally:
            conn.close()
    return data

def registrar_pago_bd(id_prestamo, capital, interes, fecha, id_grupo, monto_original, id_multa=0):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            q_p = "INSERT INTO Pagos (Id_prestamo, Monto_capital, Monto_interes, Fecha_pago, Id_multa) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(q_p, (id_prestamo, capital, interes, fecha, id_multa))
            total = capital + interes
            q_c = "INSERT INTO Caja (Id_grupo, Tipo_transaccion, Monto, Fecha, Detalle) VALUES (%s, 'Ingreso', %s, %s, %s)"
            cursor.execute(q_c, (id_grupo, total, fecha, f"Pago Préstamo {id_prestamo}"))
            cursor.execute("SELECT SUM(Monto_capital) FROM Pagos WHERE Id_prestamo = %s", (id_prestamo,))
            res = cursor.fetchone()
            total_abonado = float(res[0]) if res and res[0] else 0.0
            if total_abonado >= (float(monto_original) - 0.01):
                cursor.execute("UPDATE Prestamo SET Estado = 'Pagado' WHERE Id_prestamo = %s", (id_prestamo,))
                print(f"Prestamo {id_prestamo} liquidado.")
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

#---------------
#REPORTE
    
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

