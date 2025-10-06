import geopandas as gpd
from shapely.geometry import Point
from config import CRS_GEOG



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
    # --- Asegurar CRS consistente ---
    gdf_muni = gdf_muni.to_crs(CRS_GEOG)
    # --- Marcar municipios que tienen al menos un punto dentro ---
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
