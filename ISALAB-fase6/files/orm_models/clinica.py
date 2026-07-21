# orm_models/clinica.py
"""ORM models para el módulo clínico de IsaLab.

Incluye las tablas de movimientos de pacientes, muestras de laboratorio,
recepciones, historias clínicas, consultas, cirugías y vacunaciones.

Fase 6:
  * DB-M1: ``MuestraORM.urgente`` ahora es ``Boolean`` (SQLite lo
    almacena como INTEGER, así que la migración es schema-compatible).
  * DB-M2: ``CheckConstraint`` declarativas en ``estado`` y ``via``
    alineadas con ``config.ESTADOS_*`` / ``config.VIAS_ADMINISTRACION``.
  * DB-M3: columna ``updated_at`` en todas las tablas.
  * DB-M6: ``MovimientoORM.fecha_hora`` ahora es ``nullable=False`` con
    ``server_default`` para que un INSERT que no lo setee igual tenga
    valor (la migration ``b3c4d5e6f7a8`` hace el backfill + alter).
  * DB-M7: ``valor_ref`` es ahora un ``synonym`` de ``valor_referencia``
    (nombre canónico) para compatibilidad hacia atrás.
"""
from sqlalchemy import (
    Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean,
    CheckConstraint,
)
from sqlalchemy.orm import synonym
from sqlalchemy.sql import func
from database.connection import Base

# Fase 6 (DB-M2): whitelists importadas desde ``config`` para que las
# ``CheckConstraint`` declarativas y la migración ``b3c4d5e6f7a8`` usen
# exactamente la misma fuente de verdad que los servicios.
try:
    from config import (
        ESTADOS_MUESTRA, ESTADOS_RECEPCION, ESTADOS_CIRUGIA,
        VIAS_ADMINISTRACION,
    )
except Exception:  # pragma: no cover - fallback si config no cargó
    ESTADOS_MUESTRA = ['Pendiente', 'En Proceso', 'Completado', 'Descartado']
    ESTADOS_RECEPCION = ['En espera', 'En consulta', 'Finalizado', 'Cancelado']
    ESTADOS_CIRUGIA = ['Programada', 'En proceso', 'Completada', 'Cancelada']
    VIAS_ADMINISTRACION = [
        'Subcutánea (SC)', 'Intramuscular (IM)', 'Intravenosa (IV)',
        'Oral (PO)', 'Tópica', 'Intranasal', 'Otra',
    ]


def _sql_in_list(values):
    """Genera el SQL ``IN ('a', 'b', ...)`` escapando comillas simples."""
    quoted = ",".join(f"'{v.replace(chr(39), chr(39)+chr(39))}'" for v in values)
    return f"IN ({quoted})"


