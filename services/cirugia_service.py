# services/cirugia_service.py
"""Lógica de negocio — Cirugías (CIRU-XXXX)"""

from typing import List, Dict, Any

from database.repositories import CirugiaRepository
from database.connection import DatabaseManager
from database.models import Cirugia
from pydantic import ValidationError

from schemas.clinica import CirugiaSchema
from utils.exceptions import BusinessLogicError
from utils.logger import setup_logger

logger = setup_logger()


class CirugiaService:
    def __init__(self):
        self.repo = CirugiaRepository()
        self.db_manager = DatabaseManager()

    def generar_codigo(self) -> str:
        """Genera código correlativo de manera atómica."""
        return self.db_manager.generar_codigo('CIRU')

    def programar_cirugia(self, data: Dict[str, Any]) -> Cirugia:
        try:
            self._validar(data)
            # Generar código automáticamente si no se proporciona
            if not data.get('codigo'):
                data['codigo'] = self.generar_codigo()

            datos_validados = CirugiaSchema(**data)

            cirugia = Cirugia(
                codigo=datos_validados.codigo,
                animal_id=datos_validados.animal_id,
                historia_id=datos_validados.historia_id,
                fecha=datos_validados.fecha,
                tipo_cirugia=datos_validados.tipo_cirugia.strip(),
                descripcion=datos_validados.descripcion.strip() if datos_validados.descripcion else None,
                anestesia=datos_validados.anestesia.strip() if datos_validados.anestesia else None,
                protocolo_anestesico=datos_validados.protocolo_anestesico.strip() if datos_validados.protocolo_anestesico else None,
                duracion_min=datos_validados.duracion_min,
                cirujano=datos_validados.cirujano.strip() if datos_validados.cirujano else None,
                anestesiologo=datos_validados.anestesiologo.strip() if datos_validados.anestesiologo else None,
                asistente=datos_validados.asistente.strip() if datos_validados.asistente else None,
                complicaciones=datos_validados.complicaciones.strip() if datos_validados.complicaciones else None,
                cuidados_post=datos_validados.cuidados_post.strip() if datos_validados.cuidados_post else None,
                estado=datos_validados.estado)

            cirugia.id = self.repo.create(cirugia)
            logger.info(f"Cirugía registrada: {cirugia.codigo}")
            return cirugia

        except ValidationError as e:
            error_msg = "\n".join(
                [f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
            logger.error(f"Error Pydantic en cirugía: {error_msg}")
            raise BusinessLogicError(
                f"Datos inválidos en la cirugía:\n{error_msg}")
        except Exception as e:
            logger.error(f"Error inesperado en registrar_cirugia: {e}")
            raise

    def obtener_cirugia(self, cid: int) -> Cirugia:
        return self.repo.get_by_id(cid)

    def listar_cirugias(self, filtros: dict = None) -> List[Cirugia]:
        return self.repo.get_all(filtros)

    def cirugias_por_paciente(self, animal_id: int) -> List[Cirugia]:
        return self.repo.get_by_animal(animal_id)

    def obtener_historial_cirugias(self, animal_id: int) -> List[Cirugia]:
        """Alias de cirugias_por_paciente para compatibilidad con tests."""
        return self.cirugias_por_paciente(animal_id)

    def obtener_cirugias_programadas(self) -> List[Cirugia]:
        """Retorna cirugías con estado 'Programada'."""
        return self.repo.get_all({'estado': 'Programada'})

    def actualizar_estado(self, cid: int, estado: str,
                          complicaciones: str = None) -> None:
        self.repo.get_by_id(cid)
        self.repo.update_estado(cid, estado, complicaciones)
        logger.info(f"Cirugía {cid} → estado: {estado}")

    def actualizar_cirugia(self, cid: int, data: dict) -> None:
        cg = self.repo.get_by_id(cid)
        cg.tipo_cirugia = data.get('tipo_cirugia', cg.tipo_cirugia)
        cg.descripcion = data.get('descripcion', cg.descripcion)
        cg.anestesia = data.get('anestesia', cg.anestesia)
        cg.protocolo_anestesico = data.get(
            'protocolo_anestesico', cg.protocolo_anestesico)
        try:
            cg.duracion_min = int(data['duracion_min'])
        except (ValueError, TypeError):
            cg.duracion_min = cg.duracion_min
        cg.cirujano = data.get('cirujano', cg.cirujano)
        cg.anestesiologo = data.get('anestesiologo', cg.anestesiologo)
        cg.asistente = data.get('asistente', cg.asistente)
        cg.complicaciones = data.get('complicaciones', cg.complicaciones)
        cg.cuidados_post = data.get('cuidados_post', cg.cuidados_post)
        cg.estado = data.get('estado', cg.estado)
        self.repo.update(cg)
        logger.info(f"Cirugía {cid} actualizada")

    def _validar(self, data: dict) -> None:
        errores = []
        if not data.get('animal_id'):
            errores.append("Debe seleccionar un paciente")
        if not data.get('tipo_cirugia', '').strip():
            errores.append("El tipo de cirugía es obligatorio")
        if not data.get('fecha'):
            errores.append("La fecha es obligatoria")
        if errores:
            raise ValidationError(
                "Datos de cirugía inválidos", {
                    'errores': errores})
