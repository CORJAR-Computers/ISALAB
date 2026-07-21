# services/report_consentimiento.py
"""Puente para generar consentimientos informados."""

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


class ReporteConsentimientoService:
    """Genera PDFs de consentimientos informados.

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
        consentimiento_data: Dict[str, Any],
    ) -> bytes:
        self._check_perm()
        contexto = self._construir_contexto(consentimiento_data)
        return generar_reporte("consentimiento_informado", contexto)

    def generar_y_guardar(
        self,
        consentimiento_data: Dict[str, Any],
        ruta_salida: str,
    ) -> str:
        self._check_perm()
        contexto = self._construir_contexto(consentimiento_data)
        return generar_por_tipo(
            "consentimiento_informado",
            contexto,
            ruta_salida)

    # ── Contexto ─────────────────────────────────────────────────────────

    def _construir_contexto(
        self,
        consentimiento_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        # Verificación
        codigo_ver = generar_codigo_verificacion()
        codigo_barras = generar_codigo_barras_base64(codigo_ver)
        qr = generar_qr_base64(codigo_ver)
        firma = imagen_a_base64("data/imagenes/firma.png")
        sello = imagen_a_base64("data/imagenes/sello.png")

        return {
            "lab": self.lab,
            # Logo ISALAB
            "logo_isalab": imagen_a_base64("data/imagenes/logo_isalab.png"),
            # Datos del consentimiento
            "consentimiento": consentimiento_data,
            "fecha": formatear_fecha(consentimiento_data.get('fecha', '')),
            # Verificación
            "codigo_verificacion": codigo_ver,
            "codigo_barras": codigo_barras,
            "qr_base64": qr,
            # Firmas
            "firma_base64": firma,
            "sello_base64": sello,
            # Metadatos requeridos por base_report.html
            "metadatos": {
                "titulo": "Consentimiento Informado",
                "es_borrador": False,
                "es_copia": False,
                "codigo_verificacion": codigo_ver,
            },
            # Colores para la plantilla
            "colores": {
                "primario": "#1B5E7B",
                "primario_oscuro": "#0D3B4F",
                "primario_claro": "#E8F4F8",
                "secundario": "#2ECC71",
                "secundario_oscuro": "#27AE60",
                "secundario_claro": "#E8F8F0",
                "acento": "#E74C3C",
                "acento_claro": "#FDEDEC",
                "texto_principal": "#2C3E50",
                "texto_secundario": "#5D6D7E",
                "texto_claro": "#95A5A6",
                "borde": "#BDC3C7",
                "borde_claro": "#ECF0F1",
                "fondo": "#FFFFFF",
                "fondo_alternado": "#F8F9FA",
                "exito": "#27AE60",
                "advertencia": "#F39C12",
                "peligro": "#E74C3C",
                "info": "#3498DB",
            },
            # Tipografía para la plantilla
            "tipografia": {
                "familia_principal": "'Century Gothic', 'Avant Garde', Arial, sans-serif",
                "familia_monospace": "'Consolas', 'Courier New', monospace",
                "tamano_base": 10.0,
                "tamano_titulo": 14.0,
                "tamano_subtitulo": 11.0,
                "tamano_pequeno": 8.0,
                "tamano_mini": 7.0,
            },
            # Configuración del reporte
            "config": {
                "tipo_papel": "Carta",
                "mostrar_marca_agua": True,
                "marca_agua_texto": "ISALAB",
                "marca_agua_opacidad": 0.04,
                "mostrar_codigo_verificacion": True,
                "mostrar_paginacion": True,
            },
            # Márgenes
            "margenes": {
                "superior": 12.0,
                "inferior": 15.0,
                "izquierdo": 15.0,
                "derecho": 15.0,
                "encabezado": 10.0,
                "pie_pagina": 12.0,
            },
        }
