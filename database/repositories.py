# database/repositories.py
"""Patrón Repository para IsaLab - Migración SQLAlchemy CQRS"""

import sqlalchemy as sa
from typing import List, Optional, Dict
from contextlib import contextmanager

from database.connection import DatabaseManager, SessionLocal
from orm_models.animal import Animal as AnimalORM
from orm_models.clinica import (MovimientoORM, MuestraORM, RecepcionORM,
                               HistoriaClinicaORM, ConsultaORM, CirugiaORM, VacunacionORM)
from database.models import (Animal, Movimiento, Muestra, Recepcion,
                            HistoriaClinica, Consulta, Cirugia, Vacunacion)
from utils.logger import setup_logger
from utils.exceptions import NotFoundError

logger = setup_logger()


class BaseRepository:
    """Clase base que maneja la conexión segura a la base de datos."""
    def __init__(self):
        self.db = DatabaseManager()  # Solo se usa para generar códigos (ISAL-0001)

    @contextmanager
    def get_session(self):
        """
        PROTECCIÓN ANTI-CRASHES:
        Abre una sesión, hace el trabajo, y al finalizar:
        - Si todo va bien: guarda los cambios (commit) y cierra.
        - Si hay cualquier error: deshace los cambios (rollback) y cierra.
        Así la app nunca se queda "colgada" por una sesión rota.
        """
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error en transacción de BD, haciendo rollback: {e}")
            raise
        finally:
            session.close()


# ══════════════════════════════════════════════════════════════════════════
#  ANIMALES
# ══════════════════════════════════════════════════════════════════════════

class AnimalRepository(BaseRepository):

    def create(self, animal: Animal) -> int:
        with self.get_session() as session:
            orm_obj = AnimalORM(
                codigo=animal.codigo, nombre=animal.nombre, especie=animal.especie,
                raza=animal.raza, sexo=animal.sexo, color=animal.color,
                tipo_pelo=animal.tipo_pelo, senas_particulares=animal.senas_particulares,
                microchip=animal.microchip, edad=animal.edad, unidad_edad=animal.unidad_edad,
                fecha_nacimiento=animal.fecha_nacimiento, peso=animal.peso,
                propietario=animal.propietario, propietario_tipo_doc=animal.propietario_tipo_doc,
                propietario_documento=animal.propietario_documento,
                propietario_direccion=animal.propietario_direccion,
                propietario_oficio=animal.propietario_oficio,
                telefono=animal.telefono, email=animal.email,
                fecha_ingreso=animal.fecha_ingreso, observaciones=animal.observaciones,
                estado=animal.estado
            )
            session.add(orm_obj)
            session.flush()  # Obtenemos el ID sin cerrar la sesión aún
            logger.info(f"Animal creado: {orm_obj.codigo}")
            return orm_obj.id

    def get_by_id(self, animal_id: int) -> Animal:
        with self.get_session() as session:
            q = sa.text("SELECT * FROM animales WHERE id = :id")
            row = session.execute(q, {"id": animal_id}).mappings().first()
            if not row:
                raise NotFoundError(f"Animal con ID {animal_id} no encontrado")
            return Animal.from_row(dict(row))

    def get_by_codigo(self, codigo: str) -> Optional[Animal]:
        with self.get_session() as session:
            q = sa.text("SELECT * FROM animales WHERE codigo = :codigo")
            row = session.execute(q, {"codigo": codigo}).mappings().first()
            return Animal.from_row(dict(row)) if row else None

    def get_all(self, filtros: Optional[Dict] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Animal]:
        with self.get_session() as session:
            query = "SELECT * FROM animales WHERE 1=1"
            params = {}
            if filtros:
                if filtros.get('estado'):
                    query += " AND estado = :est"
                    params['est'] = filtros['estado']
                if filtros.get('especie'):
                    query += " AND especie LIKE :esp"
                    params['esp'] = f"%{filtros['especie']}%"
                if filtros.get('busqueda'):
                    query += " AND (nombre LIKE :b OR codigo LIKE :b OR propietario LIKE :b)"
                    params['b'] = f"%{filtros['busqueda']}%"

            query += " ORDER BY id DESC"
            
            if limit is not None:
                query += " LIMIT :limit"
                params['limit'] = limit
            if offset is not None:
                query += " OFFSET :offset"
                params['offset'] = offset

            rows = session.execute(sa.text(query), params).mappings().all()
            return [Animal.from_row(dict(r)) for r in rows]

    def update(self, animal: Animal) -> None:
        with self.get_session() as session:
            session.query(AnimalORM).filter(AnimalORM.id == animal.id).update({
                "nombre": animal.nombre, "especie": animal.especie, "raza": animal.raza,
                "sexo": animal.sexo, "color": animal.color, "tipo_pelo": animal.tipo_pelo,
                "senas_particulares": animal.senas_particulares,
                "microchip": animal.microchip,
                "edad": animal.edad, "unidad_edad": animal.unidad_edad,
                "fecha_nacimiento": animal.fecha_nacimiento,
                "peso": animal.peso,
                "propietario": animal.propietario,
                "propietario_tipo_doc": animal.propietario_tipo_doc,
                "propietario_documento": animal.propietario_documento,
                "propietario_direccion": animal.propietario_direccion,
                "propietario_oficio": animal.propietario_oficio,
                "telefono": animal.telefono, "email": animal.email,
                "estado": animal.estado, "observaciones": animal.observaciones
            })

    def update_estado(self, animal_id: int, estado: str) -> None:
        with self.get_session() as session:
            session.query(AnimalORM).filter(AnimalORM.id == animal_id).update({"estado": estado})

    def get_max_id(self) -> int:
        from sqlalchemy import func
        with self.get_session() as session:
            resultado = session.query(func.max(AnimalORM.id)).scalar()
            return resultado if resultado is not None else 0


