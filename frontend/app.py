#comando para correrlo: streamlit run frontend/app.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import pandas as pd
from backend.utils.analysis import principales_similares, municipios_sin_info, municipios_secundarios
from streamlit_folium import st_folium
from backend.DB.conexion import leer_tabla, leer_geografia, estadisticas_generales_cultivos, ranking_estados, cantidad_cultivos_por_anio
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from frontend.diseño import aplicar_estilos
from frontend.pantallas import inicio, municipios, cultivos, cultivo_detalle

aplicar_estilos()

pagina = st.sidebar.radio(
    "Navegación:",
    ["Inicio", "Buscador de municipios", "Cultivos"]
)

if pagina == "Inicio":
    st.title("Bienvenido a la plataforma")
    inicio.pantalla_inicio()

elif pagina == "Buscador de municipios":
    st.title("Buscador de municipios")
    municipios.pantalla_municipios()

elif pagina == "Cultivos":
    pantalla = st.session_state.get("pantalla_actual", "cultivos")

    if pantalla == "cultivos":
        cultivos.pantalla_cultivos()

    elif pantalla == "cultivo_detalle":
        cultivo_detalle.pantalla_detalle_cultivo()

