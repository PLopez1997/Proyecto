import streamlit as st
import pandas as pd
from .config.conexion import obtener_conexion 

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
        st.info("Módulo de Reportes en construcción.")

# --- SUB-FUNCIONES ---

def gestionar_miembros():
    st.header("Gestión de Miembros del Grupo")
    tab1, tab2 = st.tabs(["Registrar Nuevo Miembro", "Ver Lista de Miembros"])

    # --- PESTAÑA 1: REGISTRO ---
    with tab1:
        st.subheader("Afiliación de Nuevo Miembro")
        with st.form("form_nuevo_miembro"):
            col1, col2 = st.columns(2)
            with col1:
                # Mantenemos inputs separados para mejor experiencia de usuario
                nombre = st.text_input("Nombre")
                apellido = st.text_input("Apellido")
                dui = st.text_input("DUI (Documento Único)")
            with col2:
                telefono = st.text_input("Teléfono")
                direccion = st.text_input("Dirección")
                
               # Definimos los roles claramente: 1:Pres, 2:Tes, 3:Miembro, 4:Sec
            rol_id = st.selectbox(
                "Asignar Rol", 
                options=[1, 2, 4, 3], # El orden aquí define el orden en la lista desplegable
                format_func=lambda x: {
                    1: "Presidente", 
                    2: "Tesorero", 
                    3: "Miembro", 
                        4: "Secretario"
                    }.get(x, "Desconocido"))
            
            submitted = st.form_submit_button("Guardar Miembro")
            
            if submitted:
                if nombre and apellido and dui:
                    # AQUI CONCATENAMOS NOMBRE Y APELLIDO
                    nombre_completo = f"{nombre} {apellido}"
                    guardar_miembro_bd(nombre_completo, dui, telefono, direccion, rol_id)
                else:
                    st.error("Por favor llene los campos obligatorios.")

    # --- PESTAÑA 2: LISTADO ---
    with tab2:
        st.subheader("Directorio de Miembros")
        listar_miembros()

# --- FUNCIONES SQL ---

