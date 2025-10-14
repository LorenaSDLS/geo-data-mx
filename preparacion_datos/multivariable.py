import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import zipfile
import os 
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path 
from utils.utils import asignacion_filtrada, preTDA, limpiar_nan, municipios_similares_a
from utils.load_data import load_csv, csv_to_gdf_points, load_shapefile
from utils.file_ops import ensure_dir, extract_zip, find_first_shp
from config import CSV_CLIMA, ZIP_DIVISION, EXTRACTED_DIVISION, BUFFER_MET, CRS_GEOG, CRS_METRIC
from utils.analysis import data_resume
from utils.visualization import (plot_mapa_cobertura)
from config import CSV_CLIMA, ZIP_DIVISION, EXTRACTED_DIVISION, CRS_GEOG, CRS_METRIC, EXTRACTED_USO_SUELO, ZIP_USO_SUELO  
from TDA.tda_similarity import TDA_similarity

# datos del dataset de clima
df = load_csv(CSV_CLIMA)
ensure_dir(EXTRACTED_DIVISION)
shp_path = find_first_shp(EXTRACTED_DIVISION)
gdf_municipios = load_shapefile(shp_path)

variables = ["TMIN", "TMAX", "PRECIP"]
df_todas = {}

for var in variables:
    df_var = preTDA(df, gdf_municipios, variable=var)  # se crea preTDA_df aquí
    df_var = limpiar_nan(df_var)                         # limpiar NaN por municipio
    df_var = pd.concat([
    df_var,
    pd.DataFrame({
        'estado': df_var['CVE_ENT'],
        'municipio': df_var['NOMGEO'],
        'variable': var}, index=df_var.index)], axis=1)
    cols = ['estado', 'municipio', 'variable'] + [c for c in df_var.columns if re.match(r"\d{4}-\d{2}-\d{2}", c)]
    df_todas[var] = df_var[cols]

n_top = 5
n_sample = 20
indices_top = df_todas["TMIN"].head(n_top).index
indices_sample = df_todas["TMIN"].sample(n_sample).index

df2s = [df_todas[var].loc[indices_top] for var in variables]
df1s = [df_todas[var].loc[indices_sample] for var in variables]


for i, var in enumerate(variables):
    print(f"{var}: df1 shape {df1s[i].shape}, df2 shape {df2s[i].shape}")




serie_cols = list(df_todas["TMIN"].columns[3:])

similarity = TDA_similarity(
    serie_cols=serie_cols,
     embedding_dimension=30,
    embedding_time_delay=5,
    stride=5,
    n_components=3,
    metric="wasserstein"
    )
# Matriz multivariable y plot
D_multi = similarity.tda_matrix(df1s, df2s)
similarity.plot(D_multi, title="Similitud Topológica Multivariable")


similares = municipios_similares_a(df_todas, "Doctor Coss", variables, top_n=5)
print("Municipios más similares a Doctor Coss:", similares)
