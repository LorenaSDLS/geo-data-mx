from sqlalchemy import create_engine, inspect
import pandas as pd

# Conexión a la base de datos
engine = create_engine("postgresql+psycopg2://postgres:B-4789072@localhost:5432/agroanalytics")
inspector = inspect(engine)


# Cargar CSV
df = pd.read_csv("/Users/lorenasolis/EstInv/backend/DB/cultivos_anuales_largo.csv")

# Renombrar columnas para postgres
df = df.rename(columns={
    "Producción": "produccion",
    "Año": "anio"
})

# Subir a PostgreSQL
df.to_sql(
    "muni_cultivos",
    engine,
    if_exists="replace",   # replace = borra y crea de nuevo
    index=False
)

print("✔ Tabla 'muni_cultivos' creada y cargada correctamente")