# services/report_vacunacion.py
"""Puente ORM → ReporteBase para certificados de vacunación."""

from typing import Optional, Dict, Any

from database.repositories import VacunacionRepository, AnimalRepository
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

logger = setup_logger()


class ReporteVacunacionService:
    """Genera PDFs de certificados de vacunación / desparasitación."""

    def __init__(self):
        self.vacuna_repo = VacunacionRepository()
        self.animal_repo = AnimalRepository()
        self.lab = DatosLaboratorio()

    # ── API pública ──────────────────────────────────────────────────────

    def generar_pdf(self, vacunacion_id: int) -> bytes:
        contexto = self._construir_contexto(vacunacion_id)
        return generar_reporte("vacunacion", contexto)

    def generar_y_guardar(
        self, vacunacion_id: int, ruta_salida: str
    ) -> str:
        contexto = self._construir_contexto(vacunacion_id)
        return generar_por_tipo("vacunacion", contexto, ruta_salida)

    # ── Contexto ─────────────────────────────────────────────────────────

    def _construir_contexto(self, vacunacion_id: int) -> Dict[str, Any]:
        vacuna = self.vacuna_repo.get_by_id(vacunacion_id)
        animal = self.animal_repo.get_by_id(vacuna.animal_id)

        # Historial de vacunas previas del paciente (para mostrar esquema)
        historial = self.vacuna_repo.get_by_animal(vacuna.animal_id)

        codigo_ver = generar_codigo_verificacion()
        codigo_barras = generar_codigo_barras_base64(codigo_ver)
        qr = generar_qr_base64(codigo_ver)
        firma = imagen_a_base64("data/imagenes/firma.png")
        sello = imagen_a_base64("data/imagenes/sello.png")

        # Determinar si es vacuna o desparasitación para el título
        es_vacuna = vacuna.tipo.lower() == "vacuna"
        titulo = "CERTIFICADO DE VACUNACIÓN" if es_vacuna else "CERTIFICADO DE DESPARASITACIÓN"

        # Badge de vía de administración
        via_badge = self._badge_via(vacuna.via)

        return {
            "lab": self.lab,
            "titulo": titulo,
            "es_vacuna": es_vacuna,
            # Registro actual
            "vacuna": vacuna,
            "fecha_aplicacion": formatear_fecha(vacuna.fecha_aplicacion),
            "fecha_proxima": (
                formatear_fecha(vacuna.fecha_proxima)
                if vacuna.fecha_proxima else None
            ),
            "via_badge": via_badge,
            # Paciente
            "animal": animal,
            "edad_texto": calcular_edad(animal.fecha_ingreso),
            # Historial previo
            "historial_vacunas": [
                h for h in historial if h.id != vacuna.id
            ],
            "tiene_historial": len(historial) > 1,
            # Verificación
            "codigo_verificacion": codigo_ver,
            "codigo_barras": codigo_barras,
            "qr_base64": qr,
            # Firmas
            "firma_base64": firma,
            "sello_base64": sello,
            "veterinario_nombre": vacuna.veterinario or "—",
        }

    @staticmethod
    def _badge_via(via: Optional[str]) -> Dict[str, str]:
        """Retorna css_class y label para la vía de administración."""
        if not via:
            return {"css": "via-default", "label": "—"}
        via_map = {
            "SC": ("via-sc", "Subcutánea"),
            "IM": ("via-im", "Intramuscular"),
            "IV": ("via-iv", "Intravenosa"),
            "PO": ("via-po", "Oral"),
            "TOP": ("via-top", "Tópica"),
            "TÓPICA": ("via-top", "Tópica"),
            "ORAL": ("via-po", "Oral"),
            "SUBCUTÁNEA": ("via-sc", "Subcutánea"),
            "INTRAMUSCULAR": ("via-im", "Intramuscular"),
            "INTRAVENOSA": ("via-iv", "Intravenosa"),
        }
        css, label = via_map.get(via.upper(), ("via-default", via))
        return {"css": css, "label": label}
