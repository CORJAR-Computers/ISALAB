# gui_pyside/dialogos/dialogo_generar_reporte.py
"""Diálogo reutilizable para generar cualquier tipo de reporte PDF."""

import os
from pathlib import Path

from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QProgressBar,
)
from PySide6.QtGui import QFont

from utils.logger import setup_logger
from gui_pyside.utils.messages import show_error, show_warning
from gui_pyside.utils.platform_utils import open_file_externally

logger = setup_logger()


# ══════════════════════════════════════════════════════════════════════════
#  Worker en hilo separado — evita congelar la GUI
# ══════════════════════════════════════════════════════════════════════════

class ReportWorker(QObject):
    """Ejecuta la generación del PDF en un QThread sin bloquear la UI."""

    terminado = Signal(bytes)       # PDF bytes cuando es exitoso
    guardado = Signal(str)          # ruta del archivo cuando se guarda
    error = Signal(str)             # mensaje de error
    progreso = Signal(int)          # 0-100

    def __init__(self, tipo: str, kwargs: dict, guardar_en: str = None):
        super().__init__()
        self.tipo = tipo
        self.kwargs = kwargs
        self.guardar_en = guardar_en

    def run(self):
        try:
            self.progreso.emit(10)

            if self.tipo == "laboratorio":
                from services.report_laboratorio import ReporteLaboratorioService
                svc = ReporteLaboratorioService()
                self.progreso.emit(30)
                if self.guardar_en:
                    ruta = svc.generar_y_guardar(
                        **self.kwargs, ruta_salida=self.guardar_en)
                    self.progreso.emit(100)
                    self.guardado.emit(ruta)
                else:
                    pdf_bytes = svc.generar_pdf(**self.kwargs)
                    self.progreso.emit(100)
                    self.terminado.emit(pdf_bytes)

            elif self.tipo == "vacunacion":
                from services.report_vacunacion import ReporteVacunacionService
                svc = ReporteVacunacionService()
                self.progreso.emit(30)
                if self.guardar_en:
                    ruta = svc.generar_y_guardar(
                        **self.kwargs, ruta_salida=self.guardar_en)
                    self.progreso.emit(100)
                    self.guardado.emit(ruta)
                else:
                    pdf_bytes = svc.generar_pdf(**self.kwargs)
                    self.progreso.emit(100)
                    self.terminado.emit(pdf_bytes)

            elif self.tipo == "historia_clinica":
                from services.report_historia_clinica import ReporteHistoriaClinicaService
                svc = ReporteHistoriaClinicaService()
                self.progreso.emit(30)
                if self.guardar_en:
                    ruta = svc.generar_y_guardar(
                        **self.kwargs, ruta_salida=self.guardar_en)
                    self.progreso.emit(100)
                    self.guardado.emit(ruta)
                else:
                    pdf_bytes = svc.generar_pdf(**self.kwargs)
                    self.progreso.emit(100)
                    self.terminado.emit(pdf_bytes)

            elif self.tipo == "cirugia":
                from services.report_cirugia import ReporteCirugiaService
                svc = ReporteCirugiaService()
                self.progreso.emit(30)
                if self.guardar_en:
                    ruta = svc.generar_y_guardar(
                        **self.kwargs, ruta_salida=self.guardar_en)
                    self.progreso.emit(100)
                    self.guardado.emit(ruta)
                else:
                    pdf_bytes = svc.generar_pdf(**self.kwargs)
                    self.progreso.emit(100)
                    self.terminado.emit(pdf_bytes)

            elif self.tipo == "consulta":
                from services.report_consulta import ReporteConsultaService
                from database.repositories import ConsultaRepository
                svc = ReporteConsultaService()
                self.progreso.emit(30)
                # consulta_id viene del kwargs
                if self.guardar_en:
                    ruta = svc.generar_y_guardar(
                        **self.kwargs, ruta_salida=self.guardar_en)
                    self.progreso.emit(100)
                    self.guardado.emit(ruta)
                else:
                    # Generar con el ID directamente
                    consulta_id = self.kwargs.get('consulta_id')
                    consulta_repo = ConsultaRepository()
                    consulta = consulta_repo.get_by_id(consulta_id)
                    pdf_bytes = svc.generar_pdf(consulta)
                    self.progreso.emit(100)
                    self.terminado.emit(pdf_bytes)

            elif self.tipo == "formula_medica":
                from services.report_formula_medica import ReporteFormulaMedicaService
                svc = ReporteFormulaMedicaService()
                self.progreso.emit(30)
                if self.guardar_en:
                    ruta = svc.generar_y_guardar(
                        **self.kwargs, ruta_salida=self.guardar_en)
                    self.progreso.emit(100)
                    self.guardado.emit(ruta)
                else:
                    pdf_bytes = svc.generar_pdf(**self.kwargs)
                    self.progreso.emit(100)
                    self.terminado.emit(pdf_bytes)

            elif self.tipo == "consentimiento":
                from services.report_consentimiento import ReporteConsentimientoService
                svc = ReporteConsentimientoService()
                self.progreso.emit(30)
                if self.guardar_en:
                    ruta = svc.generar_y_guardar(
                        **self.kwargs, ruta_salida=self.guardar_en)
                    self.progreso.emit(100)
                    self.guardado.emit(ruta)
                else:
                    pdf_bytes = svc.generar_pdf(**self.kwargs)
                    self.progreso.emit(100)
                    self.terminado.emit(pdf_bytes)

            else:
                self.error.emit(f"Tipo de reporte desconocido: {self.tipo}")

        except Exception as e:
            logger.error(
                f"Error generando reporte {
                    self.tipo}: {e}",
                exc_info=True)
            self.error.emit(str(e))


