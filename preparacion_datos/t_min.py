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
from utils.utils import asignacion_filtrada, preTDA, limpiar_nan
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
#print (df.head(5))


  
#geo = csv_to_gdf_points(df)

#union = asignacion_filtrada(geo, gdf_municipios, variable="TMIN")
#print(union.head(5))
#print(union.columns)
preTDA_df = preTDA(df, gdf_municipios, variable="TMIN")
preTDA_df = limpiar_nan(preTDA_df)
print(preTDA_df.head(5))
print(preTDA_df.shape)

preTDA_df['estado'] = preTDA_df['CVE_ENT'] 
preTDA_df['municipio'] = preTDA_df['NOMGEO']
preTDA_df['variable'] = 'Tmin'

# Reordenar columnas al formato esperado
cols = ['estado', 'municipio', 'variable'] + [c for c in preTDA_df.columns if re.match(r"\d{4}-\d{2}-\d{2}", c)]
df_tmin = preTDA_df[cols]

df2_tmin = df_tmin.head(5)     # municipios "principales"
df1_tmin = df_tmin.sample(20)  # municipios "a comparar"
serie_cols = list(df_tmin.columns[3:])  

similarity = TDA_similarity(
    serie_cols=serie_cols,
    embedding_dimension=30,   
    embedding_time_delay=5,
    stride=5,
    n_components=3,
    metric="wasserstein"
)
df1s = [df1_tmin]
df2s = [df2_tmin]


D_tda = similarity.tda_matrix(df1s, df2s)

similarity.plot(D_tda, title="Similitud Topológica entre municipios (TMIN)")

