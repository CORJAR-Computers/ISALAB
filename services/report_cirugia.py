# services/report_cirugia.py
"""Puente ORM → ReporteBase para informes quirúrgicos."""

import json
from typing import Optional, Dict, Any

from database.models import HistoriaClinica
from database.repositories import (
    CirugiaRepository,
    AnimalRepository,
    HistoriaClinicaRepository,
)
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

logger = setup_logger()


class ReporteCirugiaService:
    """Genera PDFs de informes quirúrgicos."""

    def __init__(self):
        self.cirugia_repo = CirugiaRepository()
        self.animal_repo = AnimalRepository()
        self.historia_repo = HistoriaClinicaRepository()
        self.lab = DatosLaboratorio()

    # ── API pública ──────────────────────────────────────────────────────

    def generar_pdf(
        self,
        cirugia_id: int,
        datos_adicionales: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        contexto = self._construir_contexto(cirugia_id, datos_adicionales)
        return generar_reporte("cirugia", contexto)

    def generar_y_guardar(
        self,
        cirugia_id: int,
        ruta_salida: str,
        datos_adicionales: Optional[Dict[str, Any]] = None,
    ) -> str:
        contexto = self._construir_contexto(cirugia_id, datos_adicionales)
        return generar_por_tipo("cirugia", contexto, ruta_salida)

    # ── Contexto ─────────────────────────────────────────────────────────

    def _construir_contexto(
        self,
        cirugia_id: int,
        datos_adicionales: Optional[Dict],
    ) -> Dict[str, Any]:
        cirugia = self.cirugia_repo.get_by_id(cirugia_id)
        animal = self.animal_repo.get_by_id(cirugia.animal_id)

        # Historia clínica asociada (si existe)
        historia: Optional[HistoriaClinica] = None
        if cirugia.historia_id:
            try:
                historia = self.historia_repo.get_by_id(cirugia.historia_id)
            except Exception:
                historia = None

        # Merge datos adicionales con defaults
        extra = self._merge_datos_adicionales(datos_adicionales, historia)

        # Intentar parsear protocolo anestésico como JSON estructurado
        protocolo_estructurado = self._parsear_protocolo(
            cirugia.protocolo_anestesico)

        # Pronóstico CSS class
        pronostico_css = self._pronostico_css(extra.get("pronostico"))

        # Verificación
        codigo_ver = generar_codigo_verificacion()
        codigo_barras = generar_codigo_barras_base64(codigo_ver)
        qr = generar_qr_base64(codigo_ver)
        firma = imagen_a_base64("data/imagenes/firma.png")
        sello = imagen_a_base64("data/imagenes/sello.png")

        return {
            "lab": self.lab,
            # Cirugía
            "cirugia": cirugia,
            "fecha": formatear_fecha(cirugia.fecha),
            # Paciente
            "animal": animal,
            # Anestesia
            "protocolo_estructurado": protocolo_estructurado,
            # Datos extra (dx preop, hallazgos, horas, etc.)
            "datos_adicionales": extra,
            # Pronóstico badge
            "pronostico_css": pronostico_css,
            # Historia clínica referenciada
            "historia": historia,
            "diagnostico_hc": historia.diagnostico if historia else None,
            # Verificación
            "codigo_verificacion": codigo_ver,
            "codigo_barras": codigo_barras,
            "qr_base64": qr,
            # Firmas
            "firma_base64": firma,
            "sello_base64": sello,
        }

    # ── Helpers internos ─────────────────────────────────────────────────

    def _merge_datos_adicionales(
        self,
        extras: Optional[Dict],
        historia: Optional[HistoriaClinica],
    ) -> Dict[str, Any]:
        """Combina datos adicionales del caller con info de la HC."""
        base: Dict[str, Any] = {
            "sexo": "—",
            "edad_texto": "—",
            "diagnostico_preoperatorio": None,
            "hallazgos_quirurgicos": None,
            "material_extraido": None,
            "hora_inicio": None,
            "hora_fin": None,
            "pronostico": "Reservado",
            "observaciones_pronostico": None,
            "instrumentador": None,
            "mp_cirujano": None,
            "mp_anestesiologo": None,
        }

        # Tomar dx de la historia clínica como default
        if historia:
            base["diagnostico_preoperatorio"] = historia.diagnostico
            base["pronostico"] = historia.pronostico or "Reservado"
            base["observaciones_pronostico"] = historia.tratamiento

        # Sobrescribir con lo que mande el caller
        if extras:
            for k, v in extras.items():
                if v is not None:
                    base[k] = v

        return base

    def _parsear_protocolo(
        self, protocolo: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Intenta parsear el protocolo anestésico como JSON estructurado.
        Si no es JSON válido, retorna None (el template usará texto plano).

        Formato JSON esperado:
        {
            "preanestesia": "Acepromazina 0.02 mg/kg IM",
            "induccion": "Ketamina 5 mg/kg + Diazepam 0.5 mg/kg IV",
            "mantenimiento": "Isofluorano 1.5-2%",
            "reversion": "—",
            "fluidoterapia": "Ringer Lactato 10 ml/kg/h",
            "monitoreo": "FC, FR, SpO2, T°C cada 10 min",
            "signos_vitales": [
                {"momento": "Inducción", "temperatura": "38.2", "fc": "120", "fr": "20", "spo2": "98", "otros": ""},
                {"momento": "30 min", "temperatura": "37.8", "fc": "100", "fr": "18", "spo2": "97", "otros": ""},
                {"momento": "Final", "temperatura": "37.5", "fc": "90", "fr": "16", "spo2": "98", "otros": ""}
            ]
        }
        """
        if not protocolo:
            return None
        try:
            datos = json.loads(protocolo)
            if isinstance(datos, dict) and any(
                k in datos for k in (
                    "preanestesia", "induccion", "mantenimiento",
                    "monitoreo", "signos_vitales"
                )
            ):
                return datos
        except (json.JSONDecodeError, TypeError):
            pass
        return None

    @staticmethod
    def _pronostico_css(pronostico: Optional[str]) -> str:
        if not pronostico:
            return "reservado"
        p = pronostico.strip().lower()
        if p in ("bueno", "favorable"):
            return "bueno"
        elif p in ("grave", "desfavorable", "fatal"):
            return "grave"
        return "reservado"
