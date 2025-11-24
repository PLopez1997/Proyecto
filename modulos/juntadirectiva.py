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
        show_reports()

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
#----------------------------------------------------


def gestionar_caja_prestamos():
    st.header("💰 Gestión Financiera: Caja y Créditos")
    
    # Calculamos saldo
    saldo_actual = calcular_saldo_disponible()
    st.metric(label="💵 EFECTIVO DISPONIBLE EN CAJA", value=f"${saldo_actual:,.2f}")
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Nuevo Préstamo", "📥 Registrar Pago", "⚠️ Multas", "📜 Movimientos de Caja"])

    # --- PESTAÑA 1: NUEVO PRÉSTAMO ---
    with tab1:
        st.subheader("Otorgar Nuevo Préstamo")
        with st.form("form_prestamo"):
            col1, col2 = st.columns(2)
            with col1:
                miembros = obtener_lista_miembros_simple()
                # Ajuste: Id_miembro
                dict_miembros = {m['Id_miembro']: m['Nombre'] for m in miembros}
                id_miembro = st.selectbox("Solicitante", options=dict_miembros.keys(), format_func=lambda x: dict_miembros[x])
                monto = st.number_input("Monto Solicitado ($)", min_value=0.0, step=5.0)
            with col2:
                tasa = st.number_input("Tasa de Interés (%)", min_value=0.0, value=5.0)
                plazo = st.number_input("Plazo (meses)", min_value=1, value=6)
                
            fecha_inicio = st.date_input("Fecha de desembolso")
            
            # Simulación
            interes_est = monto * (tasa / 100) * plazo
            st.info(f"Total a pagar estimado: ${monto + interes_est:.2f}")

            if st.form_submit_button("Aprobar y Desembolsar"):
                if monto > saldo_actual:
                    st.error(f"⛔ Fondos insuficientes (${saldo_actual}).")
                elif monto <= 0:
                    st.error("El monto debe ser positivo.")
                else:
                    crear_prestamo_bd(id_miembro, monto, tasa, plazo, fecha_inicio)

    # --- PESTAÑA 2: REGISTRAR PAGO ---
    with tab2:
        st.subheader("Cobro de Cuotas")
        prestamos = obtener_prestamos_activos()
        
        if prestamos:
            # Ajuste: Id_prestamo
            prestamo_sel = st.selectbox(
                "Seleccione Préstamo:", 
                options=prestamos,
                format_func=lambda x: f"{x['Nombre_Miembro']} - ${x['Monto']} (Fecha: {x['Fecha_inicio']})"
            )
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            c1.metric("Monto Original", f"${prestamo_sel['Monto']}")
            c2.metric("Tasa Interés", f"{prestamo_sel['Tasa_interes']}%")
            
            with st.form("form_pago"):
                col_cap, col_int = st.columns(2)
                with col_cap:
                    abono_capital = st.number_input("Abono a Capital ($)", min_value=0.0)
                with col_int:
                    pago_interes = st.number_input("Pago de Interés ($)", min_value=0.0)
                
                fecha_pago = st.date_input("Fecha de pago")
                
                if st.form_submit_button("Registrar Pago"):
                    # Ajuste: Id_prestamo y Id_grupo
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
                # Ajuste: Id_miembro
                miembro_m = st.selectbox("Miembro", options=dict_miembros.keys(), format_func=lambda x: dict_miembros[x])
                monto_m = st.number_input("Monto ($)", min_value=0.50, step=0.25)
                motivo_m = st.text_input("Motivo", "Mora / Otros")
                
                if st.form_submit_button("Aplicar Multa"):
                    aplicar_multa_bd(miembro_m, monto_m, motivo_m)

        with col_m2:
            st.markdown("#### 📋 Pendientes de Pago")
            listar_multas_pendientes()

    # --- PESTAÑA 4: CAJA ---
    with tab4:
        st.subheader("Movimientos de Caja")
        ver_movimientos_caja()


# FUNCIONES SQL CORREGIDAS (Formato Id_cosa)


def calcular_saldo_disponible():
    conn = obtener_conexion()
    saldo = 0.0
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id')

            # 1. Sumar Ahorros (Tabla Ahorro, Columna Id_miembro)
            cursor.execute("""
                SELECT SUM(a.Monto) FROM Ahorro a 
                JOIN Miembro m ON a.Id_miembro = m.Id_miembro 
                WHERE m.Id_grupo = %s
            """, (grupo_id,))
            res_ahorro = cursor.fetchone()[0] or 0.0

            # 2. Sumar Caja (Tabla Caja, Columna Id_grupo)
            cursor.execute("SELECT Tipo_transaccion, Monto FROM Caja WHERE Id_grupo = %s", (grupo_id,))
            movimientos = cursor.fetchall()
            
            for tipo, monto in movimientos:
                if tipo == 'Ingreso':
                    saldo += monto
                elif tipo == 'Egreso':
                    saldo -= monto
            
            if not movimientos and res_ahorro > 0:
                saldo = res_ahorro 

        except Exception as e:
            st.error(f"Error saldo: {e}")
        finally:
            conn.close()
    return saldo