# ══════════════════════════════════════════════════════════════════════════
#  MOVIMIENTOS
# ══════════════════════════════════════════════════════════════════════════

class MovimientoRepository(BaseRepository):
    def create(self, movimiento: Movimiento) -> int:
        with self.get_session() as session:
            mov_orm = MovimientoORM(
                animal_id=movimiento.animal_id, tipo=movimiento.tipo,
                motivo=movimiento.motivo, responsable=movimiento.responsable,
                destino=movimiento.destino
            )
            session.add(mov_orm)
            session.flush()
            return mov_orm.id

    def get_by_animal(self, animal_id: int) -> List[Movimiento]:
        with self.get_session() as session:
            q = sa.text("SELECT * FROM movimientos WHERE animal_id = :id ORDER BY fecha_hora DESC")
            rows = session.execute(q, {"id": animal_id}).mappings().all()
            return [Movimiento(**dict(row)) for row in rows]


# ══════════════════════════════════════════════════════════════════════════
#  MUESTRAS (LABORATORIO)
# ══════════════════════════════════════════════════════════════════════════

class MuestraRepository(BaseRepository):
    def create(self, m: Muestra) -> int:
        with self.get_session() as session:
            muestra_orm = MuestraORM(
                codigo=m.codigo, animal_id=m.animal_id, empresa=m.empresa,
                tipo_muestra=m.tipo_muestra, tipo_analisis=m.tipo_analisis,
                fecha_recoleccion=m.fecha_recoleccion, fecha_entrega=m.fecha_entrega,
                resultado=m.resultado, valor_referencia=m.valor_referencia,
                observaciones=m.observaciones, tecnico=m.tecnico,
                veterinario_ref=m.veterinario_ref, urgente=m.urgente, estado=m.estado
            )
            session.add(muestra_orm)
            session.flush()
            return muestra_orm.id

    def get_all(self, filtros: Optional[Dict] = None) -> List[Muestra]:
        with self.get_session() as session:
            query = '''
                SELECT m.*, a.nombre as animal_nombre, a.codigo as animal_codigo, a.especie
                FROM muestras m 
                LEFT JOIN animales a ON m.animal_id = a.id 
                WHERE 1 = 1
                '''
            params = {}
            if filtros:
                if filtros.get('estado'):
                    query += " AND m.estado = :est"
                    params['est'] = filtros['estado']
                if filtros.get('tipo'):
                    query += " AND m.tipo_muestra = :tipo"
                    params['tipo'] = filtros['tipo']
                if filtros.get('urgente'):
                    query += " AND m.urgente = 1"

            query += " ORDER BY m.urgente DESC, m.id DESC"
            rows = session.execute(sa.text(query), params).mappings().all()
            return [Muestra.from_row(dict(r)) for r in rows]

    def get_by_id(self, muestra_id: int) -> Muestra:
        with self.get_session() as session:
            q = sa.text('''
                SELECT m.*, a.nombre as animal_nombre, a.codigo as animal_codigo, a.especie
                FROM muestras m
                LEFT JOIN animales a ON m.animal_id = a.id
                WHERE m.id = :id
                ''')
            row = session.execute(q, {"id": muestra_id}).mappings().first()
            if not row: raise NotFoundError(f"Muestra {muestra_id} no encontrada")
            return Muestra.from_row(dict(row))

    def update_estado(self, muestra_id: int, estado: str, resultado: Optional[str] = None,
                      valor_ref: Optional[str] = None) -> None:
        with self.get_session() as session:
            update_data = {"estado": estado}
            if resultado is not None or valor_ref is not None:
                update_data["resultado"] = resultado
                update_data["valor_referencia"] = valor_ref  # Mapeo al nombre de columna en la BD

            session.query(MuestraORM).filter(MuestraORM.id == muestra_id).update(update_data)


