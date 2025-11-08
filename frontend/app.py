import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import pandas as pd
from backend.utils.analysis import principales_similares, calcular_top_final
from backend.DB.conexion import leer_tabla



st.set_page_config(page_title="Municipios Similares", layout="wide")
st.title("Municipios Similares - Dashboard Climático")



tabla_muni = leer_tabla("municipios")
info_muni = leer_tabla("info_municipios")  # o la tabla que corresponda

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

    if fila.empty:
        st.warning("⚠️ No se encontró el municipio en la tabla.")
    else:
        cvegeo = fila.iloc[0]["cvegeo"]

        # Buscar si el municipio tiene info
        fila_info = info_muni[info_muni["cvegeo"] == cvegeo]

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
                    "municipio_similar", "nomgeo", "nombre_ent", "SIMILITUD_%", "confianza", "PUNTAJE_FINAL"
                ]])

