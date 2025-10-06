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
from utils.utils import asignar_puntos_a_municipios
from utils.utils import municipios_sin_puntos
from utils.load_data import load_csv, csv_to_gdf_points, load_shapefile
from utils.file_ops import ensure_dir, extract_zip, find_first_shp
from config import CSV_CLIMA, ZIP_DIVISION, EXTRACTED_DIVISION, BUFFER_MET, CRS_GEOG, CRS_METRIC
from utils.analysis import data_resume
from utils.visualization import (plot_mapa_cobertura)
from config import CSV_CLIMA, ZIP_DIVISION, EXTRACTED_DIVISION, CRS_GEOG, CRS_METRIC

def main():
    # datos del dataset de clima
    df = load_csv(CSV_CLIMA)
    #print (df.head(5))
    df_est = df["Estacion"].nunique()
    print(f"Número de estaciones únicas: {df_est}")
    df_total = len(df) // 3
    print(f"Número total de registros (3 por estación): {df_total}")
    df_coordenadas = df[['Latitud', 'Longitud']].drop_duplicates().shape[0]
    print(f"Número de coordenadas únicas: {df_coordenadas}")

    ensure_dir(EXTRACTED_DIVISION)
    shp_path = find_first_shp(EXTRACTED_DIVISION)
    gdf_municipios = load_shapefile(shp_path)

    ##print(gdf_municipios.head(3))
    print(f"Total de municipios en shapefile: {len(gdf_municipios)}")

    # Datos del shapefile de municipios
    geo = csv_to_gdf_points(df) #gdf puntos
    print(geo.head(5))
    geo_cant = geo["Estacion"].nunique()
    print(f"Número de estaciones únicas (GeoDataFrame): {geo_cant}")

    union = asignar_puntos_a_municipios(geo, gdf_municipios)
    print(union.head(5))

    plot_mapa_cobertura(union, geo)

    # Cantidad de municipios con puntos
    municipios_con = union["tiene_punto"].sum()  # True se cuenta como 1

# Cantidad de municipios sin puntos
    municipios_sin = (~union["tiene_punto"]).sum()  # False se invierte a True y se cuenta

# Total de municipios
    total_municipios = len(union)

# Porcentajes
    porcentaje_con = municipios_con / total_municipios * 100
    porcentaje_sin = municipios_sin / total_municipios * 100

    print(f"Municipios con puntos de temperatura (verde): {municipios_con} ({porcentaje_con:.2f}%)")
    print(f"Municipios sin puntos de temperatura (gris): {municipios_sin} ({porcentaje_sin:.2f}%)")

if __name__ == "__main__":
    main()
