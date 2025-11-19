from sqlalchemy import create_engine
import pandas as pd
import geopandas as gpd
from shapely import wkb
import folium
import geopandas as gpd
import matplotlib.pyplot as plt



# Engine centralizado
engine = create_engine("postgresql+psycopg2://postgres:B-4789072@localhost:5432/agroanalytics")

def leer_tabla(tabla: str, columnas=None):
    """Lee toda la tabla o solo algunas columnas"""
    query = f"SELECT * FROM {tabla}"
    if columnas:
        cols = ", ".join(columnas)
        query = f"SELECT {cols} FROM {tabla}"
    return pd.read_sql(query, engine)

def top_similares_sql(cvegeo: str, top_n: int = 10):
    """Devuelve los top N registros de similitud de un municipio desde la DB"""
    query = f"""
    SELECT *
    FROM matriz_similitud
    WHERE cvegeo_origen = '{cvegeo}' OR cvegeo_destino = '{cvegeo}'
    ORDER BY similitud DESC
    LIMIT {top_n}
    """
    return pd.read_sql(query, engine)

def leer_datos_edaficos():
    """Lee los datos edáficos de todos los municipios desde la base de datos."""
    columnas_edaficas = [
        "cvegeo_muni", "ph", "altitud", "pendiente", "pedreg", "afloram",
        "est_tam", "plas", "cic", "horizonte", 
        "col_seco_l", "col_hum_l"
    ]
    cols = ", ".join(columnas_edaficas)
    query = f"SELECT {cols} FROM edafologia"
    df = pd.read_sql(query, engine)
    df = df.rename(columns={"cvegeo_muni": "cvegeo"})
    return df

def leer_geografia():
    """Lee la tabla geografía y devuelve un GeoDataFrame con centroides"""
    # Leer geometría
    df_geo = leer_tabla("geografia", columnas=["cvegeo", "geometry"])
    
    # Convertir WKB (si viene como binario/hex)
    df_geo["geometry"] = df_geo["geometry"].apply(
        lambda x: wkb.loads(x, hex=True) if isinstance(x, str) else x
    )
    
    # Convertir a GeoDataFrame
    gdf_geo = gpd.GeoDataFrame(df_geo, geometry="geometry", crs="EPSG:4326")
    
    # Centroides
    gdf_geo["lon"] = gdf_geo.geometry.centroid.x
    gdf_geo["lat"] = gdf_geo.geometry.centroid.y
    
    return gdf_geo

def leer_centroides():
    """Lee los centroides de los municipios desde PostGIS y devuelve un DataFrame liviano"""
    query = """
    SELECT 
        cvegeo,
        ST_Y(ST_Centroid(geometry)) AS lat,
        ST_X(ST_Centroid(geometry)) AS lon
    FROM geografia
    """
    df = pd.read_sql(query, engine)
    return df



#def mapa_municipios_top():
    # recibe cvegeo_base y lista de cvegeo_similares
    # crea un mapa sencillo con todos los municipios
    # for cada municipio similar
    #     se hace un query para obtener su geometría
    #     se pinta en el mapa con un color distinto
    # retorna el mapa
    # hace un query para obtener la geometría del municipio base
    # punta el municipio base en el mapa con un color distinto
    # retorna el mapa


def mapa_municipios_top(cvegeo_base, cvegeo_similares):
    """
    Crea un mapa sencillo con el municipio base y los municipios similares.

    Parámetros:
        cvegeo_base (str): CVEGEO del municipio seleccionado.
        cvegeo_similares (list): Lista de CVEGEO de municipios similares.

    Retorna:
        folium.Map: Mapa interactivo con los municipios coloreados.
    """
    # Unir base + similares
    todos_cvegeo = [cvegeo_base] + list(cvegeo_similares)
    placeholders = ", ".join(f"'{c}'" for c in todos_cvegeo)
    
    # Query PostGIS para obtener geometrías
    query = f"SELECT cvegeo, geometry FROM geografia WHERE cvegeo IN ({placeholders})"
    gdf = gpd.read_postgis(query, engine, geom_col="geometry", crs="EPSG:4326")
    
    # Agregar columna de color
    gdf['color'] = gdf['cvegeo'].apply(lambda x: 'red' if x == cvegeo_base else 'blue')
    
    # Centrar el mapa en el municipio base
    base_geom = gdf[gdf['cvegeo'] == cvegeo_base].geometry.values[0]
    centro = [base_geom.centroid.y, base_geom.centroid.x]
    
    m = folium.Map(location=centro, zoom_start=7, tiles="cartodbpositron")
    
    # Agregar polígonos al mapa
    for _, row in gdf.iterrows():
        sim_geo = gpd.GeoSeries([row.geometry])
        sim_geo_json = sim_geo.to_json()
        folium.GeoJson(
            sim_geo_json,
            style_function=lambda feature, color=row['color']: {
                'fillColor': color,
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.5
            }
        ).add_to(m)
    
    return m



