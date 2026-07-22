# services/pdf_service.py
"""
Fachada unificada para generación de PDFs — ISALAB.
"""

import os
import json
from typing import Optional, Dict, List, Any
from config import PDF_DIR

from utils.logger import setup_logger

logger = setup_logger()


class PDFService:
    """Fachada que unifica todos los generadores de reporte."""

    # ── Muestra (Compatibilidad con muestra_dialog.py) ──────────────────

    def generar_reporte_muestra(self, muestra) -> str:
        """
        Genera y guarda PDF para un objeto Muestra.
        Detecta automáticamente si es empresa o persona natural.
        Retorna la ruta del archivo generado.
        """
        from services.report_laboratorio import ReporteLaboratorioService

        svc = ReporteLaboratorioService()

        # Determinar si es empresa (el campo viene de la GUI)
        entidad = getattr(
            muestra,
            'empresa',
            'Persona Natural') or 'Persona Natural'
        es_empresa = entidad.upper() != "PERSONA NATURAL"

        datos_empresa = None
        if es_empresa:
            datos_empresa = {"nombre": entidad}

        # Nombre del archivo
        nombre_archivo = f"resultado_{
            muestra.codigo}_id{
            muestra.animal_id}.pdf"
        ruta_salida = self.ruta_default(nombre_archivo)

        # Intentar extraer resultados estructurados del texto
        resultados = self._extraer_resultados(muestra)

        return svc.generar_y_guardar(
            muestra_id=muestra.id,
            ruta_salida=ruta_salida,
            resultados_estructurados=resultados,
            es_empresa=es_empresa,
            datos_empresa=datos_empresa,
        )

    # ── Laboratorio (API directa) ────────────────────────────────────────

    def generar_laboratorio(
        self,
        muestra_id: int,
        resultados_estructurados: Optional[List[Dict]] = None,
        es_empresa: bool = False,
        datos_empresa: Optional[Dict[str, str]] = None,
    ) -> bytes:
        from services.report_laboratorio import ReporteLaboratorioService
        svc = ReporteLaboratorioService()
        return svc.generar_pdf(
            muestra_id=muestra_id,
            resultados_estructurados=resultados_estructurados,
            es_empresa=es_empresa,
            datos_empresa=datos_empresa,
        )

    def guardar_laboratorio(
        self,
        muestra_id: int,
        ruta_salida: str,
        resultados_estructurados: Optional[List[Dict]] = None,
        es_empresa: bool = False,
        datos_empresa: Optional[Dict[str, str]] = None,
    ) -> str:
        from services.report_laboratorio import ReporteLaboratorioService
        svc = ReporteLaboratorioService()
        return svc.generar_y_guardar(
            muestra_id=muestra_id,
            ruta_salida=ruta_salida,
            resultados_estructurados=resultados_estructurados,
            es_empresa=es_empresa,
            datos_empresa=datos_empresa,
        )

    # ── Vacunación ───────────────────────────────────────────────────────

    def generar_vacunacion(self, vacunacion_id: int) -> bytes:
        from services.report_vacunacion import ReporteVacunacionService
        svc = ReporteVacunacionService()
        return svc.generar_pdf(vacunacion_id)

    def guardar_vacunacion(self, vacunacion_id: int, ruta_salida: str) -> str:
        from services.report_vacunacion import ReporteVacunacionService
        svc = ReporteVacunacionService()
        return svc.generar_y_guardar(vacunacion_id, ruta_salida)

    # ── Historia Clínica ─────────────────────────────────────────────────

    def generar_historia_clinica(
        self,
        historia_id: int,
        incluir_consultas: bool = True,
        incluir_vacunas: bool = False,
    ) -> bytes:
        from services.report_historia_clinica import ReporteHistoriaClinicaService
        svc = ReporteHistoriaClinicaService()
        return svc.generar_pdf(historia_id, incluir_consultas, incluir_vacunas)

    def guardar_historia_clinica(
        self,
        historia_id: int,
        ruta_salida: str,
        incluir_consultas: bool = True,
        incluir_vacunas: bool = False,
    ) -> str:
        from services.report_historia_clinica import ReporteHistoriaClinicaService
        svc = ReporteHistoriaClinicaService()
        return svc.generar_y_guardar(
            historia_id, ruta_salida, incluir_consultas, incluir_vacunas
        )

    # ── Cirugía ──────────────────────────────────────────────────────────

    def generar_cirugia(
        self,
        cirugia_id: int,
        datos_adicionales: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        from services.report_cirugia import ReporteCirugiaService
        svc = ReporteCirugiaService()
        return svc.generar_pdf(cirugia_id, datos_adicionales)

    def guardar_cirugia(
        self,
        cirugia_id: int,
        ruta_salida: str,
        datos_adicionales: Optional[Dict[str, Any]] = None,
    ) -> str:
        from services.report_cirugia import ReporteCirugiaService
        svc = ReporteCirugiaService()
        return svc.generar_y_guardar(
            cirugia_id, ruta_salida, datos_adicionales)

    # ── Consulta ──────────────────────────────────────────────────────────

    def generar_consulta(
        self,
        consulta_obj,
    ) -> bytes:
        """Genera PDF de una consulta ambulatoria."""
        from services.report_consulta import ReporteConsultaService
        svc = ReporteConsultaService()
        return svc.generar_pdf(consulta_obj)

    def guardar_consulta(
        self,
        consulta_id: int,
        ruta_salida: str,
    ) -> str:
        from services.report_consulta import ReporteConsultaService
        svc = ReporteConsultaService()
        return svc.generar_y_guardar(consulta_id, ruta_salida)

    # ── Recibo ────────────────────────────────────────────────────────────

    def generar_recibo(
        self,
        datos: Dict[str, Any],
    ) -> bytes:
        """Genera PDF de un recibo de pago."""
        from services.report_recibo import ReporteReciboService
        svc = ReporteReciboService()
        return svc.generar_pdf(datos)

    def guardar_recibo(
        self,
        datos: Dict[str, Any],
        ruta_salida: str,
    ) -> str:
        from services.report_recibo import ReporteReciboService
        svc = ReporteReciboService()
        return svc.generar_y_guardar(datos, ruta_salida)

    # ── Utilidades internas ──────────────────────────────────────────────

    @staticmethod
    def ruta_default(nombre_archivo: str) -> str:
        carpeta = str(PDF_DIR)
        os.makedirs(carpeta, exist_ok=True)
        return os.path.join(carpeta, nombre_archivo)

    @staticmethod
    def _extraer_resultados(muestra) -> Optional[List[Dict]]:
        """Intenta parsear muestra.resultado como JSON estructurado."""
        if not hasattr(muestra, 'resultado') or not muestra.resultado:
            return None
        try:
            datos = json.loads(muestra.resultado)
            if isinstance(datos, list):
                return datos
            elif isinstance(datos, dict):
                if "secciones" in datos:
                    items = []
                    for sec in datos["secciones"]:
                        for it in sec.get("items", []):
                            it["seccion"] = sec["nombre"]
                            items.append(it)
                    return items
                elif "items" in datos:
                    return datos["items"]
        except (json.JSONDecodeError, TypeError):
            pass
        return None


# Instancia singleton para importes rápidos
pdf_service = PDFService()
