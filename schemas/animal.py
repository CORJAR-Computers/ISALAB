# schemas/animal.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Any


class AnimalSchema(BaseModel):
    # ── Identificación ──
    codigo: str = Field(..., min_length=3, description="Código único del paciente")
    nombre: str = Field(..., min_length=1, description="El nombre es obligatorio")

    # ── Perfil Fenotípico ──
    especie: str = Field(..., min_length=1)
    raza: Optional[str] = None
    sexo: Optional[str] = None
    color: Optional[str] = None
    tipo_pelo: Optional[str] = None
    senas_particulares: Optional[str] = None
    microchip: Optional[str] = None

    # ── Datos Biométricos ──
    edad: Optional[int] = Field(None, ge=0, le=100, description="Edad entre 0 y 100")
    unidad_edad: str = Field(default="Años")
    fecha_nacimiento: Optional[str] = None
    peso: Optional[float] = Field(None, gt=0, description="Peso mayor a 0")

    # ── Datos del Propietario ──
    propietario: Optional[str] = None
    propietario_tipo_doc: Optional[str] = None
    propietario_documento: Optional[str] = None
    propietario_direccion: Optional[str] = None
    propietario_oficio: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

    # ── Estado y Gestión ──
    estado: str = "Activo"
    observaciones: Optional[str] = None
    fecha_ingreso: Optional[str] = None

    # ── Validaciones de Campo ──
    @field_validator('nombre', 'especie', 'codigo')
    @classmethod
    def limpiar_textos(cls, value: str) -> str:
        """Quita espacios al principio y al final si el usuario se equivocó"""
        return value.strip() if value else value

    # ══════════════════════════════════════════════════════════════════════
    # LA MAGIA PARA PYSIDE6: Convertir "" (vacíos) en True None
    # ══════════════════════════════════════════════════════════════════════
    @model_validator(mode='before')
    @classmethod
    def convertir_vacios_a_none(cls, data: Any) -> Any:
        """
        Los campos de texto de PySide6 siempre devuelven "" si están vacíos.
        Esta función intercepta eso y lo cambia por None para que la BD
        guarde NULL real en lugar de un string sin texto.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                # Si el valor es un string y está completamente vacío (o solo espacios)
                if isinstance(value, str) and value.strip() == "":
                    data[key] = None
        return data