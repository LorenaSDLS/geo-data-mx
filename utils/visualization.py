import matplotlib.pyplot as plt
import geopandas as gpd


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