def guardar_miembro_bd(nombre_completo, dui, telefono, direccion, rol_id):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id', 1) 
            
            # CAMBIOS REALIZADOS:
            # 1. Tabla: Miembro (singular)
            # 2. Columna `DUI/Identificación` con comillas invertidas (backticks) por tener el símbolo "/"
            # 3. Solo pasamos 'Nombre', ya no 'Apellido'
            query = """
                INSERT INTO Miembro (Nombre, `DUI/Identificación`, Telefono, Direccion, Rol, Id_grupo)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            valores = (nombre_completo, dui, telefono, direccion, rol_id, grupo_id)
            
            cursor.execute(query, valores)
            conn.commit()
            st.success(f"Miembro {nombre_completo} registrado exitosamente.")
        except Exception as e:
            st.error(f"Error al guardar en BD: {e}")
        finally:
            cursor.close()
            conn.close()

def listar_miembros():
    conn = obtener_conexion()
    if conn:
        try:
            # Usamos .get() por seguridad
            grupo_id = st.session_state.get('grupo_id')
            
            # CORRECCIÓN DE NOMBRES DE COLUMNAS AQUÍ:
            # Usamos Id_miembro, Rol y Id_grupo
            query = "SELECT Id_miembro, Nombre, `DUI/Identificación`, Telefono, Rol FROM Miembro WHERE Id_grupo = %s"
            
            df = pd.read_sql(query, conn, params=(grupo_id,))
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                st.markdown("---")
                
                # SECCIÓN DE ELIMINAR
                with st.expander("🗑️ Eliminar Miembro", expanded=False):
                    st.warning("⚠️ Cuidado: Esta acción no se puede deshacer.")
                    
                    # CORRECCIÓN AQUÍ TAMBIÉN:
                    # Python debe buscar 'Id_miembro' (tal como viene del SQL)
                    lista_miembros = {
                        row['Id_miembro']: f"{row['Nombre']} - {row['Rol']}" 
                        for index, row in df.iterrows()
                    }
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        id_a_eliminar = st.selectbox(
                            "Seleccione el miembro a eliminar:", 
                            options=lista_miembros.keys(),
                            format_func=lambda x: lista_miembros[x]
                        )
                    
                    with col2:
                        st.write("") 
                        st.write("") 
                        if st.button("Eliminar Permanentemente", type="primary"):
                            eliminar_miembro_bd(id_a_eliminar)
                            st.rerun()
                            
            else:
                st.info("No hay miembros registrados en este grupo aún.")
                
        except Exception as e:
            st.error(f"Error al cargar miembros: {e}")
        finally:
            conn.close()

def eliminar_miembro_bd(id_miembro):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            
            # CORRECCIÓN AQUÍ: Id_miembro
            query = "DELETE FROM Miembro WHERE Id_miembro = %s"
            cursor.execute(query, (id_miembro,))
            conn.commit()
            
            st.toast("✅ Miembro eliminado correctamente.")
            
        except Exception as e:
            if "1451" in str(e): 
                st.error("⛔ No puedes eliminar a este miembro porque ya tiene registros asociados.")
            else:
                st.error(f"Error al eliminar: {e}")
        finally:
            cursor.close()
            conn.close()




def gestionar_reuniones():
    st.header("Gestión Operativa de Reuniones")
    
    # AHORA TENEMOS 3 PESTAÑAS
    tab1, tab2, tab3 = st.tabs(["📅 1. Programar", "📝 2. Asistencia", "💰 3. Registrar Ahorros"])

    # --- PESTAÑA 1: CREAR (Igual que antes) ---
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

    # --- PESTAÑA 2: ASISTENCIA (Igual que antes) ---
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
            st.info("No hay reuniones creadas.")

    # --- PESTAÑA 3: AHORROS (NUEVO) ---
    with tab3:
        st.subheader("Registro de Ahorros por Reunión")
        
        reuniones_ahorro = obtener_reuniones_del_grupo()
        
        if reuniones_ahorro:
            # Seleccionamos la reunión donde está entrando el dinero
            reunion_ahorro_sel = st.selectbox("Seleccione Reunión:", options=reuniones_ahorro, format_func=lambda x: f"{x['Fecha']} - {x['tema']}", key="sel_ahorro")
            
            st.markdown("---")
            
            # Formulario para registrar ahorro INDIVIDUAL
            # (Hacerlo uno por uno es más seguro para manejar dinero)
            col_izq, col_der = st.columns(2)
            
            with col_izq:
                miembros = obtener_lista_miembros_simple()
                # Diccionario para buscar fácil
                dict_miembros = {m['Id_miembro']: m['Nombre'] for m in miembros}
                
                miembro_ahorrador = st.selectbox("Miembro que ahorra:", options=dict_miembros.keys(), format_func=lambda x: dict_miembros[x])
                
            with col_der:
                monto = st.number_input("Monto a Ahorrar ($)", min_value=0.0, step=0.01)
            
            if st.button("Registrar Ahorro", type="primary"):
                guardar_ahorro_bd(reunion_ahorro_sel['Id_reunion'], miembro_ahorrador, monto)
                
            # --- VISTA RÁPIDA DE LO AHORRADO EN ESTA REUNIÓN ---
            st.markdown("#### 📊 Resumen de esta reunión")
            ver_ahorros_reunion(reunion_ahorro_sel['Id_reunion'])
            
        else:
            st.info("Primero debe crear una reunión.")

# --- AGREGAR ESTAS FUNCIONES AL FINAL (SECCIÓN SQL) ---

def guardar_ahorro_bd(id_reunion, id_miembro, monto):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            # Insertamos el ahorro vinculándolo a la reunión
            query = "INSERT INTO Ahorro (Id_reunion, Id_miembro, Monto, Fecha) VALUES (%s, %s, %s, NOW())"
            cursor.execute(query, (id_reunion, id_miembro, monto))
            conn.commit()
            st.success(f"Ahorro de ${monto} registrado correctamente.")
        except Exception as e:
            st.error(f"Error al guardar ahorro: {e}")
        finally:
            conn.close()

def ver_ahorros_reunion(id_reunion):
    conn = obtener_conexion()
    if conn:
        try:
            # CORRECCIÓN:
            # 1. Aseguramos Id_ahorro con mayúscula.
            # 2. Si la columna fecha da error, prueba borrando ", a.Fecha" del SELECT.
            query = """
                SELECT m.Nombre, a.Monto, a.Fecha 
                FROM Ahorro a
                JOIN Miembro m ON a.Id_miembro = m.Id_miembro
                WHERE a.Id_reunion = %s
                ORDER BY a.Id_ahorro DESC
            """
            df = pd.read_sql(query, conn, params=(id_reunion,))
            
            if not df.empty:
                # Formateamos la columna Fecha para que se vea limpia (sin la hora)
                if 'Fecha' in df.columns:
                    df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
                
                st.dataframe(df, use_container_width=True)
                
                # Calculamos el total
                total = df['Monto'].sum()
                st.metric("Total Recaudado hoy", f"${total:,.2f}")
            else:
                st.info("Aún no hay ahorros registrados en esta sesión.")
        except Exception as e:
            # Esto nos mostrará el error REAL en la pantalla para poder arreglarlo
            st.error(f"Error SQL: {e}")
        finally:
            conn.close()

def crear_reunion_bd(fecha, tema):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id')
            
            # Insertamos en tabla Reunion (respetando 'tema' y 'Id_grupo')
            query = "INSERT INTO Reunion (Fecha, tema, Id_grupo) VALUES (%s, %s, %s)"
            cursor.execute(query, (fecha, tema, grupo_id))
            conn.commit()
            
            st.success(f"Reunión del {fecha} creada exitosamente.")
            st.rerun() # Recargar para que aparezca en la otra pestaña
        except Exception as e:
            st.error(f"Error al crear reunión: {e}")
        finally:
            conn.close()

def obtener_reuniones_del_grupo():
    conn = obtener_conexion()
    data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True) # Importante: dictionary=True
            grupo_id = st.session_state.get('grupo_id')
            
            # Ordenamos por fecha descendente (las más nuevas primero)
            query = "SELECT Id_reunion, Fecha, tema FROM Reunion WHERE Id_grupo = %s ORDER BY Fecha DESC"
            cursor.execute(query, (grupo_id,))
            data = cursor.fetchall()
        except Exception as e:
            st.error(f"Error al cargar reuniones: {e}")
        finally:
            conn.close()
    return data

def obtener_lista_miembros_simple():
    # Función auxiliar ligera solo para obtener ID y Nombres
    conn = obtener_conexion()
    data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            grupo_id = st.session_state.get('grupo_id')
            query = "SELECT Id_miembro, Nombre, `DUI/Identificación` FROM Miembro WHERE Id_grupo = %s"
            cursor.execute(query, (grupo_id,))
            data = cursor.fetchall()
        finally:
            conn.close()
    return data

def guardar_asistencia_bd(id_reunion, diccionario_asistencia):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Preparamos la query de inserción
            query = "INSERT INTO Asistencia (Id_reunion, Id_miembro, Estado) VALUES (%s, %s, %s)"
            
            # Convertimos el diccionario en una lista de tuplas para insertar masivamente
            valores = []
            for id_miembro, estado in diccionario_asistencia.items():
                valores.append((id_reunion, id_miembro, estado))
            
            # executemany es más eficiente para guardar varios registros a la vez
            cursor.executemany(query, valores)
            conn.commit()
            
            st.toast("✅ Asistencia guardada correctamente.")
        except Exception as e:
            # Si intentas guardar asistencia dos veces para la misma reunión, podría dar error duplicate
            st.error(f"Error al guardar asistencia (¿quizás ya la tomaste?): {e}")
        finally:
            conn.close()

#----------------------------------------------------
#PARTE 3 PESTAÑA 3 CAJA Y PRESTAMOS
#----------------------------------------------------


# --- AGREGAR ESTO EN TU MENU PRINCIPAL ---
# elif choice == "Caja y Préstamos":
#     gestionar_caja_prestamos()

# --- NUEVA FUNCIÓN PRINCIPAL ---

def gestionar_caja_prestamos():
    st.header("💰 Gestión Financiera: Caja y Créditos")
    
    # Calculamos el dinero disponible en tiempo real
    saldo_actual = calcular_saldo_disponible()
    
    # KPI Principal: Caja Disponible
    st.metric(label="💵 EFECTIVO DISPONIBLE EN CAJA", value=f"${saldo_actual:,.2f}")
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Nuevo Préstamo", "📥 Registrar Pago", "⚠️ Multas", "📜 Movimientos de Caja"])

    # --- PESTAÑA 1: SOLICITAR PRÉSTAMO ---
    with tab1:
        st.subheader("Otorgar Nuevo Préstamo")
        
        with st.form("form_prestamo"):
            col1, col2 = st.columns(2)
            with col1:
                miembros = obtener_lista_miembros_simple()
                dict_miembros = {m['Id_miembro']: m['Nombre'] for m in miembros}
                id_miembro = st.selectbox("Solicitante", options=dict_miembros.keys(), format_func=lambda x: dict_miembros[x])
                
                monto = st.number_input("Monto Solicitado ($)", min_value=0.0, step=5.0)
            
            with col2:
                # Interés mensual típico (ej. 5% o 10%)
                tasa = st.number_input("Tasa de Interés (%)", min_value=0.0, value=5.0, step=0.1)
                # Plazo (asumimos meses para simplificar, ajusta según tu regla)
                plazo = st.number_input("Plazo (meses)", min_value=1, value=6)
                
            fecha_inicio = st.date_input("Fecha de desembolso")
            
            # Cálculo informativo para el usuario
            interes_estimado = monto * (tasa / 100) * plazo
            total_pagar = monto + interes_estimado
            st.info(f"📝 Simulación: El miembro pagará ${interes_estimado:.2f} de interés. Total a devolver: ${total_pagar:.2f}")

            submitted = st.form_submit_button("Aprobar y Desembolsar")
            if submitted:
                if monto > saldo_actual:
                    st.error(f"⛔ Fondos insuficientes. Solo tienes ${saldo_actual} en caja.")
                elif monto <= 0:
                    st.error("El monto debe ser mayor a 0.")
                else:
                    crear_prestamo_bd(id_miembro, monto, tasa, plazo, fecha_inicio)

    # --- PESTAÑA 2: REGISTRAR PAGO ---
    with tab2:
        st.subheader("Cobro de Cuotas")
        
        # 1. Buscar préstamos ACTIVOS
        prestamos_activos = obtener_prestamos_activos()
        
        if prestamos_activos:
            prestamo_sel = st.selectbox(
                "Seleccione el Préstamo a abonar:", 
                options=prestamos_activos,
                format_func=lambda x: f"{x['Nombre_Miembro']} - Deuda Orig: ${x['Monto']} (Fecha: {x['Fecha_inicio']})"
            )
            
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            # Mostramos cuánto ha pagado hasta ahora (necesitaríamos una consulta extra, por ahora simple)
            c1.metric("Monto Original", f"${prestamo_sel['Monto']}")
            c2.metric("Tasa Interés", f"{prestamo_sel['Tasa_interes']}%")
            
            with st.form("form_pago"):
                col_cap, col_int = st.columns(2)
                with col_cap:
                    abono_capital = st.number_input("Abono a Capital ($)", min_value=0.0, step=1.0)
                with col_int:
                    pago_interes = st.number_input("Pago de Interés ($)", min_value=0.0, step=1.0)
                
                fecha_pago = st.date_input("Fecha de pago")
                
                if st.form_submit_button("Registrar Pago"):
                    if abono_capital == 0 and pago_interes == 0:
                        st.warning("Debe ingresar al menos un valor.")
                    else:
                        registrar_pago_bd(prestamo_sel['Id_prestamo'], abono_capital, pago_interes, fecha_pago, prestamo_sel['Id_grupo'])
        else:
            st.info("No hay préstamos activos pendientes de pago.")

    # --- PESTAÑA 3: MULTAS ---
    with tab3:
        st.subheader("Gestión de Multas y Mora")
        
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.markdown("#### 😡 Aplicar Nueva Multa")
            with st.form("form_multa"):
                miembro_multa = st.selectbox("Miembro", options=dict_miembros.keys(), format_func=lambda x: dict_miembros[x], key="sel_multa")
                monto_multa = st.number_input("Monto Multa ($)", min_value=1.0, step=0.5)
                motivo = st.text_input("Motivo (Ej. Llegada tarde, Falta injustificada)")
                
                # Opcional: Vincular a reunión si aplica
                
                if st.form_submit_button("Aplicar Multa"):
                    aplicar_multa_bd(miembro_multa, monto_multa, motivo)

        with col_m2:
            st.markdown("#### 📋 Multas Pendientes")
            listar_multas_pendientes()

    # --- PESTAÑA 4: HISTORIAL CAJA ---
    with tab4:
        st.subheader("Libro Diario de Caja")
        ver_movimientos_caja()

# ==========================================
# FUNCIONES SQL (Backend)
# ==========================================

def calcular_saldo_disponible():
    """
    Calcula: (Ahorros + Pagos Capital + Pagos Interes + Multas Pagadas) - (Prestamos Entregados - Egresos Varios)
    Nota: Usamos la tabla 'Caja' si registras todo ahí, o sumamos las tablas individuales.
    Para ser más exactos, sumaremos las tablas operativas.
    """
    conn = obtener_conexion()
    saldo = 0.0
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id')

            # 1. Sumar Ahorros
            cursor.execute("SELECT SUM(Monto) FROM Ahorro JOIN Miembro ON Ahorro.Id_miembro = Miembro.Id_miembro WHERE Miembro.Id_grupo = %s", (grupo_id,))
            res_ahorro = cursor.fetchone()[0] or 0.0

            # 2. Sumar Pagos (Capital + Interes) de préstamos de este grupo
            # (Requiere JOIN complejo, simplificamos asumiendo que el pago tiene fecha y logica)
            # Para simplificar y no hacer queries gigantes, usaremos la tabla CAJA si está bien llevada.
            # PERO, como estamos construyendo el sistema, lo mejor es sumar la tabla CAJA directamente.
            
            cursor.execute("SELECT Tipo_transaccion, Monto FROM Caja WHERE Id_grupo = %s", (grupo_id,))
            movimientos = cursor.fetchall()
            
            for tipo, monto in movimientos:
                if tipo == 'Ingreso':
                    saldo += monto
                elif tipo == 'Egreso':
                    saldo -= monto
            
            # Ajuste inicial: Si la caja está vacía, asumimos que el saldo es la suma de ahorros (si no se han registrado en caja aún)
            if not movimientos and res_ahorro > 0:
                saldo = res_ahorro 

        except Exception as e:
            st.error(f"Error calculando saldo: {e}")
        finally:
            conn.close()
    return saldo

def crear_prestamo_bd(id_miembro, monto, tasa, plazo, fecha):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id')
            
            # CORRECCIÓN DE NOMBRES AQUÍ TAMBIÉN:
            # Id_Miembro, Tasa_Interes, Fecha_Inicio
            query_prestamo = """
                INSERT INTO Prestamo (Id_Miembro, Monto, Tasa_Interes, Plazo, Fecha_Inicio, Estado) 
                VALUES (%s, %s, %s, %s, %s, 'Activo')
            """
            cursor.execute(query_prestamo, (id_miembro, monto, tasa, plazo, fecha))
            
            # Registrar salida de caja (Este se mantiene igual si tu tabla Caja no ha cambiado)
            query_caja = """
                INSERT INTO Caja (Id_grupo, Tipo_transaccion, Monto, Fecha, Detalle)
                VALUES (%s, 'Egreso', %s, %s, %s)
            """
            detalle = f"Préstamo a miembro ID {id_miembro}"
            cursor.execute(query_caja, (grupo_id, monto, fecha, detalle))
            
            conn.commit()
            st.success("✅ Préstamo otorgado y desembolsado de caja.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al crear préstamo: {e}")
        finally:
            conn.close()

def registrar_pago_bd(id_prestamo, capital, interes, fecha, id_grupo):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            
            # 1. Insertar en tabla Pago
            # Nota: Tu tabla Pago en la foto tiene Monto_capital y Monto_interes? 
            # Si no, ajusta los campos. Asumo que sí por lógica contable.
            query_pago = """
                INSERT INTO Pago (Id_prestamo, Monto_capital, Monto_interes, Fecha) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query_pago, (id_prestamo, capital, interes, fecha))
            
            # 2. Registrar el INGRESO en Caja
            total_recibido = capital + interes
            query_caja = """
                INSERT INTO Caja (Id_grupo, Tipo_transaccion, Monto, Fecha, Detalle)
                VALUES (%s, 'Ingreso', %s, %s, %s)
            """
            detalle = f"Pago Prestamo ID {id_prestamo} (C:${capital} I:${interes})"
            cursor.execute(query_caja, (id_grupo, total_recibido, fecha, detalle))
            
            # 3. Opcional: Verificar si el préstamo se saldó (requiere calcular saldos)
            # Por ahora lo dejamos activo.
            
            conn.commit()
            st.success(f"✅ Pago de ${total_recibido} registrado correctamente.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al registrar pago: {e}")
        finally:
            conn.close()

