# orm_models/animal.py
"""ORM model for the ``animales`` table (pacientes)."""
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean, CheckConstraint,
)
from sqlalchemy.sql import func
# Importamos Base directamente de tu gestor de conexiones
from database.connection import Base

# Fase 6 (DB-M2): whitelists importadas desde ``config`` para que las
# ``CheckConstraint`` declarativas y la migración ``b3c4d5e6f7a8`` usen
# exactamente la misma fuente de verdad que los servicios.
try:
    from config import ESTADOS_ANIMAL
except Exception:  # pragma: no cover - fallback defensivo si config no cargó
    ESTADOS_ANIMAL = ['Activo', 'En Tratamiento', 'Cuarentena', 'Dado de Alta']


class Animal(Base):
    """Paciente del centro veterinario.

    Fase 6:
      * DB-M2: ``__table_args__`` agrega ``CheckConstraint`` en ``sexo``
        y ``estado`` alineados con los valores que efectivamente usa la
        UI (``Macho``/``Hembra``/``Desconocido``) y con la whitelist
        ``ESTADOS_ANIMAL`` de ``config.py``. SQLite las hace cumplir;
        PostgreSQL también.
      * DB-M3: columna ``updated_at`` auditada por el listener
        ``before_flush`` de ``database/connection.py``.
    """

    __tablename__ = "animales"

    # CheckConstraints declarativos (DB-M2). En SQLite se aplican al
    # crear la tabla; para tablas existentes, la migración
    # ``b3c4d5e6f7a8`` las agrega vía ``batch_alter_table``.
    __table_args__ = (
        # Sexo: la UI envía ``Macho``/``Hembra``/``Desconocido`` (combo
        # en ``animal_dialog.py``). La spec sugería ('M','H','MD') pero
        # eso habría roto todos los INSERTs existentes — usamos los
        # valores reales.
        CheckConstraint(
            "sexo IN ('Macho', 'Hembra', 'Desconocido')",
            name="ck_animales_sexo",
        ),
        # Estado: alineado con ``config.ESTADOS_ANIMAL`` (whitelist que
        # ya usan los servicios en sus validaciones de negocio).
        CheckConstraint(
            "estado IN ('Activo', 'En Tratamiento', 'Cuarentena', 'Dado de Alta')",
            name="ck_animales_estado",
        ),
    )

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
    # Fase 6 (DB-M3): columna de auditoría para UPDATEs. Se setea
    # automáticamente por el listener ``before_flush`` registrado en
    # ``database/connection.py`` (ver ``_set_updated_at``).
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
