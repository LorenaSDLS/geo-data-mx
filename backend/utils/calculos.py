
import pandas as pd
from backend.DB.conexion import leer_tabla, top_similares_sql

#Diccionarios

# Diccionarios globales para variables categóricas
niveles_horizonte = {
    "N": 1, "Ócrico": 2, "Mólico": 3, "Fólico": 4, "Úmbrico": 5,
    "Cámbico": 6, "Árgico": 7, "Cálcico": 8, "Nítico": 9, "Vértico": 10,
    "Gípsico": 11, "Férrico": 12, "Dúrico": 13, "Petrocálcico": 14,
    "Petrodúrico": 15, "Ándico": 16, "Vítrico": 17,
    "Cálcico, Árgico": (8 + 7)/2, "Árgico, Cálcico": (7 + 8)/2,
    "Gípsico, Cálcico": (11 + 8)/2, "Vértico, Cálcico": (10 + 8)/2
}

niveles_col_seco_l = {
    "Negro": 0, "Oscuro": 2, "Marrón oscuro": 3, "Marrón": 4, "Marrón claro": 5,
    "Amarillento": 6, "Amarillo pálido": 7, "Claro": 8, "Muy claro": 9, "Blanco": 10,
    "Marrón oscuro, Marrón": (3 + 4)/2, "Marrón, Marrón claro": (4 + 5)/2
}

niveles_col_hum_l = {
    "Negro": 0, "Oscuro": 2, "Marrón oscuro": 3, "Marrón": 4, "Marrón claro": 5,
    "Amarillento": 6, "Amarillo pálido": 7, "Claro": 8, "Muy claro": 9, "Blanco": 10,
    "Marrón oscuro, Marrón": (3 + 4)/2, "Marrón, Marrón claro": (4 + 5)/2
}


# --- FUNCIONES AUXILIARES PARA CÁLCULO DE SIMILITUDES --- #
#función para sacar el promedio de alguna variable de clima
def promedio_climatico(tabla="clima", variable="TMIN"):
    """
    Calcula el promedio de una variable climática (TMIN, TMAX, PRECIP) por municipio.
    
    Retorna un DataFrame con:
    - cvegeo_muni
    - promedio_variable
    """
    # Leer la tabla completa
    df = leer_tabla(tabla)

    # Filtrar columnas que corresponden a la variable
    cols_variable = [col for col in df.columns if col.startswith(variable)]
    
    # Calcular el promedio por fila (por año, o por registro)
    df["promedio_" + variable] = df[cols_variable].mean(axis=1)
    
    # Agrupar por municipio si hay múltiples años
    df_promedio = df.groupby("cvegeo_muni")["promedio_" + variable].mean().reset_index()
    
    return df_promedio
"""
prom_tmin = promedio_climatico(variable="TMIN")
prom_tmax = promedio_climatico(variable="TMAX")
prom_precip = promedio_climatico(variable="PRECIP")

print(prom_tmin.head(20))
print(prom_tmax.head(20))
print(prom_precip.head(20))
"""
#función para pasar las variables categóricas a numéricas
def convertir_variables_categoricas_simple(df):
    df["horizonte_num"] = df["horizonte"].map(niveles_horizonte)
    df["col_seco_num"] = df["col_seco_l"].map(niveles_col_seco_l)
    df["col_hum_num"] = df["col_hum_l"].map(niveles_col_hum_l)

    # Normalizar
    for col in ["horizonte_num", "col_seco_num", "col_hum_num"]:
        min_val = df[col].min()
        max_val = df[col].max()
        df[col] = (df[col] - min_val) / (max_val - min_val) if max_val != min_val else 1.0

    return df[["horizonte_num", "col_seco_num", "col_hum_num"]]


