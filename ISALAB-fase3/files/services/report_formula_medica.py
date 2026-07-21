# services/report_formula_medica.py
"""Puente para generar fórmulas médicas."""

from typing import Optional, Dict, Any

from reports import (
    generar_reporte,
    generar_por_tipo,
    formatear_fecha,
    generar_codigo_verificacion,
    generar_codigo_barras_base64,
    generar_qr_base64,
    imagen_a_base64,
    DatosLaboratorio,
)
from utils.logger import setup_logger
from utils.security import Authorizer

logger = setup_logger()


class ReporteFormulaMedicaService:
    """Genera PDFs de fórmulas médicas.

    Fase 3 (issue C1 — RBAC bypass): toda generación de PDF requiere
    rol ``asistente`` o superior.
    """

    def __init__(self, usuario_actual: Optional[dict] = None):
        self.lab = DatosLaboratorio()
        self.authorizer = Authorizer(usuario_actual)

    def _check_perm(self) -> None:
        self.authorizer.require_role('asistente')

    # ── API pública ──────────────────────────────────────────────────────

    def generar_pdf(
        self,
        formula_data: Dict[str, Any],
    ) -> bytes:
        self._check_perm()
        contexto = self._construir_contexto(formula_data)
        return generar_reporte("formula_medica", contexto)

    def generar_y_guardar(
        self,
        formula_data: Dict[str, Any],
        ruta_salida: str,
    ) -> str:
        self._check_perm()
        contexto = self._construir_contexto(formula_data)
        return generar_por_tipo("formula_medica", contexto, ruta_salida)

    # ── Contexto ─────────────────────────────────────────────────────────

    def _construir_contexto(
        self,
        formula_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        # Verificación
        codigo_ver = generar_codigo_verificacion()
        codigo_barras = generar_codigo_barras_base64(codigo_ver)
        qr = generar_qr_base64(codigo_ver)
        firma = imagen_a_base64("data/imagenes/firma.png")
        sello = imagen_a_base64("data/imagenes/sello.png")

        return {
            "lab": self.lab,
            # Datos de la fórmula
            "formula": formula_data,
            "fecha": formatear_fecha(formula_data.get('fecha', '')),
            # Verificación
            "codigo_verificacion": codigo_ver,
            "codigo_barras": codigo_barras,
            "qr_base64": qr,
            # Firmas
            "firma_base64": firma,
            "sello_base64": sello,
            "veterinario_nombre": formula_data.get('veterinario', '—'),
        }
