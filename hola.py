import os
import sys

from pathlib import Path
import geopandas as gpd
import pandas as pd







shp_path = (Path('/Users/lorenasolis/EstInv/data/raw/edafologia/perfiles_serieii.shp'))
gdf = gpd.read_file(shp_path, encoding="latin1")
print(gdf.head())

##print(gdf_municipios.head(3))
print(f"Total de municipios en shapefile: {len(gdf)}")
print(gdf.columns)
print(gdf.head(5))

clima = pd.read_csv('/Users/lorenasolis/EstInv/data/raw/df_limpio_master_corregido.csv')
print(clima.head(5))
print(clima.columns)


