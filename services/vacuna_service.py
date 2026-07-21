# services/vacuna_service.py
"""Lógica de negocio — Vacunación y Desparasitación (VAC-XXXX)"""

from typing import List, Dict, Any

from database.repositories import VacunacionRepository
from database.connection import DatabaseManager
from database.models import Vacunacion
from pydantic import ValidationError

from schemas.clinica import VacunacionSchema
from utils.exceptions import BusinessLogicError
from utils.logger import setup_logger

logger = setup_logger()


class VacunaService:
    def __init__(self):
        self.repo = VacunacionRepository()
        self.db_manager = DatabaseManager()

    def generar_codigo(self) -> str:
        """Genera código correlativo de manera atómica."""
        return self.db_manager.generar_codigo('VAC')

    def registrar(self, data: Dict[str, Any]) -> Vacunacion:
        try:
            # Generar código automáticamente si no se proporciona
            if not data.get('codigo'):
                data['codigo'] = self.generar_codigo()

            datos_validados = VacunacionSchema(**data)

            vacunacion = Vacunacion(
                codigo=datos_validados.codigo,
                animal_id=datos_validados.animal_id,
                tipo=datos_validados.tipo.strip(),
                producto=datos_validados.producto.strip(),
                lote=datos_validados.lote.strip() if datos_validados.lote else None,
                dosis=datos_validados.dosis.strip() if datos_validados.dosis else None,
                via=datos_validados.via.strip() if datos_validados.via else None,
                fecha_aplicacion=datos_validados.fecha_aplicacion,
                fecha_proxima=datos_validados.fecha_proxima,
                veterinario=datos_validados.veterinario.strip() if datos_validados.veterinario else None,
                observaciones=datos_validados.observaciones.strip() if datos_validados.observaciones else None)

            vacunacion.id = self.repo.create(vacunacion)
            logger.info(f"Vacunación registrada: {vacunacion.codigo}")
            return vacunacion

        except ValidationError as e:
            error_msg = "\n".join(
                [f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
            logger.error(f"Error Pydantic en vacunación: {error_msg}")
            raise BusinessLogicError(
                f"Datos inválidos en la vacunación:\n{error_msg}")
        except Exception as e:
            logger.error(f"Error inesperado en registrar_vacunacion: {e}")
            raise

    def obtener(self, vid: int) -> Vacunacion:
        return self.repo.get_by_id(vid)

    def listar(self, filtros: dict = None) -> List[Vacunacion]:
        return self.repo.get_all(filtros)

    def por_paciente(self, animal_id: int) -> List[Vacunacion]:
        return self.repo.get_by_animal(animal_id)

    def proximas_a_vencer(self, dias: int = 30) -> List[Vacunacion]:
        """Vacunas/desparasitaciones que vencen en los próximos `dias` días."""
        return self.repo.get_proximas(dias)

    def _validar(self, data: dict) -> None:
        errores = []
        if not data.get('animal_id'):
            errores.append("Debe seleccionar un paciente")
        if data.get('tipo') not in ('Vacuna', 'Desparasitación'):
            errores.append("El tipo debe ser 'Vacuna' o 'Desparasitación'")
        if not data.get('producto', '').strip():
            errores.append("El nombre del producto es obligatorio")
        if not data.get('fecha_aplicacion'):
            errores.append("La fecha de aplicación es obligatoria")
        if errores:
            raise ValidationError(
                "Datos de vacunación inválidos", {
                    'errores': errores})
