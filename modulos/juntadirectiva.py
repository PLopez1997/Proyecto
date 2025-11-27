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
# SECCIÓN 3: CAJA Y PRÉSTAMOS (LÓGICA MEJORADA)
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

    # --- REGISTRAR PAGO (MEJORADO) ---
    with tab2:
        st.subheader("Cobro de Cuotas")
        # Esta función ahora trae el 'Saldo_Pendiente' calculado desde SQL
        prestamos = obtener_prestamos_activos() 
        
        if prestamos:
            # Dropdown inteligente con Saldo Restante
            prestamo_sel = st.selectbox(
                "Seleccione Préstamo:", 
                options=prestamos,
                format_func=lambda x: f"{x['Nombre_Miembro']} - Restan: ${x['Saldo_Pendiente']:,.2f} (Orig: ${x['Monto']})"
            )
            
            st.markdown("---")
            # Métricas visuales
            col1, col2, col3 = st.columns(3)
            col1.metric("Monto Original", f"${prestamo_sel['Monto']:,.2f}")
            col2.metric("Saldo Pendiente", f"${prestamo_sel['Saldo_Pendiente']:,.2f}", delta_color="inverse")
            col3.metric("Tasa Interés", f"{prestamo_sel['Interes']}%")

            st.info(f"💡 Para liquidar este préstamo se requiere un abono a capital de: **${prestamo_sel['Saldo_Pendiente']:,.2f}**")

            with st.form("form_pago"):
                c1, c2 = st.columns(2)
                
                # Input limitado al saldo restante para evitar sobrepagos
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
                        # Llamamos a la función que inserta y verifica si liquida
                        registrar_pago_bd(
                            id_prestamo=prestamo_sel['Id_prestamo'], 
                            capital=abono_capital, 
                            interes=pago_interes, 
                            fecha=fecha_pago_input, 
                            id_grupo=prestamo_sel['Id_grupo'],
                            monto_original=prestamo_sel['Monto'],
                            id_multa=0 # Default
                        )
                        
                        # Mensaje feedback usuario
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

 # --- PESTAÑA 3: MULTAS ---
    with tab3:
        st.subheader("Gestión de Multas")
        c1, c2 = st.columns(2)
        
        # Columna Izquierda: Crear Multa Manual (Lo que habías borrado)
        with c1:
            st.markdown("#### 😡 Multa Manual")
…                            st.error("El motivo es obligatorio.")
                else:
                    st.warning("No hay miembros registrados para multar.")

        # Columna Derecha: Ver y Pagar Multas Pendientes
        with c2:
            st.markdown("#### 📋 Pendientes de Pago")
            listar_multas_pendientes()


    # --- CAJA ---
    with tab4:
        st.subheader("Movimientos de Caja")
        ver_movimientos_caja()

# ==========================================
# FUNCIONES SQL (BACKEND)
# ==========================================

# ... (Las funciones de Miembros y Reuniones se mantienen igual, solo pondré las modificadas) ...
# Para ahorrar espacio en la respuesta, asumo que las funciones:
# guardar_miembro_bd, listar_miembros, eliminar_miembro_bd, obtener_lista_miembros_simple
# crear_reunion_bd, obtener_reuniones_del_grupo, guardar_asistencia_bd, guardar_ahorro_bd, ver_ahorros_reunion
# calcular_saldo_disponible, crear_prestamo_bd, aplicar_multa_bd, listar_multas_pendientes, pagar_multa_bd, ver_movimientos_caja
# ... SON LAS MISMAS QUE EN EL CÓDIGO ANTERIOR. 

# AQUI ESTAN LAS MODIFICACIONES CLAVE:

# --- 1. MODIFICADA PARA CALCULAR SALDO RESTANTE ---
def obtener_prestamos_activos():
    conn = obtener_conexion_safe()
    data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            grupo_id = st.session_state.get('grupo_id')
            
            # LEFT JOIN con la tabla PAGOS para sumar lo que se ha abonado a capital
            # COALESCE convierte NULL en 0 si no hay pagos aún.
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

# --- 2. MODIFICADA PARA CAMBIO DE ESTADO AUTOMÁTICO ---
def registrar_pago_bd(id_prestamo, capital, interes, fecha, id_grupo, monto_original, id_multa=0):
    conn = obtener_conexion_safe()
    if conn:
        try:
            cursor = conn.cursor()
            
            # A. Insertar el Pago (Usando Fecha_pago correcto)
            q_p = "INSERT INTO Pagos (Id_prestamo, Monto_capital, Monto_interes, Fecha_pago, Id_multa) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(q_p, (id_prestamo, capital, interes, fecha, id_multa))
            
            # B. Registrar Ingreso en Caja
            total = capital + interes
            q_c = "INSERT INTO Caja (Id_grupo, Tipo_transaccion, Monto, Fecha, Detalle) VALUES (%s, 'Ingreso', %s, %s, %s)"
            cursor.execute(q_c, (id_grupo, total, fecha, f"Pago Préstamo {id_prestamo}"))
            
            # C. VERIFICACIÓN DE LIQUIDACIÓN
            # Obtenemos la suma total de capital pagado para este préstamo hasta el momento
            cursor.execute("SELECT SUM(Monto_capital) FROM Pagos WHERE Id_prestamo = %s", (id_prestamo,))
            res = cursor.fetchone()
            total_abonado = float(res[0]) if res and res[0] else 0.0
            
            # Si lo abonado es mayor o igual al monto original (con pequeño margen de error flotante)
            if total_abonado >= (float(monto_original) - 0.01):
                cursor.execute("UPDATE Prestamo SET Estado = 'Pagado' WHERE Id_prestamo = %s", (id_prestamo,))
                print(f"Prestamo {id_prestamo} liquidado.")
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

# --- Funciones Auxiliares que necesitas que estén para que corra el script completo ---
# (Repito las necesarias para que el copy-paste funcione directo)

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

def listar_multas_pendientes():
    conn = obtener_conexion_safe()
    if conn:
        try:
            grupo_id = st.session_state.get('grupo_id')
            df = pd.read_sql("SELECT mu.Id_multa, m.Nombre, mu.Monto FROM Multa mu JOIN Miembro m ON mu.Id_miembro=m.Id_miembro WHERE m.Id_grupo=%s AND mu.Estado='Pendiente'", conn, params=(grupo_id,))
            if not df.empty: st.dataframe(df, use_container_width=True)
            else: st.info("Sin multas.")
        except: pass
        finally: conn.close()

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