def crear_prestamo_bd(id_miembro, monto, tasa, plazo, fecha):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id')
            
            # FORMATO Id_cosa: Id_miembro, Tasa_interes, Fecha_inicio
            query_p = """
                INSERT INTO Prestamo (Id_miembro, Monto, Tasa_interes, Plazo, Fecha_inicio, Estado) 
                VALUES (%s, %s, %s, %s, %s, 'Activo')
            """
            cursor.execute(query_p, (id_miembro, monto, tasa, plazo, fecha))
            
            # Tabla Caja: Id_grupo
            query_c = "INSERT INTO Caja (Id_grupo, Tipo_transaccion, Monto, Fecha, Detalle) VALUES (%s, 'Egreso', %s, %s, %s)"
            cursor.execute(query_c, (grupo_id, monto, fecha, f"Préstamo a ID {id_miembro}"))
            
            conn.commit()
            st.success("✅ Préstamo creado.")
            st.rerun()
        except Exception as e:
            st.error(f"Error crear préstamo: {e}")
        finally:
            conn.close()

def registrar_pago_bd(id_prestamo, capital, interes, fecha, id_grupo):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            
            # FORMATO Id_cosa: Id_prestamo, Monto_capital, Monto_interes
            query_p = "INSERT INTO Pago (Id_prestamo, Monto_capital, Monto_interes, Fecha) VALUES (%s, %s, %s, %s)"
            cursor.execute(query_p, (id_prestamo, capital, interes, fecha))
            
            # Tabla Caja: Id_grupo
            total = capital + interes
            query_c = "INSERT INTO Caja (Id_grupo, Tipo_transaccion, Monto, Fecha, Detalle) VALUES (%s, 'Ingreso', %s, %s, %s)"
            cursor.execute(query_c, (id_grupo, total, fecha, f"Pago Préstamo ID {id_prestamo}"))
            
            conn.commit()
            st.success("✅ Pago registrado.")
            st.rerun()
        except Exception as e:
            st.error(f"Error pago: {e}")
        finally:
            conn.close()

