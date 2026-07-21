# services/consulta_service.py
"""Lógica de negocio — Consultas ambulatorias (CONS-XXXX)"""

from typing import List, Dict, Any, Optional

from database.repositories import ConsultaRepository
from database.connection import DatabaseManager
from database.models import Consulta
from pydantic import ValidationError as PydanticValidationError

from schemas.clinica import ConsultaSchema
from utils.exceptions import BusinessLogicError
from utils.logger import setup_logger
from utils.security import Authorizer

logger = setup_logger()


class ConsultaService:
    """Servicio de consultas ambulatorias.

    Fase 3 (issue C1 — RBAC bypass):
        - ``registrar_consulta`` y ``actualizar_consulta`` requieren
          rol ``veterinario`` o superior (son acciones clínicas).
        - Lectura (``obtener_consulta``, ``listar_consultas``,
          ``consultas_por_paciente``, ``generar_codigo``) solo requiere
          usuario autenticado.
    """

    def __init__(self, usuario_actual: Optional[dict] = None):
        self.repo = ConsultaRepository()
        self.db_manager = DatabaseManager()
        self.authorizer = Authorizer(usuario_actual)

    def generar_codigo(self) -> str:
        """Genera código correlativo de manera atómica."""
        # RBAC: cualquier usuario autenticado puede generar (consumir)
        self.authorizer.require_authenticated()
        return self.db_manager.generar_codigo('CONS')

    def registrar_consulta(self, data: Dict[str, Any]) -> Consulta:
        # RBAC: requiere rol veterinario o superior
        self.authorizer.require_role('veterinario')

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

        except PydanticValidationError as e:
            error_msg = "\n".join(
                [f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
            logger.error(f"Error Pydantic en consulta: {error_msg}")
            raise BusinessLogicError(
                f"Datos inválidos en la consulta:\n{error_msg}")
        except Exception as e:
            logger.error(f"Error inesperado en registrar_consulta: {e}")
            raise

    def obtener_consulta(self, cid: int) -> Consulta:
        # RBAC: cualquier usuario autenticado
        self.authorizer.require_authenticated()
        return self.repo.get_by_id(cid)

    def listar_consultas(self, filtros: dict = None) -> List[Consulta]:
        # RBAC: cualquier usuario autenticado
        self.authorizer.require_authenticated()
        return self.repo.get_all(filtros)

    def consultas_por_paciente(self, animal_id: int) -> List[Consulta]:
        # RBAC: cualquier usuario autenticado
        self.authorizer.require_authenticated()
        return self.repo.get_by_animal(animal_id)

    def actualizar_consulta(self, cid: int, data: dict) -> None:
        # RBAC: requiere rol veterinario o superior
        self.authorizer.require_role('veterinario')
        c = self.repo.get_by_id(cid)
        c.motivo = data.get('motivo', c.motivo)
        c.evolucion = data.get('evolucion', c.evolucion)
        c.examen_fisico = data.get('examen_fisico', c.examen_fisico)
        c.tratamiento = data.get('tratamiento', c.tratamiento)
        c.medicamentos = data.get('medicamentos', c.medicamentos)
        c.proxima_consulta = data.get('proxima_consulta', c.proxima_consulta)
        c.veterinario = data.get('veterinario', c.veterinario)
        c.observaciones = data.get('observaciones', c.observaciones)
        self.repo.update(c)
        logger.info(f"Consulta {cid} actualizada")

    def _validar(self, data: dict) -> None:
        errores = []
        if not data.get('animal_id'):
            errores.append("Debe seleccionar un paciente")
        if not data.get('motivo', '').strip():
            errores.append("El motivo de consulta es obligatorio")
        if errores:
            raise BusinessLogicError(
                f"Datos de consulta inválidos: {'; '.join(errores)}")
