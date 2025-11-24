import streamlit as st
import pandas as pd
import hashlib
from modulos.config.conexion import obtener_conexion

def administrador_page():
   

# ======================================================
#                  HELPERS
# ======================================================

def table_columns(conn, table_name):
    """Devuelve las columnas reales de una tabla, o lista vacía."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        cols = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return cols
    except Exception:
        return []


def pick_column(cols, candidates):
    """Retorna la primera coincidencia entre columnas reales y posibles nombres."""
    for c in candidates:
        if c in cols:
            return c
    return None


# ======================================================
#              LECTURA FLEXIBLE DE REFERENCIAS
# ======================================================

def fetch_referencia_data():
    conn = obtener_conexion()
    if not conn:
        st.warning("No hay conexión a BD; usando datos simulados.")
        return {
            "distritos": pd.DataFrame({"Id_distrito": [], "Nombre": []}),
            "ciclos": pd.DataFrame({"Id_ciclo": [], "Nombre": []}),
            "grupos": pd.DataFrame({"Id_grupo": [], "Nombre": []})
        }

    try:
        # Detectar tablas reales
        distrito_table = next((t for t in ["Distrito", "distrito", "Distritos", "distritos"] if table_columns(conn, t)), None)
        ciclo_table = next((t for t in ["Ciclo", "ciclo", "Ciclos", "ciclos"] if table_columns(conn, t)), None)
        grupo_table = next((t for t in ["Grupo", "grupo", "Grupos", "grupos"] if table_columns(conn, t)), None)

        ref = {}

        # ------------------ DISTRITOS ------------------
        if distrito_table:
            cols = table_columns(conn, distrito_table)
            id_col = pick_column(cols, ["Id_distrito", "id_distrito", "Id", "Id_distr"])
            label_col = pick_column(cols, ["Nombre", "nombre", "Descripcion", "descripcion", "Label", "label"])

            if id_col and label_col:
                ref["distritos"] = pd.read_sql(
                    f"SELECT `{id_col}` AS Id_distrito, `{label_col}` AS Nombre FROM `{distrito_table}`",
                    conn
                )
            elif id_col:
                ref["distritos"] = pd.read_sql(f"SELECT `{id_col}` AS Id_distrito FROM `{distrito_table}`", conn)
                ref["distritos"]["Nombre"] = ref["distritos"]["Id_distrito"].astype(str)
            else:
                ref["distritos"] = pd.DataFrame({"Id_distrito": [], "Nombre": []})
        else:
            ref["distritos"] = pd.DataFrame({"Id_distrito": [], "Nombre": []})

        # ------------------ CICLOS ------------------
        if ciclo_table:
            cols = table_columns(conn, ciclo_table)
            id_col = pick_column(cols, ["Id_ciclo", "id_ciclo", "Id"])
            label_col = pick_column(cols, ["Nombre", "nombre", "Descripcion", "descripcion", "Periodo", "Ciclo"])

            if id_col and label_col:
                ref["ciclos"] = pd.read_sql(
                    f"SELECT `{id_col}` AS Id_ciclo, `{label_col}` AS Nombre FROM `{ciclo_table}`",
                    conn
                )
            elif id_col:
                ref["ciclos"] = pd.read_sql(
                    f"SELECT `{id_col}` AS Id_ciclo FROM `{ciclo_table}`",
                    conn
                )
                ref["ciclos"]["Nombre"] = "Ciclo " + ref["ciclos"]["Id_ciclo"].astype(str)
            else:
                ref["ciclos"] = pd.DataFrame({"Id_ciclo": [], "Nombre": []})
        else:
            ref["ciclos"] = pd.DataFrame({"Id_ciclo": [], "Nombre": []})

        # ------------------ GRUPOS ------------------
        if grupo_table:
            cols = table_columns(conn, grupo_table)
            id_col = pick_column(cols, ["Id_grupo", "id_grupo", "Id"])
            label_col = pick_column(cols, ["Nombre", "nombre", "Descripcion", "descripcion", "Grupo"])

            # --- CREACIÓN DE GRUPO ---
            st.subheader("➕ Crear nuevo grupo")
            nuevo_nombre = st.text_input("Nombre del Grupo:")
            nuevo_distrito = st.selectbox("Seleccione el distrito del grupo:", [1, 2, 3])

            if st.button("Guardar Grupo"):
                if nuevo_nombre.strip() == "":
                    st.error("Debe ingresar un nombre.")
                else:
                    try:
                        cur = conn.cursor()
                        cur.execute(
                            f"INSERT INTO `{grupo_table}` (Nombre, Id_distrito) VALUES (%s, %s)",
                            (nuevo_nombre, nuevo_distrito)
                        )
                        conn.commit()
                        st.success("Grupo creado exitosamente.")
                    except Exception as e:
                        st.error(f"Error al guardar el grupo: {e}")

            # ---- LECTURA ----
            if id_col and label_col:
                ref["grupos"] = pd.read_sql(
                    f"""SELECT `{id_col}` AS Id_grupo,
                                `{label_col}` AS Nombre,
                                Id_distrito
                        FROM `{grupo_table}`""",
                    conn
                )
            elif id_col:
                ref["grupos"] = pd.read_sql(
                    f"SELECT `{id_col}` AS Id_grupo, Id_distrito FROM `{grupo_table}`",
                    conn
                )
                ref["grupos"]["Nombre"] = ref["grupos"]["Id_grupo"].astype(str)
            else:
                ref["grupos"] = pd.DataFrame({"Id_grupo": [], "Nombre": [], "Id_distrito": []})

        else:
            ref["grupos"] = pd.DataFrame({"Id_grupo": [], "Nombre": [], "Id_distrito": []})

        return ref

    except Exception as e:
        st.warning(f"No se pudieron cargar datos de referencia. Error: {e}")
        return {
            "distritos": pd.DataFrame({"Id_distrito": [], "Nombre": []}),
            "ciclos": pd.DataFrame({"Id_ciclo": [], "Nombre": []}),
            "grupos": pd.DataFrame({"Id_grupo": [], "Nombre": []})
        }

    finally:
        conn.close()


# ======================================================
#              MENÚ PRINCIPAL DE USUARIOS
# ======================================================

def menu_gestion_usuarios():
    st.header("👤 Gestión de Usuarios y Accesos")
    tab1, tab2 = st.tabs(["➕ Crear Usuario", "📋 Lista de Usuarios"])

    with tab1:
        create_user_form()

    with tab2:
        listar_usuarios()


# ======================================================
#                FORMULARIO CREAR USUARIO
# ======================================================

def create_user_form():
    st.subheader("Registrar Credenciales")
    st.info("Crea un usuario para un miembro, directiva o promotora.")

    conn = obtener_conexion()
    if not conn:
        st.error("Sin conexión a BD")
        return

    df_miembros = pd.DataFrame()
    df_promotoras = pd.DataFrame()

    try:
        df_miembros = pd.read_sql("""
            SELECT m.Id_miembro, m.Nombre, m.`DUI/Identificación` as DUI,
                   m.Id_grupo, g.Nombre as NombreGrupo
            FROM Miembro m
            JOIN Grupo g ON m.Id_grupo = g.Id_grupo
        """, conn)

        try:
            df_promotoras = pd.read_sql("""
                SELECT p.Id_promotora, p.Nombre, p.Id_distrito,
                       d.Nombre as NombreDistrito
                FROM Promotora p
                LEFT JOIN Distrito d ON p.Id_distrito = d.Id_distrito
            """, conn)
        except:
            pass

    except Exception as e:
        st.error(f"Error cargando datos auxiliares: {e}")
    finally:
        conn.close()

    # ---------- FORMULARIO ----------
    c1, c2 = st.columns(2)
    new_username = c1.text_input("Usuario")
    new_password = c2.text_input("Contraseña", type="password")
    new_rol = st.selectbox("Rol", ['miembro', 'junta directiva', 'promotora', 'administrador'])

    id_miembro_final = id_grupo_final = None
    id_promotora_final = id_distrito_final = None

    st.markdown("---")

    # --------- LÓGICA PARA MIEMBRO / DIRECTIVA ---------
    if new_rol in ("junta directiva", "miembro"):
        if not df_miembros.empty:
            st.write("👤 **Vincular a Miembro:**")

            opciones = {
                row.Id_miembro: f"{row.Nombre} - {row.NombreGrupo}"
                for _, row in df_miembros.iterrows()
            }

            id_sel = st.selectbox("Seleccionar Persona:", options=opciones.keys(),
                                  format_func=lambda x: opciones[x])

            if id_sel:
                fila = df_miembros[df_miembros.Id_miembro == id_sel].iloc[0]
                id_miembro_final = id_sel
                id_grupo_final = int(fila.Id_grupo)
                st.info(f"Se vinculará al miembro {fila['Nombre']} del grupo {fila['NombreGrupo']}")

        else:
            st.warning("No hay miembros registrados.")

    # ------------------ PROMOTORA ------------------
    elif new_rol == 'promotora':
        if not df_promotoras.empty:
            st.write("👩‍💼 **Vincular a Promotora:**")

            opciones = {
                row.Id_promotora: f"{row.Nombre} (Distrito: {row.NombreDistrito})"
                for _, row in df_promotoras.iterrows()
            }

            id_sel = st.selectbox("Seleccionar Promotora:", options=opciones.keys(),
                                  format_func=lambda x: opciones[x])

            if id_sel:
                fila = df_promotoras[df_promotoras.Id_promotora == id_sel].iloc[0]
                id_promotora_final = id_sel

                if pd.notna(fila.Id_distrito):
                    id_distrito_final = int(fila.Id_distrito)
                    st.info(f"Se vinculará al distrito {fila['NombreDistrito']}")
                else:
                    st.warning("Esta promotora no tiene distrito asignado.")
        else:
            st.warning("No hay promotoras registradas.")

    st.markdown("---")

    # ------------------ BOTÓN GUARDAR ------------------
    if st.button("Crear Usuario", type="primary"):
        if new_username and new_password:
            guardar_usuario_bd(
                new_username, new_password, new_rol,
                id_miembro_final, id_grupo_final,
                id_promotora_final, id_distrito_final
            )
        else:
            st.error("Debe ingresar usuario y contraseña.")


# ======================================================
#                 FUNCIONES BD USUARIOS
# ======================================================

def guardar_usuario_bd(usuario, password, rol, id_miembro, id_grupo, id_promotora, id_distrito):
    conn = obtener_conexion()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT Usuario FROM Login WHERE Usuario=%s", (usuario,))
        if cursor.fetchone():
            st.error("El usuario ya existe.")
            return

        query = """
            INSERT INTO Login (Usuario, Contraseña, Rol, Id_miembro, Id_grupo, Id_promotora, Id_distrito)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                usuario, password, rol,
                int(id_miembro) if id_miembro else None,
                int(id_grupo) if id_grupo else None,
                int(id_promotora) if id_promotora else None,
                int(id_distrito) if id_distrito else None
            )
        )
        conn.commit()
        st.success("Usuario creado exitosamente.")

    except Exception as e:
        st.error(f"Error al guardar usuario: {e}")

    finally:
        conn.close()


# ======================================================
#                   LISTA DE USUARIOS
# ======================================================

def listar_usuarios():
    conn = obtener_conexion()
    if not conn:
        return

    try:
        st.subheader("Usuarios del Sistema")
        df = pd.read_sql(
            "SELECT Id_usuario, Usuario, Rol, Id_miembro, Id_promotora, Id_grupo FROM Login",
            conn
        )
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error("Error al listar usuarios: " + str(e))

    finally:
        conn.close()


