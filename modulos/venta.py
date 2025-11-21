# modulos/venta.py
import streamlit as st
def mostrar_venta():
 # Aquí se muestra "Hola Mundo"
 st.title("Administrador")
 st.write("Este es el entorno del administrador")
import streamlit as st
from modulos.config.conexion import obtener_conexion
import pandas as pd

# ============================================
# PANEL DEL ADMINISTRADOR
# ============================================

def administrador_page():
    st.title("Panel de Control - Administrador")

    tabs = st.tabs(["📍 Distritos (Grupos)", "👤 Registrar Usuarios"])

    with tabs[0]:
        panel_grupos()

    with tabs[1]:
        panel_usuarios()


# ============================================
# SECCIÓN 1: GESTIÓN DE GRUPOS
# ============================================

def panel_grupos():
    st.subheader("📌 Gestión de Distritos (Tabla: grupos)")

    con = obtener_conexion()
    cursor = con.cursor()

    # Mostrar datos existentes
    cursor.execute("SELECT * FROM grupos")
    data = cursor.fetchall()
    columnas = [i[0] for i in cursor.description]

    df = pd.DataFrame(data, columns=columnas)
    st.dataframe(df, use_container_width=True)

    st.divider()
    st.subheader("➕ Agregar nuevo distrito")

    nombre = st.text_input("Nombre del distrito")
    fecha_inicio = st.date_input("Fecha de inicio")
    id_ciclo = st.number_input("ID Ciclo", min_value=1, step=1)
    tasa_interes = st.number_input("Tasa de interés (%)")
    tipo_multa = st.text_input("Tipo de multa")
    regla_interna = st.text_area("Regla interna")

    if st.button("Registrar nuevo distrito"):
        query = """
            INSERT INTO grupos (Nombre, Fecha_inicio, Id_ciclo, Tasa_interes, Tipo_multa, Regla_interna)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (nombre, fecha_inicio, id_ciclo, tasa_interes, tipo_multa, regla_interna))
        con.commit()
        st.success("Distrito registrado correctamente.")
        st.rerun()

    st.divider()
    st.subheader("✏️ Editar Distrito Existente")

    id_editar = st.selectbox("Selecciona un ID a editar", df["Id_cliente"] if "Id_cliente" in df else [])

    if id_editar:
        nuevo_nombre = st.text_input("Nuevo nombre")
        nuevo_tasa = st.number_input("Nueva tasa de interés", min_value=0.0)
        nuevo_multa = st.text_input("Nuevo tipo de multa")

        if st.button("Actualizar información"):
            query = """
                UPDATE grupos SET Nombre=%s, Tasa_interes=%s, Tipo_multa=%s
                WHERE Id_cliente=%s
            """
            cursor.execute(query, (nuevo_nombre, nuevo_tasa, nuevo_multa, id_editar))
            con.commit()
            st.success("Distrito actualizado.")
            st.rerun()

    con.close()


# ============================================
# SECCIÓN 2: REGISTRO DE USUARIOS
# ============================================

def panel_usuarios():
    st.subheader("👤 Registrar nuevo usuario")

    usuario = st.text_input("Usuario")
    contraseña = st.text_input("Contraseña", type="password")
    roles = ["administrador", "promotora", "miembro", "junta directiva"]
    rol = st.selectbox("Rol", roles)

    if st.button("Registrar usuario"):
        con = obtener_conexion()
        cursor = con.cursor()

        query = """
            INSERT INTO login (Usuario, Contraseña, Rol)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (usuario, contraseña, rol))
        con.commit()
        con.close()

        st.success("Usuario registrado correctamente.")
        st.rerun()
