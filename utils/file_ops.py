from pathlib import Path
import zipfile

""" Crear una carpeta si no existe"""
def ensure_dir(path:Path):
    path.mkdir(parents=True, exist_ok=True)

""" Extraer un archivo ZIP si no existe la carpeta destino. True -> se extrajo, False -> ya existía"""
def extract_zip(zip_path:Path, extract_to:Path):
    if not extract_to.exists():
        with zipfile.ZipFile(zip_path,"r") as z:
            z.extractall(extract_to)
        return True
    return False

""" Buscar el primer archivo .shp en una ruta dada. Devuelve None si no encuentra nada"""
def find_first_shp(root: Path):
    return next(root.rglob("*.shp"),None)

