import geopandas as gpd
from shapely.geometry import Point
from config import CRS_GEOG
import re
import pandas as pd
import numpy as np
from TDA.tda_similarity import TDA_similarity




def asignar_puntos_a_municipios(df, gdf_muni):
    """
    Marca municipios que tienen al menos un punto de temperatura.
    Parámetros:
        df: DataFrame con columnas 'Longitud' y 'Latitud'
        gdf_muni: GeoDataFrame de municipios
    Retorna:
        GeoDataFrame de municipios con columna 'tiene_punto' (True/False)
    """
    # --- Crear GeoDataFrame de puntos ---
    gdf_points = gpd.GeoDataFrame(
        df.copy(),
        geometry=[Point(xy) for xy in zip(df["Longitud"], df["Latitud"])],
        crs=CRS_GEOG
    )
    gdf_muni = gdf_muni.to_crs(CRS_GEOG)
    # Marcar municipios que tienen al menos un punto dentro 
    gdf_joined = gpd.sjoin(gdf_points, gdf_muni, how="left", predicate="intersects")
    municipios_con_puntos = gdf_joined["NOMGEO"].dropna().unique()
    gdf_muni["tiene_punto"] = gdf_muni["NOMGEO"].isin(municipios_con_puntos)
    print(f"Se asignaron municipios a {gdf_joined['NOMGEO'].notna().sum()} estaciones de {len(gdf_joined)} totales.")
    print(f"{gdf_joined['NOMGEO'].isna().sum()} estaciones quedaron fuera de algún polígono.")
    return gdf_muni

def municipios_sin_puntos(gdf_muni):
    """
    Devuelve un GeoDataFrame de municipios que no tienen ningún punto de temperatura.
    Parámetros:
        gdf_muni: GeoDataFrame de municipios con columna 'tiene_punto'
    Retorna:
            GeoDataFrame de municipios sin puntos
        
    """
    return gdf_muni[~gdf_muni["tiene_punto"]].copy()


def asignacion_filtrada (df, gdf_muni, variable=None):
    """
    Marca municipios que tienen al menos un punto de una variable específica.
    Si variable es None, usa todos los puntos.
    """
    if variable is not None:
        df = df[df["Variable"] == variable]

    gdf_points = gpd.GeoDataFrame(
        df.copy(),
        geometry=[Point(xy) for xy in zip(df["Longitud"], df["Latitud"])],
        crs=CRS_GEOG
    )
    gdf_muni = gdf_muni.to_crs(CRS_GEOG)
    gdf_joined = gpd.sjoin(gdf_points, gdf_muni, how="left", predicate="intersects")
    

    return gdf_joined

def preTDA(df, gdf_muni, variable):
    """
    Prepara los datos de clima (TMIN, TMAX, PRECIPITACION, etc.)
    para análisis topológico, agrupando por municipio y fecha.

    Parámetros:
        df : DataFrame del dataset de clima original.
        gdf_muni : GeoDataFrame de municipios (división política).
        variable : str -> nombre de la variable ('TMIN', 'TMAX', 'PRECIPITACION', etc.)

    Retorna:
        df_muni : DataFrame con filas = municipios, columnas = fechas, valores = promedio por municipio.
    """

    gdf_joined = asignacion_filtrada(df, gdf_muni, variable=variable)
    gdf_joined = gdf_joined.dropna(subset=["NOMGEO"])
    columnas_fecha = [col for col in gdf_joined.columns if re.match(r"\d{4}-\d{2}-\d{2}", col)]
    df_muni = (
        gdf_joined.groupby("NOMGEO")[columnas_fecha]
        .mean()
        .reset_index()
    )
    if "CVE_ENT" in gdf_joined.columns and "CVE_MUN" in gdf_joined.columns:
        claves = gdf_joined.groupby("NOMGEO")[["CVE_ENT", "CVE_MUN"]].first().reset_index()
        df_muni = df_muni.merge(claves, on="NOMGEO", how="left")
    print(f" DataFrame de {variable}: {len(df_muni)} municipios × {len(columnas_fecha)} fechas")
    return df_muni

    
def limpiar_nan(df):
    """
    Interpola valores NaN por municipio en las columnas de fechas.
    Rellena hacia ambos lados si los extremos también son NaN.
    """

    columnas_fecha = [col for col in df.columns if re.match(r"\d{4}-\d{2}-\d{2}", col)]
    df_clean = df.copy()
    df_clean[columnas_fecha] = df_clean[columnas_fecha].interpolate(axis=1, limit_direction='both')
    print(f"{df_clean[columnas_fecha].isna().sum().sum()} valores NaN restantes.")
    return df_clean

def municipios_similares_a(df_todas, municipio_name, variables, top_n=5):
    """
    Devuelve los top_n municipios más similares a un municipio dado según las variables.
    
    df_todas: dict de DataFrames por variable
    municipio_name: nombre del municipio de referencia
    variables: lista de variables usadas en TDA
    top_n: número de municipios similares a devolver
    """
    # Construir df1: el municipio que buscamos
    df1s = [df_todas[var].loc[[df_todas[var][df_todas[var]['municipio'] == municipio_name].index[0]]] 
            for var in variables]
    
    # df2: todos los municipios posibles
    df2s = [df_todas[var] for var in variables]
    
    serie_cols = list(df_todas[variables[0]].columns[3:])
    similarity = TDA_similarity(
        serie_cols=serie_cols,
        embedding_dimension=30,
        embedding_time_delay=5,
        stride=5,
        n_components=3,
        metric="wasserstein"
    )
    
    # Calcular distancias
    D = similarity.tda_matrix(df1s, df2s)
    
    # Construir DataFrame con nombres
    df2_names = df2s[0]['municipio'].tolist()
    D_df = pd.DataFrame(D, index=[municipio_name], columns=df2_names)
    
    # Top_n más similares
    top_similares = D_df.loc[municipio_name].sort_values().head(top_n).index.tolist()
    return top_similares
