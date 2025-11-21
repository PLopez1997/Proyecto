# Mostrar el menú lateral
opciones = ["Grupos", "Otra opción"] # Agrega más opciones si las necesitas
seleccion = st.sidebar.selectbox("Selecciona una opción", opciones)
# Según la opción seleccionada, mostramos el contenido correspondiente
if seleccion == "Grupos":
    administrador_page()
elif seleccion == "Otra opción":
    st.write("Has seleccionado otra opción.") # Aquí podrías agregar el contenido de otras opciones
