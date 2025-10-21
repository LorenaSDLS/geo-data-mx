import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

def load_csv(csv_path: Path) -> pd.DataFrame:
    """ 
    Lee un archivo CSV y devuelve un DataFrame de pandas
    Parámetros: 
        csv_path (Path): ruta al archivo CSV
    Retorna: 
        pd.DataFrame: datos cargados del CSV
    """
    df=pd.read_csv(csv_path)
    return df

def csv_to_gdf_points(df, lon_col="Longitud", lat_col="Latitud", crs="EPSG:4326"):
    """
    Convierte un DataFrame de pandas con columnas de longitud y latitud en un GeoDataFrame de puntos
    Parámetros:
        df (pd.DataFrame): DataFrame con columnas de longitud y latitud
        lon_col (str): nombre de la columna de longitud
        lat_col (str): nombre de la columna de latitud
        crs (str): sistema de referencia de coordenadas (CRS) para los puntos
    Retorna:
        gpd.GeoDataFrame: GeoDataFrame de puntos
    
    """
    # --- Seleccionar columnas relevantes ---
    cols = [lon_col, lat_col, "Altitud", "Estacion", "Estado", "Municipio"]
    cols = [c for c in cols if c in df.columns]  # evitar error si falta alguna

     # --- Eliminar duplicados por coordenadas ---
    df_unique = df[cols].drop_duplicates(subset=[lon_col, lat_col])


    geo_df = gpd.GeoDataFrame(
        df_unique,
        geometry=[Point(xy) for xy in zip(df_unique[lon_col], df_unique[lat_col])],
        crs=crs
    )
    print(f"Reducido de {len(df)} filas a {len(geo_df)} puntos únicos.")
    return geo_df

def load_shapefile(shp_path, crs="EPSG:4326"):
    """
    Lee un archivo shapefile y devuelve un GeoDataFrame de geopandas
    Parámetros:
        shp_path (Path): ruta al archivo shapefile (.shp)
        crs (str): sistema de referencia de coordenadas (CRS) para el GeoDataFrame
    Retorna:
        gpd.GeoDataFrame: datos cargados del shapefile
    """
    try:
        gdf = gpd.read_file(shp_path, encoding="utf-8")
    except UnicodeDecodeError:
        gdf = gpd.read_file(shp_path, encoding="latin-1")
    return gdf.to_crs(crs)