# ══════════════════════════════════════════════════════════════════════════
#  MÓDULO CLÍNICO
# ══════════════════════════════════════════════════════════════════════════

class RecepcionRepository(BaseRepository):
    def generar_codigo(self) -> str:
        return self.db.generar_codigo('ISAL')

    def create(self, r: Recepcion) -> int:
        with self.get_session() as session:
            orm_obj = RecepcionORM(
                codigo=r.codigo, animal_id=r.animal_id, fecha_hora=r.fecha_hora,
                motivo=r.motivo, veterinario=r.veterinario, estado=r.estado,
                proxima_cita=r.proxima_cita, observaciones=r.observaciones
            )
            session.add(orm_obj)
            session.flush()
            return orm_obj.id

    def get_by_id(self, rid: int) -> Recepcion:
        with self.get_session() as session:
            q = sa.text('''
                SELECT r.*, a.nombre as animal_nombre, a.codigo as animal_codigo,
                       a.especie, a.propietario
                FROM recepciones r
                LEFT JOIN animales a ON r.animal_id = a.id
                WHERE r.id = :id
                ''')
            row = session.execute(q, {"id": rid}).mappings().first()
            if not row: raise NotFoundError(f"Recepción {rid} no encontrada")
            return Recepcion.from_row(dict(row))

    def get_all(self, filtros: dict = None) -> list:
        with self.get_session() as session:
            query = '''
                SELECT r.*, a.nombre as animal_nombre, a.codigo as animal_codigo,
                       a.especie, a.propietario
                FROM recepciones r 
                LEFT JOIN animales a ON r.animal_id = a.id 
                WHERE 1 = 1
                '''
            params = {}
            if filtros:
                if filtros.get('estado'):
                    query += " AND r.estado = :est"
                    params['est'] = filtros['estado']
                if filtros.get('animal_id'):
                    query += " AND r.animal_id = :aid"
                    params['aid'] = filtros['animal_id']
                if filtros.get('busqueda'):
                    query += " AND (r.codigo LIKE :b OR a.nombre LIKE :b OR a.codigo LIKE :b OR r.motivo LIKE :b)"
                    params['b'] = f"%{filtros['busqueda']}%"
                if filtros.get('fecha_hoy'):
                    query += " AND date(r.fecha_hora) = :hoy"
                    params['hoy'] = filtros['fecha_hoy']
            query += " ORDER BY r.fecha_hora DESC"
            rows = session.execute(sa.text(query), params).mappings().all()
            return [Recepcion.from_row(dict(r)) for r in rows]

    def update_estado(self, rid: int, estado: str, proxima_cita: str = None) -> None:
        with self.get_session() as session:
            session.query(RecepcionORM).filter(RecepcionORM.id == rid).update({
                "estado": estado, "proxima_cita": proxima_cita
            })

    def get_by_animal(self, animal_id: int) -> list:
        return self.get_all({'animal_id': animal_id})


