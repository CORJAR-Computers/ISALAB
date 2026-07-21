"""Pydantic schemas for IsaLab request/response validation.

Re-exports the main schema classes so callers can do::

    from schemas import AnimalSchema, RecepcionSchema
"""
from schemas.animal import AnimalSchema
from schemas.clinica import (
    RecepcionSchema,
    ConsultaSchema,
    CirugiaSchema,
    VacunacionSchema,
    HistoriaClinicaSchema,
)

__all__ = [
    "AnimalSchema",
    "RecepcionSchema",
    "ConsultaSchema",
    "CirugiaSchema",
    "VacunacionSchema",
    "HistoriaClinicaSchema",
]