def datos_cultivos_municipio(cvegeo: str):
    """
    Consulta la tabla 'muni_cultivos' y regresa:
    - df_general: total histórico por cultivo
    - df_anual: producción por año (2014–2024)
    - fig_general: gráfica de barras por cultivo
    - fig_anual: gráfica de línea de la producción anual
    """

    # 0. Leer tabla completa
    query = f"""
        SELECT *
        FROM muni_cultivos
        WHERE cvegeo = '{cvegeo}'
    """
    df = pd.read_sql(query, engine)

    if df.empty:
        return None, None, None, None   # no hay info para este municipio

    # --- 1. AGRUPACIÓN GENERAL POR CULTIVO ---
    df_general = (
        df.groupby("nomcultivo")["produccion"]
        .sum()
        .reset_index()
        .sort_values("produccion", ascending=False)
    )

    # --- 2. AGRUPACIÓN ANUAL ---
    df_anual = (
        df.groupby("anio")["produccion"]
        .sum()
        .reset_index()
        .sort_values("anio")
    )

    # --- 3. GRÁFICA: TOTAL POR CULTIVO ---
    # --- 3. GRÁFICA: TOTAL POR CULTIVO ---
    fig_general, ax1 = plt.subplots(figsize=(8, 10))  # más alto
    ax1.barh(df_general["nomcultivo"], df_general["produccion"])
    ax1.set_title(f"Producción total por cultivo — {cvegeo}")
    ax1.set_xlabel("Producción total")
    ax1.set_ylabel("Cultivo")
    plt.tight_layout()



    # --- 4. GRÁFICA: PRODUCCIÓN POR AÑO ---
    fig_anual, ax2 = plt.subplots(figsize=(8, 4))
    ax2.plot(df_anual["anio"], df_anual["produccion"], marker="o")
    ax2.set_title(f"Producción total anual — {cvegeo}")
    ax2.set_xlabel("Año")
    ax2.set_ylabel("Producción")
    ax2.grid(True)

    return df_general, df_anual, fig_general, fig_anual

def estadisticas_generales_cultivos():
    """
    Regresa estadísticas generales del país:
    - df_top10: top 10 cultivos más producidos en 10 años
    - df_anual: producción total del país por año
    - fig_top10: gráfica de barras horizontal
    - fig_anual: gráfica de línea por año
    """

    query = """
        SELECT nomcultivo, anio, produccion
        FROM muni_cultivos
    """
    df = pd.read_sql(query, engine)

    if df.empty:
        return None, None, None, None

    # ---- Top 10 cultivos en 10 años ----
    df_top10 = (
        df.groupby("nomcultivo")["produccion"]
        .sum()
        .reset_index()
        .sort_values("produccion", ascending=False)
        .head(10)
    )

    # ---- Evolución total anual ----
    df_anual = (
        df.groupby("anio")["produccion"]
        .sum()
        .reset_index()
        .sort_values("anio")
    )

    # ---- Gráfica Top 10 ----
    fig_top10, ax1 = plt.subplots(figsize=(8, 8))
    ax1.barh(df_top10["nomcultivo"], df_top10["produccion"])
    ax1.set_title("Top 10 cultivos más producidos en México (2014–2024)")
    ax1.set_xlabel("Producción total")
    ax1.set_ylabel("Cultivo")
    plt.tight_layout()

    # ---- Gráfica anual ----
    fig_anual, ax2 = plt.subplots(figsize=(8, 4))
    ax2.plot(df_anual["anio"], df_anual["produccion"], marker="o")
    ax2.set_title("Producción agrícola total por año (México)")
    ax2.set_xlabel("Año")
    ax2.set_ylabel("Producción total")
    ax2.grid(True)

    return df_top10, df_anual, fig_top10, fig_anual

def ranking_estados():
    """
    Ranking de estados por producción total en los últimos 10 años.
    Regresa un DataFrame con:
    - Estado
    - Producción total
    """

    query = """
        SELECT m.nombre_ent AS estado, c.produccion
        FROM muni_cultivos c
        JOIN municipios m ON c.cvegeo = m.cvegeo
    """
    df = pd.read_sql(query, engine)
    

    if df.empty:
        return pd.DataFrame(columns=["Estado", "Produccion"])
    df.columns = df.columns.str.strip().str.lower()


    df_rank = (
        df.groupby("estado")["produccion"]
        .sum()
        .reset_index()
        .sort_values("produccion", ascending=False)
    )

    df_rank.rename(columns={
        "estado": "Estado",
        "produccion": "Producción"
    }, inplace=True)

    
    return df_rank

def cantidad_cultivos_por_anio():
    """
    Cuenta cuántos cultivos distintos hubo cada año.
    Regresa un DataFrame:
    - Año
    - Cultivos (cantidad)
    """

    query = """
        SELECT anio, nomcultivo
        FROM muni_cultivos
    """
    df = pd.read_sql(query, engine)

    if df.empty:
        return pd.DataFrame(columns=["Año", "Cultivos"])

    df_count = (
        df.groupby("anio")["nomcultivo"]
        .nunique()
        .reset_index()
        .sort_values("anio")
    )

    df_count.rename(columns={"anio": "Año", "nomcultivo": "Cultivos"}, inplace=True)
    return df_count
