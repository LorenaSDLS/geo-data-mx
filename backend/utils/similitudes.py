import pandas as pd
import numpy as np
from backend.DB.conexion import leer_datos_edaficos
from backend.utils.calculos import *
import pandas as pd
import numpy as np
from backend.DB.conexion import engine  # para hacer consultas directas a la DB

from backend.utils.calculos import *
from backend.DB.conexion import leer_tabla, top_similares_sql

def candidatos_secundarios(cvegeo: str, top_n: int = 10):
    """
    Devuelve hasta 40 municipios candidatos secundarios para un municipio dado,
    incluyendo sus top similares y los top similares de esos candidatos.
    """

    # Tabla con nombres de municipios
    tabla_muni = leer_tabla("municipios")
    # Top 10 municipios similares desde la DB
    similares = top_similares_sql(cvegeo=cvegeo, top_n=top_n + 1)
    # Identificar el "otro" municipio en cada fila
     # Crear la columna 'municipio_similar'
    similares["municipio_similar"] = [
        row["cvegeo_destino"] if row["cvegeo_origen"] == cvegeo else row["cvegeo_origen"]
        for _, row in similares.iterrows()
    ]
    # guardar los 10 id de los candidatos en una lista
    lista_candidatos = similares["municipio_similar"].tolist()[:top_n]
    # por cada candidato en la lista, obtener su top 3 similares y guardar su id obteniendo al final 40 id
    for candidato in lista_candidatos.copy():
        similares_candidato = top_similares_sql(cvegeo=candidato, top_n=4)
        similares_candidato["municipio_similar"] = [
            row["cvegeo_destino"] if row["cvegeo_origen"] == candidato else row["cvegeo_origen"]
            for _, row in similares_candidato.iterrows()
        ]
        for id_similar in similares_candidato["municipio_similar"]:
            if id_similar != cvegeo and id_similar not in lista_candidatos:
                lista_candidatos.append(id_similar)
                if len(lista_candidatos) >= 40:
                    break
        if len(lista_candidatos) >= 40:
            break

    return lista_candidatos[:40]

def obtener_info_secundarios(cvegeo_base: str, top_n: int = 10):
    """
    Obtiene la información relevante de los municipios secundarios similares.
    
    Retorna:
    - lista de municipios secundarios
    - DataFrame con promedios climáticos
    - diccionario con min y max de variables climáticas y edafológicas
    """
    # 1️⃣ Obtener lista de candidatos secundarios
    lista_secundarios = candidatos_secundarios(cvegeo=cvegeo_base, top_n=top_n)

    # 2️⃣ Obtener promedios climáticos para TMIN, TMAX y PRECIP
    prom_tmin = promedio_climatico(variable="TMIN")
    prom_tmax = promedio_climatico(variable="TMAX")
    prom_precip = promedio_climatico(variable="PRECIP")

    # Filtrar solo los municipios secundarios
    prom_tmin = prom_tmin[prom_tmin["cvegeo_muni"].isin(lista_secundarios)].reset_index(drop=True)
    prom_tmax = prom_tmax[prom_tmax["cvegeo_muni"].isin(lista_secundarios)].reset_index(drop=True)
    prom_precip = prom_precip[prom_precip["cvegeo_muni"].isin(lista_secundarios)].reset_index(drop=True)

    # 3️⃣ Construir diccionario de mínimos y máximos globales
    dicc_min_max = diccionario_min_max()

    # 4️⃣ Devolver todo
    return {
        "lista_secundarios": lista_secundarios,
        "prom_tmin": prom_tmin,
        "prom_tmax": prom_tmax,
        "prom_precip": prom_precip,
        "min_max_global": dicc_min_max
    }


