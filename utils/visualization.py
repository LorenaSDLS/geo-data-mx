import matplotlib.pyplot as plt
import geopandas as gpd

def plot_municipios_y_puntos(gdf_muni, df_puntos):
    """
    Muestra todos los municipios (borde) y los puntos de temperatura.
    Parametros:
        gdf_muni: GeoDataFrame de municipios
        df_puntos: DataFrame con columnas 'Longitud' y 'Latitud'
    Retorna:
        None (muestra el gráfico)
    """
    ax = gdf_muni.plot(figsize=(10, 8), color="white", edgecolor="black")
    gpd.GeoDataFrame(df_puntos, geometry=gpd.points_from_xy(df_puntos.Longitud, df_puntos.Latitud),
                     crs=gdf_muni.crs).plot(ax=ax, color="purple", markersize=5)
    ax.set_title("Municipios y estaciones de temperatura")
    plt.show()


def plot_municipios_sin_puntos(gdf_muni):
    """
    Muestra un gráfico delos municipios que no tienen ningún punto de temperatura y los que si tienen.
    Parametros:
        gdf_muni: GeoDataFrame de municipios con columna 'tiene_punto'
    Retorna:
        None (muestra el gráfico)
    """
    gdf_sin = gdf_muni[~gdf_muni["tiene_punto"]]
    ax = gdf_muni.plot(figsize=(10, 8), color="white", edgecolor="black")
    gdf_sin.plot(ax=ax, color="red", edgecolor="black", alpha=0.6)
    ax.set_title("Municipios sin estaciones de temperatura")
    plt.show()


def plot_mapa_cobertura(gdf_muni):
    """
    Muestra un mapa completo con municipios con puntos en verde y sin puntos en gris.
    Parametros:
        gdf_muni: GeoDataFrame de municipios con columna 'tiene_punto'
    Retorna:
        None (muestra el gráfico)
    """
    colors = gdf_muni["tiene_punto"].map({True: "green", False: "grey"})
    fig, ax = plt.subplots(figsize=(12, 10))
    gdf_muni.plot(ax=ax, color=colors, edgecolor="black")
    ax.set_title("Cobertura de estaciones de temperatura por municipio", fontsize=14)
    plt.show()



def plot_mapa_cobertura(gdf_muni, gdf_puntos):
    """
    Muestra un mapa completo con municipios con puntos en verde y sin puntos en gris.
    Parametros:
        gdf_muni: GeoDataFrame de municipios con columna 'tiene_punto'
        gdf_puntos: GeoDataFrame de puntos de estaciones
    Retorna:
        None (muestra el gráfico)

    """
    fig, ax = plt.subplots(figsize=(10, 8))
    # Municipios sin puntos
    gdf_muni[~gdf_muni["tiene_punto"]].plot(ax=ax, color="lightgrey", edgecolor="black", label="Sin puntos")
    # Municipios con puntos
    gdf_muni[gdf_muni["tiene_punto"]].plot(ax=ax, color="lightgreen", edgecolor="black", label="Con puntos")
    # Puntos de estaciones
    gdf_puntos.plot(ax=ax, color="red", markersize=2, alpha=0.2, label="Estaciones")
    plt.legend()
    plt.title("Cobertura de estaciones de temperatura por municipio")
    plt.xlabel("Longitud")
    plt.ylabel("Latitud")
    plt.show()