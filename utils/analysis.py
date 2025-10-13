import pandas as pd

def data_resume(df):
    print(f"Total de filas: {len(df)}")
    num_estaciones = len(df) // 3
    print(f"Total de estaciones: {num_estaciones}")
    num_municipios = df[['Longitud','Latitud']].drop_duplicates().shape[0]
    print(f"Total de municipios: {num_municipios}")

def punto_temp_duplicados(df):
    duplicated = df.duplicated(subset=['Latitud', 'Longitud'], keep=False)
    if duplicated.any():
        print("Hay puntos de temperatura duplicados:")
        print(df[duplicated])
    else:
        print("No hay puntos de temperatura duplicados.")
    return df[duplicated]
