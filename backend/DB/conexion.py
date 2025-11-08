from sqlalchemy import create_engine
import pandas as pd

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
