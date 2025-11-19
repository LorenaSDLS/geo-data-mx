import pandas as pd
import sys
import os
import folium
import geopandas as gpd
from shapely import wkb
from sqlalchemy import create_engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.DB.conexion import leer_tabla, top_similares_sql, leer_datos_edaficos, mapa_municipios_top, datos_cultivos_municipio
import numpy as np
from backend.utils.similitudes import *
from backend.DB.geografia import *

# ------------------ Categorías de datos ------------------ #
# (principales, sin info y secundarios)

#función para obtener los principales similares
def principales_similares(cvegeo: str, top_n: int = 10):
    """
    Devuelve los municipios con mayor índice de similitud del municipio elegido.
    """
    # Tabla con nombres de municipios
    tabla_muni = leer_tabla("municipios")
    # Top 10 municipios similares desde la DB
    similares = top_similares_sql(cvegeo=cvegeo, top_n=top_n + 1)
    # Identificar el "otro" municipio en cada fila
    similares["municipio_similar"] = [
        row["cvegeo_destino"] if row["cvegeo_origen"] == cvegeo else row["cvegeo_origen"]
        for _, row in similares.iterrows()
    ]
    # Excluir el municipio base
    similares = similares[similares["municipio_similar"] != cvegeo]
    # Merge con nombres de municipios
    top_similares = similares.merge(
        tabla_muni[["cvegeo", "nomgeo", "nombre_ent"]],
        left_on="municipio_similar",
        right_on="cvegeo",
        how="left"
    )

    # Índice de similitud en porcentaje
    top_similares["SIMILITUD"] = top_similares["similitud"] * 100
    # Selección de columnas finales
    resultado_principales = top_similares[["cvegeo","nomgeo", "nombre_ent", "SIMILITUD"]].head(top_n).reset_index(drop=True)
    resultado_principales.columns = ["cvegeo","Municipio", "Estado", "Similitud"]
    resultado_principales.index += 1
    #  Crear mapa usando la lista de CVEGEO
    lista_cvegeo = resultado_principales["cvegeo"].tolist()
    mapa = mapa_municipios_top(cvegeo, lista_cvegeo)
    
    cultivos_general, cultivos_anual, graf1, graf2 = datos_cultivos_municipio(cvegeo)
    return resultado_principales, mapa, cultivos_general, cultivos_anual, graf1, graf2


    #return resultado_principales, mapa

#función en caso de que el municipio seleccionado no tenga información
def municipios_sin_info(cvegeo_base: str, min_municipios: int = 10, incremento_km: float = 5.0):
    """
    Función principal para municipios sin info, usando consultas optimizadas en PostGIS.
    """
    cercanos = municipios_cercanos(cvegeo_base, min_municipios, incremento_km=20.0)
    print("Resultado final de municipios cercanos:")
    print(cercanos[["nomgeo", "nombre_ent"]])  # solo nombre y estado
    # Crear tabla limpia
    tabla_limpia = cercanos[["cvegeo","nomgeo", "nombre_ent", "distancia_km"]].copy()
    tabla_limpia.index = range(1, len(tabla_limpia) + 1)  # índice empezando en 1
    tabla_limpia = tabla_limpia.rename(columns={
        "nomgeo": "Municipio",
        "nombre_ent": "Estado",
        "distancia_km": "Distancia (km)"
    })
    # 3️⃣ Crear mapa solo con los municipios ya definidos
    if not tabla_limpia.empty:
        lista_cvegeo = tabla_limpia["cvegeo"].tolist()
        mapa = mapa_municipios_top(cvegeo_base, lista_cvegeo)
    else:
        mapa = None  # No hay municipios, no se crea mapa

    cultivos_general, cultivos_anual, graf1, graf2 = datos_cultivos_municipio(cvegeo_base)
    return tabla_limpia, mapa, cultivos_general, cultivos_anual, graf1, graf2
    #return tabla_limpia, mapa

#función en caso de que el municipio seleccionado tenga información pero no sea principal

def municipios_secundarios(cvegeo_base: str, top_n: int = 10):
    """
    Función principal para municipios que tienen información pero no son principales.
    Mejora: usa pesos y evita valores muy bajos en la similitud promedio.
    """
    import pandas as pd

    # 1. Obtener candidatos secundarios (hasta 40)
    lista_candidatos = candidatos_secundarios(cvegeo_base, top_n=top_n)

    # 2. Construir la matriz normalizada para el municipio base + candidatos
    matriz_norm, columnas_norm = matriz_normalizada(cvegeo_base, lista_candidatos)
    matriz_norm = matriz_norm.reset_index(drop=True)

    # 3. Definir pesos (mayor peso para variables climáticas)
    pesos = {col: 3 if col.startswith("promedio_") else 1 for col in columnas_norm}


    # 4. Calcular la matriz de similitud
    matriz_sim = pd.DataFrame(index=matriz_norm["cvegeo_muni"], columns=matriz_norm["cvegeo_muni"], dtype=float)
    for i, muni_i in enumerate(matriz_norm["cvegeo_muni"]):
        for j, muni_j in enumerate(matriz_norm["cvegeo_muni"]):
            sim_vals = []
            for col in columnas_norm:
                x = matriz_norm.at[i, col]
                y = matriz_norm.at[j, col]
                if pd.isna(x) or pd.isna(y):
                    val = 0.0
                else:
                    val = 1 - abs(x - y)
                sim_vals.append(val * pesos[col])
            # Promedio ponderado
            matriz_sim.at[muni_i, muni_j] = sum(sim_vals) / sum(pesos[col] for col in columnas_norm) * 100  # porcentaje

    # 5. Tomar la fila del municipio base y obtener top_n similares
    fila_base = matriz_sim.loc[cvegeo_base].sort_values(ascending=False)
    top_similares_cvegeo = fila_base.index[fila_base.index != cvegeo_base][:top_n]
    top_sim_valores = fila_base[top_similares_cvegeo]

    # 6. Merge con nombres de municipios
    tabla_muni = leer_tabla("municipios")
    resultado = pd.DataFrame({
        "cvegeo": top_similares_cvegeo,
        "SIMILITUD": top_sim_valores.values
    }).merge(
        tabla_muni[["cvegeo", "nomgeo", "nombre_ent"]],
        on="cvegeo",
        how="left"
    )

    # 7. Seleccionar columnas finales
    resultado_final = resultado[["cvegeo","nomgeo", "nombre_ent", "SIMILITUD"]].copy()
    resultado_final.columns = ["cvegeo","Municipio", "Estado", "Similitud"]
    resultado_final.index = range(1, len(resultado_final) + 1)
    lista_cvegeo = resultado_final["cvegeo"].tolist()
    mapa = mapa_municipios_top(cvegeo_base, lista_cvegeo)

    cultivos_general, cultivos_anual, graf1, graf2 = datos_cultivos_municipio(cvegeo_base)
    return resultado_final, mapa, cultivos_general, cultivos_anual, graf1, graf2


    #return resultado_final, mapa
