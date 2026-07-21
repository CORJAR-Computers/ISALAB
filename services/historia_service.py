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
        # Fase 5 (H-S5): antes, los campos usaban ``data.get('X') or h.X``
        # lo que significaba que NO se podía limpiar un campo: si el
        # usuario lo dejaba en blanco (``''``), ``'' or h.X`` evaluaba a
        # ``h.X`` (el valor previo). Para campos de texto ahora usamos
        # el patrón ``data.get('X', h.X) or None`` que permite setear a
        # ``None`` pasando ``''`` explícitamente (lo que es razonable:
        # un string vacío = sin valor). Para los vitales numéricos
        # (temperatura, FC, FR, peso) usamos el helper ``_coerce_or_keep``
        # que distingue "no vino en data" (mantener previo) de "vino
        # vacío/None" (limpiar a None) de "vino un 0 legítimo" (setear 0).
        h.anamnesis = data.get('anamnesis', h.anamnesis) or None
        h.examen_fisico = data.get('examen_fisico', h.examen_fisico) or None
        # Fase 5 (H-S5): usamos ``data.get('X', _MISSING)`` para distinguir
        # "key no presente" (mantener valor previo) de "key presente con
        # valor None o ''" (limpiar a None). Antes se usaba ``or h.X``
        # que impedía tanto limpiar campos como setear 0 legítimo.
        h.temperatura = _coerce_or_keep(
            data.get('temperatura', _MISSING), h.temperatura, _float)
        h.frecuencia_cardiaca = _coerce_or_keep(
            data.get('frecuencia_cardiaca', _MISSING),
            h.frecuencia_cardiaca, _int)
        h.frecuencia_respiratoria = _coerce_or_keep(
            data.get('frecuencia_respiratoria', _MISSING),
            h.frecuencia_respiratoria, _int)
        h.peso_consulta = _coerce_or_keep(
            data.get('peso_consulta', _MISSING), h.peso_consulta, _float)
        h.diagnostico = data.get('diagnostico', h.diagnostico) or None
        h.diagnostico_diferencial = data.get(
            'diagnostico_diferencial', h.diagnostico_diferencial) or None
        h.tratamiento = data.get('tratamiento', h.tratamiento) or None
        h.pronostico = data.get('pronostico', h.pronostico) or None
        h.veterinario = data.get('veterinario', h.veterinario) or None
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
# Fase 5 (H-S5): antes, ``_float`` y ``_int`` trataban ``'0'`` y ``0``
# como ``None`` (``val not in (None, '', '0', 0)``), lo que impedía
# registrar una temperatura de 0°C (inusual pero posible en crioterapia)
# o una frecuencia cardiaca de 0 (paro cardíaco — un caso clínico
# perfectamente válido para documentar). Ahora solo tratan como
# ``None`` los valores *ausentes* (``None`` y ``''``); cualquier otro
# string/numérico se intenta convertir.


def _float(val) -> Optional[float]:
    """Convierte ``val`` a ``float``, o ``None`` si está ausente."""
    if val is None or val == '':
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _int(val) -> Optional[int]:
    """Convierte ``val`` a ``int``, o ``None`` si está ausente."""
    if val is None or val == '':
        return None
    try:
        return int(float(val))  # acepta "0.0" → 0
    except (ValueError, TypeError):
        return None


def _coerce_or_keep(new_val, current_val, converter) -> Optional[float]:
    """Decide el valor final de un campo numérico al actualizar.

    - Si ``new_val`` es ``None`` y NO estaba en ``data`` (es decir, el
      caller NO pasó la key), mantiene ``current_val``.
    - Si ``new_val`` es ``''`` o explícitamente pasado como ``None``,
      limpia a ``None`` (el usuario borró el campo).
    - Si ``new_val`` es un valor numérico (incluyendo ``0`` o ``'0'``),
      lo convierte y lo setea.

    Como no podemos distinguir "key no presente" de "key presente con
    valor None" usando ``dict.get`` (ambos retornan None), el caller
    debe pasar ``data.get('X', _MISSING)`` o usar ``'X' in data`` para
    distinguir. Esta función acepta el valor retornado por
    ``data.get('X', _MISSING)`` para mantener el comportamiento.
    """
    if new_val is _MISSING:
        # No vino en data → mantener el valor actual.
        return current_val
    # Vino en data (incluso si es None o '').
    return converter(new_val)


class _MissingSentinel:
    """Sentinel para distinguir "key ausente" de "key presente con None"."""

    def __repr__(self):
        return "<MISSING>"


_MISSING = _MissingSentinel()
