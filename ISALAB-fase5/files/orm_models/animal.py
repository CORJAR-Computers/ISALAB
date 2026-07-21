# orm_models/animal.py
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
# Importamos Base directamente de tu gestor de conexiones
from database.connection import Base

class Animal(Base):
    __tablename__ = "animales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, index=True)
    nombre = Column(String(100), nullable=False)
    especie = Column(String(50))
    raza = Column(String(50))
    sexo = Column(String(20))
    color = Column(String(50))
    tipo_pelo = Column(String(50))
    senas_particulares = Column(Text)
    microchip = Column(String(50))
    # -------------------------------------------
    edad = Column(Integer)
    unidad_edad = Column(String(20), default="Años")  # "Años" o "Meses"
    fecha_nacimiento = Column(String(20))  # Opcional, por si se la saben
    peso = Column(Float)
    propietario = Column(String(150))
    propietario_tipo_doc = Column(String(20))
    propietario_documento = Column(String(50))
    propietario_direccion = Column(String(150))
    propietario_oficio = Column(String(100))
    # -------------------------------------
    telefono = Column(String(50))
    email = Column(String(100))
    fecha_ingreso = Column(String(20))
    observaciones = Column(Text)
    estado = Column(String(20), default="Activo")
    # Fase 5 (H-D3): ``created_at`` ahora está mapeado. Antes estaba
    # comentado, aunque la migración ``agregar_created_at_todas_tablas``
    # (Fase 2) ya añadía la columna a la BD. Eso significaba que el ORM
    # no la veía y cualquier ``session.query(Animal).filter(...)``
    # ignoraba la columna. La columna usa ``server_default=now()`` en
    # la migración, así que aquí solo necesitamos declararla lectura.
    created_at = Column(DateTime, server_default=func.now())