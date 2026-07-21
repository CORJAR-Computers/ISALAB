# gui_pyside/dialogs/consulta_dialog.py
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QComboBox, QTextEdit, QPushButton, QMessageBox,
                               QFormLayout, QGroupBox)

from gui_pyside.dialogs.base_dialog import BaseDialog
from gui_pyside.styles import IsaStyles, style_input, style_button, style_group
from gui_pyside.components.components import ErrorHandler
from gui_pyside.utils.messages import show_error, show_warning
from services.consulta_service import ConsultaService
from services.animal_service import AnimalService
from services.recepcion_service import RecepcionService
from config import MOTIVOS_CONSULTA, ICONS, DIALOG_SIZES
from utils.logger import setup_logger

logger = setup_logger()


class NuevaConsultaDialog(BaseDialog):
    def __init__(self, parent=None, on_save=None):
        width, height = DIALOG_SIZES['large']
        super().__init__(
            parent, f"{
                ICONS['add']} Nueva Consulta", width, height)
        self.on_save = on_save
        self.service = ConsultaService()
        self.animal_service = AnimalService()
        self._build()

    def _build(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        self.content_layout.addLayout(main_layout)

        # --- CARD IZQUIERDA ---
        left_card = QGroupBox("Evaluación Clínica")
        style_group(left_card, IsaStyles.ACCENT)
        left_layout = QFormLayout(left_card)
        left_layout.setSpacing(14)

        self.animal_combo = QComboBox()
        self.animal_combo.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        self._cargar_animales()
        style_input(self.animal_combo)
        left_layout.addRow("Paciente *:", self.animal_combo)

        self.motivo_combo = QComboBox()
        self.motivo_combo.addItems(MOTIVOS_CONSULTA)
        self.motivo_combo.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        style_input(self.motivo_combo)
        left_layout.addRow("Motivo *:", self.motivo_combo)

        self.evolucion = QTextEdit()
        self.evolucion.setPlaceholderText(
            "Estado actual, síntomas reportados...")
        self.evolucion.setMaximumHeight(100)
        self.evolucion.setStyleSheet(IsaStyles.get_textarea_style())
        left_layout.addRow("Evolución:", self.evolucion)

        self.examen_fisico = QTextEdit()
        self.examen_fisico.setPlaceholderText(
            "Hallazgos al revisar al paciente...")
        self.examen_fisico.setMaximumHeight(100)
        self.examen_fisico.setStyleSheet(IsaStyles.get_textarea_style())
        left_layout.addRow("Examen Físico:", self.examen_fisico)

        # --- CARD DERECHA ---
        right_card = QGroupBox("Plan Médico")
        style_group(right_card, IsaStyles.PRIMARY)
        right_layout = QFormLayout(right_card)
        right_layout.setSpacing(14)

        self.tratamiento = QTextEdit()
        self.tratamiento.setPlaceholderText("Procedimientos a realizar...")
        self.tratamiento.setMaximumHeight(80)
        self.tratamiento.setStyleSheet(IsaStyles.get_textarea_style())
        right_layout.addRow("Tratamiento:", self.tratamiento)

        self.medicamentos = QTextEdit()
        self.medicamentos.setPlaceholderText("Fórmulas, dosis, frecuencia...")
        self.medicamentos.setMaximumHeight(80)
        self.medicamentos.setStyleSheet(IsaStyles.get_textarea_style())
        right_layout.addRow("Medicamentos:", self.medicamentos)

        self.proxima_consulta = QLineEdit()
        self.proxima_consulta.setPlaceholderText("Ej: En 15 días o 2026-05-10")
        style_input(self.proxima_consulta)
        right_layout.addRow("Próxima Cita:", self.proxima_consulta)

        self.veterinario = QLineEdit()
        self.veterinario.setPlaceholderText("Nombre del Dr(a).")
        style_input(self.veterinario)
        right_layout.addRow("Veterinario:", self.veterinario)

        self.observaciones = QTextEdit()
        self.observaciones.setPlaceholderText("Notas internas...")
        self.observaciones.setMaximumHeight(60)
        self.observaciones.setStyleSheet(IsaStyles.get_textarea_style())
        right_layout.addRow("Notas:", self.observaciones)

        main_layout.addWidget(left_card, 1)
        main_layout.addWidget(right_card, 1)

        # Botones
        self.btn_guardar.setText(f"{ICONS['save']} Guardar Consulta")
        style_button(self.btn_guardar, 'primary')
        self.btn_cancelar.setText(f"{ICONS['cancel']} Cancelar")
        style_button(self.btn_cancelar, 'ghost')

        self.set_save_callback(self._guardar)

    def _cargar_animales(self):
        self.animal_combo.clear()
        try:
            animales = self.animal_service.listar_animales(
                {'estado': 'Activo'})
            for a in animales:
                self.animal_combo.addItem(f"{a.nombre} ({a.codigo})", a.id)
        except Exception as e:
            logger.warning(
                f"No se pudieron cargar pacientes para consulta: {e}")

    @ErrorHandler.handle_exception
    def _guardar(self):
        animal_id = self.animal_combo.currentData()
        if not animal_id:
            show_warning(self,
                         f"{ICONS['warning']} Error",
                         "Debe seleccionar un paciente")
            return

        data = {
            'animal_id': animal_id,
            'motivo': self.motivo_combo.currentText(),
            'evolucion': self.evolucion.toPlainText().strip(),
            'examen_fisico': self.examen_fisico.toPlainText().strip(),
            'tratamiento': self.tratamiento.toPlainText().strip(),
            'medicamentos': self.medicamentos.toPlainText().strip(),
            'proxima_consulta': self.proxima_consulta.text().strip(),
            'veterinario': self.veterinario.text().strip(),
            'observaciones': self.observaciones.toPlainText().strip()
        }

        self.service.registrar_consulta(data)
        QMessageBox.information(self,
                                f"{ICONS['success']} Éxito",
                                "Consulta registrada correctamente")

        if self.on_save:
            self.on_save()
        self.accept()


class EditarConsultaDialog(NuevaConsultaDialog):
    def __init__(self, parent=None, consulta_id=None, on_save=None):
        self.consulta_id = consulta_id
        super().__init__(parent, on_save)
        self.setWindowTitle(f"{ICONS['edit']} Editar Consulta")
        self.animal_combo.setEnabled(False)
        self.animal_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {IsaStyles.LIGHT_BG};
                color: {IsaStyles.GRAY};
                border: 2px solid {IsaStyles.BORDER};
                min-height: {IsaStyles.INPUT_HEIGHT}px;
            }}
        """)
        self._cargar_datos()

    def _cargar_datos(self):
        try:
            consulta = self.service.obtener_consulta(self.consulta_id)
            idx = self.animal_combo.findData(consulta.animal_id)
            if idx >= 0:
                self.animal_combo.setCurrentIndex(idx)

            self.motivo_combo.setCurrentText(consulta.motivo)
            self.evolucion.setPlainText(consulta.evolucion or "")
            self.examen_fisico.setPlainText(consulta.examen_fisico or "")
            self.tratamiento.setPlainText(consulta.tratamiento or "")
            self.medicamentos.setPlainText(consulta.medicamentos or "")
            self.proxima_consulta.setText(consulta.proxima_consulta or "")
            self.veterinario.setText(consulta.veterinario or "")
            self.observaciones.setPlainText(consulta.observaciones or "")
        except Exception as e:
            show_error(self, "No se pudo cargar la consulta.", e)
            self.reject()

    @ErrorHandler.handle_exception
    def _guardar(self):
        data = {
            'motivo': self.motivo_combo.currentText(),
            'evolucion': self.evolucion.toPlainText().strip(),
            'examen_fisico': self.examen_fisico.toPlainText().strip(),
            'tratamiento': self.tratamiento.toPlainText().strip(),
            'medicamentos': self.medicamentos.toPlainText().strip(),
            'proxima_consulta': self.proxima_consulta.text().strip(),
            'veterinario': self.veterinario.text().strip(),
            'observaciones': self.observaciones.toPlainText().strip()
        }

        self.service.actualizar_consulta(self.consulta_id, data)
        QMessageBox.information(self,
                                f"{ICONS['success']} Éxito",
                                "Consulta actualizada")
        if self.on_save:
            self.on_save()
        self.accept()


class DetalleConsultaDialog(BaseDialog):
    def __init__(self, parent=None, consulta_id=None):
        width, height = DIALOG_SIZES['large']
        super().__init__(
            parent, f"{
                ICONS['view']} Detalle de Consulta", width, height)
        self.consulta_id = consulta_id
        self.service = ConsultaService()
        self.animal_service = AnimalService()
        self.recepcion_service = RecepcionService()
        self.c = None  # Inicializar para evitar errores si falla la BD
        self._build()

    def _build(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        self.content_layout.addLayout(main_layout)

        try:
            # 1. Guardamos el objeto en self.c para imprimirlo luego
            self.c = self.service.obtener_consulta(self.consulta_id)

            # Card Izq
            izq = QGroupBox("Información General")
            style_group(izq, IsaStyles.SECONDARY)
            izq_lay = QFormLayout(izq)
            izq_lay.addRow("Código:", QLabel(f"<b>{self.c.codigo}</b>"))
            izq_lay.addRow("Paciente:", QLabel(
                f"{self.c.animal_nombre} ({self.c.animal_codigo})"))
            izq_lay.addRow("Fecha:", QLabel(self.c.fecha))
            izq_lay.addRow("Motivo:", QLabel(self.c.motivo))
            izq_lay.addRow("Veterinario:", QLabel(self.c.veterinario or 'N/A'))

            if self.c.evolucion:
                izq_lay.addRow("Evolución:", QLabel(self.c.evolucion))
            if self.c.examen_fisico:
                izq_lay.addRow("Ex. Físico:", QLabel(self.c.examen_fisico))

            main_layout.addWidget(izq)

            # Card Der
            der = QGroupBox("Tratamiento")
            style_group(der, IsaStyles.ACCENT)
            der_lay = QVBoxLayout(der)

            if self.c.tratamiento:
                lbl = QLabel(f"<b>Tratamiento:</b><br>{self.c.tratamiento}")
                lbl.setWordWrap(True)
                der_lay.addWidget(lbl)
            if self.c.medicamentos:
                lbl = QLabel(f"<b>Medicamentos:</b><br>{self.c.medicamentos}")
                lbl.setWordWrap(True)
                der_lay.addWidget(lbl)
            if self.c.proxima_consulta:
                der_lay.addWidget(
                    QLabel(f"<b>Próxima Cita:</b> {self.c.proxima_consulta}"))

            der_lay.addStretch()

            # --- BOTÓN DE IMPRIMIR CONSULTA ---
            self.btn_imprimir = QPushButton("🖨️ Imprimir Consulta")
            style_button(self.btn_imprimir, 'primary')
            self.btn_imprimir.clicked.connect(self._imprimir_pdf)
            der_lay.addWidget(self.btn_imprimir)

            # --- BOTÓN DE FÓRMULA MÉDICA ---
            self.btn_formula = QPushButton("💊 Imprimir Fórmula Médica")
            style_button(self.btn_formula, 'accent')
            self.btn_formula.clicked.connect(self._abrir_formula_medica)
            der_lay.addWidget(self.btn_formula)

            main_layout.addWidget(der)

        except Exception as e:
            main_layout.addWidget(QLabel(f"Error: {e}"))

        self.btn_guardar.setText(f"{ICONS['success']} Cerrar")
        style_button(self.btn_guardar, 'secondary')

        # 3. Solución al RuntimeWarning (Silenciar desconexión)
        try:
            self.set_save_callback(self.accept)
        except RuntimeError:
            pass

        self.set_save_callback(self.accept)
        self.btn_cancelar.hide()

    # --- 4. FUNCIÓN QUE GENERA Y ABRE EL PDF ---
    def _imprimir_pdf(self):
        self.btn_imprimir.setText("Generando PDF... ⏳")
        self.btn_imprimir.setEnabled(False)

        from gui_pyside.dialogs.dialogo_generar_reporte import DialogoGenerarReporte

        # Usar el diálogo reutilizable
        dlg = DialogoGenerarReporte(self)
        dlg.generar_consulta(consulta_id=self.consulta_id)
        dlg.exec()

        self.btn_imprimir.setText("🖨️ Imprimir Consulta")
        self.btn_imprimir.setEnabled(True)

    def _abrir_formula_medica(self):
        """Abre el diálogo de fórmula médica."""
        from gui_pyside.dialogs.formula_medica_dialog import FormulaMedicaDialog

        # Verificar que self.c existe
        if not self.c:
            show_warning(
                self,
                "Error",
                "No se pudo cargar la información de la consulta")
            return

        # Obtener datos del animal
        try:
            animal = self.animal_service.obtener_animal(self.c.animal_id)
            animal_data = {
                'nombre': animal.nombre,
                'especie': animal.especie,
                'propietario': animal.propietario or 'N/A',
            }
        except Exception:
            animal_data = {
                'nombre': self.c.animal_nombre,
                'especie': 'N/A',
                'propietario': 'N/A',
            }

        dialog = FormulaMedicaDialog(
            self,
            consulta_id=self.consulta_id,
            animal_data=animal_data)
        dialog.exec()