def obtener_prestamos_activos():
    conn = obtener_conexion()
    data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            grupo_id = st.session_state.get('grupo_id')
            
            # CORRECCIÓN DE NOMBRES SEGÚN TU IMAGEN:
            # p.Id_Prestamo (Mayúsculas P)
            # p.Tasa_Interes (Mayúsculas I)
            # p.Fecha_Inicio (Mayúsculas I)
            # p.Id_Miembro (Mayúsculas M en la tabla Prestamo)
            
            query = """
                SELECT p.Id_Prestamo, p.Monto, p.Tasa_Interes, p.Fecha_Inicio, 
                       m.Nombre as Nombre_Miembro, p.Id_Miembro, m.Id_grupo
                FROM Prestamo p
                JOIN Miembro m ON p.Id_Miembro = m.Id_miembro
                WHERE m.Id_grupo = %s AND p.Estado = 'Activo'
            """
            cursor.execute(query, (grupo_id,))
            data = cursor.fetchall()
        except Exception as e:
             st.error(f"Error cargando préstamos: {e}")
        finally:
            conn.close()
    return data

def aplicar_multa_bd(id_miembro, monto, motivo):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            # AJUSTE DE NOMBRES: Id_Miembro (con M mayúscula)
            query = "INSERT INTO Multa (Id_Miembro, Monto, Motivo, Estado) VALUES (%s, %s, %s, 'Pendiente')"
            cursor.execute(query, (id_miembro, monto, motivo))
            conn.commit()
            st.toast("Multa aplicada.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al aplicar multa: {e}")
        finally:
            conn.close()

