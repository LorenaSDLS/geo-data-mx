import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import pandas as pd
from backend.utils.analysis import principales_similares, municipios_sin_info, municipios_secundarios
from streamlit_folium import st_folium
from backend.DB.conexion import leer_tabla, leer_geografia
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

from frontend.diseño import aplicar_estilos

# Aplicar los estilos
aplicar_estilos()

st.title("Detección de municipios similares")

tabla_muni = leer_tabla("municipios")
info_muni = leer_tabla("info_municipios")

# ---- Sidebar: Selección de estado y municipio ----
estado_sel = st.sidebar.selectbox("Selecciona un estado", sorted(tabla_muni["nombre_ent"].unique()))
municipios_estado = tabla_muni[tabla_muni["nombre_ent"] == estado_sel]["nomgeo"].unique()
municipio_sel = st.sidebar.selectbox("Selecciona un municipio", sorted(municipios_estado))

# ---- Botón: Buscar información del municipio ----
if st.sidebar.button("Consultar información del municipio"):
    # Buscar el CVEGEO del municipio seleccionado
    fila = tabla_muni[
        (tabla_muni["nombre_ent"] == estado_sel) &
        (tabla_muni["nomgeo"] == municipio_sel)
    ]

    cvegeo = fila.iloc[0]["cvegeo"]
        # Guardar en session_state
    st.session_state["cvegeo_seleccionado"] = cvegeo
    st.session_state["consulta_realizada"] = True


    # Buscar si el municipio tiene info
# ---- Renderizar resultados si ya se hizo una consulta ----
if st.session_state.get("consulta_realizada", False):
    cvegeo = st.session_state["cvegeo_seleccionado"]
    fila_info = info_muni[info_muni["cvegeo"] == cvegeo]

    if fila_info.empty or not bool(fila_info.iloc[0].get("tiene_info", False)):
        st.error("Este municipio no cuenta con información disponible.")
        st.subheader("Municipios cercanos con información disponible:")
        cercanos, mapa = municipios_sin_info(cvegeo)
        st.dataframe(cercanos)
        st.subheader("Mapa de municipios cercanos con información disponible:")
        st_folium(mapa, width=600, height=400, key=f"mapa_{cvegeo}")

    else:
        es_principal = bool(fila_info.iloc[0].get("es_principal", False))

        if es_principal:
            st.success("🌾 Municipio con información y cultivo.")
            top_similares, mapa = principales_similares(cvegeo, top_n=10)
            st.subheader("Municipios similares:")
            st.dataframe(top_similares)
            st.subheader("Mapa de municipios similares:")
            st_folium(mapa, width=600, height=400, key=f"mapa_{cvegeo}")

        else:
            st.info("Municipio con información.")
            top_similares, mapa = municipios_secundarios(cvegeo, top_n=10)
            st.subheader("Municipios similares:")
            st.dataframe(top_similares)
            st.subheader("Mapa de municipios similares:")
            st_folium(mapa, width=600, height=400, key=f"mapa_{cvegeo}")
