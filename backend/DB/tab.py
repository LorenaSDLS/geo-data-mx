from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Float

Base = declarative_base()

class Municipios(Base):
    __tablename__ = "municipios"
    cvegeo = Column(String, primary_key=True)
    cve_ent = Column(String)
    cve_mun = Column(String)
    nombre_ent = Column(String)
    nomgeo = Column(String)

class InfoMunicipios(Base):
    __tablename__ = "info_municipios"
    cvegeo = Column(String, primary_key=True)
    tiene_info = Column(Boolean)
    es_principal = Column(Boolean)

class MatrizSimilitud(Base):
    __tablename__ = "matriz_similitud"
    cvegeo_origen = Column(String, primary_key=True)
    cvegeo_destino = Column(String, primary_key=True)
    similitud = Column(Float)

class MatrizConfianza(Base):
    __tablename__ = "matriz_confianza"
    municipio = Column(String, primary_key=True)
    municipio_principal = Column(String)
    confianza = Column(Float)
