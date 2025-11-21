import streamlit as st
from modulos.login import login  # tu función login

# --- CONTROL PRINCIPAL ---
if st.session_state.get("sesion_iniciada"):

    Rol = st.session_state.get("tipo_usuario")

    if Rol == "promotora":
        from modulos.promotora import promotora_page
        promotora_page()

    elif Rol == "junta directiva":
        from modulos.junta_directiva import junta_directiva_page
        junta_directiva_page()

    elif Rol == "administrador":
        from modulos.administrador import administrador_page
        mostrar_administrador()

    elif Rol == "miembro":
        from modulos.miembro import miembro_page
        miembro_page()

else:
    login()
