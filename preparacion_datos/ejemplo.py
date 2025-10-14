import pandas as pd
import re
from utils.utils import preTDA, limpiar_nan, asignacion_filtrada
from utils.load_data import load_csv, load_shapefile
from utils.file_ops import ensure_dir, find_first_shp
from TDA.tda_similarity import TDA_similarity
from config import CSV_CLIMA, EXTRACTED_DIVISION

variables = ["TMIN", "TMAX", "PRECIP"]

# -------------------- Cargar datos --------------------
df = load_csv(CSV_CLIMA)
ensure_dir(EXTRACTED_DIVISION)
shp_path = find_first_shp(EXTRACTED_DIVISION)
gdf_municipios = load_shapefile(shp_path)

df_todas = {}
for var in variables:
    df_var = preTDA(df, gdf_municipios, variable=var)
    df_var = limpiar_nan(df_var)
    df_var = pd.concat([
        df_var,
        pd.DataFrame({
            'estado': df_var['CVE_ENT'],
            'municipio': df_var['NOMGEO'],
            'variable': var
        }, index=df_var.index)
    ], axis=1)
    cols = ['estado', 'municipio', 'variable'] + [c for c in df_var.columns if re.match(r"\d{4}-\d{2}-\d{2}", c)]
    df_todas[var] = df_var[cols]

# -------------------- Función rápida para MVP --------------------
def municipios_similares_mvp(municipio_objetivo, df_todas, variables, top_n=5):
    # df1s: municipio objetivo
    df1s = [df_todas[var][df_todas[var]['municipio'] == municipio_objetivo] for var in variables]
    # df2s: todos los demás municipios
    df2s = [df_todas[var][df_todas[var]['municipio'] != municipio_objetivo] for var in variables]

    serie_cols = list(df_todas["TMIN"].columns[3:])
    similarity = TDA_similarity(
        serie_cols=serie_cols,
        embedding_dimension=30,
        embedding_time_delay=5,
        stride=5,
        n_components=3,
        metric="wasserstein"
    )
    D_multi = similarity.tda_matrix(df1s, df2s)

    df2_names = df2s[0]['municipio'].tolist()
    D_df = pd.DataFrame(D_multi, index=[municipio_objetivo], columns=df2_names)
    similares = D_df.loc[municipio_objetivo].sort_values().head(top_n).index.tolist()
    return similares

# -------------------- MVP interactivo --------------------
if __name__ == "__main__":
    while True:
        municipio_objetivo = input("Escribe el nombre del municipio (o 'salir'): ")
        if municipio_objetivo.lower() == 'salir':
            break
        if municipio_objetivo not in df_todas["TMIN"]['municipio'].values:
            print("Municipio no encontrado. Intenta de nuevo.")
            continue
        top_similares = municipios_similares_mvp(municipio_objetivo, df_todas, variables, top_n=5)
        print(f"Municipios más similares a {municipio_objetivo}: {top_similares}")
        print("-"*50)