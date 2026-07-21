# gui_pyside/dialogs/vacuna_dialog.py
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QComboBox, QTextEdit, QPushButton, QFormLayout,
                               QGroupBox, QDateEdit, QMessageBox)
from PySide6.QtCore import QDate

from gui_pyside.dialogs.base_dialog import BaseDialog
from gui_pyside.dialogs.animal_dialog import NuevoAnimalDialog
from gui_pyside.utils.messages import show_error, show_warning
from gui_pyside.styles import IsaStyles, style_input, style_button, style_group
from gui_pyside.components.components import ErrorHandler
from services.vacuna_service import VacunaService
from services.animal_service import AnimalService
from config import VACUNAS_DISPONIBLES, DESPARASITANTES, VIAS_ADMINISTRACION, ICONS, DIALOG_SIZES
from utils.logger import setup_logger

logger = setup_logger()


class NuevaVacunacionDialog(BaseDialog):
    def __init__(self, parent=None, on_save=None):
        width, height = DIALOG_SIZES['large']
        super().__init__(
            parent, f"{
                ICONS['add']} Registro Preventivo", width, height)
        self.on_save = on_save
        self.service = VacunaService()
        self.animal_service = AnimalService()
        self._build()

    def _build(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        self.content_layout.addLayout(main_layout)

        # --- CARD IZQUIERDA ---
        left_card = QGroupBox("Información del Producto")
        style_group(left_card, IsaStyles.ACCENT)
        left_layout = QFormLayout(left_card)
        left_layout.setSpacing(14)

        self.animal_combo = QComboBox()
        self._cargar_animales()
        style_input(self.animal_combo)
        left_layout.addRow("Paciente:", self.animal_combo)

        btn_nuevo = QPushButton(f"{ICONS['add']} Nuevo Paciente")
        btn_nuevo.clicked.connect(self._abrir_nuevo_paciente)
        style_button(btn_nuevo, 'secondary')
        left_layout.addRow("", btn_nuevo)

        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["Vacuna", "Desparasitación"])
        style_input(self.tipo_combo)
        left_layout.addRow("Tipo:", self.tipo_combo)

        self.producto_combo = QComboBox()
        self.producto_combo.setEditable(True)
        style_input(self.producto_combo)
        left_layout.addRow("Producto:", self.producto_combo)

        self.tipo_combo.currentTextChanged.connect(self._actualizar_productos)
        self._actualizar_productos(self.tipo_combo.currentText())

        self.lote = QLineEdit()
        self.lote.setPlaceholderText("Nº Lote")
        style_input(self.lote)
        left_layout.addRow("Lote:", self.lote)

        self.dosis = QLineEdit()
        self.dosis.setPlaceholderText("Ej: 1 ml")
        style_input(self.dosis)
        left_layout.addRow("Dosis:", self.dosis)

        self.via = QComboBox()
        self.via.addItems(VIAS_ADMINISTRACION)
        self.via.setEditable(True)
        style_input(self.via)
        left_layout.addRow("Vía:", self.via)

        # --- CARD DERECHA ---
        right_card = QGroupBox("Programación")
        style_group(right_card, IsaStyles.PRIMARY)
        right_layout = QFormLayout(right_card)
        right_layout.setSpacing(14)

        self.fecha_app = QDateEdit(QDate.currentDate())
        self.fecha_app.setCalendarPopup(True)
        style_input(self.fecha_app)
        right_layout.addRow("Aplicación:", self.fecha_app)

        self.fecha_prox = QDateEdit(QDate.currentDate().addYears(1))
        self.fecha_prox.setCalendarPopup(True)
        style_input(self.fecha_prox)
        right_layout.addRow("Próxima:", self.fecha_prox)

        self.veterinario = QLineEdit()
        self.veterinario.setPlaceholderText("Dr(a).")
        style_input(self.veterinario)
        right_layout.addRow("Veterinario:", self.veterinario)

        self.observaciones = QTextEdit()
        self.observaciones.setPlaceholderText("Reacciones adversas...")
        self.observaciones.setMaximumHeight(100)
        self.observaciones.setStyleSheet(IsaStyles.get_textarea_style())
        right_layout.addRow("Notas:", self.observaciones)

        main_layout.addWidget(left_card, 1)
        main_layout.addWidget(right_card, 1)

        self.btn_guardar.setText(f"{ICONS['save']} Guardar")
        style_button(self.btn_guardar, 'primary')
        self.btn_cancelar.setText(f"{ICONS['cancel']} Cancelar")
        style_button(self.btn_cancelar, 'ghost')

        self.set_save_callback(self._guardar)

    def _actualizar_productos(self, tipo):
        self.producto_combo.clear()
        items = VACUNAS_DISPONIBLES if tipo == "Vacuna" else DESPARASITANTES
        self.producto_combo.addItems(items)

    def _cargar_animales(self):
        self.animal_combo.clear()
        try:
            animales = self.animal_service.listar_animales(
                {'estado': 'Activo'})
            for a in animales:
                self.animal_combo.addItem(f"{a.nombre} ({a.codigo})", a.id)
        except Exception as e:
            logger.warning(
                f"No se pudieron cargar pacientes para vacunación: {e}")

    def _abrir_nuevo_paciente(self):
        dialog = NuevoAnimalDialog(
            parent=self.parent(),
            on_save=self._cargar_animales)
        dialog.exec()

    @ErrorHandler.handle_exception
    def _guardar(self):
        animal_id = self.animal_combo.currentData()
        if not animal_id:
            show_warning(self,
                         f"{ICONS['warning']} Error",
                         "Seleccione un paciente")
            return

        data = {
            'animal_id': animal_id,
            'tipo': self.tipo_combo.currentText(),
            'producto': self.producto_combo.currentText(),
            'lote': self.lote.text().strip(),
            'dosis': self.dosis.text().strip(),
            'via': self.via.currentText(),
            'fecha_aplicacion': self.fecha_app.date().toString("yyyy-MM-dd"),
            'fecha_proxima': self.fecha_prox.date().toString("yyyy-MM-dd"),
            'veterinario': self.veterinario.text().strip(),
            'observaciones': self.observaciones.toPlainText().strip()
        }

        if not data['producto']:
            show_warning(self,
                         f"{ICONS['warning']} Error",
                         "Especifique el producto")
            return

        self.service.registrar(data)
        QMessageBox.information(
            self, f"{
                ICONS['success']} Éxito", f"{
                data['tipo']} registrada")

        if self.on_save:
            self.on_save()
        self.accept()


