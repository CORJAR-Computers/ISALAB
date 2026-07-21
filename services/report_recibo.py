# services/report_recibo.py
"""Puente para generacion de recibos de pago (PDF)."""

from datetime import datetime
from typing import Dict, Any

from reports import generar_reporte, generar_por_tipo, DatosLaboratorio
from utils.logger import setup_logger

logger = setup_logger()


class ReporteReciboService:
    """Genera PDFs de comprobantes de pago."""

    def __init__(self):
        self.lab = DatosLaboratorio()

    # -- API publica ----------------------------------------------------------

    def generar_pdf(self, datos: Dict[str, Any]) -> bytes:
        """Retorna los bytes del PDF del recibo."""
        contexto = self._construir_contexto(datos)
        return generar_reporte("recibo", contexto)

    def generar_y_guardar(self, datos: Dict[str, Any], ruta_salida: str) -> str:
        """Genera el PDF y lo guarda en ruta_salida. Retorna la ruta."""
        contexto = self._construir_contexto(datos)
        # generar_por_tipo retorna bytes cuando no hay clase registrada;
        # escribimos manualmente.
        pdf_bytes = generar_reporte("recibo", contexto)
        with open(ruta_salida, "wb") as f:
            f.write(pdf_bytes)
        logger.info(f"Recibo guardado en {ruta_salida}")
        return ruta_salida

    # -- Contexto -------------------------------------------------------------

    def _construir_contexto(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        fecha_str = datos.get(
            "fecha",
            datetime.now().strftime("%d/%m/%Y"),
        )
        return {
            "lab": self.lab,
            "datos": datos,
            "fecha_str": fecha_str,
        }