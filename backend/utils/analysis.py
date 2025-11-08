import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from .calculos import aplicar_confianza, calcular_tda
from backend.DB.conexion import leer_tabla, top_similares_sql



def principales_similares(cvegeo: str, top_n: int = 10, preseleccion: int = 40):
    """
    Devuelve los municipios más similares a un municipio dado,
    ponderando 50% similitud (0-100) y 50% confianza.
    
    Parámetros:
    - cvegeo: str -> CVEGEO del municipio base
    - top_n: int -> cantidad de municipios a mostrar
    - preseleccion: int -> cantidad de candidatos a considerar antes de calcular el puntaje final
    """

    # -------------------------------
    # Cargar matrices
    # -------------------------------

    matriz_confianza = leer_tabla("matriz_confianza")
    tabla_muni = leer_tabla("municipios")
    similares = top_similares_sql(cvegeo=cvegeo, top_n=preseleccion)

    # -------------------------------
    # 2️⃣ Filtrar filas donde aparece el municipio
    # -------------------------------


    # Identificar el "otro" municipio en cada fila
    similares["municipio_similar"] = similares.apply(
        lambda row: row["cvegeo_destino"] if row["cvegeo_origen"] == cvegeo else row["cvegeo_origen"],
        axis=1
    )


    # -------------------------------
    # Seleccionar preseleccionados por similitud
    # -------------------------------
    similares_top = similares.sort_values("similitud", ascending=False).drop_duplicates(subset=["municipio_similar"]).head(preseleccion)

    # -------------------------------
    # Buscar confianza solo de los preseleccionados
    # -------------------------------
    confianza_subset = matriz_confianza[
        matriz_confianza["municipio_principal"].isin(similares_top["municipio_similar"]) &
        (matriz_confianza["municipio"] == cvegeo)
    ][["municipio_principal", "confianza"]]

    similares_top = similares_top.merge(
        confianza_subset,
        left_on="municipio_similar",
        right_on="municipio_principal",
        how="left"
    )

    # Si alguna confianza falta, asumimos 0
    similares_top["confianza"] = similares_top["confianza"].fillna(0)

    # -------------------------------
    # Calcular puntaje ponderado (similitud 0-100)
    # -------------------------------
    similares_top["PUNTAJE"] = 0.5 * (similares_top["similitud"] * 100) + 0.5 * similares_top["confianza"]

    # -------------------------------
    # Ordenar y tomar top N
    # -------------------------------
    top_similares = similares_top[similares_top["confianza"] > 0]
    top_similares = top_similares.sort_values("PUNTAJE", ascending=False).head(top_n)

    # -------------------------------
    # Merge con nombres de municipios
    # -------------------------------
    top_similares = top_similares.merge(
        tabla_muni[["cvegeo", "nomgeo", "nombre_ent"]],
        left_on="municipio_similar",
        right_on="cvegeo",
        how="left"
    )

    # -------------------------------
    # Selección final de columnas
    # -------------------------------
    top_similares["SIMILITUD_%"] = top_similares["similitud"] * 100

    top_similares = (
        top_similares
        .sort_values("PUNTAJE", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    top_similares.index += 1

    return top_similares[["municipio_similar", "nomgeo", "nombre_ent", "SIMILITUD_%", "confianza", "PUNTAJE"]].reset_index(drop=True)



def obtener_preseleccion(cvegeo: str, preseleccion: int = 40):
    """
    Devuelve los N municipios más similares al municipio base según la matriz de similitud.
    """
 
    
    # Filtrar filas donde aparece el municipio
    similares = top_similares_sql(cvegeo=cvegeo, top_n=preseleccion)


    # Identificar el "otro" municipio
    similares["municipio_similar"] = similares.apply(
        lambda row: row["cvegeo_destino"] if row["cvegeo_origen"] == cvegeo else row["cvegeo_origen"],
        axis=1
    )

    # Top N por similitud
    top_preseleccion = similares.sort_values("similitud", ascending=False)\
                                .drop_duplicates(subset=["municipio_similar"])\
                                .head(preseleccion)
    
    # Guardar tabla intermedia
    top_preseleccion.to_parquet(f"debug_top_preseleccion_{cvegeo}.parquet", index=False)
    
    return top_preseleccion

def expandir_top(top_ponderado: pd.DataFrame, cvegeo: str, expand_n: int = 3):
    """
    Para cada top 10 municipio, busca sus top 'expand_n' similares y calcula tabla top 30.
    """
    
    
    municipios_base = top_ponderado["municipio_similar"].tolist()
    similares_expandidos = []

    for muni in municipios_base:
        subset = top_similares_sql(cvegeo=muni, top_n=expand_n)


        subset["municipio_similar"] = subset.apply(
            lambda row: row["cvegeo_destino"] if row["cvegeo_origen"] == muni else row["cvegeo_origen"],
            axis=1
        )

        top_expand = subset.sort_values("similitud", ascending=False)\
                           .drop_duplicates(subset=["municipio_similar"])\
                           .head(expand_n)
        
        similares_expandidos.append(top_expand)

    top30 = pd.concat(similares_expandidos).drop_duplicates(subset=["municipio_similar"])
    
    # Guardar tabla intermedia
    top30.to_parquet(f"debug_top30_{cvegeo}.parquet", index=False)
    
    return top30

def calcular_top_final(cvegeo: str, top_n: int = 10):
    # Paso 1: Preselección top 40
    top40 = obtener_preseleccion(cvegeo, preseleccion=40)
    
    # Paso 2: Añadir confianza y puntaje parcial
    top10_ponderado = aplicar_confianza(top40, cvegeo).head(top_n)
    
    # Paso 3: Expandir top 10 → top 30
    top30 = expandir_top(top10_ponderado, cvegeo, expand_n=3)
    
    # Paso 4: Añadir confianza de cvegeo
    top30 = aplicar_confianza(top30, cvegeo)
    
    # Paso 5: Calcular TDA
    top30 = calcular_tda(cvegeo, top30)
    
    # Paso 6: Puntaje final: 0.25 similitud + 0.50 TDA + 0.25 confianza
    top30["PUNTAJE_FINAL"] = 100 * (0.25 * (top30["similitud"]*100) + 0.50 * top30["TDA"]*100 + 0.25 * top30["confianza"]) / 100

        # --- Agregar nombres y formato ---
    tabla_muni = leer_tabla("municipios")
    top30 = top30.merge(
        tabla_muni[["cvegeo", "nomgeo", "nombre_ent"]],
        left_on="municipio_similar",
        right_on="cvegeo",
        how="left"
    )

    # Crear la columna en porcentaje
    top30["SIMILITUD_%"] = (top30["similitud"] * 100).round(2)
    top30 = (
        top30
        .sort_values("PUNTAJE_FINAL", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    top30.index += 1


    
    # Guardar tabla final
    top30.to_parquet(f"debug_top_final_{cvegeo}.parquet", index=False)

    
    # Ordenar y top N
    return top30.sort_values("PUNTAJE_FINAL", ascending=False).head(top_n)
