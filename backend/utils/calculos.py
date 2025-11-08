
import pandas as pd
from backend.DB.conexion import leer_tabla, top_similares_sql

def aplicar_confianza(top_preseleccion: pd.DataFrame, cvegeo: str):
    """
    Agrega la confianza de la matriz de confianza y calcula puntaje ponderado.
    Descarta municipios con confianza 0.
    """
    matriz_confianza = leer_tabla("matriz_confianza")
    
    # Filtrar confianza solo para los preseleccionados
    confianza_subset = matriz_confianza[
        (matriz_confianza["municipio"] == cvegeo) &
        (matriz_confianza["municipio_principal"].isin(top_preseleccion["municipio_similar"]))
    ][["municipio_principal", "confianza"]]

    top_preseleccion = top_preseleccion.merge(
        confianza_subset,
        left_on="municipio_similar",
        right_on="municipio_principal",
        how="left"
    )

    # Confianza faltante → 0
    top_preseleccion["confianza"] = top_preseleccion["confianza"].fillna(0)

    # Filtrar confianza cero
    top_preseleccion = top_preseleccion[top_preseleccion["confianza"] > 0].copy()

    # Calcular puntaje ponderado
    top_preseleccion["PUNTAJE"] = 0.5 * (top_preseleccion["similitud"] * 100) + 0.5 * top_preseleccion["confianza"]

    # Guardar tabla intermedia
    top_preseleccion.to_parquet(f"debug_top_confianza_{cvegeo}.parquet", index=False)
    
    return top_preseleccion

def calcular_tda(municipio_id: str, candidatos: pd.DataFrame):
    """
    Devuelve un score TDA 0-1 para cada municipio candidato.
    Por ahora, placeholder simple: devuelve similitud * 0.01 (o algún valor aleatorio para test).
    """
    import numpy as np
    candidatos = candidatos.copy()
    np.random.seed(42)
    candidatos["TDA"] = np.random.rand(len(candidatos))  # simula TDA
    return candidatos