class DetalleVacunacionDialog(BaseDialog):
    def __init__(self, parent=None, vacuna_id=None):
        width, height = DIALOG_SIZES['medium']
        super().__init__(
            parent, f"{
                ICONS['view']} Detalle Aplicación", width, height)
        self.vacuna_id = vacuna_id
        self.service = VacunaService()
        self._build()

    def _build(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        self.content_layout.addLayout(main_layout)

        try:
            # 1. Guardamos el objeto en self.v para poder imprimirlo después
            self.v = self.service.obtener(self.vacuna_id)

            izq = QGroupBox("Datos")
            style_group(izq, IsaStyles.ACCENT)
            izq_lay = QFormLayout(izq)
            izq_lay.addRow("Código:", QLabel(f"<b>{self.v.codigo}</b>"))
            izq_lay.addRow("Paciente:", QLabel(f"{self.v.animal_nombre}"))
            izq_lay.addRow("Tipo:", QLabel(self.v.tipo))
            izq_lay.addRow("Producto:", QLabel(f"<b>{self.v.producto}</b>"))

            main_layout.addWidget(izq)

            der = QGroupBox("Tiempos")
            style_group(der, IsaStyles.PRIMARY)
            der_lay = QVBoxLayout(der)
            der_lay.addWidget(
                QLabel(f"<b>Aplicación:</b> {self.v.fecha_aplicacion}"))

            if self.v.fecha_proxima:
                lbl = QLabel(f"<b>Próxima:</b> {self.v.fecha_proxima}")
                lbl.setStyleSheet(f"color: {IsaStyles.WARNING}")
                der_lay.addWidget(lbl)
            if self.v.observaciones:
                der_lay.addWidget(
                    QLabel(f"<b>Notas:</b><br>{self.v.observaciones}"))

            der_lay.addStretch()

            # --- 2. NUEVO BOTÓN DE IMPRIMIR ---
            self.btn_imprimir = QPushButton("🖨️ Imprimir Certificado")
            style_button(self.btn_imprimir, 'primary')
            self.btn_imprimir.clicked.connect(self._imprimir_pdf)
            der_lay.addWidget(self.btn_imprimir)

            main_layout.addWidget(der)

        except Exception as e:
            main_layout.addWidget(QLabel(f"Error: {e}"))

        self.btn_guardar.setText(f"{ICONS['success']} Cerrar")
        style_button(self.btn_guardar, 'secondary')
        self.set_save_callback(self.accept)
        self.btn_cancelar.hide()

    # --- 4. FUNCIÓN QUE GENERA Y ABRE EL PDF ---
    def _imprimir_pdf(self):
        self.btn_imprimir.setText("Generando PDF... ⏳")
        self.btn_imprimir.setEnabled(False)

        from services.pdf_service import PDFService
        from gui_pyside.workers import PDFWorker

        self.pdf_service = PDFService()

        # ⚠️ CAMBIO 1 y 2: Cambiar la función y la variable de datos
        self.worker = PDFWorker(self.pdf_service.generar_vacunacion, self.v)

        self.worker.finished.connect(self._pdf_exito)
        self.worker.error.connect(self._pdf_error)

        self.worker.start()

    def _pdf_exito(self, ruta_pdf):
        # Fase 4 (C4): `os.startfile` solo existe en Windows —
        # usamos el helper multiplataforma para no romper el botón
        # "🖨️ Imprimir Certificado" en macOS/Linux.
        from gui_pyside.utils.platform_utils import open_file_externally
        open_file_externally(ruta_pdf)
        # ⚠️ CAMBIO 3: Restaurar el texto correcto del botón
        self.btn_imprimir.setText("🖨️ Imprimir Certificado")
        self.btn_imprimir.setEnabled(True)

    def _pdf_error(self, error_msg):
        # ⚠️ CAMBIO 3: Restaurar el texto correcto del botón
        self.btn_imprimir.setText("🖨️ Imprimir Certificado")
        self.btn_imprimir.setEnabled(True)
        show_error(self, "No se pudo generar el PDF.", Exception(error_msg))
