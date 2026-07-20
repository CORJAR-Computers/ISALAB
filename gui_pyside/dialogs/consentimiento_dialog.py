# gui_pyside/dialogs/consentimiento_dialog.py
"""Diálogo para generar consentimiento informado."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QTextEdit, QGroupBox, QFormLayout, QScrollArea)
from PySide6.QtCore import QDate

from gui_pyside.dialogs.base_dialog import BaseDialog
from gui_pyside.styles import IsaStyles, style_input, style_button, style_group
from gui_pyside.utils.messages import show_warning
from gui_pyside.components.components import ErrorHandler
from config import ICONS, DIALOG_SIZES


class ConsentimientoInformadoDialog(BaseDialog):
    """Diálogo para generar e imprimir consentimiento informado."""

    def __init__(self, parent=None, recepcion_data=None):
        width, height = DIALOG_SIZES['xlarge']
        super().__init__(
            parent, f"{
                ICONS['add']} Consentimiento Informado", width, height)
        self.recepcion_data = recepcion_data
        self._build()

    def _build(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        self.content_layout.addLayout(main_layout)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        form_widget = QWidget()
        scroll.setWidget(form_widget)
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(14)

        main_layout.addWidget(scroll)

        # Datos de la recepción (si están disponibles)
        if self.recepcion_data:
            rec_group = QGroupBox("Datos de la Atención")
            style_group(rec_group, IsaStyles.PRIMARY)
            rec_layout = QFormLayout(rec_group)

            if self.recepcion_data.get('codigo'):
                lbl_codigo = QLabel(f"<b>{self.recepcion_data['codigo']}</b>")
                rec_layout.addRow("Código:", lbl_codigo)

            if self.recepcion_data.get('animal_nombre'):
                lbl_animal = QLabel(self.recepcion_data['animal_nombre'])
                rec_layout.addRow("Paciente:", lbl_animal)

            if self.recepcion_data.get('propietario'):
                lbl_propietario = QLabel(self.recepcion_data['propietario'])
                rec_layout.addRow("Propietario:", lbl_propietario)

            form_layout.addRow(rec_group)

        # Fecha
        self.fecha_edit = QLineEdit()
        self.fecha_edit.setText(QDate.currentDate().toString("yyyy-MM-dd"))
        style_input(self.fecha_edit)
        form_layout.addRow("Fecha:", self.fecha_edit)

        # Tipo de procedimiento
        self.tipo_procedimiento = QLineEdit()
        self.tipo_procedimiento.setPlaceholderText(
            "Ej: Consulta general, Cirugía, Examen de laboratorio...")
        self.tipo_procedimiento.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        style_input(self.tipo_procedimiento)
        form_layout.addRow("Tipo de Procedimiento *:", self.tipo_procedimiento)

        # Datos del propietario
        propietario_group = QGroupBox("Datos del Propietario")
        style_group(propietario_group, IsaStyles.ACCENT)
        propietario_layout = QFormLayout(propietario_group)

        self.propietario = QLineEdit()
        self.propietario.setPlaceholderText("Nombre completo")
        self.propietario.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        if self.recepcion_data and self.recepcion_data.get('propietario'):
            self.propietario.setText(self.recepcion_data['propietario'])
        style_input(self.propietario)
        propietario_layout.addRow("Nombre *:", self.propietario)

        self.documento_propietario = QLineEdit()
        self.documento_propietario.setPlaceholderText(
            "Cédula de ciudadanía / NIT")
        self.documento_propietario.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        style_input(self.documento_propietario)
        propietario_layout.addRow("Documento *:", self.documento_propietario)

        self.telefono = QLineEdit()
        self.telefono.setPlaceholderText("Teléfono de contacto")
        self.telefono.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        if self.recepcion_data and self.recepcion_data.get('telefono'):
            self.telefono.setText(self.recepcion_data['telefono'])
        style_input(self.telefono)
        propietario_layout.addRow("Teléfono:", self.telefono)

        form_layout.addRow(propietario_group)

        # Descripción del procedimiento
        desc_group = QGroupBox("Descripción del Procedimiento")
        style_group(desc_group, IsaStyles.WARNING)
        desc_layout = QVBoxLayout(desc_group)

        self.descripcion = QTextEdit()
        self.descripcion.setPlaceholderText(
            "Describa el procedimiento a realizar:\n"
            "- Objetivos y propósito\n"
            "- Técnica a utilizar\n"
            "- Duración estimada\n"
            "- Beneficios esperados"
        )
        self.descripcion.setMaximumHeight(120)
        self.descripcion.setStyleSheet(IsaStyles.get_textarea_style())
        desc_layout.addWidget(self.descripcion)

        form_layout.addRow(desc_group)

        # Riesgos
        riesgos_group = QGroupBox("Riesgos y Complicaciones Potenciales")
        style_group(riesgos_group, IsaStyles.DANGER)
        riesgos_layout = QVBoxLayout(riesgos_group)

        self.riesgos = QTextEdit()
        self.riesgos.setPlaceholderText(
            "Describa los posibles riesgos:\n"
            "- Reacciones adversas\n"
            "- Complicaciones potenciales\n"
            "- Efectos secundarios"
        )
        self.riesgos.setMaximumHeight(100)
        self.riesgos.setStyleSheet(IsaStyles.get_textarea_style())
        riesgos_layout.addWidget(self.riesgos)

        form_layout.addRow(riesgos_group)

        # Cuidados post-procedimiento
        cuidados_group = QGroupBox("Cuidados Post-Procedimiento")
        style_group(cuidados_group, IsaStyles.ACCENT)
        cuidados_layout = QVBoxLayout(cuidados_group)

        self.cuidados_post = QTextEdit()
        self.cuidados_post.setPlaceholderText(
            "Instrucciones para el cuidado después del procedimiento:\n"
            "- Medicamentos\n"
            "- Reposo\n"
            "- Alimentación\n"
            "- Seguimiento"
        )
        self.cuidados_post.setMaximumHeight(100)
        self.cuidados_post.setStyleSheet(IsaStyles.get_textarea_style())
        cuidados_layout.addWidget(self.cuidados_post)

        form_layout.addRow(cuidados_group)

        # Veterinario
        vet_group = QGroupBox("Médico Veterinario")
        style_group(vet_group, IsaStyles.PRIMARY)
        vet_layout = QFormLayout(vet_group)

        self.veterinario = QLineEdit()
        self.veterinario.setPlaceholderText("Nombre del Dr(a). Veterinario(a)")
        self.veterinario.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        if self.recepcion_data and self.recepcion_data.get('veterinario'):
            self.veterinario.setText(self.recepcion_data['veterinario'])
        style_input(self.veterinario)
        vet_layout.addRow("Veterinario *:", self.veterinario)

        self.mp_veterinario = QLineEdit()
        self.mp_veterinario.setPlaceholderText("Matrícula profesional")
        self.mp_veterinario.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        style_input(self.mp_veterinario)
        vet_layout.addRow("T.P.:", self.mp_veterinario)

        form_layout.addRow(vet_group)

        # Botones
        self.btn_guardar.setText(f"{ICONS['print']} 🖨️ Generar Consentimiento")
        style_button(self.btn_guardar, 'primary')
        self.btn_cancelar.setText(f"{ICONS['cancel']} Cancelar")
        style_button(self.btn_cancelar, 'ghost')

        self.set_save_callback(self._generar_consentimiento)

    @ErrorHandler.handle_exception
    def _generar_consentimiento(self):
        """Genera e imprime el consentimiento informado."""
        # Validar campos mínimos
        if not self.tipo_procedimiento.text().strip():
            show_warning(
                self,
                "Campo requerido",
                "Debe ingresar el tipo de procedimiento")
            return

        if not self.propietario.text().strip():
            show_warning(
                self,
                "Campo requerido",
                "Debe ingresar el nombre del propietario")
            return

        if not self.documento_propietario.text().strip():
            show_warning(
                self,
                "Campo requerido",
                "Debe ingresar el documento del propietario")
            return

        if not self.descripcion.toPlainText().strip():
            show_warning(
                self,
                "Campo requerido",
                "Debe describir el procedimiento")
            return

        if not self.veterinario.text().strip():
            show_warning(
                self,
                "Campo requerido",
                "Debe ingresar el nombre del veterinario")
            return

        # Recopilar datos
        consentimiento_data = {
            'fecha': self.fecha_edit.text().strip(),
            'codigo_recepcion': self.recepcion_data.get(
                'codigo',
                '') if self.recepcion_data else '',
            'tipo_procedimiento': self.tipo_procedimiento.text().strip(),
            'animal_nombre': self.recepcion_data.get(
                'animal_nombre',
                'N/A') if self.recepcion_data else 'N/A',
            'animal_codigo': self.recepcion_data.get(
                'animal_codigo',
                '') if self.recepcion_data else '',
            'especie': self.recepcion_data.get(
                'especie',
                'N/A') if self.recepcion_data else 'N/A',
            'raza': self.recepcion_data.get(
                'raza',
                '') if self.recepcion_data else '',
            'propietario': self.propietario.text().strip(),
            'documento_propietario': self.documento_propietario.text().strip(),
            'telefono': self.telefono.text().strip(),
            'descripcion_procedimiento': self.descripcion.toPlainText().strip(),
            'riesgos': self.riesgos.toPlainText().strip(),
            'cuidados_post': self.cuidados_post.toPlainText().strip(),
            'veterinario': self.veterinario.text().strip(),
            'mp_veterinario': self.mp_veterinario.text().strip(),
        }

        # Generar PDF
        from gui_pyside.dialogs.dialogo_generar_reporte import DialogoGenerarReporte

        self.btn_guardar.setText("Generando PDF... ⏳")
        self.btn_guardar.setEnabled(False)

        try:
            dlg = DialogoGenerarReporte(self)
            dlg.generar_consentimiento(consentimiento_data)
            dlg.exec()
        finally:
            self.btn_guardar.setText(
                f"{ICONS['print']} 🖨️ Generar Consentimiento")
            self.btn_guardar.setEnabled(True)
