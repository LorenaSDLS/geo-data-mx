import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import pandas as pd
from backend.utils.analysis import principales_similares, calcular_top_final


st.set_page_config(page_title="Municipios Similares", layout="wide")
st.title("Municipios Similares - Dashboard Climático")



tabla_muni = pd.read_parquet("/Users/lorenasolis/EstInv/data/tabla_municipios.parquet")
info_muni = pd.read_parquet("/Users/lorenasolis/EstInv/data/municipios_estado_info.parquet")

# ---- Sidebar: Selección de estado y municipio ----
estado_sel = st.sidebar.selectbox("Selecciona un estado", sorted(tabla_muni["NOM_ENT"].unique()))
municipios_estado = tabla_muni[tabla_muni["NOM_ENT"] == estado_sel]["NOMGEO"].unique()
municipio_sel = st.sidebar.selectbox("Selecciona un municipio", sorted(municipios_estado))

# ---- Botón: Buscar información del municipio ----
if st.sidebar.button("Consultar información del municipio"):
    # Buscar el CVEGEO del municipio seleccionado
    fila = tabla_muni[
        (tabla_muni["NOM_ENT"] == estado_sel) &
        (tabla_muni["NOMGEO"] == municipio_sel)
    ]

    if fila.empty:
        st.warning("⚠️ No se encontró el municipio en la tabla.")
    else:
        cvegeo = fila.iloc[0]["CVEGEO"]

        # Buscar si el municipio tiene info
        fila_info = info_muni[info_muni["CVEGEO"] == cvegeo]

        if fila_info.empty or not bool(fila_info.iloc[0].get("tiene_info", False)):
            st.error("🚫 Municipio sin info.")
        else:
            es_principal = bool(fila_info.iloc[0].get("es_principal", False))
            
            if es_principal:
                st.success("🌾 Municipio con info y cultivo.")
                # función para buscar en la matriz de similitud
                # Buscar municipios similares
                top_similares = principales_similares(cvegeo, top_n=10)

                # Mostrar resultados
                st.subheader("Municipios más similares:")
                st.dataframe(top_similares)
                
            else:
                st.info("✅ Municipio con info.")
                top_similares = calcular_top_final(cvegeo, top_n=10)
                st.subheader("Municipios más similares (Top 10 con TDA):")
                st.dataframe(top_similares[[
                    "municipio_similar", "NOMGEO", "NOM_ENT", "SIMILITUD_%", "Confianza", "PUNTAJE_FINAL"
                ]])