class MovimientoORM(Base):
    """Movimiento de un paciente (entrada/salida/traslado).

    Fase 6 (DB-M6): ``fecha_hora`` ahora es ``nullable=False`` con
    ``server_default``. Antes era ``String(50)`` nullable, y como
    ``MovimientoRepository.create`` no lo seteaba explícitamente,
    quedaba siempre en NULL. La migración ``b3c4d5e6f7a8`` hace el
    backfill + ``ALTER COLUMN`` vía ``batch_alter_table``.
    """

    __tablename__ = "movimientos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    animal_id = Column(Integer, ForeignKey("animales.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String(20), nullable=False)
    # Mantenemos String(50) (no DateTime) porque así está en la
    # migración baseline y porque ``recepciones.fecha_hora`` también
    # lo es — cambiar el tipo requeriría data-migration arriesgada.
    # ``server_default`` usa la función SQL ``datetime('now')`` que
    # retorna ISO-8601, así que es ordenable lexicográficamente.
    fecha_hora = Column(
        String(50),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    motivo = Column(Text, nullable=False)
    responsable = Column(String(100), nullable=False)
    destino = Column(String(150))
    # Fase 5 (H-D3): ``created_at`` mapeado (la columna ya existía en la
    # BD gracias a la migración de Fase 2; solo faltaba declararla acá).
    created_at = Column(DateTime, server_default=func.now())
    # Fase 6 (DB-M3)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())


class MuestraORM(Base):
    """Muestra de laboratorio (LAB-XXXX).

    Fase 6:
      * DB-M1: ``urgente`` ahora es ``Boolean`` (SQLite lo almacena
        como INTEGER 0/1, así que es schema-compatible con la columna
        existente).
      * DB-M2: ``CheckConstraint`` en ``estado`` usando
        ``config.ESTADOS_MUESTRA``.
      * DB-M7: ``valor_ref`` es ``synonym('valor_referencia')`` — el
        nombre canónico es ``valor_referencia`` pero el alias
        ``valor_ref`` sigue funcionando para no romper servicios ni
        reportes que lo usan.
    """

    __tablename__ = "muestras"

    __table_args__ = (
        CheckConstraint(
            f"estado {_sql_in_list(ESTADOS_MUESTRA)}",
            name="ck_muestras_estado",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, nullable=False)
    animal_id = Column(Integer, ForeignKey("animales.id", ondelete="CASCADE"), nullable=False)
    empresa = Column(String(100))
    tipo_muestra = Column(String(50), nullable=False)
    tipo_analisis = Column(String(100))
    fecha_recoleccion = Column(String(20), nullable=False)
    fecha_entrega = Column(String(20))
    estado = Column(String(20), default="Pendiente")
    resultado = Column(Text)
    # Fase 6 (DB-M7): nombre canónico ``valor_referencia``.
    valor_referencia = Column(Text)
    # Fase 6 (DB-M7): ``valor_ref`` como synonym — el ORM acepta ambos
    # nombres en queries y asignaciones. Compatibilidad hacia atrás.
    valor_ref = synonym('valor_referencia')
    observaciones = Column(Text)
    tecnico = Column(String(100))
    veterinario_ref = Column(String(100))
    # Fase 6 (DB-M1): Boolean en lugar de Integer. SQLite lo guarda
    # como INTEGER 0/1 (mismo storage que antes), así que la columna
    # existente es compatible. ``default=False`` y ``nullable=False``
    # porque el campo SIEMPRE debe tener un valor booleano definido.
    urgente = Column(Boolean, nullable=False, default=False)
    # Fase 5 (H-D3)
    created_at = Column(DateTime, server_default=func.now())
    # Fase 6 (DB-M3)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())


class RecepcionORM(Base):
    """Recepción/ingreso de paciente (ISAL-XXXX).

    Fase 6 (DB-M2): ``CheckConstraint`` en ``estado`` alineado con
    ``config.ESTADOS_RECEPCION``.
    """

    __tablename__ = "recepciones"

    __table_args__ = (
        CheckConstraint(
            f"estado {_sql_in_list(ESTADOS_RECEPCION)}",
            name="ck_recepciones_estado",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, nullable=False)
    animal_id = Column(Integer, ForeignKey("animales.id", ondelete="CASCADE"), nullable=False)
    fecha_hora = Column(String(50))
    motivo = Column(Text, nullable=False)
    veterinario = Column(String(100))
    estado = Column(String(20), default="En espera")
    proxima_cita = Column(String(20))
    observaciones = Column(Text)
    # Fase 5 (H-D3)
    created_at = Column(DateTime, server_default=func.now())
    # Fase 6 (DB-M3)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())


class HistoriaClinicaORM(Base):
    """Historia clínica general ligada a una recepción."""

    __tablename__ = "historias_clinicas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recepcion_id = Column(Integer, ForeignKey("recepciones.id", ondelete="CASCADE"), nullable=False)
    animal_id = Column(Integer, ForeignKey("animales.id", ondelete="CASCADE"), nullable=False)
    fecha = Column(String(20), nullable=False)
    anamnesis = Column(Text)
    examen_fisico = Column(Text)
    temperatura = Column(Float)
    frecuencia_cardiaca = Column(Integer)
    frecuencia_respiratoria = Column(Integer)
    peso_consulta = Column(Float)
    dieta = Column(String(150))
    enfermedades_previas = Column(Text)
    cirugias_previas = Column(Text)
    esterilizado = Column(String(2)) # Ej: "Si", "No"
    numero_partos = Column(Integer)
    esquema_vacunal = Column(Text)
    ultima_desparasitacion = Column(String(100))
    tratamientos_recientes = Column(Text)
    viajes_recientes = Column(String(100))
    convive_con_animales = Column(String(150))
    comportamiento = Column(String(100))
    condicion_corporal = Column(String(20)) # Ej: "4/5"
    tllc = Column(String(20)) # Tiempo de Llenado Capilar
    trpc = Column(String(20)) # Tiempo de Retorno Pliegue Cutáneo
    mucosas = Column(String(50))
    pulso = Column(String(50))
    deshidratacion = Column(String(50))
    diagnostico = Column(Text)
    diagnostico_diferencial = Column(Text)
    tratamiento = Column(Text)
    pronostico = Column(Text)
    veterinario = Column(String(100))
    # Fase 5 (H-D3)
    created_at = Column(DateTime, server_default=func.now())
    # Fase 6 (DB-M3)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())


class ConsultaORM(Base):
    """Consulta ambulatoria de seguimiento (CONS-XXXX)."""

    __tablename__ = "consultas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, nullable=False)
    animal_id = Column(Integer, ForeignKey("animales.id", ondelete="CASCADE"), nullable=False)
    historia_id = Column(Integer, ForeignKey("historias_clinicas.id", ondelete="SET NULL"))
    fecha = Column(String(20), nullable=False)
    motivo = Column(Text, nullable=False)
    evolucion = Column(Text)
    examen_fisico = Column(Text)
    tratamiento = Column(Text)
    medicamentos = Column(Text)
    proxima_consulta = Column(String(20))
    veterinario = Column(String(100))
    observaciones = Column(Text)
    # Fase 5 (H-D3)
    created_at = Column(DateTime, server_default=func.now())
    # Fase 6 (DB-M3)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())


class CirugiaORM(Base):
    """Registro quirúrgico (CIRU-XXXX).

    Fase 6 (DB-M2): ``CheckConstraint`` en ``estado`` alineado con
    ``config.ESTADOS_CIRUGIA``.
    """

    __tablename__ = "cirugias"

    __table_args__ = (
        CheckConstraint(
            f"estado {_sql_in_list(ESTADOS_CIRUGIA)}",
            name="ck_cirugias_estado",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, nullable=False)
    animal_id = Column(Integer, ForeignKey("animales.id", ondelete="CASCADE"), nullable=False)
    historia_id = Column(Integer, ForeignKey("historias_clinicas.id", ondelete="SET NULL"))
    fecha = Column(String(20), nullable=False)
    tipo_cirugia = Column(String(100), nullable=False)
    descripcion = Column(Text)
    anestesia = Column(String(50))
    protocolo_anestesico = Column(Text)
    duracion_min = Column(Integer)
    cirujano = Column(String(100))
    anestesiologo = Column(String(100))
    asistente = Column(String(100))
    complicaciones = Column(Text)
    cuidados_post = Column(Text)
    estado = Column(String(20), default="Programada")
    # Fase 5 (H-D3)
    created_at = Column(DateTime, server_default=func.now())
    # Fase 6 (DB-M3)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())


class VacunacionORM(Base):
    """Registro de vacunación / desparasitación (VAC-XXXX).

    Fase 6 (DB-M2): ``CheckConstraint`` en ``via`` alineado con
    ``config.VIAS_ADMINISTRACION``. (La spec sugería ``Muestra.via`` pero
    ``MuestraORM`` no tiene columna ``via``; ``VacunacionORM`` sí.)
    """

    __tablename__ = "vacunaciones"

    __table_args__ = (
        CheckConstraint(
            f"via {_sql_in_list(VIAS_ADMINISTRACION)}",
            name="ck_vacunaciones_via",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, nullable=False)
    animal_id = Column(Integer, ForeignKey("animales.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String(50), nullable=False)
    producto = Column(String(100), nullable=False)
    lote = Column(String(50))
    dosis = Column(String(50))
    via = Column(String(50))
    fecha_aplicacion = Column(String(20), nullable=False)
    fecha_proxima = Column(String(20))
    veterinario = Column(String(100))
    observaciones = Column(Text)
    # Fase 5 (H-D3)
    created_at = Column(DateTime, server_default=func.now())
    # Fase 6 (DB-M3)
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
