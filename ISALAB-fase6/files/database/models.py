# database/models.py
"""Modelos de datos IsaLab"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Animal:
    id: Optional[int] = None
    codigo: str = ""
    nombre: str = ""
    especie: str = ""
    raza: Optional[str] = None
    # --- Campos que faltaban ---
    sexo: Optional[str] = None
    color: Optional[str] = None
    tipo_pelo: Optional[str] = None
    senas_particulares: Optional[str] = None
    microchip: Optional[str] = None
    # ---------------------------
    edad: Optional[int] = None
    unidad_edad: Optional[str] = "Años"
    fecha_nacimiento: Optional[str] = None
    peso: Optional[float] = None
    propietario: Optional[str] = None
    # --- Campos que faltaban ---
    propietario_tipo_doc: Optional[str] = None
    propietario_documento: Optional[str] = None
    propietario_direccion: Optional[str] = None
    propietario_oficio: Optional[str] = None
    # ---------------------------
    telefono: Optional[str] = None
    email: Optional[str] = None
    fecha_ingreso: str = ""
    estado: str = "Activo"
    observaciones: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> 'Animal':
        # Usamos get() por si acaso la query no trae todos los campos (como en búsquedas rápidas)
        return cls(**{k: row.get(k) for k in cls.__dataclass_fields__ if k in row})


@dataclass
class Movimiento:
    id: Optional[int] = None
    animal_id: int = 0
    tipo: str = ""
    fecha_hora: str = ""
    motivo: str = ""
    responsable: str = ""
    destino: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> 'Movimiento':
        # Fase 6 (DB-M5): acceso uniforme con ``row.get(k)`` para
        # tolerar queries que no traen todas las columnas.
        return cls(**{k: row.get(k) for k in cls.__dataclass_fields__ if k in row})


@dataclass
class Muestra:
    id: Optional[int] = None
    codigo: str = ""
    animal_id: int = 0
    empresa: Optional[str] = None  # <-- FALTABA
    tipo_muestra: str = ""
    tipo_analisis: Optional[str] = None
    fecha_recoleccion: str = ""
    fecha_entrega: Optional[str] = None
    estado: str = "Pendiente"
    resultado: Optional[str] = None
    valor_referencia: Optional[str] = None  # Alias para consistencia con BD
    observaciones: Optional[str] = None
    tecnico: Optional[str] = None
    veterinario_ref: Optional[str] = None
    urgente: int = 0
    created_at: Optional[str] = None
    animal_nombre: Optional[str] = None
    animal_codigo: Optional[str] = None
    especie: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> 'Muestra':
        return cls(**{k: row.get(k) for k in cls.__dataclass_fields__ if k in row})

    @property
    def valor_ref(self) -> Optional[str]:
        """Alias para compatibilidad hacia atrás."""
        return self.valor_referencia

    @valor_ref.setter
    def valor_ref(self, value: Optional[str]):
        """Alias para compatibilidad hacia atrás."""
        self.valor_referencia = value
    def es_urgente(self) -> bool:
        return self.urgente == 1


@dataclass
class Recepcion:
    """Ingreso/recepción de un paciente. Código ISAL-XXXX."""
    id: Optional[int] = None
    codigo: str = ""  # ISAL-0001
    animal_id: int = 0
    fecha_hora: str = ""
    motivo: str = ""
    veterinario: Optional[str] = None
    estado: str = "En espera"
    proxima_cita: Optional[str] = None
    observaciones: Optional[str] = None
    created_at: Optional[str] = None
    # Campos join
    animal_nombre: Optional[str] = None
    animal_codigo: Optional[str] = None
    especie: Optional[str] = None
    propietario: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> 'Recepcion':
        # Fase 6 (DB-M5): estandarizado a ``row.get(k)`` — antes usaba
        # ``row[k]`` que fallaba con KeyError si la query omitía algún
        # campo. ``.get()`` retorna ``None`` y el dataclass acepta eso.
        return cls(**{k: row.get(k) for k in cls.__dataclass_fields__ if k in row})


@dataclass
class HistoriaClinica:
    """Historia clínica general ligada a una recepción."""
    id: Optional[int] = None
    recepcion_id: int = 0
    animal_id: int = 0
    fecha: str = ""
    anamnesis: Optional[str] = None
    examen_fisico: Optional[str] = None
    temperatura: Optional[float] = None
    frecuencia_cardiaca: Optional[int] = None
    frecuencia_respiratoria: Optional[int] = None
    peso_consulta: Optional[float] = None
    # --- Campos clínicos que faltaban ---
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
    # ------------------------------------
    diagnostico: Optional[str] = None
    diagnostico_diferencial: Optional[str] = None
    tratamiento: Optional[str] = None
    pronostico: Optional[str] = None
    veterinario: Optional[str] = None
    created_at: Optional[str] = None
    animal_nombre: Optional[str] = None
    animal_codigo: Optional[str] = None
    especie: Optional[str] = None
    recepcion_codigo: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> 'HistoriaClinica':
        return cls(**{k: row.get(k) for k in cls.__dataclass_fields__ if k in row})


@dataclass
class Consulta:
    """Consulta ambulatoria de seguimiento."""
    id: Optional[int] = None
    codigo: str = ""  # CONS-0001
    animal_id: int = 0
    historia_id: Optional[int] = None  # puede no tener historia previa
    fecha: str = ""
    motivo: str = ""
    evolucion: Optional[str] = None  # Cómo evolucionó desde la última visita
    examen_fisico: Optional[str] = None
    tratamiento: Optional[str] = None
    medicamentos: Optional[str] = None  # Lista de medicamentos prescritos
    proxima_consulta: Optional[str] = None
    veterinario: Optional[str] = None
    observaciones: Optional[str] = None
    created_at: Optional[str] = None
    # Campos join
    animal_nombre: Optional[str] = None
    animal_codigo: Optional[str] = None
    especie: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> 'Consulta':
        return cls(**{k: row.get(k) for k in cls.__dataclass_fields__ if k in row})


@dataclass
class Cirugia:
    """Registro quirúrgico."""
    id: Optional[int] = None
    codigo: str = ""  # CIRU-0001
    animal_id: int = 0
    historia_id: Optional[int] = None
    fecha: str = ""
    tipo_cirugia: str = ""
    descripcion: Optional[str] = None
    anestesia: Optional[str] = None
    protocolo_anestesico: Optional[str] = None
    duracion_min: Optional[int] = None  # minutos
    cirujano: Optional[str] = None
    anestesiologo: Optional[str] = None
    asistente: Optional[str] = None
    complicaciones: Optional[str] = None
    cuidados_post: Optional[str] = None
    estado: str = "Programada"
    created_at: Optional[str] = None
    # Campos join
    animal_nombre: Optional[str] = None
    animal_codigo: Optional[str] = None
    especie: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> 'Cirugia':
        return cls(**{k: row.get(k) for k in cls.__dataclass_fields__ if k in row})


@dataclass
class Vacunacion:
    """Registro de vacunación y desparasitación."""
    id: Optional[int] = None
    codigo: str = ""  # VAC-0001
    animal_id: int = 0
    tipo: str = "Vacuna"  # 'Vacuna' | 'Desparasitación'
    producto: str = ""  # Nombre de la vacuna o desparasitante
    lote: Optional[str] = None
    dosis: Optional[str] = None
    via: Optional[str] = None  # SC, IM, PO, Tópico
    fecha_aplicacion: str = ""
    fecha_proxima: Optional[str] = None
    veterinario: Optional[str] = None
    observaciones: Optional[str] = None
    created_at: Optional[str] = None
    # Campos join
    animal_nombre: Optional[str] = None
    animal_codigo: Optional[str] = None
    especie: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> 'Vacunacion':
        return cls(**{k: row.get(k) for k in cls.__dataclass_fields__ if k in row})