#función para obtener el valor mínnimo y máximo globar de una variable de edafologia
def min_max_edafologia(variable: str, tabla: str = "edafologia"):
    """
    Devuelve el valor mínimo y máximo global de una variable edafológica.

    Parámetros:
    - variable: str → nombre de la columna en la tabla de edafología
    - tabla: str → nombre de la tabla en la base de datos (por defecto 'edafologia')

    Retorna:
    - (min_val, max_val)
    """
    # Leer solo la columna de interés
    df = leer_tabla(tabla, columnas=[variable])
    
    # Valores mínimo y máximo global
    min_val = df[variable].min()
    max_val = df[variable].max()
    
    return min_val, max_val


#función para obtener el valor minimo y máximo de la variables de clima
def min_max_climatico(variable="TMIN", tabla="clima"):
    """
    Devuelve el valor mínimo y máximo global de una variable climática.
    
    Parámetros:
    - variable: str → 'TMIN', 'TMAX' o 'PRECIP'
    - tabla: str → nombre de la tabla en la base de datos
    
    Retorna:
    - (min_val, max_val)
    """
    # Obtener promedio por municipio
    df_prom = promedio_climatico(tabla=tabla, variable=variable)
    
    # Valores mínimos y máximos globales
    min_val = df_prom["promedio_" + variable].min()
    max_val = df_prom["promedio_" + variable].max()
    
    return min_val, max_val

# función para hacer un diccionario de mínimos y máximos globales
def diccionario_min_max(climaticas: list = ["TMIN", "TMAX", "PRECIP"],
                        edafologicas: list = ["ph", "arcilla", "arena", "limo"]):
    """
    Genera un diccionario con los valores mínimos y máximos globales de variables climáticas y edafológicas.
    
    Retorna:
    {
        "TMIN": {"min": 12.3, "max": 28.4},
        "TMAX": {"min": 18.5, "max": 35.2},
        "PRECIP": {"min": 0, "max": 320},
        "ph": {"min": 4.2, "max": 8.7},
        ...
    }
    """
    min_max_dict = {}

    # Variables climáticas
    for var in climaticas:
        df_prom = promedio_climatico(variable=var)  # tu función
        min_val = df_prom["promedio_" + var].min()
        max_val = df_prom["promedio_" + var].max()
        min_max_dict[var] = {"min": min_val, "max": max_val}

    # Variables edafológicas
    for var in edafologicas:
        min_val, max_val = min_max_edafologia(var)  # tu función
        min_max_dict[var] = {"min": min_val, "max": max_val}

    return min_max_dict


#fórmula de normalización xnom=(x-xmin)/(xmax-xmin)
def normalizar_valor(x, nombre_var=None, tipo="clima", tabla_edafologia=None, xmin=None, xmax=None):
    """
    Normaliza un valor usando xnorm = (x - xmin) / (xmax - xmin)
    
    Parámetros:
    - x: float -> valor a normalizar
    - nombre_var: str -> nombre de la variable (para calcular xmin y xmax si no se pasan)
    - tipo: "clima" o "edafologia"
    - tabla_edafologia: str -> tabla de edafología (si tipo="edafologia")
    - xmin, xmax: float -> mínimo y máximo global de la variable (opcional)
    
    Retorna:
    - valor normalizado entre 0 y 1
    """
    if xmin is None or xmax is None:
        if tipo == "clima":
            df = promedio_climatico(variable=nombre_var)
            col_prom = "promedio_" + nombre_var
            xmin = df[col_prom].min()
            xmax = df[col_prom].max()
        elif tipo == "edafologia":
            if tabla_edafologia is None:
                raise ValueError("Se debe indicar la tabla de edafología")
            df = leer_tabla(tabla_edafologia, columnas=[nombre_var])
            xmin = df[nombre_var].min()
            xmax = df[nombre_var].max()
        else:
            raise ValueError("tipo debe ser 'clima' o 'edafologia'")

    if xmax == xmin:
        return 0.0  # evitar división por cero
    return (x - xmin) / (xmax - xmin)


# formula de similitud y escala: similitud=1-abs(xnom1 - xnom2)
def similitud_escala(x, y):
    import math
    # si x o y es NaN, devolvemos 0.0
    if x is None or y is None or math.isnan(x) or math.isnan(y):
        return 0.0
    return 1 - abs(x - y)  # x e y normalizados entre 0 y 1

