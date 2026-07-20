# services/recepcion_service.py
"""Lógica de negocio — Recepción de pacientes (ISAL-XXXX)"""

from datetime import datetime
from typing import List

from database.repositories import RecepcionRepository, AnimalRepository
from database.models import Recepcion
from utils.logger import setup_logger
from schemas.clinica import RecepcionSchema
from pydantic import ValidationError
from utils.exceptions import BusinessLogicError

logger = setup_logger()


class RecepcionService:
    def __init__(self):
        self.repo = RecepcionRepository()
        self.animal_repo = AnimalRepository()

    # ── Código ────────────────────────────────────────────────────────────
    def generar_codigo(self) -> str:
        """Retorna el próximo código ISAL-XXXX sin consumirlo (vista previa)."""
        # Consultamos el último sin incrementar para mostrar en el formulario;
        # el incremento real ocurre en registrar_recepcion().
        from database.connection import DatabaseManager
        db = DatabaseManager()
        row = db.fetch_one(
            "SELECT ultimo FROM codigo_contadores WHERE prefijo = ?", ('ISAL',))
        siguiente = (row['ultimo'] + 1) if row else 1
        return f"ISAL-{siguiente:04d}"

    # ── CRUD ──────────────────────────────────────────────────────────────
    def registrar_recepcion(self, data: dict):
        try:
            # Generar código automáticamente si no se proporciona
            if not data.get('codigo'):
                data['codigo'] = self.generar_codigo()

            # 1. El guardia de seguridad revisa los datos
            datos_validados = RecepcionSchema(**data)

            # 2. Si pasa, lo convertimos a nuestro modelo tradicional y
            # guardamos
            recepcion = Recepcion(
                codigo=datos_validados.codigo,
                animal_id=datos_validados.animal_id,
                fecha_hora=datos_validados.fecha_hora,
                motivo=datos_validados.motivo,
                veterinario=datos_validados.veterinario,
                estado=datos_validados.estado,
                proxima_cita=datos_validados.proxima_cita,
                observaciones=datos_validados.observaciones
            )
            return self.repo.create(recepcion)

        except ValidationError as e:
            # Formateamos el error para que la interfaz lo muestre bonito
            error_msg = "\n".join(
                [f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
            raise BusinessLogicError(
                f"Datos inválidos en recepción:\n{error_msg}")

    def obtener_recepcion(self, rid: int) -> Recepcion:
        return self.repo.get_by_id(rid)

    def listar_recepciones(self, filtros: dict = None) -> List[Recepcion]:
        return self.repo.get_all(filtros)

    def historial_paciente(self, animal_id: int) -> List[Recepcion]:
        return self.repo.get_by_animal(animal_id)

    def actualizar_estado(self, rid: int, estado: str,
                          proxima_cita: str = None) -> None:
        self.repo.get_by_id(rid)   # valida existencia
        self.repo.update_estado(rid, estado, proxima_cita)
        logger.info(f"Recepción {rid} → estado: {estado}")

    def recepciones_hoy(self) -> List[Recepcion]:
        hoy = datetime.now().strftime('%Y-%m-%d')
        todas = self.repo.get_all()
        return [r for r in todas if r.fecha_hora.startswith(hoy)]

    # ── Validación ────────────────────────────────────────────────────────
    def _validar(self, data: dict) -> None:
        errores = []
        if not data.get('animal_id'):
            errores.append("Debe seleccionar un paciente")
        if not data.get('motivo', '').strip():
            errores.append("El motivo de consulta es obligatorio")
        if errores:
            raise ValidationError(
                "Datos de recepción inválidos", {
                    'errores': errores})