class HistoriaClinicaRepository(BaseRepository):
    def create(self, h: HistoriaClinica) -> int:
        with self.get_session() as session:
            orm_obj = HistoriaClinicaORM(
                recepcion_id=h.recepcion_id, animal_id=h.animal_id, fecha=h.fecha,
                anamnesis=h.anamnesis, examen_fisico=h.examen_fisico, temperatura=h.temperatura,
                frecuencia_cardiaca=h.frecuencia_cardiaca, frecuencia_respiratoria=h.frecuencia_respiratoria,
                peso_consulta=h.peso_consulta,
                # Nuevos campos clínicos
                dieta=h.dieta, enfermedades_previas=h.enfermedades_previas,
                cirugias_previas=h.cirugias_previas, esterilizado=h.esterilizado,
                numero_partos=h.numero_partos, esquema_vacunal=h.esquema_vacunal,
                ultima_desparasitacion=h.ultima_desparasitacion,
                tratamientos_recientes=h.tratamientos_recientes, viajes_recientes=h.viajes_recientes,
                convive_con_animales=h.convive_con_animales, comportamiento=h.comportamiento,
                condicion_corporal=h.condicion_corporal, tllc=h.tllc, trpc=h.trpc,
                mucosas=h.mucosas, pulso=h.pulso, deshidratacion=h.deshidratacion,
                # Fin nuevos campos
                diagnostico=h.diagnostico, diagnostico_diferencial=h.diagnostico_diferencial,
                tratamiento=h.tratamiento, pronostico=h.pronostico, veterinario=h.veterinario
            )
            session.add(orm_obj)
            session.flush()
            return orm_obj.id

    def get_by_id(self, hid: int) -> HistoriaClinica:
        with self.get_session() as session:
            q = sa.text('''
                SELECT h.*, a.nombre as animal_nombre, a.codigo as animal_codigo,
                       a.especie, r.codigo as recepcion_codigo
                FROM historias_clinicas h
                LEFT JOIN animales a ON h.animal_id = a.id
                LEFT JOIN recepciones r ON h.recepcion_id = r.id
                WHERE h.id = :id
                ''')
            row = session.execute(q, {"id": hid}).mappings().first()
            if not row: raise NotFoundError(f"Historia {hid} no encontrada")
            return HistoriaClinica.from_row(dict(row))

    def get_by_animal(self, animal_id: int) -> list:
        with self.get_session() as session:
            q = sa.text('''
                SELECT h.*, a.nombre as animal_nombre, a.codigo as animal_codigo,
                       a.especie, r.codigo as recepcion_codigo
                FROM historias_clinicas h
                LEFT JOIN animales a ON h.animal_id = a.id
                LEFT JOIN recepciones r ON h.recepcion_id = r.id
                WHERE h.animal_id = :id
                ORDER BY h.fecha DESC
                ''')
            rows = session.execute(q, {"id": animal_id}).mappings().all()
            return [HistoriaClinica.from_row(dict(r)) for r in rows]

    def get_by_recepcion(self, recepcion_id: int):
        with self.get_session() as session:
            q = sa.text("SELECT * FROM historias_clinicas WHERE recepcion_id = :id")
            row = session.execute(q, {"id": recepcion_id}).mappings().first()
            return HistoriaClinica.from_row(dict(row)) if row else None

    def update(self, h: HistoriaClinica) -> None:
        with self.get_session() as session:
            session.query(HistoriaClinicaORM).filter(HistoriaClinicaORM.id == h.id).update({
                "anamnesis": h.anamnesis, "examen_fisico": h.examen_fisico,
                "temperatura": h.temperatura, "frecuencia_cardiaca": h.frecuencia_cardiaca,
                "frecuencia_respiratoria": h.frecuencia_respiratoria, "peso_consulta": h.peso_consulta,
                "dieta": h.dieta, "enfermedades_previas": h.enfermedades_previas,
                "cirugias_previas": h.cirugias_previas, "esterilizado": h.esterilizado,
                "numero_partos": h.numero_partos, "esquema_vacunal": h.esquema_vacunal,
                "ultima_desparasitacion": h.ultima_desparasitacion,
                "tratamientos_recientes": h.tratamientos_recientes, "viajes_recientes": h.viajes_recientes,
                "convive_con_animales": h.convive_con_animales, "comportamiento": h.comportamiento,
                "condicion_corporal": h.condicion_corporal, "tllc": h.tllc, "trpc": h.trpc,
                "mucosas": h.mucosas, "pulso": h.pulso, "deshidratacion": h.deshidratacion,
                "diagnostico": h.diagnostico, "diagnostico_diferencial": h.diagnostico_diferencial,
                "tratamiento": h.tratamiento, "pronostico": h.pronostico, "veterinario": h.veterinario
            })


