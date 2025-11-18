from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from geoalchemy2 import Geometry




Base = declarative_base()

class InfoMunicipios(Base):
    __tablename__ = "info_municipios"
    cvegeo = Column(String, primary_key=True)
    tiene_info = Column(Boolean, nullable=False)
    es_principal = Column(Boolean, nullable=False)

    municipios = relationship("Municipios", back_populates="info")

class Municipios(Base):
    __tablename__ = "municipios"
    cvegeo = Column(String, ForeignKey("info_municipios.cvegeo"), primary_key=True)
    cve_ent = Column(String)
    cve_mun = Column(String)
    nombre_ent = Column(String)
    nomgeo = Column(String)

    info = relationship("InfoMunicipios", back_populates="municipios")
    geografia = relationship("Geografia", back_populates="municipio")


class MatrizSimilitud(Base):
    __tablename__ = "matriz_similitud"
    cvegeo_origen = Column(String, ForeignKey("info_municipios.cvegeo"), primary_key=True)
    cvegeo_destino = Column(String, ForeignKey("info_municipios.cvegeo"), primary_key=True)
    similitud = Column(Float)

class MatrizConfianza(Base):
    __tablename__ = "matriz_confianza"
    municipio = Column(String, ForeignKey("info_municipios.cvegeo"), primary_key=True)
    municipio_principal = Column(String, ForeignKey("info_municipios.cvegeo"))
    confianza = Column(Float)

class Geografia(Base):
    __tablename__ = "geografia"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cvegeo = Column(String, ForeignKey("municipios.cvegeo"))
    area = Column(Float)
    perimeter = Column(Float)
    geometry = Column(Geometry("MULTIPOLYGON"))
    municipio = relationship("Municipios", back_populates="geografia")

class Edafologia(Base):
    __tablename__ = "edafologia"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cvegeo_muni = Column(String, ForeignKey("info_municipios.cvegeo"))
    altitud = Column(Float)
    pendiente = Column(Float)
    pedreg = Column(Float)
    afloram = Column(Float)
    est_tam = Column(Float)
    plas = Column(Float)
    ph = Column(Float)
    cic = Column(Float)
    horizonte = Column(String)
    col_seco_l = Column(String)
    col_hum_l = Column(String)

class Clima(Base):
    __tablename__ = "clima"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cvegeo_muni = Column(String, ForeignKey("info_municipios.cvegeo"))
    anio = Column(Integer)

    precip_enero = Column(Float)
    tmax_enero = Column(Float)
    tmin_enero = Column(Float)
    precip_febrero = Column(Float)
    tmax_febrero = Column(Float)
    tmin_febrero = Column(Float)
    precip_marzo = Column(Float)
    tmax_marzo = Column(Float)
    tmin_marzo = Column(Float)
    precip_abril = Column(Float)
    tmax_abril = Column(Float)
    tmin_abril = Column(Float)
    precip_mayo = Column(Float)
    tmax_mayo = Column(Float)
    tmin_mayo = Column(Float)
    precip_junio = Column(Float)
    tmax_junio = Column(Float)
    tmin_junio = Column(Float)
    precip_julio = Column(Float)
    tmax_julio = Column(Float)
    tmin_julio = Column(Float)
    precip_agosto = Column(Float)
    tmax_agosto = Column(Float)
    tmin_agosto = Column(Float)
    precip_septiembre = Column(Float)
    tmax_septiembre = Column(Float)
    tmin_septiembre = Column(Float)
    precip_octubre = Column(Float)
    tmax_octubre = Column(Float)
    tmin_octubre = Column(Float)
    precip_noviembre = Column(Float)
    tmax_noviembre = Column(Float)
    tmin_noviembre = Column(Float)
    precip_diciembre = Column(Float)
    tmax_diciembre = Column(Float)
    tmin_diciembre = Column(Float)

