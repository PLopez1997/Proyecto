# ==============================================================================
# ARCHIVO: distrito.py
# DESCRIPCIÓN: Entorno de visualización (solo lectura) para Promotoras.
# Muestra datos filtrados en cascada: Distrito -> Grupo -> Miembro -> Finanzas.
# ==============================================================================

import streamlit as st
import pandas as pd

# --- IMPORTACIÓN SEGURA DE LA CONEXIÓN ---
# Intenta varias rutas para encontrar el archivo de conexión
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
# SECCIÓN 1: FUNCIONES AUXILIARES DE CONSULTA SQL (BACKEND)
# ==============================================================================

def obtener_info_distrito(id_distrito):
    """Obtiene los datos generales del distrito."""
    conn = obtener_conexion() # Paréntesis corregidos: () es vital para ejecutar la función
    data = None
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            # Asegúrate que los nombres de columnas coincidan con tu BD
            query = "SELECT * FROM Distrito WHERE id_distrito = %s"
            cursor.execute(query, (id_distrito,))
            data = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception as e:
            st.error(f"Error BD (Distrito): {e}")
    return data

def obtener_grupos_del_distrito_df(id_distrito):
    """Devuelve un DataFrame con los grupos de UN distrito específico."""
    conn = obtener_conexion()
    
    # Creamos un DF vacío con estructura por defecto para evitar errores si falla la consulta
    df = pd.DataFrame(columns=['id_grupo', 'nombre_grupo', 'ubicacion_grupo', 'fecha_creacion'])
    
    if conn:
        try:
            # Usamos ALIAS (AS) para que Python reciba los nombres estandarizados
            # Ajusta 'Nombre', 'Ubicacion' si en tu BD se llaman diferente
            query = """
                SELECT Id_grupo AS id_grupo, Nombre AS nombre_grupo, Fecha_inicio AS fecha_creacion 
                FROM Grupo 
                WHERE Id_distrito = %s
            """
            df_resultado = pd.read_sql(query, conn, params=(id_distrito,))
            if not df_resultado.empty:
                df = df_resultado
            
            conn.close()
        except Exception as e:
            st.error(f"Error BD (Grupos): {e}")
    return df

def obtener_miembros_del_grupo_df(id_grupo):
    """Devuelve un DataFrame con los miembros de UN grupo específico."""
    conn = obtener_conexion()
    
    # Estructura vacía por defecto
    df = pd.DataFrame(columns=['id_miembro', 'nombre_completo', 'dni_miembro'])
    
    if conn:
        try:
            # Concatenamos nombre para mostrarlo mejor en el selector
            query = """
                SELECT Id_miembro AS id_miembro, Nombre AS nombre_completo, 
                       Direccion, Telefono, Dni AS dni_miembro, Fecha_ingreso
                FROM Miembro 
                WHERE Id_grupo = %s
            """
            df_resultado = pd.read_sql(query, conn, params=(id_grupo,))
            if not df_resultado.empty:
                df = df_resultado
            
            conn.close()
        except Exception as e:
            st.error(f"Error BD (Miembros): {e}")
    return df

# --- Funciones privadas para detalles financieros ---

def _ejecutar_consulta_df(query, parametro_id):
    """Función genérica privada para ejecutar consultas y devolver DataFrames de forma segura"""
    conn = obtener_conexion()
    df = pd.DataFrame() # DF vacío por defecto
    if conn:
        try:
            df = pd.read_sql(query, conn, params=(parametro_id,))
            conn.close()
        except Exception as e:
            # No mostramos error rojo en pantalla para no ensuciar la interfaz
            print(f"Error consulta detalle: {e}")
    return df

def obtener_prestamos_miembro(id_miembro):
    sql = """SELECT Id_prestamo, Monto AS monto_prestamo, Tasa_interes, Plazo AS plazo_meses, 
             Fecha_inicio, Estado AS estado_prestamo 
             FROM Prestamo WHERE Id_miembro = %s"""
    return _ejecutar_consulta_df(sql, id_miembro)

def obtener_ahorros_miembro(id_miembro):
    sql = """SELECT Id_ahorro, Monto AS monto_ahorro, Fecha AS fecha_ahorro, Tipo_ahorro 
             FROM Ahorro WHERE Id_miembro = %s"""
    return _ejecutar_consulta_df(sql, id_miembro)

def obtener_multas_miembro(id_miembro):
    sql = """SELECT Id_multa, Monto AS monto_multa, Fecha AS fecha_multa, Motivo AS motivo_multa, Estado AS estado_multa 
             FROM Multa WHERE Id_miembro = %s"""
    return _ejecutar_consulta_df(sql, id_miembro)

def obtener_pagos_miembro(id_miembro):
    # Ajusta 'Monto_capital' si tu columna se llama diferente en la tabla Pago
    sql = """
            SELECT P.Id_pago, P.Monto_capital, P.Fecha_pago, Pr.Id_prestamo
            FROM Pago P
            INNER JOIN Prestamo Pr ON P.Id_prestamo = Pr.Id_prestamo
            WHERE Pr.Id_miembro = %s
          """
    return _ejecutar_consulta_df(sql, id_miembro)


# ==============================================================================
# SECCIÓN 2: INTERFAZ GRÁFICA (FRONTEND con Streamlit)
# ==============================================================================