def matriz_normalizada(cvegeo_base: str,
                       candidatos: list,
                       tabla_clima="clima",
                       tabla_edafologia="edafologia",
                       vars_climaticas=["TMIN", "TMAX", "PRECIP"],
                       vars_edaf_num=["altitud", "pendiente", "pedreg", "afloram", "est_tam", "plas", "ph", "cic"],
                       vars_edaf_categ=["horizonte", "col_seco_l", "col_hum_l"]):
    """
    Construye la matriz normalizada de valores para el municipio base y sus candidatos.
    
    Retorna:
    - df_matriz: pd.DataFrame -> matriz normalizada
    - columnas_norm: list -> nombres de columnas normalizadas
    """
    import pandas as pd

    # Lista de todos los municipios (base + candidatos)
    todos_munis = [cvegeo_base] + candidatos

    # Diccionario con valores mínimos y máximos globales
    min_max_dict = diccionario_min_max(climaticas=vars_climaticas, edafologicas=vars_edaf_num)

    # --- 1. Variables climáticas ---
    df_clima = pd.DataFrame({"cvegeo_muni": todos_munis})
    for var in vars_climaticas:
        df_prom = promedio_climatico(tabla=tabla_clima, variable=var)
        df_clima = df_clima.merge(df_prom, how="left", left_on="cvegeo_muni", right_on="cvegeo_muni")
        col_prom = "promedio_" + var
        df_clima[col_prom + "_norm"] = df_clima[col_prom].apply(
            lambda x: normalizar_valor(x, nombre_var=var, tipo="clima",
                                       xmin=min_max_dict[var]["min"],
                                       xmax=min_max_dict[var]["max"])
        )

    # --- 2. Variables edafológicas numéricas ---
    df_edaf = leer_tabla(tabla_edafologia, columnas=["cvegeo_muni"] + vars_edaf_num + vars_edaf_categ)
    df_edaf = df_edaf[df_edaf["cvegeo_muni"].isin(todos_munis)]

    # Normalizar variables numéricas
    for var in vars_edaf_num:
        df_edaf[var + "_norm"] = df_edaf[var].apply(
            lambda x: normalizar_valor(x, nombre_var=var, tipo="edafologia",
                                       tabla_edafologia=tabla_edafologia,
                                       xmin=min_max_dict[var]["min"],
                                       xmax=min_max_dict[var]["max"])
        )

    # --- 3. Variables edafológicas categóricas ---
    df_edaf_categ_norm = convertir_variables_categoricas_simple(df_edaf)

    # --- 4. Combinar todo ---
    df_matriz = pd.concat([
        df_clima[["cvegeo_muni"] + [col + "_norm" for col in ["promedio_" + v for v in vars_climaticas]]],
        df_edaf[[col + "_norm" for col in vars_edaf_num]],
        df_edaf_categ_norm
    ], axis=1)

    # Lista final de columnas normalizadas
    columnas_norm = [col for col in df_matriz.columns if col.endswith("_norm")]

    return df_matriz, columnas_norm


def matriz_similitud_secundarios(matriz_normalizada: pd.DataFrame, variables: list):
    """
    Calcula la matriz de similitud entre los municipios secundarios y el municipio base.
    
    Parámetros:
    - matriz_normalizada: pd.DataFrame → filas = municipios (primera fila = municipio base), 
                                               columnas = variables normalizadas
    - variables: list → lista de nombres de columnas a usar para calcular similitud
    
    Retorna:
    - pd.DataFrame → matriz de similitud (filas y columnas = municipios)
    """
    # Número de municipios
    n = matriz_normalizada.shape[0]

    # Inicializar matriz de similitud
    matriz_sim = pd.DataFrame(np.zeros((n, n)), 
                              index=matriz_normalizada.index, 
                              columns=matriz_normalizada.index)

    # Recorrer cada par de municipios
    for i in range(n):
        for j in range(i, n):  # matriz simétrica, podemos usar solo la mitad
            similitudes = []
            for var in variables:
                x1 = matriz_normalizada.iloc[i][var]
                x2 = matriz_normalizada.iloc[j][var]
                s = similitud_escala(x1, x2)
                similitudes.append(s)
            # promedio de similitudes por todas las variables
            valor_sim = np.mean(similitudes)
            matriz_sim.iloc[i, j] = valor_sim
            matriz_sim.iloc[j, i] = valor_sim  # simétrica

    return matriz_sim



def info_secundarios_similares(matriz_sim: pd.DataFrame, tabla_municipios: str = "municipios", top_n: int = 10):
    """
    Obtiene los top N municipios más similares al municipio base usando la matriz de similitud
    y la tabla de municipios desde la base de datos.

    Parámetros:
    - matriz_sim: pd.DataFrame → matriz de similitud (filas y columnas = cvegeo)
    - tabla_municipios: str → nombre de la tabla de municipios en la base de datos
    - top_n: int → cantidad de municipios más similares a retornar

    Retorna:
    - pd.DataFrame → columnas: 'municipio', 'estado', 'similitud_%'
    """
    # Leer información de municipios desde la DB
    municipios = leer_tabla(tabla_municipios)

    # Municipio base (asumimos que es la primera fila de la matriz)
    municipio_base = matriz_sim.index[0]

    # Fila del municipio base
    similitudes_base = matriz_sim.loc[municipio_base].copy()
    similitudes_base = similitudes_base.drop(municipio_base)  # excluir el mismo

    # Ordenar de mayor a menor
    similitudes_ordenadas = similitudes_base.sort_values(ascending=False).head(top_n)

    # Obtener info de municipios
    info = municipios.set_index("cvegeo").loc[similitudes_ordenadas.index][["nomgeo", "nombre_ent"]].copy()
    info["similitud_%"] = (similitudes_ordenadas * 100).round(2)

    # Resetear índice y renombrar columnas
    info = info.reset_index(drop=True)
    info = info.rename(columns={"nomgeo": "municipio", "nombre_ent": "estado"})

    return info

