# app.py
import streamlit as st
from modulos.venta import mostrar_venta  # Importamos la función mostrar_venta del módulo venta

# Llamamos a la función mostrar_venta para mostrar el mensaje en la app
mostrar_venta()

from modulos.login import login
login()

