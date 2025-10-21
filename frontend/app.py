import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.utils import preTDA, limpiar_nan, municipios_similares_a
from preparacion_datos.ejemplo import municipios_similares_mvp
from utils.load_data import load_csv, load_shapefile
from utils.file_ops import ensure_dir, find_first_shp
from config import CSV_CLIMA, EXTRACTED_DIVISION
import geopandas as gpd



#__________________________



# ---- Configuración de página ----
st.set_page_config(page_title="Municipios Similares", layout="wide")
st.title("Municipios Similares - Dashboard Climático")

# ---- Función para cargar y preprocesar datos ----
@st.cache_resource  # Se ejecuta una sola vez y se guarda en caché
def cargar_y_preprocesar():
    # Cargar CSV
    df = load_csv(CSV_CLIMA)

    # Asegurar carpeta
    ensure_dir(EXTRACTED_DIVISION)

    # Cargar shapefile
    shp_path = find_first_shp(EXTRACTED_DIVISION)
    gdf_municipios = gpd.read_file(shp_path)
    gdf_municipios['estado'] = gdf_municipios['CVE_ENT']

    # Variables climáticas
    variables = ["TMIN", "TMAX", "PRECIP"]
    df_todas = {}

    # Preprocesamiento
    for var in variables:
        df_var = preTDA(df, gdf_municipios, variable=var)
        df_var = limpiar_nan(df_var)
        df_var = pd.concat([
            df_var,
            pd.DataFrame({
                'estado': df_var['CVE_ENT'],
                'municipio': df_var['NOMGEO'],
                'variable': var
            }, index=df_var.index)
        ], axis=1)
        cols = ['estado', 'municipio', 'variable'] + [c for c in df_var.columns if c[:4].isdigit()]
        df_todas[var] = df_var[cols]

    return df_todas, gdf_municipios, variables

# ---- Cargar datos una sola vez ----
df_todas, gdf_municipios, variables = cargar_y_preprocesar()

# ---- Calcular municipios similares (solo cuando se cambia selección) ----
@st.cache_resource
def calcular_similares(municipio, df_todas, variables, top_n=5):
    #return municipios_similares_mvp(municipio, df_todas, variables, top_n=top_n)
    return municipios_similares_a(df_todas, municipio, variables, top_n=top_n)

# ---- Sidebar: Selección de estado y municipio ----
estado_sel = st.sidebar.selectbox("Selecciona un estado", gdf_municipios['estado'].unique())
municipios_estado = gdf_municipios[gdf_municipios['estado'] == estado_sel]['NOMGEO'].tolist()
municipio_sel = st.sidebar.selectbox("Selecciona un municipio", municipios_estado)
top_n = st.sidebar.slider("Número de municipios similares a mostrar", min_value=1, max_value=10, value=5)

# ---- Botón de aceptar ----
if st.sidebar.button("Cargar"):
    top_similares = calcular_similares(municipio_sel, df_todas, variables, top_n=top_n)
    st.write(f"Municipios más similares a **{municipio_sel}**:", top_similares)

    for var in variables:
        cols_fecha = [c for c in df_todas[var].columns if c[:4].isdigit()]
        df_plot = df_todas[var].set_index('municipio').loc[top_similares + [municipio_sel], cols_fecha].T
        fig = px.line(df_plot,
                      labels={'index':'Fecha', 'value': var, 'variable':'Municipio'},
                      title=f"{var} de municipios similares")
        st.plotly_chart(fig, use_container_width=True)



