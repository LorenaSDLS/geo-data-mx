from sqlalchemy import create_engine, inspect
import pandas as pd

# Conexión a la base de datos
engine = create_engine("postgresql+psycopg2://postgres:B-4789072@localhost:5432/agroanalytics")
inspector = inspect(engine)

# Lista todas las tablas
tablas = inspector.get_table_names()
print("Tablas en la base de datos:")
for t in tablas:
    print("-", t)