# ══════════════════════════════════════════════════════════════════════════
#  Diálogo de generación
# ══════════════════════════════════════════════════════════════════════════

class DialogoGenerarReporte(QDialog):
    """
    Diálogo modal que muestra progreso y permite guardar/abrir el PDF.

    Uso desde cualquier ventana:

        # Ejemplo 1: Reporte de laboratorio (persona natural)
        dlg = DialogoGenerarReporte(self)
        dlg.generar_laboratorio(muestra_id=42)

        # Ejemplo 2: Reporte de laboratorio (empresa)
        dlg = DialogoGenerarReporte(self)
        dlg.generar_laboratorio(
            muestra_id=42,
            es_empresa=True,
            datos_empresa={
                "nombre": "C.V. RUFFOS HOUSE",
                "nit": "901.234.567-8",
                "municipio": "Sincelejo",
                "departamento": "Sucre",
            }
        )

        # Ejemplo 3: Certificado de vacunación
        dlg = DialogoGenerarReporte(self)
        dlg.generar_vacunacion(vacunacion_id=15)

        # Ejemplo 4: Historia clínica completa
        dlg = DialogoGenerarReporte(self)
        dlg.generar_historia_clinica(historia_id=8, incluir_vacunas=True)

        # Ejemplo 5: Informe quirúrgico
        dlg = DialogoGenerarReporte(self)
        dlg.generar_cirugia(
            cirugia_id=3,
            datos_adicionales={
                "sexo": "HEMBRA",
                "edad_texto": "6 años",
                "diagnostico_preoperatorio": "Masa mamaria",
                "hallazgos_quirurgicos": "Masa de 3cm...",
                "hora_inicio": "09:30",
                "hora_fin": "10:45",
                "pronostico": "Bueno",
                "instrumentador": "Carlos Pérez",
                "mp_cirujano": "12345",
            }
        )
    """

    DIRECTORIO_PDFS = "data/pdfs"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generar Reporte PDF — ISALAB")
        self.setMinimumWidth(420)
        self.setModal(True)

        self._pdf_bytes: bytes = b""
        self._ruta_guardado: str = ""
        self._thread: QThread = None
        self._worker: ReportWorker = None

        self._construir_ui()

    # ── UI ───────────────────────────────────────────────────────────────

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Título
        titulo = QLabel("Generación de Reporte")
        titulo.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(titulo)

        # Estado
        self.lbl_estado = QLabel("Preparando...")
        self.lbl_estado.setWordWrap(True)
        layout.addWidget(self.lbl_estado)

        # Barra de progreso
        self.barra = QProgressBar()
        self.barra.setRange(0, 100)
        self.barra.setValue(0)
        layout.addWidget(self.barra)

        # Botones
        btn_layout = QHBoxLayout()

        self.btn_guardar = QPushButton("💾  Guardar como PDF")
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.clicked.connect(self._guardar_como)
        btn_layout.addWidget(self.btn_guardar)

        self.btn_abrir = QPushButton("📂  Abrir PDF")
        self.btn_abrir.setEnabled(False)
        self.btn_abrir.clicked.connect(self._abrir_pdf)
        btn_layout.addWidget(self.btn_abrir)

        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_cerrar)

        layout.addLayout(btn_layout)

    # ── Métodos públicos (API para la GUI) ──────────────────────────────

    def generar_laboratorio(
        self,
        muestra_id: int,
        resultados_estructurados: list = None,
        es_empresa: bool = False,
        datos_empresa: dict = None,
    ):
        """Dispara la generación de un reporte de laboratorio."""
        self._lanzar_worker(
            tipo="laboratorio",
            kwargs={
                "muestra_id": muestra_id,
                "resultados_estructurados": resultados_estructurados,
                "es_empresa": es_empresa,
                "datos_empresa": datos_empresa,
            },
        )

    def generar_vacunacion(self, vacunacion_id: int):
        self._lanzar_worker(
            tipo="vacunacion",
            kwargs={"vacunacion_id": vacunacion_id},
        )

    def generar_historia_clinica(
        self,
        historia_id: int,
        incluir_consultas: bool = True,
        incluir_vacunas: bool = False,
    ):
        self._lanzar_worker(
            tipo="historia_clinica",
            kwargs={
                "historia_id": historia_id,
                "incluir_consultas": incluir_consultas,
                "incluir_vacunas": incluir_vacunas,
            },
        )

    def generar_cirugia(
        self,
        cirugia_id: int,
        datos_adicionales: dict = None,
    ):
        self._lanzar_worker(
            tipo="cirugia",
            kwargs={
                "cirugia_id": cirugia_id,
                "datos_adicionales": datos_adicionales,
            },
        )

    def generar_consulta(
        self,
        consulta_id: int,
    ):
        self._lanzar_worker(
            tipo="consulta",
            kwargs={
                "consulta_id": consulta_id,
            },
        )

    def generar_formula_medica(
        self,
        formula_data: dict,
    ):
        self._lanzar_worker(
            tipo="formula_medica",
            kwargs={
                "formula_data": formula_data,
            },
        )

    def generar_consentimiento(
        self,
        consentimiento_data: dict,
    ):
        self._lanzar_worker(
            tipo="consentimiento",
            kwargs={
                "consentimiento_data": consentimiento_data,
            },
        )

    # ── Interno: hilo + señales ─────────────────────────────────────────

    def _lanzar_worker(self, tipo: str, kwargs: dict):
        self.lbl_estado.setText(
            f"Generando reporte de {
                tipo.replace(
                    '_', ' ')}...")
        self.barra.setValue(0)
        self.btn_guardar.setEnabled(False)
        self.btn_abrir.setEnabled(False)
        self._pdf_bytes = b""
        self._ruta_guardado = ""

        # Crear hilo y worker
        self._thread = QThread(self)
        self._worker = ReportWorker(tipo, kwargs)
        self._worker.moveToThread(self._thread)

        # Conectar señales
        self._thread.started.connect(self._worker.run)
        self._worker.progreso.connect(self.barra.setValue)
        self._worker.terminado.connect(self._on_terminado)
        self._worker.guardado.connect(self._on_guardado)
        self._worker.error.connect(self._on_error)
        self._worker.terminado.connect(self._thread.quit)
        self._worker.guardado.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._limpiar_thread)

        self._thread.start()

    def _on_terminado(self, pdf_bytes: bytes):
        self._pdf_bytes = pdf_bytes
        self.lbl_estado.setText(
            f"✅ Reporte generado exitosamente ({len(pdf_bytes):,} bytes)"
        )
        self.btn_guardar.setEnabled(True)
        self.btn_abrir.setEnabled(True)

    def _on_guardado(self, ruta: str):
        self._ruta_guardado = ruta
        self._pdf_bytes = Path(ruta).read_bytes() if Path(
            ruta).exists() else b""
        self.lbl_estado.setText(f"✅ Guardado en: {ruta}")
        self.btn_guardar.setEnabled(True)
        self.btn_abrir.setEnabled(True)

    def _on_error(self, mensaje: str):
        self.lbl_estado.setText(f"❌ Error: {mensaje}")
        show_error(
            self,
            "No se pudo generar el reporte PDF.",
            Exception(mensaje))

    def _limpiar_thread(self):
        if self._thread:
            self._thread.deleteLater()
            self._thread = None
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

    # ── Guardar / Abrir ──────────────────────────────────────────────────

    def _guardar_como(self):
        if not self._pdf_bytes:
            return

        ruta_default = os.path.join(
            self.DIRECTORIO_PDFS, "reporte_isalab.pdf"
        )
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte PDF",
            ruta_default,
            "PDF (*.pdf);;Todos los archivos (*)",
        )
        if not ruta:
            return

        try:
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            with open(ruta, "wb") as f:
                f.write(self._pdf_bytes)
            self._ruta_guardado = ruta
            self.lbl_estado.setText(f"✅ Guardado en: {ruta}")
            logger.info(f"Reporte guardado: {ruta}")
        except Exception as e:
            show_error(self, "No se pudo guardar el PDF.", e)

    def _abrir_pdf(self):
        ruta = self._ruta_guardado

        # Si no se ha guardado aún, guardar en temp y abrir
        if not ruta and self._pdf_bytes:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False, prefix="isalab_"
            )
            tmp.write(self._pdf_bytes)
            tmp.close()
            ruta = tmp.name
            self._ruta_guardado = ruta

        if not ruta or not os.path.exists(ruta):
            show_warning(self, "Sin PDF", "No hay PDF para abrir.")
            return

        try:
            if not open_file_externally(ruta):
                show_warning(self, "Aviso",
                    "No se pudo abrir el PDF. Verifique que tenga "
                    "una aplicación predeterminada para archivos PDF.")
            else:
                logger.info(f"PDF abierto: {ruta}")
        except Exception as e:
            show_error(self, "No se pudo abrir el PDF.", e)

    # ── Cleanup al cerrar ────────────────────────────────────────────────

    def closeEvent(self, event):
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        event.accept()