class ConsultaRepository(BaseRepository):
    def generar_codigo(self) -> str:
        return self.db.generar_codigo('CONS')

    def create(self, c: Consulta) -> int:
        with self.get_session() as session:
            orm_obj = ConsultaORM(
                codigo=c.codigo, animal_id=c.animal_id, historia_id=c.historia_id,
                fecha=c.fecha, motivo=c.motivo, evolucion=c.evolucion,
                examen_fisico=c.examen_fisico, tratamiento=c.tratamiento,
                medicamentos=c.medicamentos, proxima_consulta=c.proxima_consulta,
                veterinario=c.veterinario, observaciones=c.observaciones
            )
            session.add(orm_obj)
            session.flush()
            return orm_obj.id

    def get_by_id(self, cid: int) -> Consulta:
        with self.get_session() as session:
            q = sa.text('''
                SELECT c.*, a.nombre as animal_nombre, a.codigo as animal_codigo, a.especie
                FROM consultas c
                LEFT JOIN animales a ON c.animal_id = a.id
                WHERE c.id = :id
                ''')
            row = session.execute(q, {"id": cid}).mappings().first()
            if not row: raise NotFoundError(f"Consulta {cid} no encontrada")
            return Consulta.from_row(dict(row))

    def get_all(self, filtros: dict = None) -> list:
        with self.get_session() as session:
            query = '''
                SELECT c.*, a.nombre as animal_nombre, a.codigo as animal_codigo, a.especie
                FROM consultas c 
                LEFT JOIN animales a ON c.animal_id = a.id 
                WHERE 1 = 1
                '''
            params = {}
            if filtros:
                if filtros.get('animal_id'):
                    query += " AND c.animal_id = :aid"
                    params['aid'] = filtros['animal_id']
                if filtros.get('busqueda'):
                    query += " AND (c.codigo LIKE :b OR a.nombre LIKE :b)"
                    params['b'] = f"%{filtros['busqueda']}%"
            query += " ORDER BY c.fecha DESC"
            rows = session.execute(sa.text(query), params).mappings().all()
            return [Consulta.from_row(dict(r)) for r in rows]

    def get_by_animal(self, animal_id: int) -> list:
        return self.get_all({'animal_id': animal_id})

    def update(self, c: Consulta) -> None:
        with self.get_session() as session:
            session.query(ConsultaORM).filter(ConsultaORM.id == c.id).update({
                "motivo": c.motivo, "evolucion": c.evolucion, "examen_fisico": c.examen_fisico,
                "tratamiento": c.tratamiento, "medicamentos": c.medicamentos,
                "proxima_consulta": c.proxima_consulta, "veterinario": c.veterinario,
                "observaciones": c.observaciones
            })


class CirugiaRepository(BaseRepository):
    def generar_codigo(self) -> str:
        return self.db.generar_codigo('CIRU')

    def create(self, cg: Cirugia) -> int:
        with self.get_session() as session:
            orm_obj = CirugiaORM(
                codigo=cg.codigo, animal_id=cg.animal_id, historia_id=cg.historia_id,
                fecha=cg.fecha, tipo_cirugia=cg.tipo_cirugia, descripcion=cg.descripcion,
                anestesia=cg.anestesia, protocolo_anestesico=cg.protocolo_anestesico,
                duracion_min=cg.duracion_min, cirujano=cg.cirujano, anestesiologo=cg.anestesiologo,
                asistente=cg.asistente, complicaciones=cg.complicaciones, cuidados_post=cg.cuidados_post,
                estado=cg.estado
            )
            session.add(orm_obj)
            session.flush()
            return orm_obj.id

    def get_by_id(self, cid: int) -> Cirugia:
        with self.get_session() as session:
            q = sa.text('''
                SELECT cg.*, a.nombre as animal_nombre, a.codigo as animal_codigo, a.especie
                FROM cirugias cg
                LEFT JOIN animales a ON cg.animal_id = a.id
                WHERE cg.id = :id
                ''')
            row = session.execute(q, {"id": cid}).mappings().first()
            if not row: raise NotFoundError(f"Cirugía {cid} no encontrada")
            return Cirugia.from_row(dict(row))

    def get_all(self, filtros: dict = None) -> list:
        with self.get_session() as session:
            query = '''
                SELECT cg.*, a.nombre as animal_nombre, a.codigo as animal_codigo, a.especie
                FROM cirugias cg 
                LEFT JOIN animales a ON cg.animal_id = a.id 
                WHERE 1 = 1
                '''
            params = {}
            if filtros:
                if filtros.get('estado'):
                    query += " AND cg.estado = :est"
                    params['est'] = filtros['estado']
                if filtros.get('animal_id'):
                    query += " AND cg.animal_id = :aid"
                    params['aid'] = filtros['animal_id']
                if filtros.get('busqueda'):
                    query += " AND (cg.codigo LIKE :b OR a.nombre LIKE :b)"
                    params['b'] = f"%{filtros['busqueda']}%"
            query += " ORDER BY cg.fecha DESC"
            rows = session.execute(sa.text(query), params).mappings().all()
            return [Cirugia.from_row(dict(r)) for r in rows]

    def get_by_animal(self, animal_id: int) -> list:
        return self.get_all({'animal_id': animal_id})

    def update_estado(self, cid: int, estado: str, complicaciones: str = None) -> None:
        with self.get_session() as session:
            session.query(CirugiaORM).filter(CirugiaORM.id == cid).update({
                "estado": estado, "complicaciones": complicaciones
            })

    def update(self, cg: Cirugia) -> None:
        with self.get_session() as session:
            session.query(CirugiaORM).filter(CirugiaORM.id == cg.id).update({
                "tipo_cirugia": cg.tipo_cirugia, "descripcion": cg.descripcion, "anestesia": cg.anestesia,
                "protocolo_anestesico": cg.protocolo_anestesico, "duracion_min": cg.duracion_min,
                "cirujano": cg.cirujano, "anestesiologo": cg.anestesiologo, "asistente": cg.asistente,
                "complicaciones": cg.complicaciones, "cuidados_post": cg.cuidados_post, "estado": cg.estado
            })


