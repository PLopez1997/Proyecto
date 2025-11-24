import streamlit as st
from modulos.login import login_page  # Asegúrate que en login.py la función se llame login_page

# ---- CONTROL PRINCIPAL -----

if st.session_state.get("logged_in") == True:

    # 2. Recuperamos el rol y el nombre de la sesión
    Rol = st.session_state.get("user_role")
    Usuario = st.session_state.get("user_name")

    # --- BARRA LATERAL COMÚN (Opcional pero recomendada) ---
    with st.sidebar:
        st.write(f"👤 Usuario: {Usuario}")
        st.write(f"🔑 Rol: {Rol}")
        # Botón de cerrar sesión (Vital para poder salir y probar otros roles)
        if st.button("Cerrar Sesión"):
            st.session_state["logged_in"] = False
            st.session_state["user_role"] = None
            st.session_state["grupo_id"] = None
            st.rerun()

    # --- RUTEO DE MÓDULOS ---
    # Aquí es donde llamamos a tus módulos existentes.
    # Nota: No cambiamos nada DE los módulos, solo CUÁNDO se llaman.

    if Rol == "promotora":
        from modulos.promotora import app as promotora_page
        promotora_page()

    elif Rol == "junta directiva": 
        from modulos.juntadirectiva import junta_directiva_page 
        junta_directiva_page()

    elif Rol == "administrador":
        # Esto carga tu módulo de admin intacto
        from modulos.administrador import administrador_page
        administrador_page()

    elif Rol == "miembro":
        from modulos.miembro import miembro_page
        miembro_page()

    else:
        st.error(f"El rol '{Rol}' no tiene un módulo asignado.")
        if st.button("Volver al Login"):
            st.session_state["logged_in"] = False
            st.rerun()

else:
    # No hay sesión iniciada: mostrar login
    login_page()
