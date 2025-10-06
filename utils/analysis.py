import pandas as pd

def data_resume(df):
    print(f"Total de filas: {len(df)}")
    num_estaciones = len(df) // 3
    print(f"Total de estaciones: {num_estaciones}")
    num_municipios = df[['Longitud','Latitud']].drop_duplicates().shape[0]
    print(f"Total de municipios: {num_municipios}")
