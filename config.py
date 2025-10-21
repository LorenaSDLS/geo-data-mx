from pathlib import Path

#Ruta base del proyecto
base_path = Path("/Users/lorenasolis/EstInv")
#rutas para datos
RAW_PATH = base_path / "data" / "raw"
PROCESSED_PATH = base_path / "data" / "processed"


#Archivos de entradas principales
CSV_CLIMA = RAW_PATH / "climatologia_limpio.csv"
CSV_CLIMA_ANUAL = PROCESSED_PATH / "datos_anuales.csv"
ZIP_DIVISION = RAW_PATH / "division_politica.zip"
EXTRACTED_DIVISION = RAW_PATH / "divpoli_limpia"
ZIP_USO_SUELO = RAW_PATH / "uso_de_suelo.zip"
EXTRACTED_USO_SUELO = RAW_PATH / "uso_de_suelo_limpio"

#Definición de sistemas de coordenadas
CRS_GEOG = "EPSG:4326" #Lat/lon (WGS84)
CRS_METRIC = "EPSG:3857" #Proyección métrica (Web Mercator) Ppara buffers en metros

#parámetros espaciales
BUFFER_MET=100  # radio de Buffer de 100 metros para asignar puntos a municipios
NEIGHBOR_RADIUS_KM = 10 #RADIO BASE PARA VECINOS
NEIGHBOR_MAX_KM = 50 #RADIO MÁXIMO PARA VECINOS