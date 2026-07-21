# schemas/clinica.py
from pydantic import BaseModel, Field
from typing import Optional

class RecepcionSchema(BaseModel):
    codigo: str = Field(..., min_length=3)
    animal_id: int = Field(..., gt=0, description="ID del paciente válido")
    # Fase 5 (H-D6): campo ``empresa`` eliminado — era DEAD CODE.
    # ``RecepcionORM`` no tiene columna ``empresa`` (solo ``MuestraORM``
    # la tiene, y se usa para distinguir Persona Natural vs entidad
    # jurídica al generar PDFs de laboratorio). ``RecepcionService``
    # nunca persistía este campo (ver ``registrar_recepcion`` que
    # construye ``Recepcion(codigo=..., animal_id=..., ...)`` sin
    # pasar ``empresa``), y ningún diálogo de recepción lo enviaba en
    # ``data``. Su mera presencia en el schema confundía a futuros
    # desarrolladores.
    fecha_hora: str = Field(...)
    motivo: str = Field(..., min_length=1, description="El motivo es obligatorio")
    veterinario: Optional[str] = None
    estado: str = "En espera"
    proxima_cita: Optional[str] = None
    observaciones: Optional[str] = None

class ConsultaSchema(BaseModel):
    codigo: str = Field(..., min_length=3)
    animal_id: int = Field(..., gt=0)
    historia_id: Optional[int] = None
    fecha: str = Field(...)
    motivo: str = Field(..., min_length=1)
    evolucion: Optional[str] = None
    examen_fisico: Optional[str] = None
    tratamiento: Optional[str] = None
    medicamentos: Optional[str] = None
    proxima_consulta: Optional[str] = None
    veterinario: Optional[str] = None
    observaciones: Optional[str] = None

class CirugiaSchema(BaseModel):
    codigo: str = Field(..., min_length=3)
    animal_id: int = Field(..., gt=0)
    historia_id: Optional[int] = None
    fecha: str = Field(...)
    tipo_cirugia: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    anestesia: Optional[str] = None
    protocolo_anestesico: Optional[str] = None
    duracion_min: Optional[int] = Field(None, ge=0, description="La duración no puede ser negativa")
    cirujano: Optional[str] = None
    anestesiologo: Optional[str] = None
    asistente: Optional[str] = None
    complicaciones: Optional[str] = None
    cuidados_post: Optional[str] = None
    estado: str = "Programada"

class VacunacionSchema(BaseModel):
    codigo: str = Field(..., min_length=3)
    animal_id: int = Field(..., gt=0)
    tipo: str = Field(..., min_length=1)
    producto: str = Field(..., min_length=1, description="El nombre del producto es obligatorio")
    lote: Optional[str] = None
    dosis: Optional[str] = None
    via: Optional[str] = None
    fecha_aplicacion: str = Field(...)
    fecha_proxima: Optional[str] = None
    veterinario: Optional[str] = None
    observaciones: Optional[str] = None

class HistoriaClinicaSchema(BaseModel):
    recepcion_id: int = Field(..., gt=0)
    animal_id: int = Field(..., gt=0)
    fecha: str = Field(...)

    # Textos largos tradicionales
    anamnesis: Optional[str] = None
    examen_fisico: Optional[str] = None
    diagnostico: Optional[str] = None
    diagnostico_diferencial: Optional[str] = None
    tratamiento: Optional[str] = None
    pronostico: Optional[str] = None
    veterinario: Optional[str] = None

    # Constantes numéricas básicas
    temperatura: Optional[float] = None
    frecuencia_cardiaca: Optional[int] = None
    frecuencia_respiratoria: Optional[int] = None
    peso_consulta: Optional[float] = None

    # --- NUEVOS CAMPOS AGREGADOS ---
    dieta: Optional[str] = None
    enfermedades_previas: Optional[str] = None
    cirugias_previas: Optional[str] = None
    esterilizado: Optional[str] = None
    numero_partos: Optional[int] = None
    esquema_vacunal: Optional[str] = None
    ultima_desparasitacion: Optional[str] = None
    tratamientos_recientes: Optional[str] = None
    viajes_recientes: Optional[str] = None
    convive_con_animales: Optional[str] = None
    comportamiento: Optional[str] = None
    condicion_corporal: Optional[str] = None
    tllc: Optional[str] = None
    trpc: Optional[str] = None
    mucosas: Optional[str] = None
    pulso: Optional[str] = None
    deshidratacion: Optional[str] = None