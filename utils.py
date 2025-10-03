import geopandas as gpd
from shapely.geometry import Point
import pandas as pd

def asignar_puntos_a_municipios(df, gdf_muni):
    gdf_points = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df["Longitud"], df["Latitud"])],
        crs="EPSG:4326"
    )
    gdf_muni = gdf_muni.to_crs("EPSG:4326")
    gdf_joined = gpd.sjoin(gdf_points, gdf_muni, how="left", predicate="within")
    return gdf_joined

def municipios_sin_puntos(gdf_muni, gdf_joined, columna_nombre="NOMGEO"):
    """
    Devuelve un GeoDataFrame de municipios que no tienen ningún punto de temperatura asignado.
    
    gdf_muni: GeoDataFrame del shapefile de municipios
    gdf_joined: GeoDataFrame de puntos unidos al shapefile (spatial join)
    columna_nombre: nombre de la columna que identifica el municipio en el shapefile
    """
    # Municipios que sí tienen puntos
    municipios_con_puntos = gdf_joined[columna_nombre].unique()
    
    # Filtrar los municipios que NO están en la lista anterior
    sin_puntos = gdf_muni[~gdf_muni[columna_nombre].isin(municipios_con_puntos)]
    
    return sin_puntos
