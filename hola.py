# datos del dataset de clima

import os
from utils.file_ops import ensure_dir, extract_zip, find_first_shp
from utils.load_data import load_shapefile, load_csv
from config import ZIP_USO_SUELO, EXTRACTED_USO_SUELO, CSV_CLIMA, CSV_CLIMA_ANUAL
import pandas as pd
from pathlib import Path
"""
df= load_csv(CSV_CLIMA)

# Cargar el CSV
df = pd.read_csv(CSV_CLIMA)

# Asegurar formato de fecha
df["Fecha"] = pd.to_datetime(df["Fecha"])
df["Año"] = df["Fecha"].dt.year

# Agrupamos cada variable de interés
variables = ["TMIN", "TMAX", "PRECIP"]

# Filtrar solo esas variables
df = df[df["Variable"].isin(variables)]

# Calcular el promedio anual por municipio, estado y variable
df_prom = (
    df.groupby(["Estado", "Municipio", "Año", "Variable"], as_index=False)
    .agg({
        "Valor": "mean",
        "Latitud": "first",
        "Longitud": "first",
        "Altitud": "first"
    })
)

# Pivotear para tener una columna por variable
df_final = df_prom.pivot_table(
    index=["Estado", "Municipio", "Año", "Latitud", "Longitud", "Altitud"],
    columns="Variable",
    values="Valor"
).reset_index()

# Renombrar columnas
df_final.rename(columns={
    "TMIN": "TMINProm",
    "TMAX": "TMAXProm",
    "PRECIP": "PRECIPProm"
}, inplace=True)

# Guardar en CSV
df_final.to_csv("datos_anuales.csv", index=False)

print(df_final.head())
"""

df=load_csv('/Users/lorenasolis/EstInv/data/processed/uso_suelo_con_municipios.csv')
print(df.columns)
print(len(df))
print(df.head(5))

shp_path = find_first_shp(Path('/Users/lorenasolis/EstInv/data/processed/uso_de_suelo_con_municipios'))
gdf_municipios = load_shapefile(shp_path)

##print(gdf_municipios.head(3))
print(f"Total de municipios en shapefile: {len(gdf_municipios)}")
print(gdf_municipios.columns)
print(gdf_municipios.head(5))
