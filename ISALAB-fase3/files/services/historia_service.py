# services/historia_service.py
"""Lógica de negocio — Historia clínica"""

from datetime import datetime
from typing import List, Optional

from database.repositories import HistoriaClinicaRepository, RecepcionRepository
from database.models import HistoriaClinica
from utils.exceptions import BusinessLogicError
from utils.logger import setup_logger
from utils.security import Authorizer

logger = setup_logger()


class HistoriaService:
    """Servicio de historias clínicas.

    Fase 3 (issue C1 — RBAC bypass):
        - ``crear_historia`` y ``actualizar_historia`` requieren rol
          ``veterinario`` o superior (son acciones clínicas).
        - Lectura solo requiere usuario autenticado.
    """

    def __init__(self, usuario_actual: Optional[dict] = None):
        self.repo = HistoriaClinicaRepository()
        self.rec_repo = RecepcionRepository()
        self.authorizer = Authorizer(usuario_actual)

    def crear_historia(self, data: dict) -> HistoriaClinica:
        # RBAC: requiere rol veterinario o superior
        self.authorizer.require_role('veterinario')

        self._validar(data)
        historia = HistoriaClinica(
            recepcion_id=int(data['recepcion_id']),
            animal_id=int(data['animal_id']),
            fecha=data.get('fecha') or datetime.now().strftime('%Y-%m-%d'),
            anamnesis=data.get('anamnesis') or None,
            examen_fisico=data.get('examen_fisico') or None,
            temperatura=_float(data.get('temperatura')),
            frecuencia_cardiaca=_int(data.get('frecuencia_cardiaca')),
            frecuencia_respiratoria=_int(data.get('frecuencia_respiratoria')),
            peso_consulta=_float(data.get('peso_consulta')),
            diagnostico=data.get('diagnostico') or None,
            diagnostico_diferencial=data.get('diagnostico_diferencial') or None,
            tratamiento=data.get('tratamiento') or None,
            pronostico=data.get('pronostico') or None,
            veterinario=data.get('veterinario', '').strip() or None,
        )
        historia.id = self.repo.create(historia)
        logger.info(
            f"Historia clínica {
                historia.id} para animal {
                historia.animal_id}")
        return historia

    def obtener_historia(self, hid: int) -> HistoriaClinica:
        # RBAC: cualquier usuario autenticado
        self.authorizer.require_authenticated()
        return self.repo.get_by_id(hid)

    def historias_por_paciente(self, animal_id: int) -> List[HistoriaClinica]:
        # RBAC: cualquier usuario autenticado
        self.authorizer.require_authenticated()
        return self.repo.get_by_animal(animal_id)

    def historia_de_recepcion(
            self,
            recepcion_id: int) -> Optional[HistoriaClinica]:
        # RBAC: cualquier usuario autenticado
        self.authorizer.require_authenticated()
        return self.repo.get_by_recepcion(recepcion_id)

    def actualizar_historia(self, hid: int, data: dict) -> None:
        # RBAC: requiere rol veterinario o superior
        self.authorizer.require_role('veterinario')

        h = self.repo.get_by_id(hid)
        h.anamnesis = data.get('anamnesis') or h.anamnesis
        h.examen_fisico = data.get('examen_fisico') or h.examen_fisico
        h.temperatura = _float(data.get('temperatura')) or h.temperatura
        h.frecuencia_cardiaca = _int(
            data.get('frecuencia_cardiaca')) or h.frecuencia_cardiaca
        h.frecuencia_respiratoria = _int(
            data.get('frecuencia_respiratoria')) or h.frecuencia_respiratoria
        h.peso_consulta = _float(data.get('peso_consulta')) or h.peso_consulta
        h.diagnostico = data.get('diagnostico') or h.diagnostico
        h.diagnostico_diferencial = data.get(
            'diagnostico_diferencial') or h.diagnostico_diferencial
        h.tratamiento = data.get('tratamiento') or h.tratamiento
        h.pronostico = data.get('pronostico') or h.pronostico
        h.veterinario = data.get('veterinario') or h.veterinario
        self.repo.update(h)
        logger.info(f"Historia clínica {hid} actualizada")

    def _validar(self, data: dict) -> None:
        errores = []
        if not data.get('recepcion_id'):
            errores.append("La recepción es obligatoria")
        if not data.get('animal_id'):
            errores.append("El paciente es obligatorio")
        if errores:
            raise BusinessLogicError(
                f"Datos de historia clínica inválidos: {'; '.join(errores)}")


# ── helpers de conversión segura ──────────────────────────────────────────
def _float(val) -> Optional[float]:
    try:
        return float(val) if val not in (None, '', '0', 0) else None
    except (ValueError, TypeError):
        return None


def _int(val) -> Optional[int]:
    try:
        return int(val) if val not in (None, '', '0', 0) else None
    except (ValueError, TypeError):
        return None
