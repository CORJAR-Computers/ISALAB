# services/consulta_service.py
"""Lógica de negocio — Consultas ambulatorias (CONS-XXXX)"""

from typing import List, Dict, Any

from database.repositories import ConsultaRepository
from database.connection import DatabaseManager
from database.models import Consulta
from pydantic import ValidationError

from schemas.clinica import ConsultaSchema
from utils.exceptions import BusinessLogicError
from utils.logger import setup_logger

logger = setup_logger()


class ConsultaService:
    def __init__(self):
        self.repo = ConsultaRepository()
        self.db_manager = DatabaseManager()

    def generar_codigo(self) -> str:
        """Genera código correlativo de manera atómica."""
        return self.db_manager.generar_codigo('CONS')

    def registrar_consulta(self, data: Dict[str, Any]) -> Consulta:
        try:
            # Generar código automáticamente si no se proporciona
            if not data.get('codigo'):
                data['codigo'] = self.generar_codigo()

            datos_validados = ConsultaSchema(**data)

            consulta = Consulta(
                codigo=datos_validados.codigo,
                animal_id=datos_validados.animal_id,
                historia_id=datos_validados.historia_id,
                fecha=datos_validados.fecha,
                motivo=datos_validados.motivo.strip(),
                evolucion=datos_validados.evolucion.strip() if datos_validados.evolucion else None,
                examen_fisico=datos_validados.examen_fisico.strip() if datos_validados.examen_fisico else None,
                tratamiento=datos_validados.tratamiento.strip() if datos_validados.tratamiento else None,
                medicamentos=datos_validados.medicamentos.strip() if datos_validados.medicamentos else None,
                proxima_consulta=datos_validados.proxima_consulta,
                veterinario=datos_validados.veterinario.strip() if datos_validados.veterinario else None,
                observaciones=datos_validados.observaciones.strip() if datos_validados.observaciones else None)

            consulta.id = self.repo.create(consulta)
            logger.info(f"Consulta registrada: {consulta.codigo}")
            return consulta

        except ValidationError as e:
            error_msg = "\n".join(
                [f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
            logger.error(f"Error Pydantic en consulta: {error_msg}")
            raise BusinessLogicError(
                f"Datos inválidos en la consulta:\n{error_msg}")
        except Exception as e:
            logger.error(f"Error inesperado en registrar_consulta: {e}")
            raise

    def obtener_consulta(self, cid: int) -> Consulta:
        return self.repo.get_by_id(cid)

    def listar_consultas(self, filtros: dict = None) -> List[Consulta]:
        return self.repo.get_all(filtros)

    def consultas_por_paciente(self, animal_id: int) -> List[Consulta]:
        return self.repo.get_by_animal(animal_id)

    def actualizar_consulta(self, cid: int, data: dict) -> None:
        c = self.repo.get_by_id(cid)
        # Usamos 'in data' para distinguir "campo no enviado" de "campo vacío intencionalmente"
        if 'motivo' in data:
            c.motivo = data['motivo']
        if 'evolucion' in data:
            c.evolucion = data['evolucion'] or None
        if 'examen_fisico' in data:
            c.examen_fisico = data['examen_fisico'] or None
        if 'tratamiento' in data:
            c.tratamiento = data['tratamiento'] or None
        if 'medicamentos' in data:
            c.medicamentos = data['medicamentos'] or None
        if 'proxima_consulta' in data:
            c.proxima_consulta = data['proxima_consulta']
        if 'veterinario' in data:
            c.veterinario = data['veterinario'] or None
        if 'observaciones' in data:
            c.observaciones = data['observaciones'] or None
        self.repo.update(c)
        logger.info(f"Consulta {cid} actualizada")

    def _validar(self, data: dict) -> None:
        errores = []
        if not data.get('animal_id'):
            errores.append("Debe seleccionar un paciente")
        if not data.get('motivo', '').strip():
            errores.append("El motivo de consulta es obligatorio")
        if errores:
            raise ValidationError(
                "Datos de consulta inválidos", {
                    'errores': errores})
