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
from config import CSV_CLIMA, ZIP_DIVISION, EXTRACTED_DIVISION, CRS_GEOG, CRS_METRIC, EXTRACTED_USO_SUELO, ZIP_USO_SUELO, CSV_CLIMA_ANUAL

def main():
    """
    # datos del dataset de clima
    df = load_csv(CSV_CLIMA)
    print (df.head(5))
   
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
    
    union = asignar_puntos_a_municipios(geo, gdf_municipios)
    print(union.head(5))
    print(union.columns)

   #plot_mapa_cobertura(union, geo)

    # Cantidad de municipios con puntos
    #municipios_con = union["tiene_punto"].sum()  # True se cuenta como 1

# Cantidad de municipios sin puntos
    #municipios_sin = (~union["tiene_punto"]).sum()  # False se invierte a True y se cuenta

# Total de municipios
    #total_municipios = len(union)

# Porcentajes
    #porcentaje_con = municipios_con / total_municipios * 100
    #porcentaje_sin = municipios_sin / total_municipios * 100

    #print(f"Municipios con puntos de temperatura (verde): {municipios_con} ({porcentaje_con:.2f}%)")
    #print(f"Municipios sin puntos de temperatura (gris): {municipios_sin} ({porcentaje_sin:.2f}%)")

#-------------------------Leer el shapefile de uso de suelo
"""


    
    extract_zip(ZIP_USO_SUELO, EXTRACTED_USO_SUELO)
    ensure_dir(EXTRACTED_USO_SUELO)
    print(list(EXTRACTED_USO_SUELO.iterdir()))

    shp_path_suelo = find_first_shp(EXTRACTED_USO_SUELO)
    gdf_suelo = load_shapefile(shp_path_suelo)
    print(f"Total de polígonos de uso de suelo en shapefile: {len(gdf_suelo)}")
    print(gdf_suelo.head(3))
    print(gdf_suelo.columns)
    """
    gdf_suelo = gdf_suelo.to_crs("EPSG:32614")
    gdf_municipios = gdf_municipios.to_crs("EPSG:32614")
    #print(gdf_suelo['DESCRIPCIO'].unique())
    #gdf_suelo = gdf_suelo.to_crs(gdf_municipios.crs)
    # Intersección entre uso de suelo y municipios
    gdf_union = gpd.overlay(gdf_suelo, gdf_municipios, how='intersection')
    #gdf_union = gpd.sjoin(gdf_suelo, gdf_municipios, how="inner", predicate="intersects")
    

    gdf_union["area_km2"] = gdf_union.geometry.area / 10**6
    ## Área total de cada municipio
    area_total_mun = gdf_union.groupby("NOMGEO")["area_km2"].sum().rename("area_total_mun")
    gdf_union = gdf_union.merge(area_total_mun, on="NOMGEO")
    
    # Calcular porcentaje de cada uso de suelo dentro del municipio
    gdf_union["porcentaje"] = gdf_union["area_km2"] / gdf_union["area_total_mun"] * 100

    csv_resumen = gdf_union[["NOM_ENT", "NOMGEO", "GRUPO_USO", "area_km2", "porcentaje"]]
    csv_resumen.to_csv("uso_suelo_con_municipios.csv", index=False)

    gdf_union.to_file("uso_suelo_con_municipios.shp")

    # Agrupa por municipio y categoría de uso de suelo
    resumen = (
        gdf_union.groupby(["NOM_ENT", "NOMGEO", "GRUPO_USO"])["area_km2"]
        .sum()
        .reset_index()
)
    print(resumen.head(10))
  
    fig, ax = plt.subplots(figsize=(12, 10))

# Polígonos de uso de suelo
    gdf_union.plot(
        column="GRUPO_USO",
        ax=ax,
        cmap="tab20",
        legend=True,
        missing_kwds={"color": "lightgrey", "label": "Sin datos"}
)

# Enmallado de los municipios encima
    gdf_municipios.boundary.plot(ax=ax, edgecolor="black", linewidth=0.8)

    plt.title("Uso de suelo por municipio con enmallado de división territorial")
    plt.axis("off")

# Guardar figura para frontend
    #plt.savefig("uso_suelo_municipios.png", dpi=150, bbox_inches='tight')
    plt.show()



   







 

"""

if __name__ == "__main__":
    main()