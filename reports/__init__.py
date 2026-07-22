# reports/__init__.py
"""Sistema de generación de reportes PDF — ISALAB"""

from reports.config import (
    DatosLaboratorio,
    ColoresMarca,
    Tipografia,
    Margenes,
    ConfiguracionReporte,
)
from reports.base import ReporteBase
from reports.generators import generar_reporte, generar_por_tipo

# Helpers re-exportados para comodidad de los services
from reports.helpers import (
    formatear_fecha,
    formatear_valor_numerico,
    clasificar_valor,
    imagen_a_base64,
    calcular_edad,
    calcular_edad_anios,
    generar_codigo_verificacion,
)
from reports.barcode_utils import (
    generar_codigo_barras_base64,
    generar_qr_base64,
)

__all__ = [
    # Config
    "DatosLaboratorio",
    "ColoresMarca",
    "Tipografia",
    "Margenes",
    "ConfiguracionReporte",
    # Base
    "ReporteBase",
    # Generators
    "generar_reporte",
    "generar_por_tipo",
    # Helpers
    "formatear_fecha",
    "formatear_valor_numerico",
    "clasificar_valor",
    "imagen_a_base64",
    "calcular_edad",
    "calcular_edad_anios",
    "generar_codigo_verificacion",
    "generar_codigo_barras_base64",
    "generar_qr_base64",
]