def listar_multas_pendientes():
    conn = obtener_conexion()
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
                # Opcional: Botón para pagar multa
                st.dataframe(df, use_container_width=True)
                
                # Selector para pagar multas
                multa_a_pagar = st.selectbox("Seleccionar Multa para Pagar", options=df['Id_multa'], key="sel_pagar_multa")
                if st.button("Marcar como Pagada"):
                    pagar_multa_bd(multa_a_pagar)
            else:
                st.info("🎉 No hay multas pendientes.")
        except Exception as e:
            st.error(f"Error SQL (Verifica nombres de columnas en BD): {e}")
        finally:
            conn.close()

# --- Función extra necesaria para el botón de "Pagar" ---

def pagar_multa_bd(id_multa):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            # Actualizamos estado
            cursor.execute("UPDATE Multa SET Estado = 'Pagado' WHERE Id_multa = %s", (id_multa,))
            
            # Y registramos el ingreso en CAJA (importante para el saldo)
            grupo_id = st.session_state.get('grupo_id')
            # Recuperamos monto para la caja
            cursor.execute("SELECT Monto FROM Multa WHERE Id_Multa = %s", (id_multa,))
            monto = cursor.fetchone()[0]
            
            cursor.execute("INSERT INTO Caja (Id_grupo, Tipo_transaccion, Monto, Fecha, Detalle) VALUES (%s, 'Ingreso', %s, NOW(), 'Pago de Multa')", 
                           (grupo_id, monto))
            
            conn.commit()
            st.success("Multa pagada y registrada en caja.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()

def ver_movimientos_caja():
    conn = obtener_conexion()
    if conn:
        try:
            grupo_id = st.session_state.get('grupo_id')
            query = "SELECT Fecha, Tipo_transaccion, Monto, Detalle FROM Caja WHERE Id_grupo = %s ORDER BY Fecha DESC"
            df = pd.read_sql(query, conn, params=(grupo_id,))
            st.dataframe(df, use_container_width=True)
        finally:
            conn.close()