def app():
    # -----------------------------------------------------------
    # 1. Validación de Seguridad
    # -----------------------------------------------------------
    if 'id_distrito_actual' not in st.session_state or st.session_state['id_distrito_actual'] is None:
        st.warning("⚠️ No se ha detectado un distrito. Por favor inicie sesión nuevamente.")
        return # Salimos suavemente sin error rojo

    id_distrito_sesion = st.session_state['id_distrito_actual']

    # -----------------------------------------------------------
    # 2. Header e Información del Distrito
    # -----------------------------------------------------------
    info_distrito = obtener_info_distrito(id_distrito_sesion)

    st.title("🏡 Entorno de Promotora")

    if info_distrito:
        col1, col2, col3 = st.columns(3)
        # Usamos .get() para evitar errores si la columna se llama distinto
        col1.metric("Distrito", info_distrito.get('nombre_distrito', 'S/D'))
        col2.metric("Ubicación", info_distrito.get('ubicacion_distrito', 'S/D'))
        col3.metric("Coordinador", info_distrito.get('coordinador_distrito', 'S/D'))
        st.divider()
    else:
        # Mensaje discreto si falla la carga del distrito pero queremos seguir
        st.caption("Cargando información del distrito...")

    st.subheader("Navegación de Grupos y Miembros")

    # -----------------------------------------------------------
    # 3. Selector de GRUPOS (Nivel 1)
    # -----------------------------------------------------------
    df_grupos = obtener_grupos_del_distrito_df(id_distrito_sesion)

    if df_grupos.empty:
        st.info(f"No hay grupos registrados en este distrito todavía.")
        return

    # Diccionario seguro: { "Nombre": ID }
    try:
        grupos_dict = dict(zip(df_grupos['nombre_grupo'], df_grupos['id_grupo']))
        grupo_seleccionado_nombre = st.selectbox("📂 Paso 1: Seleccione un Grupo", options=grupos_dict.keys())
    except KeyError:
        st.error("Error en las columnas de la tabla Grupo. Verifique que existan 'Nombre' e 'Id_grupo' (o sus alias).")
        st.dataframe(df_grupos) # Muestra qué llegó para depurar
        return

    if grupo_seleccionado_nombre:
        id_grupo_seleccionado = grupos_dict[grupo_seleccionado_nombre]

        with st.expander(f"Ver lista de todos los grupos"):
             st.dataframe(df_grupos, hide_index=True, use_container_width=True)

        # -----------------------------------------------------------
        # 4. Selector de MIEMBROS (Nivel 2)
        # -----------------------------------------------------------
        st.markdown("---")
        df_miembros = obtener_miembros_del_grupo_df(id_grupo_seleccionado)

        if df_miembros.empty:
             st.warning(f"El grupo '{grupo_seleccionado_nombre}' aún no tiene miembros registrados.")
             return # Detenemos aquí para no mostrar errores abajo

        # Diccionario seguro
        try:
            # Aseguramos que DNI sea string para evitar errores al concatenar
            lista_nombres_visual = df_miembros['nombre_completo'] + " (DNI: " + df_miembros['dni_miembro'].astype(str) + ")"
            miembros_dict = dict(zip(lista_nombres_visual, df_miembros['id_miembro']))
            miembro_seleccionado_nombre = st.selectbox("👤 Paso 2: Seleccione un Miembro del grupo", options=miembros_dict.keys())
        except KeyError:
             st.error("Error en columnas de Miembro. Verifique 'Nombre' y 'Dni'.")
             st.dataframe(df_miembros)
             return

        if miembro_seleccionado_nombre:
            id_miembro_seleccionado = miembros_dict[miembro_seleccionado_nombre]

            # -----------------------------------------------------------
            # 5. Vista de Detalles Financieros (Nivel 3)
            # -----------------------------------------------------------
            st.markdown("---")
            st.header(f"Detalles de: {miembro_seleccionado_nombre.split(' (')[0]}")

            tab1, tab2, tab3, tab4 = st.tabs(["💰 Préstamos", "🐷 Ahorros", "🧾 Pagos Realizados", "⚠️ Multas"])

            with tab1:
                df_prestamos = obtener_prestamos_miembro(id_miembro_seleccionado)
                if df_prestamos.empty: st.info("Sin préstamos registrados.")
                else: st.dataframe(df_prestamos, hide_index=True, use_container_width=True)

            with tab2:
                df_ahorros = obtener_ahorros_miembro(id_miembro_seleccionado)
                if df_ahorros.empty: st.info("Sin ahorros registrados.")
                else:
                    # Protección contra error de suma en columna inexistente
                    if 'monto_ahorro' in df_ahorros.columns:
                        total = df_ahorros['monto_ahorro'].sum()
                        st.metric("Total Ahorrado", f"${total:,.2f}")
                    st.dataframe(df_ahorros, hide_index=True, use_container_width=True)

            with tab3:
                df_pagos = obtener_pagos_miembro(id_miembro_seleccionado)
                if df_pagos.empty: st.info("Sin registros de pagos.")
                else: st.dataframe(df_pagos, hide_index=True, use_container_width=True)

            with tab4:
                df_multas = obtener_multas_miembro(id_miembro_seleccionado)
                if df_multas.empty: st.success("Sin multas.")
                else: st.dataframe(df_multas, hide_index=True, use_container_width=True)

# Solo para pruebas locales
if __name__ == "__main__":
    st.session_state['id_distrito_actual'] = 1
    st.set_page_config(layout="wide")
    app()