def obtener_prestamos_activos():
    conn = obtener_conexion()
    data = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            grupo_id = st.session_state.get('grupo_id')
            
            # FORMATO Id_cosa: Id_prestamo, Tasa_interes, Fecha_inicio, Id_miembro
            query = """
                SELECT p.Id_prestamo, p.Monto, p.Tasa_interes, p.Fecha_inicio, 
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
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            # FORMATO Id_cosa: Id_miembro
            query = "INSERT INTO Multa (Id_miembro, Monto, Motivo, Estado) VALUES (%s, %s, %s, 'Pendiente')"
            cursor.execute(query, (id_miembro, monto, motivo))
            conn.commit()
            st.toast("Multa aplicada.")
        except Exception as e:
            st.error(f"Error multa: {e}")
        finally:
            conn.close()

def listar_multas_pendientes():
    conn = obtener_conexion()
    if conn:
        try:
            grupo_id = st.session_state.get('grupo_id')
            
            # FORMATO Id_cosa: Id_multa, Id_miembro
            query = """
                SELECT mu.Id_multa, m.Nombre, mu.Monto, mu.Motivo 
                FROM Multa mu
                JOIN Miembro m ON mu.Id_miembro = m.Id_miembro
                WHERE m.Id_grupo = %s AND mu.Estado = 'Pendiente'
            """
            df = pd.read_sql(query, conn, params=(grupo_id,))
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                # Selector usando Id_multa
                id_pagar = st.selectbox("Pagar Multa ID:", df['Id_multa'])
                if st.button("Marcar Pagada"):
                    pagar_multa_bd(id_pagar)
            else:
                st.info("No hay multas pendientes.")
        except Exception as e:
            st.error(f"Error listando multas: {e}")
        finally:
            conn.close()

def pagar_multa_bd(id_multa):
    conn = obtener_conexion()
    if conn:
        try:
            cursor = conn.cursor()
            grupo_id = st.session_state.get('grupo_id')
            
            # 1. Obtener monto antes de actualizar
            # FORMATO Id_cosa: Id_multa
            cursor.execute("SELECT Monto FROM Multa WHERE Id_multa = %s", (id_multa,))
            row = cursor.fetchone()
            if row:
                monto = row[0]
                
                # 2. Actualizar estado
                cursor.execute("UPDATE Multa SET Estado = 'Pagado' WHERE Id_multa = %s", (id_multa,))
                
                # 3. Ingreso a Caja
                cursor.execute("INSERT INTO Caja (Id_grupo, Tipo_transaccion, Monto, Fecha, Detalle) VALUES (%s, 'Ingreso', %s, NOW(), 'Pago Multa')", (grupo_id, monto))
                
                conn.commit()
                st.success("Multa pagada.")
                st.rerun()
        except Exception as e:
            st.error(f"Error pagando multa: {e}")
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

#Asistencia

def guardar_asistencia_bd(id_reunion, diccionario_asistencia):
    conn = obtener_conexion()
    
    # --- CONFIGURACIÓN DE MULTAS AUTOMÁTICAS ---
    MONTO_AUSENCIA = 1.00  # Costo por inasistencia
    MONTO_EXCUSADO = 0.50  # Costo por excusa (si aplica)
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # 1. Insertar Asistencia (Id_reunion, Id_miembro)
            query_asist = "INSERT INTO Asistencia (Id_reunion, Id_miembro, Estado) VALUES (%s, %s, %s)"
            
            valores_asistencia = []
            multas_automaticas = []
            
            for id_miembro, estado in diccionario_asistencia.items():
                # Preparamos dato para tabla Asistencia
                valores_asistencia.append((id_reunion, id_miembro, estado))
                
                # LÓGICA DE MULTA AUTOMÁTICA 
                if estado == "Ausente":
                    # (Id_miembro, Monto, Motivo, Estado)
                    multas_automaticas.append((id_miembro, MONTO_AUSENCIA, "Inasistencia Automática", "Pendiente"))
                    
                elif estado == "Excusado":
                    multas_automaticas.append((id_miembro, MONTO_EXCUSADO, "Ausencia Justificada", "Pendiente"))
            
            # Ejecutamos inserción masiva de asistencias
            cursor.executemany(query_asist, valores_asistencia)
            
            # 2. Crear Multas Automáticas (si existen)
            if multas_automaticas:
                query_multa = "INSERT INTO Multa (Id_miembro, Monto, Motivo, Estado) VALUES (%s, %s, %s, %s)"
                cursor.executemany(query_multa, multas_automaticas)
            
            conn.commit()
            
            # Mensaje informativo
            msg = "✅ Asistencia guardada."
            if multas_automaticas:
                msg += f" Se generaron {len(multas_automaticas)} multas automáticas."
            st.toast(msg)
            
        except Exception as e:
            if "1062" in str(e):
                st.error("Error: Ya se tomó asistencia para esta reunión.")
            else:
                st.error(f"Error al guardar asistencia: {e}")
        finally:
            conn.close()

def show_reports():
    st.header("📊 Reportes Consolidados")
    
    conn = obtener_conexion()
    if not conn:
        st.error("No hay conexión con la base de datos.")
        return

    try:
        grupo_id = st.session_state.get('grupo_id')
        
        # 1. CONSULTA DIRECTA (Ya sabemos qué columnas existen)
        # Traemos todos los movimientos de ESTE grupo ordenados por fecha
        query = """
            SELECT Fecha, Detalle, Tipo_transaccion, Monto 
            FROM Caja 
            WHERE Id_grupo = %s 
            ORDER BY Fecha DESC
        """
        df = pd.read_sql(query, conn, params=(grupo_id,))

        if not df.empty:
            # --- SECCIÓN 1: TARJETAS DE INDICADORES (KPIs) ---
            # Pandas hace el cálculo matemático rápido aquí
            total_ingresos = df[df['Tipo_transaccion'] == 'Ingreso']['Monto'].sum()
            total_egresos = df[df['Tipo_transaccion'] == 'Egreso']['Monto'].sum()
            saldo_actual = total_ingresos - total_egresos

            # Mostramos los números grandes arriba
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Ingresos Históricos", f"${total_ingresos:,.2f}")
            col2.metric("Total Egresos Históricos", f"${total_egresos:,.2f}")
            col3.metric("💰 SALDO ACTUAL EN CAJA", f"${saldo_actual:,.2f}", delta="Disponible")

            st.markdown("---")

            # --- SECCIÓN 2: TABLA DETALLADA ---
            st.subheader("📜 Libro Diario")
            
            # Formateamos la fecha para quitar la hora si molesta
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha']).dt.date
            
            # Coloreamos visualmente: Ingresos positivos, Egresos negativos (solo para gráfico/vista)
            df['Flujo'] = df.apply(lambda x: x['Monto'] if x['Tipo_transaccion'] == 'Ingreso' else -x['Monto'], axis=1)
            
            # Mostramos la tabla limpia (sin la columna de cálculo 'Flujo')
            st.dataframe(
                df[['Fecha', 'Detalle', 'Tipo_transaccion', 'Monto']], 
                use_container_width=True
            )

            # --- SECCIÓN 3: GRÁFICO VISUAL ---
            st.subheader("Tendencia de Movimientos")
            st.bar_chart(df, x="Fecha", y="Flujo", color="Tipo_transaccion")
            
        else:
            st.info("📂 No hay movimientos registrados en la caja de este grupo todavía.")
            st.write("Vaya a la sección 'Caja y Préstamos' o 'Reuniones' para registrar transacciones.")

    except Exception as e:
        st.error(f"Error cargando reportes: {e}")
    finally:
        conn.close()

