"""ORM models for the IsaLab veterinary diagnostic system.

Re-exports the main ORM classes so callers can do::

    from orm_models import Animal, MuestraORM, RecepcionORM

instead of importing each module individually.
"""
from orm_models.animal import Animal
from orm_models.clinica import (
    MovimientoORM,
    MuestraORM,
    RecepcionORM,
    HistoriaClinicaORM,
    ConsultaORM,
    CirugiaORM,
    VacunacionORM,
)

__all__ = [
    "Animal",
    "MovimientoORM",
    "MuestraORM",
    "RecepcionORM",
    "HistoriaClinicaORM",
    "ConsultaORM",
    "CirugiaORM",
    "VacunacionORM",
]
