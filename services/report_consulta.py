# services/report_consulta.py
"""Puente ORM → ReporteBase para consultas ambulatorias."""

from typing import Optional, Dict, Any

from database.repositories import (
    ConsultaRepository,
    AnimalRepository,
)
from reports import (
    generar_reporte,
    generar_por_tipo,
    formatear_fecha,
    generar_codigo_verificacion,
    generar_codigo_barras_base64,
    generar_qr_base64,
    imagen_a_base64,
    calcular_edad,
    DatosLaboratorio,
)
from utils.logger import setup_logger
from utils.security import Authorizer

logger = setup_logger()


class ReporteConsultaService:
    """Genera PDFs de consultas ambulatorias.

    Fase 3 (issue C1 — RBAC bypass): toda generación de PDF requiere
    rol ``asistente`` o superior.
    """

    def __init__(self, usuario_actual: Optional[dict] = None):
        self.consulta_repo = ConsultaRepository()
        self.animal_repo = AnimalRepository()
        self.lab = DatosLaboratorio()
        self.authorizer = Authorizer(usuario_actual)

    def _check_perm(self) -> None:
        self.authorizer.require_role('asistente')

    # ── API pública ──────────────────────────────────────────────────────

    def generar_pdf(
        self,
        consulta_obj,
    ) -> bytes:
        self._check_perm()
        contexto = self._construir_contexto(consulta_obj)
        return generar_reporte("consulta", contexto)

    def generar_y_guardar(
        self,
        consulta_id: int,
        ruta_salida: str,
    ) -> str:
        self._check_perm()
        consulta = self.consulta_repo.get_by_id(consulta_id)
        contexto = self._construir_contexto(consulta)
        return generar_por_tipo("consulta", contexto, ruta_salida)

    # ── Contexto ─────────────────────────────────────────────────────────

    def _construir_contexto(
        self,
        consulta,
    ) -> Dict[str, Any]:
        animal = self.animal_repo.get_by_id(consulta.animal_id)

        # Verificación
        codigo_ver = generar_codigo_verificacion()
        codigo_barras = generar_codigo_barras_base64(codigo_ver)
        qr = generar_qr_base64(codigo_ver)
        firma = imagen_a_base64("data/imagenes/firma.png")
        sello = imagen_a_base64("data/imagenes/sello.png")

        return {
            "lab": self.lab,
            # Consulta
            "consulta": consulta,
            "fecha": formatear_fecha(consulta.fecha),
            # Paciente
            "animal": animal,
            "edad_texto": calcular_edad(animal.fecha_ingreso),
            # Verificación
            "codigo_verificacion": codigo_ver,
            "codigo_barras": codigo_barras,
            "qr_base64": qr,
            # Firmas
            "firma_base64": firma,
            "sello_base64": sello,
            "veterinario_nombre": consulta.veterinario or "—",
        }
