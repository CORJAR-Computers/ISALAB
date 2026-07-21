# orm_models/clinica.py
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from database.connection import Base

class MovimientoORM(Base):
    __tablename__ = "movimientos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    animal_id = Column(Integer, ForeignKey("animales.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String(20), nullable=False)
    fecha_hora = Column(String(50)) # Usamos String para compatibilidad con el TIMESTAMP de SQLite
    motivo = Column(Text, nullable=False)
    responsable = Column(String(100), nullable=False)
    destino = Column(String(150))
    # Fase 5 (H-D3): ``created_at`` mapeado (la columna ya existía en la
    # BD gracias a la migración de Fase 2; solo faltaba declararla acá).
    created_at = Column(DateTime, server_default=func.now())

class MuestraORM(Base):
    __tablename__ = "muestras"

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
    valor_referencia = Column(Text)
    observaciones = Column(Text)
    tecnico = Column(String(100))
    veterinario_ref = Column(String(100))
    urgente = Column(Integer, default=0)
    # Fase 5 (H-D3)
    created_at = Column(DateTime, server_default=func.now())

class RecepcionORM(Base):
    __tablename__ = "recepciones"

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

class HistoriaClinicaORM(Base):
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

class ConsultaORM(Base):
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

class CirugiaORM(Base):
    __tablename__ = "cirugias"

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

class VacunacionORM(Base):
    __tablename__ = "vacunaciones"

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