class VacunacionRepository(BaseRepository):
    def generar_codigo(self) -> str:
        return self.db.generar_codigo('VAC')

    def create(self, v: Vacunacion) -> int:
        with self.get_session() as session:
            orm_obj = VacunacionORM(
                codigo=v.codigo, animal_id=v.animal_id, tipo=v.tipo, producto=v.producto,
                lote=v.lote, dosis=v.dosis, via=v.via, fecha_aplicacion=v.fecha_aplicacion,
                fecha_proxima=v.fecha_proxima, veterinario=v.veterinario, observaciones=v.observaciones
            )
            session.add(orm_obj)
            session.flush()
            return orm_obj.id

    def get_by_id(self, vid: int) -> Vacunacion:
        with self.get_session() as session:
            q = sa.text('''
                SELECT v.*, a.nombre as animal_nombre, a.codigo as animal_codigo, a.especie
                FROM vacunaciones v
                LEFT JOIN animales a ON v.animal_id = a.id
                WHERE v.id = :id
                ''')
            row = session.execute(q, {"id": vid}).mappings().first()
            if not row: raise NotFoundError(f"Vacunación {vid} no encontrada")
            return Vacunacion.from_row(dict(row))

    def get_all(self, filtros: dict = None) -> list:
        with self.get_session() as session:
            query = '''
                SELECT v.*, a.nombre as animal_nombre, a.codigo as animal_codigo, a.especie
                FROM vacunaciones v 
                LEFT JOIN animales a ON v.animal_id = a.id 
                WHERE 1 = 1
                '''
            params = {}
            if filtros:
                if filtros.get('tipo'):
                    query += " AND v.tipo = :tipo"
                    params['tipo'] = filtros['tipo']
                if filtros.get('animal_id'):
                    query += " AND v.animal_id = :aid"
                    params['aid'] = filtros['animal_id']
                if filtros.get('proximas'):
                    query += " AND v.fecha_proxima BETWEEN date('now') AND date('now', :dias)"
                    params['dias'] = f"+{filtros['proximas']} days"
                if filtros.get('busqueda'):
                    query += " AND (v.codigo LIKE :b OR a.nombre LIKE :b OR v.producto LIKE :b)"
                    params['b'] = f"%{filtros['busqueda']}%"
            query += " ORDER BY v.fecha_aplicacion DESC"
            rows = session.execute(sa.text(query), params).mappings().all()
            return [Vacunacion.from_row(dict(r)) for r in rows]

    def get_by_animal(self, animal_id: int) -> list:
        return self.get_all({'animal_id': animal_id})

    def get_proximas(self, dias: int = 30) -> list:
        return self.get_all({'proximas': dias})