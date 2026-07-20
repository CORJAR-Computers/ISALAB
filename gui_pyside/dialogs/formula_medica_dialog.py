# gui_pyside/dialogs/formula_medica_dialog.py
"""Diálogo para fórmula médica con impresión PDF."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QTextEdit, QGroupBox, QFormLayout,
                               QDateEdit, QScrollArea)
from PySide6.QtCore import QDate

from gui_pyside.dialogs.base_dialog import BaseDialog
from gui_pyside.styles import IsaStyles, style_input, style_button, style_group
from gui_pyside.utils.messages import show_warning
from gui_pyside.components.components import ErrorHandler
from config import ICONS, DIALOG_SIZES


class FormulaMedicaDialog(BaseDialog):
    """Diálogo para crear e imprimir fórmula médica."""

    def __init__(self, parent=None, consulta_id=None, animal_data=None):
        width, height = DIALOG_SIZES['large']
        super().__init__(
            parent, f"{
                ICONS['add']} Fórmula Médica", width, height)
        self.consulta_id = consulta_id
        self.animal_data = animal_data
        self._build()

    def _build(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        self.content_layout.addLayout(main_layout)

        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        form_widget = QWidget()
        scroll.setWidget(form_widget)
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(14)

        main_layout.addWidget(scroll)

        # Fecha
        self.fecha = QDateEdit(QDate.currentDate())
        self.fecha.setCalendarPopup(True)
        style_input(self.fecha)
        form_layout.addRow("Fecha:", self.fecha)

        # Datos del paciente
        if self.animal_data:
            paciente_info = QLabel(
                f"<b>Paciente:</b> {self.animal_data.get('nombre', 'N/A')}<br>"
                f"<b>Propietario:</b> {self.animal_data.get('propietario', 'N/A')}"
            )
            paciente_info.setStyleSheet(f"""
                color: {IsaStyles.SECONDARY};
                padding: 10px;
                background-color: {IsaStyles.LIGHT_BG};
                border-radius: 6px;
                border-left: 4px solid {IsaStyles.ACCENT};
            """)
            form_layout.addRow("Paciente:", paciente_info)

        # Diagnóstico
        self.diagnostico = QTextEdit()
        self.diagnostico.setPlaceholderText("Diagnóstico clínico...")
        self.diagnostico.setMaximumHeight(60)
        self.diagnostico.setStyleSheet(IsaStyles.get_textarea_style())
        form_layout.addRow("Diagnóstico:", self.diagnostico)

        # Fórmula médica (medicamentos)
        formula_group = QGroupBox("Medicamentos y Dosis")
        style_group(formula_group, IsaStyles.PRIMARY)
        formula_layout = QVBoxLayout(formula_group)

        self.medicamentos = QTextEdit()
        self.medicamentos.setPlaceholderText(
            "Ej:\n"
            "1. Amoxicilina 250mg - 1 tableta cada 8 horas por 7 días\n"
            "2. Meloxicam 7.5mg - 1 tableta cada 24 horas por 5 días\n"
            "3. Suero fisiológico - Lavado de herida 2 veces al día"
        )
        self.medicamentos.setMaximumHeight(150)
        self.medicamentos.setStyleSheet(IsaStyles.get_textarea_style())
        formula_layout.addWidget(self.medicamentos)

        form_layout.addRow(formula_group)

        # Indicaciones especiales
        indicaciones_group = QGroupBox("Indicaciones y Recomendaciones")
        style_group(indicaciones_group, IsaStyles.ACCENT)
        indicaciones_layout = QVBoxLayout(indicaciones_group)

        self.indicaciones = QTextEdit()
        self.indicaciones.setPlaceholderText(
            "Ej:\n"
            "- Reposo absoluto por 48 horas\n"
            "- No bañar durante el tratamiento\n"
            "- Control en 7 días\n"
            "- Dieta blanda"
        )
        self.indicaciones.setMaximumHeight(120)
        self.indicaciones.setStyleSheet(IsaStyles.get_textarea_style())
        indicaciones_layout.addWidget(self.indicaciones)

        form_layout.addRow(indicaciones_group)

        # Veterinario
        self.veterinario = QLineEdit()
        self.veterinario.setPlaceholderText("Nombre del Dr(a). Veterinario(a)")
        self.veterinario.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        style_input(self.veterinario)
        form_layout.addRow("Veterinario(a):", self.veterinario)

        # Botones
        self.btn_guardar.setText(f"{ICONS['print']} 🖨️ Imprimir Fórmula")
        style_button(self.btn_guardar, 'primary')
        self.btn_cancelar.setText(f"{ICONS['cancel']} Cancelar")
        style_button(self.btn_cancelar, 'ghost')

        self.set_save_callback(self._imprimir_formula)

    @ErrorHandler.handle_exception
    def _imprimir_formula(self):
        """Genera e imprime la fórmula médica."""
        # Validar campos mínimos
        if not self.medicamentos.toPlainText().strip():
            show_warning(
                self,
                "Campo requerido",
                "Debe ingresar los medicamentos")
            return

        if not self.veterinario.text().strip():
            show_warning(
                self,
                "Campo requerido",
                "Debe ingresar el nombre del veterinario")
            return

        # Recopilar datos
        formula_data = {
            'fecha': self.fecha.date().toString("yyyy-MM-dd"),
            'animal_nombre': self.animal_data.get(
                'nombre',
                'N/A') if self.animal_data else 'N/A',
            'propietario': self.animal_data.get(
                'propietario',
                'N/A') if self.animal_data else 'N/A',
            'especie': self.animal_data.get(
                'especie',
                'N/A') if self.animal_data else 'N/A',
            'diagnostico': self.diagnostico.toPlainText().strip(),
            'medicamentos': self.medicamentos.toPlainText().strip(),
            'indicaciones': self.indicaciones.toPlainText().strip(),
            'veterinario': self.veterinario.text().strip(),
        }

        # Generar PDF
        from gui_pyside.dialogs.dialogo_generar_reporte import DialogoGenerarReporte

        self.btn_guardar.setText("Generando PDF... ⏳")
        self.btn_guardar.setEnabled(False)

        try:
            dlg = DialogoGenerarReporte(self)
            dlg.generar_formula_medica(formula_data)
            dlg.exec()
        finally:
            self.btn_guardar.setText(f"{ICONS['print']} 🖨️ Imprimir Fórmula")
            self.btn_guardar.setEnabled(True)
