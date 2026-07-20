# gui_pyside/dialogs/historia_dialog.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QComboBox, QTextEdit, QPushButton,
                               QFrame, QMessageBox, QFormLayout, QScrollArea,
                               QGroupBox, QDoubleSpinBox, QSpinBox, QTabWidget)
from PySide6.QtCore import QDate

from gui_pyside.dialogs.base_dialog import BaseDialog
from gui_pyside.styles import IsaStyles, style_input, style_button, style_group
from gui_pyside.components.components import ErrorHandler
from gui_pyside.utils.messages import show_error, show_warning
from services.historia_service import HistoriaService
from services.recepcion_service import RecepcionService
from config import ICONS
from services.pdf_service import PDFService

PRONOSTICOS = ['Bueno', 'Reservado', 'Grave', 'Pendiente']


# =============================================================================
# NUEVA HISTORIA CLÍNICA (3 Pestañas Avanzadas)
# =============================================================================
class NuevaHistoriaDialog(BaseDialog):
    def __init__(self, parent=None, on_save=None, recepcion_id=None):
        width, height = 950, 750
        super().__init__(
            parent, f"{
                ICONS['add']} Nueva Historia Clínica", width, height)
        self.on_save = on_save
        self.recepcion_id = recepcion_id
        self.service = HistoriaService()
        self.rec_svc = RecepcionService()
        self._build()

    def _build(self):
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {IsaStyles.BORDER}; border-radius: 8px; background-color: white; padding: 10px; }}
            QTabBar::tab {{ background-color: {IsaStyles.LIGHT_BG}; border: 1px solid {IsaStyles.BORDER}; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; padding: 10px 20px; margin-right: 4px; font-weight: bold; color: {IsaStyles.GRAY}; }}
            QTabBar::tab:selected {{ background-color: {IsaStyles.PRIMARY}; color: white; }}
        """)

        self._build_tab1_constantes()
        self._build_tab2_anamnesis()
        self._build_tab3_diagnostico()

        self.content_layout.addWidget(self.tabs)

        self.btn_guardar.setText(f"{ICONS['save']} Guardar Historia")
        style_button(self.btn_guardar, 'primary')
        self.btn_cancelar.setText(f"{ICONS['cancel']} Cancelar")
        style_button(self.btn_cancelar, 'ghost')

        self.set_save_callback(self._guardar)

    def _build_tab1_constantes(self):
        tab1 = QWidget()
        layout = QVBoxLayout(tab1)
        layout.setSpacing(16)

        # Recepción y Profesional
        top_layout = QHBoxLayout()

        rec_group = QGroupBox("Recepción y Profesional")
        style_group(rec_group, IsaStyles.PRIMARY)
        rec_layout = QFormLayout(rec_group)

        recepciones = self.rec_svc.listar_recepciones(
            {'estado': 'En consulta'}) or self.rec_svc.listar_recepciones({})
        rec_list = [
            f"{r.id} | {r.codigo} — {r.animal_nombre}" for r in recepciones]
        self.recepcion_combo = QComboBox()
        self.recepcion_combo.addItems(rec_list)
        style_input(self.recepcion_combo)
        rec_layout.addRow("Recepción *:", self.recepcion_combo)

        if self.recepcion_id:
            for i, texto in enumerate(rec_list):
                if texto.startswith(f"{self.recepcion_id} |"):
                    self.recepcion_combo.setCurrentIndex(i)
                    break

        self.veterinario = QLineEdit()
        style_input(self.veterinario)
        rec_layout.addRow("Veterinario:", self.veterinario)

        self.pronostico = QComboBox()
        self.pronostico.addItems(PRONOSTICOS)
        style_input(self.pronostico)
        rec_layout.addRow("Pronóstico:", self.pronostico)

        top_layout.addWidget(rec_group, 1)
        layout.addLayout(top_layout)

        # Constantes Fisiológicas Avanzadas
        signos_group = QGroupBox("Constantes Fisiológicas")
        style_group(signos_group, IsaStyles.ACCENT)
        signos_layout = QHBoxLayout(signos_group)

        col1 = QFormLayout()
        self.temperatura = QDoubleSpinBox()
        self.temperatura.setRange(0, 45)
        self.temperatura.setSuffix(" °C")
        style_input(self.temperatura)
        self.peso = QDoubleSpinBox()
        self.peso.setRange(0, 300)
        self.peso.setSuffix(" kg")
        style_input(self.peso)
        self.fc = QSpinBox()
        self.fc.setRange(0, 300)
        self.fc.setSuffix(" lpm")
        style_input(self.fc)
        self.fr = QSpinBox()
        self.fr.setRange(0, 150)
        self.fr.setSuffix(" rpm")
        style_input(self.fr)

        col1.addRow("Temp:", self.temperatura)
        col1.addRow("Peso:", self.peso)
        col1.addRow("FC:", self.fc)
        col1.addRow("FR:", self.fr)

        col2 = QFormLayout()
        self.tllc = QComboBox()
        self.tllc.addItems(["", "< 2s", "2s", "> 2s"])
        style_input(self.tllc)
        self.trpc = QComboBox()
        self.trpc.addItems(["", "< 2s", "2s", "> 2s"])
        style_input(self.trpc)
        self.mucosas = QComboBox()
        self.mucosas.addItems(
            ["", "Rosadas", "Pálidas", "Cianóticas", "Ictéricas", "Hiperémicas"])
        style_input(self.mucosas)
        self.cond_corp = QComboBox()
        self.cond_corp.addItems(["", "1/5", "2/5", "3/5", "4/5", "5/5"])
        style_input(self.cond_corp)

        col2.addRow("TLLC:", self.tllc)
        col2.addRow("TRPC:", self.trpc)
        col2.addRow("Mucosas:", self.mucosas)
        col2.addRow("C. Corporal:", self.cond_corp)

        col3 = QFormLayout()
        self.pulso = QComboBox()
        self.pulso.addItems(["", "Fuerte", "Débil", "Saltón", "Irregular"])
        style_input(self.pulso)
        self.deshidratacion = QComboBox()
        self.deshidratacion.addItems(["", "0-5%", "6-8%", "9-11%", "12-15%"])
        style_input(self.deshidratacion)

        col3.addRow("Pulso:", self.pulso)
        col3.addRow("% Deshid.:", self.deshidratacion)

        signos_layout.addLayout(col1)
        signos_layout.addLayout(col2)
        signos_layout.addLayout(col3)
        layout.addWidget(signos_group)
        layout.addStretch()

        self.tabs.addTab(tab1, "🩺 Consulta y Constantes")

    def _build_tab2_anamnesis(self):
        tab2 = QWidget()
        layout = QVBoxLayout(tab2)

        # Datos Previos
        prev_group = QGroupBox("Antecedentes y Preventiva")
        style_group(prev_group, IsaStyles.SECONDARY)
        prev_layout = QFormLayout(prev_group)

        row1 = QHBoxLayout()
        self.dieta = QLineEdit()
        self.dieta.setPlaceholderText("Ej: Croquetas, BARF...")
        style_input(self.dieta)
        self.esterilizado = QComboBox()
        self.esterilizado.addItems(["", "Sí", "No"])
        style_input(self.esterilizado)
        self.n_partos = QSpinBox()
        style_input(self.n_partos)

        row1.addWidget(QLabel("Dieta:"))
        row1.addWidget(self.dieta, 2)
        row1.addWidget(QLabel("Esterilizado:"))
        row1.addWidget(self.esterilizado, 1)
        row1.addWidget(QLabel("N° Partos:"))
        row1.addWidget(self.n_partos, 1)
        prev_layout.addRow(row1)

        row2 = QHBoxLayout()
        self.vacunas = QLineEdit()
        self.vacunas.setPlaceholderText("Esquema vacunal actual")
        style_input(self.vacunas)
        self.desparasitacion = QLineEdit()
        self.desparasitacion.setPlaceholderText(
            "Última desparasitación (Fecha/Producto)")
        style_input(self.desparasitacion)
        row2.addWidget(QLabel("Vacunas:"))
        row2.addWidget(self.vacunas, 1)
        row2.addWidget(QLabel("Desparasitación:"))
        row2.addWidget(self.desparasitacion, 1)
        prev_layout.addRow(row2)

        row3 = QHBoxLayout()
        self.viajes = QLineEdit()
        self.viajes.setPlaceholderText("¿Viajes recientes?")
        style_input(self.viajes)
        self.convive = QLineEdit()
        self.convive.setPlaceholderText("¿Convive con otros animales?")
        style_input(self.convive)
        self.comportamiento = QLineEdit()
        self.comportamiento.setPlaceholderText("Ej: Alerta, decaído...")
        style_input(self.comportamiento)
        row3.addWidget(QLabel("Viajes:"))
        row3.addWidget(self.viajes)
        row3.addWidget(QLabel("Convive con:"))
        row3.addWidget(self.convive)
        row3.addWidget(QLabel("Comportamiento:"))
        row3.addWidget(self.comportamiento)
        prev_layout.addRow(row3)

        self.enf_previas = QLineEdit()
        style_input(self.enf_previas)
        self.cirugias = QLineEdit()
        style_input(self.cirugias)
        self.trat_recientes = QLineEdit()
        style_input(self.trat_recientes)
        prev_layout.addRow("Enf. Previas:", self.enf_previas)
        prev_layout.addRow("Cirugías:", self.cirugias)
        prev_layout.addRow("Trat. Recientes:", self.trat_recientes)

        layout.addWidget(prev_group)

        # Anamnesis General
        anam_group = QGroupBox(
            "Motivo de Consulta y Relato del Propietario (Anamnesis)")
        style_group(anam_group, IsaStyles.WARNING)
        anam_layout = QVBoxLayout(anam_group)
        self.anamnesis = QTextEdit()
        self.anamnesis.setStyleSheet(IsaStyles.get_textarea_style())
        anam_layout.addWidget(self.anamnesis)
        layout.addWidget(anam_group, 1)

        self.tabs.addTab(tab2, "📋 Anamnesis Completa")

    def _build_tab3_diagnostico(self):
        tab3 = QWidget()
        layout = QVBoxLayout(tab3)

        exam_group = QGroupBox("Exploración por Sistemas (Examen Físico)")
        style_group(exam_group, IsaStyles.GRAY)
        exam_layout = QVBoxLayout(exam_group)
        self.examen = QTextEdit()
        self.examen.setStyleSheet(IsaStyles.get_textarea_style())
        exam_layout.addWidget(self.examen)
        layout.addWidget(exam_group, 1)

        diag_row = QHBoxLayout()
        diag1_group = QGroupBox("Diagnóstico Principal")
        style_group(diag1_group, IsaStyles.PRIMARY)
        diag1_layout = QVBoxLayout(diag1_group)
        self.diagnostico = QTextEdit()
        self.diagnostico.setStyleSheet(IsaStyles.get_textarea_style())
        diag1_layout.addWidget(self.diagnostico)
        diag_row.addWidget(diag1_group, 1)

        diag2_group = QGroupBox("Diagnóstico Diferencial")
        style_group(diag2_group, IsaStyles.WARNING)
        diag2_layout = QVBoxLayout(diag2_group)
        self.diagnostico_diff = QTextEdit()
        self.diagnostico_diff.setStyleSheet(IsaStyles.get_textarea_style())
        diag2_layout.addWidget(self.diagnostico_diff)
        diag_row.addWidget(diag2_group, 1)

        layout.addLayout(diag_row, 1)

        trat_group = QGroupBox("Plan de Tratamiento / Recomendaciones")
        style_group(trat_group, IsaStyles.ACCENT)
        trat_layout = QVBoxLayout(trat_group)
        self.tratamiento = QTextEdit()
        self.tratamiento.setStyleSheet(IsaStyles.get_textarea_style())
        trat_layout.addWidget(self.tratamiento)
        layout.addWidget(trat_group, 1)

        self.tabs.addTab(tab3, "📝 Examen y Diagnóstico")

    def _get_text(self, widget):
        text = widget.toPlainText().strip() if isinstance(
            widget, QTextEdit) else widget.text().strip()
        return text if text else None

    @ErrorHandler.handle_exception
    def _guardar(self):
        rec_texto = self.recepcion_combo.currentText()
        if not rec_texto or '|' not in rec_texto:
            show_warning(self, "Error", "Seleccione una recepción válida")
            return

        try:
            rec_id = int(rec_texto.split('|')[0].strip())
            rec = self.rec_svc.obtener_recepcion(rec_id)
        except Exception as e:
            show_error(self, "Recepción inválida.", e)
            return

        data = {
            'recepcion_id': rec_id,
            'animal_id': rec.animal_id,
            'fecha': QDate.currentDate().toString("yyyy-MM-dd"),

            # Textos largos
            'anamnesis': self._get_text(self.anamnesis),
            'examen_fisico': self._get_text(self.examen),
            'diagnostico': self._get_text(self.diagnostico),
            'diagnostico_diferencial': self._get_text(self.diagnostico_diff),
            'tratamiento': self._get_text(self.tratamiento),
            'pronostico': self.pronostico.currentText(),
            'veterinario': self._get_text(self.veterinario),

            # Constantes
            'temperatura': self.temperatura.value() if self.temperatura.value() > 0 else None,
            'peso_consulta': self.peso.value() if self.peso.value() > 0 else None,
            'frecuencia_cardiaca': self.fc.value() if self.fc.value() > 0 else None,
            'frecuencia_respiratoria': self.fr.value() if self.fr.value() > 0 else None,
            'tllc': self.tllc.currentText() or None,
            'trpc': self.trpc.currentText() or None,
            'mucosas': self.mucosas.currentText() or None,
            'condicion_corporal': self.cond_corp.currentText() or None,
            'pulso': self.pulso.currentText() or None,
            'deshidratacion': self.deshidratacion.currentText() or None,

            # Anamnesis específica
            'dieta': self._get_text(self.dieta),
            'esterilizado': self.esterilizado.currentText() or None,
            'numero_partos': self.n_partos.value() if self.n_partos.value() > 0 else None,
            'esquema_vacunal': self._get_text(self.vacunas),
            'ultima_desparasitacion': self._get_text(self.desparasitacion),
            'viajes_recientes': self._get_text(self.viajes),
            'convive_con_animales': self._get_text(self.convive),
            'comportamiento': self._get_text(self.comportamiento),
            'enfermedades_previas': self._get_text(self.enf_previas),
            'cirugias_previas': self._get_text(self.cirugias),
            'tratamientos_recientes': self._get_text(self.trat_recientes)
        }

        self.service.crear_historia(data)
        QMessageBox.information(
            self, "✅ Éxito", "Historia creada correctamente")
        if self.on_save:
            self.on_save()
        self.accept()


# =============================================================================
# EDITAR HISTORIA CLÍNICA (Reutiliza la vista de pestañas)
# =============================================================================
class EditarHistoriaDialog(NuevaHistoriaDialog):
    def __init__(self, parent=None, historia_id=None, on_save=None):
        self.historia_id = historia_id
        super().__init__(parent, on_save)
        self.setWindowTitle(f"{ICONS['edit']} Editar Historia Clínica")
        self.recepcion_combo.setEnabled(False)
        self._cargar_datos()

    def _cargar_datos(self):
        h = self.service.obtener_historia(self.historia_id)

        # Cargar Constantes
        if h.temperatura:
            self.temperatura.setValue(h.temperatura)
        if h.peso_consulta:
            self.peso.setValue(h.peso_consulta)
        if h.frecuencia_cardiaca:
            self.fc.setValue(h.frecuencia_cardiaca)
        if h.frecuencia_respiratoria:
            self.fr.setValue(h.frecuencia_respiratoria)
        if h.veterinario:
            self.veterinario.setText(h.veterinario)
        if h.pronostico:
            self.pronostico.setCurrentText(h.pronostico)

        if hasattr(h, 'tllc') and h.tllc:
            self.tllc.setCurrentText(h.tllc)
        if hasattr(h, 'trpc') and h.trpc:
            self.trpc.setCurrentText(h.trpc)
        if hasattr(h, 'mucosas') and h.mucosas:
            self.mucosas.setCurrentText(h.mucosas)
        if hasattr(h, 'condicion_corporal') and h.condicion_corporal:
            self.cond_corp.setCurrentText(
                h.condicion_corporal)
        if hasattr(h, 'pulso') and h.pulso:
            self.pulso.setCurrentText(h.pulso)
        if hasattr(h, 'deshidratacion') and h.deshidratacion:
            self.deshidratacion.setCurrentText(h.deshidratacion)

        # Cargar Anamnesis Especializada
        if hasattr(h, 'dieta') and h.dieta:
            self.dieta.setText(h.dieta)
        if hasattr(h, 'esterilizado') and h.esterilizado:
            self.esterilizado.setCurrentText(h.esterilizado)
        if hasattr(h, 'numero_partos') and h.numero_partos:
            self.n_partos.setValue(h.numero_partos)
        if hasattr(h, 'esquema_vacunal') and h.esquema_vacunal:
            self.vacunas.setText(h.esquema_vacunal)
        if hasattr(h, 'ultima_desparasitacion') and h.ultima_desparasitacion:
            self.desparasitacion.setText(
                h.ultima_desparasitacion)
        if hasattr(h, 'viajes_recientes') and h.viajes_recientes:
            self.viajes.setText(h.viajes_recientes)
        if hasattr(h, 'convive_con_animales') and h.convive_con_animales:
            self.convive.setText(h.convive_con_animales)
        if hasattr(h, 'comportamiento') and h.comportamiento:
            self.comportamiento.setText(h.comportamiento)
        if hasattr(h, 'enfermedades_previas') and h.enfermedades_previas:
            self.enf_previas.setText(
                h.enfermedades_previas)
        if hasattr(h, 'cirugias_previas') and h.cirugias_previas:
            self.cirugias.setText(h.cirugias_previas)
        if hasattr(h, 'tratamientos_recientes') and h.tratamientos_recientes:
            self.trat_recientes.setText(
                h.tratamientos_recientes)

        # Cargar Textos Largos
        if h.anamnesis:
            self.anamnesis.setPlainText(h.anamnesis)
        if h.examen_fisico:
            self.examen.setPlainText(h.examen_fisico)
        if h.diagnostico:
            self.diagnostico.setPlainText(h.diagnostico)
        if h.diagnostico_diferencial:
            self.diagnostico_diff.setPlainText(h.diagnostico_diferencial)
        if h.tratamiento:
            self.tratamiento.setPlainText(h.tratamiento)

    @ErrorHandler.handle_exception
    def _guardar(self):
        data = {
            'anamnesis': self._get_text(self.anamnesis),
            'examen_fisico': self._get_text(self.examen),
            'diagnostico': self._get_text(self.diagnostico),
            'diagnostico_diferencial': self._get_text(self.diagnostico_diff),
            'tratamiento': self._get_text(self.tratamiento),
            'pronostico': self.pronostico.currentText(),
            'veterinario': self._get_text(self.veterinario),

            'temperatura': self.temperatura.value() if self.temperatura.value() > 0 else None,
            'peso_consulta': self.peso.value() if self.peso.value() > 0 else None,
            'frecuencia_cardiaca': self.fc.value() if self.fc.value() > 0 else None,
            'frecuencia_respiratoria': self.fr.value() if self.fr.value() > 0 else None,
            'tllc': self.tllc.currentText() or None,
            'trpc': self.trpc.currentText() or None,
            'mucosas': self.mucosas.currentText() or None,
            'condicion_corporal': self.cond_corp.currentText() or None,
            'pulso': self.pulso.currentText() or None,
            'deshidratacion': self.deshidratacion.currentText() or None,

            'dieta': self._get_text(self.dieta),
            'esterilizado': self.esterilizado.currentText() or None,
            'numero_partos': self.n_partos.value() if self.n_partos.value() > 0 else None,
            'esquema_vacunal': self._get_text(self.vacunas),
            'ultima_desparasitacion': self._get_text(self.desparasitacion),
            'viajes_recientes': self._get_text(self.viajes),
            'convive_con_animales': self._get_text(self.convive),
            'comportamiento': self._get_text(self.comportamiento),
            'enfermedades_previas': self._get_text(self.enf_previas),
            'cirugias_previas': self._get_text(self.cirugias),
            'tratamientos_recientes': self._get_text(self.trat_recientes)
        }
        self.service.actualizar_historia(self.historia_id, data)
        QMessageBox.information(self, "✅ Éxito", "Historia actualizada")
        if self.on_save:
            self.on_save()
        self.accept()


# =============================================================================
# DETALLE DE HISTORIA CLÍNICA (con impresión PDF)
# =============================================================================
class DetalleHistoriaDialog(BaseDialog):
    def __init__(self, parent=None, historia_id=None):
        width, height = 900, 700
        super().__init__(
            parent, f"{
                ICONS['view']} Detalle Historia Clínica", width, height)
        self.service = HistoriaService()
        self.pdf_service = PDFService()

        # Manejar errores de base de datos
        try:
            self.historia = self.service.obtener_historia(historia_id)
        except Exception as e:
            show_error(self, "No se pudo cargar la historia clínica.", e)
            self.historia = None
            self.reject()
            return

        self._build()
        self._setup_print_button()

    def _setup_print_button(self):
        from PySide6.QtCore import Qt
        self.btn_print = QPushButton(f"{ICONS['print']} Imprimir PDF")
        style_button(self.btn_print, 'primary')
        self.btn_print.setCursor(Qt.PointingHandCursor)
        self.btn_print.clicked.connect(self._imprimir_pdf)

        footer_layout = self.footer.layout()
        stretch = footer_layout.takeAt(footer_layout.count() - 1)
        footer_layout.insertWidget(footer_layout.count(), self.btn_print)
        footer_layout.addItem(stretch)

    @ErrorHandler.handle_exception
    def _imprimir_pdf(self):
        self.btn_print.setText("Generando Historia Pro... ⏳")
        self.btn_print.setEnabled(False)

        # Usar el diálogo reutilizable de reportes
        from gui_pyside.dialogs.dialogo_generar_reporte import DialogoGenerarReporte

        dlg = DialogoGenerarReporte(self)
        dlg.generar_historia_clinica(
            historia_id=self.historia.id,
            incluir_consultas=True,
            incluir_vacunas=True)

        # Reconectar para restaurar el botón cuando termine
        # El diálogo se encarga de todo el proceso
        dlg.exec()

        self.btn_print.setText("🖨️ Imprimir Historia Pro")
        self.btn_print.setEnabled(True)

    def _build(self):
        def crear_fila(label, valor):
            if not valor:
                return None
            w = QWidget()
            lay = QHBoxLayout(w)
            lay.setContentsMargins(0, 2, 0, 2)
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet(
                f"color: {
                    IsaStyles.GRAY}; font-size: 11px; min-width: 130px;")
            val = QLabel(str(valor))
            val.setStyleSheet(f"color: {IsaStyles.DARK}; font-size: 12px;")
            val.setWordWrap(True)
            lay.addWidget(lbl)
            lay.addWidget(val)
            lay.addStretch()
            return w

        header = QLabel(
            f"{ICONS['info']} Historia #{self.historia.id} - {self.historia.animal_nombre}")
        header.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {IsaStyles.PRIMARY}; margin-bottom: 5px;")
        self.content_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        scroll.setWidget(content)
        self.content_layout.addWidget(scroll)
        layout = QVBoxLayout(content)
        layout.setSpacing(12)

        # Agrupar Signos y Anamnesis arriba
        top_row = QHBoxLayout()

        signos = QGroupBox("Constantes")
        style_group(signos, IsaStyles.ACCENT)
        signos_layout = QVBoxLayout(signos)
        for lbl_text, v in [("Temp", f"{self.historia.temperatura} °C" if self.historia.temperatura else None),
                            ("Peso", f"{self.historia.peso_consulta} kg" if self.historia.peso_consulta else None),
                            ("FC", f"{self.historia.frecuencia_cardiaca} lpm" if self.historia.frecuencia_cardiaca else None),
                            ("FR",
                             f"{self.historia.frecuencia_respiratoria} rpm" if self.historia.frecuencia_respiratoria else None),
                            ("TLLC", getattr(self.historia, 'tllc', None)),
                            ("Mucosas", getattr(self.historia, 'mucosas', None)),
                            ("C. Corporal", getattr(self.historia, 'condicion_corporal', None))]:
            f = crear_fila(lbl_text, v)
            if f:
                signos_layout.addWidget(f)
        top_row.addWidget(signos, 1)

        prev = QGroupBox("Antecedentes")
        style_group(prev, IsaStyles.SECONDARY)
        prev_layout = QVBoxLayout(prev)
        for lbl_text, v in [
            ("Dieta", getattr(
                self.historia, 'dieta', None)), ("Esterilizado", getattr(
                    self.historia, 'esterilizado', None)), ("Vacunas", getattr(
                self.historia, 'esquema_vacunal', None)), ("Desparasitación", getattr(
                    self.historia, 'ultima_desparasitacion', None)), ("Enf. Previas", getattr(
                        self.historia, 'enfermedades_previas', None))]:
            f = crear_fila(lbl_text, v)
            if f:
                prev_layout.addWidget(f)
        top_row.addWidget(prev, 1)

        layout.addLayout(top_row)

        secciones = [
            (getattr(
                self.historia,
                'anamnesis',
                None),
                "Anamnesis / Motivo Consulta",
                IsaStyles.WARNING),
            (getattr(
                self.historia,
                'examen_fisico',
                None),
                "Examen Físico",
                IsaStyles.GRAY),
            (getattr(
                self.historia,
                'diagnostico',
                None),
                "Diagnóstico Principal",
                IsaStyles.PRIMARY),
            (getattr(
                self.historia,
                'tratamiento',
                None),
             "Plan de Tratamiento",
             IsaStyles.ACCENT),
        ]

        for valor, titulo, color in secciones:
            if valor:
                g = QGroupBox(titulo)
                style_group(g, color)
                g_layout = QVBoxLayout(g)
                lbl = QLabel(str(valor))
                lbl.setWordWrap(True)
                g_layout.addWidget(lbl)
                layout.addWidget(g)

        self.btn_guardar.setText(f"{ICONS['success']} Cerrar")
        style_button(self.btn_guardar, 'secondary')
        self.set_save_callback(self.accept)
        self.btn_cancelar.hide()
