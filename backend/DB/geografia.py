import geopandas as gpd
from .conexion import engine
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Point
import folium
from backend.DB.conexion import leer_tabla



def calculo_centroide(cvegeo: str) -> tuple:

    #Obtiene las coordenadas del centroide de un municipio desde PostGIS.
    
    #Parámetros:
    #- cvegeo: str -> CVEGEO del municipio
    
    #Retorna:
    #- (lon, lat) del centroide
  
    query = f"""
    SELECT ST_X(ST_Centroid(geometry)) AS lon,
           ST_Y(ST_Centroid(geometry)) AS lat
    FROM geografia
    WHERE cvegeo = '{cvegeo}'
    """
    
    df = pd.read_sql(query, engine)
    
    if df.empty:
        raise ValueError(f"Municipio {cvegeo} no encontrado")
    
    return (df["lon"].iloc[0], df["lat"].iloc[0])



def buffer_municipio(cvegeo_base: str, min_municipios: int = 10, incremento_km: float = 10.0):

    #Devuelve los municipios cercanos al municipio base que tienen información disponible,
    #usando buffer en la base de datos PostGIS.
    
    #Parámetros:
    #- cvegeo_base: CVEGEO del municipio base
    #- min_municipios: mínimo de municipios a devolver
    #- incremento_km: radio inicial del buffer en km (se incrementa si no alcanza min_municipios)
    
    #Retorna:
    #- DataFrame con columnas: cvegeo, nomgeo, nombre_ent, distancia_m
  
    radio = incremento_km * 1000  # metros
    municipios_cercanos = pd.DataFrame()
    print(f"Buscando municipios cercanos a {cvegeo_base}...")  # debug

    while len(municipios_cercanos) < min_municipios:
        print(f"Radio actual: {radio/1000} km")  # debug
        query = f"""
        WITH centroide AS (
            SELECT ST_Centroid(geometry) AS geom
            FROM geografia
            WHERE cvegeo = '{cvegeo_base}'
        )
        SELECT g.cvegeo, m.nomgeo, m.nombre_ent,
               ST_Distance(ST_Transform(g.geometry, 3857), ST_Transform(c.geom, 3857)) AS distancia_m,
               ST_X(ST_Centroid(g.geometry)) AS lon,
               ST_Y(ST_Centroid(g.geometry)) AS lat
        FROM geografia g
        JOIN municipios m ON g.cvegeo = m.cvegeo
        JOIN info_municipios i ON g.cvegeo = i.cvegeo
        CROSS JOIN centroide c
        WHERE g.cvegeo != '{cvegeo_base}'
            AND i.tiene_info = TRUE
            AND ST_DWithin(ST_Transform(g.geometry, 3857), ST_Transform(c.geom, 3857), {radio})

        """
        municipios_cercanos = pd.read_sql(query, engine)
        print(f"Municipios encontrados: {len(municipios_cercanos)}")  # debug
        if len(municipios_cercanos) >= min_municipios:
            break
        radio += incremento_km * 1000  # aumentar buffer si no hay suficientes

    # Ordenar por distancia
    municipios_cercanos = municipios_cercanos.sort_values("distancia_m").reset_index(drop=True)
    return municipios_cercanos


def municipios_cercanos(cvegeo_base: str, min_municipios: int = 10, incremento_km: float = 20.0):
    """
    Devuelve los municipios cercanos al municipio base, ordenados por distancia.
    """
    df_cercanos = buffer_municipio(cvegeo_base, min_municipios, incremento_km)
    # Convertir distancia a km
    df_cercanos["distancia_km"] = df_cercanos["distancia_m"] / 1000
    df_cercanos = df_cercanos.drop(columns="distancia_m")
    return df_cercanos


def plot_mapa_municipios(cvegeo_base: str, df_cercanos: pd.DataFrame):
    """
    Plotea mapa interactivo con folium.
    Municipio base en rojo, cercanos en verde.
    """
    # Obtener centroide del municipio base
    lon, lat = calculo_centroide(cvegeo_base)
    
    mapa = folium.Map(location=[lat, lon], zoom_start=10)
    
    # Municipio base
    folium.CircleMarker([lat, lon], radius=8, color='red', fill=True, fill_opacity=0.7, popup="Base").add_to(mapa)
    
    # Municipios cercanos
    for _, row in df_cercanos.iterrows():
        folium.CircleMarker([row.get("lat", lat), row.get("lon", lon)], radius=6, color='green', fill=True, fill_opacity=0.5, popup=row["nomgeo"]).add_to(mapa)
    
    return mapa

"""
def municipios_sin_info(cvegeo_base: str, min_municipios: int = 10, incremento_km: float = 5.0):
"""
    #Función principal para municipios sin info, usando consultas optimizadas en PostGIS.

"""
    cercanos = municipios_cercanos(cvegeo_base, min_municipios, incremento_km=20.0)
    print("Resultado final de municipios cercanos:")
    print(cercanos[["nomgeo", "nombre_ent"]])  # solo nombre y estado
    # Crear tabla limpia
    tabla_limpia = cercanos[["nomgeo", "nombre_ent", "distancia_km"]].copy()
    tabla_limpia.index = range(1, len(tabla_limpia) + 1)  # índice empezando en 1
    tabla_limpia = tabla_limpia.rename(columns={
        "nomgeo": "Municipio",
        "nombre_ent": "Estado",
        "distancia_km": "Distancia (km)"
    })
    
    return tabla_limpia
"""