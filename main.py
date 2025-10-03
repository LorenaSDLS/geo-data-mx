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
from utils import asignar_puntos_a_municipios
from utils import municipios_sin_puntos



# Definir rutas de forma portable
base_path = Path("/Users/lorenasolis/EstInv")
csv_path = base_path / "df_limpio_master_corregido.csv"
zip_path = base_path / "division_politica.zip"
extract_path = base_path / "division_politica"

# --- 1. Cargar el dataset de temperaturas ---
df = pd.read_csv(csv_path)
print(f"Total de filas: {len(df)}")

num_estaciones = len(df) // 3
print(f"Total de estaciones: {num_estaciones}")

num_municipios = df['Municipio'].nunique()
print(f"Total de municipios: {num_municipios}")

# --- 2. Extraer archivos de ZIP si no existe carpeta ---
if not extract_path.exists():
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
        print("Archivos extraídos.")
else:
    print("Carpeta ya existe, no se vuelve a extraer.")

# Listar archivos extraídos
for file in extract_path.rglob("*"):
    print(" ", file.name)

# --- 3. Cargar shapefile ---
shp_files = list(extract_path.rglob("*.shp"))
if not shp_files:
    raise FileNotFoundError("No se encontró ningún archivo .shp en la carpeta extraída.")

gdf = gpd.read_file(shp_files[0])  # usa el primero encontrado
#print(gdf.head())
num_municipios_shp = gdf['NOMGEO'].nunique()
print(f"Total de municipios en shapefile: {num_municipios_shp}")

# --- 4. Visualizar ---
#fig, ax = plt.subplots(figsize=(10, 10))
#gdf.plot(ax=ax, edgecolor="black", facecolor="lightblue")
#ax.set_title("División política de municipios", fontsize=14)
#plt.show()

gdf_joined = asignar_puntos_a_municipios(df, gdf)

gdf_sin_puntos = municipios_sin_puntos(gdf, gdf_joined, columna_nombre="NOMGEO")
print(f"Total de municipios sin puntos: {len(gdf_sin_puntos)}")
print(gdf_sin_puntos[["NOMGEO"]])  # muestra nombres de municipios sin puntos


ax = gdf.plot(figsize=(10,8), color="white", edgecolor="black")
gdf_joined.plot(ax=ax, color="purple", markersize=5)  # <- aquí los puntos
ax.set_title("Municipios y estaciones de temperatura")
plt.show()

gdf_sin_puntos = municipios_sin_puntos(gdf, gdf_joined, columna_nombre="NOMGEO")
print(f"Total de municipios sin puntos: {len(gdf_sin_puntos)}")
print(gdf_sin_puntos[["NOMGEO"]])  # muestra nombres de municipios sin puntos
ax = gdf.plot(figsize=(10,8), color="white", edgecolor="black")
gdf_sin_puntos.plot(ax=ax, color="red", markersize=20)
ax.set_title("Municipios sin estaciones de temperatura")
plt.show()
# Crear columna indicando si el municipio tiene puntos
gdf["tiene_punto"] = gdf["NOMGEO"].isin(gdf_joined["NOMGEO"])
colors = {True: "green", False: "grey"}
gdf["color"] = gdf["tiene_punto"].map(colors)
# Plotear
fig, ax = plt.subplots(figsize=(12,10))
gdf.plot(ax=ax, color=gdf["color"], edgecolor="black")
ax.set_title("Municipios con (verde) y sin (gris) estaciones", fontsize=14)
plt.show()

