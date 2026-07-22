# gui_pyside/dialogs/recibo_dialog.py
from PySide6.QtWidgets import (QVBoxLayout, QLineEdit, QComboBox,
                               QDoubleSpinBox, QMessageBox, QFormLayout,
                               QGroupBox)
from PySide6.QtCore import QDate
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

from gui_pyside.dialogs.base_dialog import BaseDialog
from services.animal_service import AnimalService
from services.pdf_service import PDFService
from gui_pyside.styles import IsaStyles, style_input, style_button
from gui_pyside.utils.messages import show_warning
from gui_pyside.components.components import ErrorHandler
from config import ICONS, DIALOG_SIZES
from utils.logger import setup_logger

logger = setup_logger()


class GenerarReciboDialog(BaseDialog):
    def __init__(self, parent=None):
        width, height = DIALOG_SIZES['medium']
        super().__init__(
            parent, f"{
                ICONS['print']} Generar Recibo", width, height)
        self.animal_service = AnimalService()
        self.pdf_service = PDFService()
        self._build()

    def _build(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Grupo Cliente
        grupo_cliente = QGroupBox("Cliente y Paciente")
        grupo_cliente.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {IsaStyles.BORDER};
                border-radius: 8px;
                padding: 16px;
                margin-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px;
                color: {IsaStyles.PRIMARY};
            }}
        """)
        form_cliente = QFormLayout(grupo_cliente)
        form_cliente.setSpacing(14)

        self.paciente_combo = QComboBox()
        self._cargar_pacientes()
        style_input(self.paciente_combo)
        form_cliente.addRow("Paciente:", self.paciente_combo)

        self.cliente_txt = QLineEdit()
        self.cliente_txt.setPlaceholderText("Nombre de quien paga")
        style_input(self.cliente_txt)
        form_cliente.addRow("A nombre de:", self.cliente_txt)

        self.paciente_combo.currentIndexChanged.connect(
            self._autocompletar_propietario)
        self._autocompletar_propietario()

        # Grupo Cobro
        grupo_cobro = QGroupBox("Detalle del Cobro")
        grupo_cobro.setStyleSheet(grupo_cliente.styleSheet())
        form_cobro = QFormLayout(grupo_cobro)
        form_cobro.setSpacing(14)

        self.servicio_txt = QLineEdit()
        self.servicio_txt.setPlaceholderText("Ej: Consulta + Vacuna Rabia")
        style_input(self.servicio_txt)
        form_cobro.addRow("Concepto *:", self.servicio_txt)

        self.metodo_pago = QComboBox()
        self.metodo_pago.addItems(
            ["Efectivo", "Transferencia", "Tarjeta Crédito", "Tarjeta Débito"])
        style_input(self.metodo_pago)
        form_cobro.addRow("Método:", self.metodo_pago)

        self.total_spin = QDoubleSpinBox()
        self.total_spin.setRange(0, 99999999)
        self.total_spin.setPrefix("$ ")
        self.total_spin.setDecimals(2)
        style_input(self.total_spin)
        form_cobro.addRow("Total *:", self.total_spin)

        layout.addWidget(grupo_cliente)
        layout.addWidget(grupo_cobro)
        layout.addStretch()
        self.content_layout.addLayout(layout)

        self.btn_guardar.setText(f"{ICONS['print']} Generar PDF")
        style_button(self.btn_guardar, 'primary')
        self.set_save_callback(self._generar)

    def _cargar_pacientes(self):
        try:
            animales = self.animal_service.listar_animales()
            self.animales_data = {a.id: a for a in animales}
            for a in animales:
                self.paciente_combo.addItem(f"{a.nombre} ({a.codigo})", a.id)
        except Exception as e:
            logger.warning(f"No se pudieron cargar pacientes para recibo: {e}")

    def _autocompletar_propietario(self):
        animal_id = self.paciente_combo.currentData()
        if animal_id and hasattr(self, 'animales_data'):
            animal = self.animales_data.get(animal_id)
            if animal and animal.propietario:
                self.cliente_txt.setText(animal.propietario)
            else:
                self.cliente_txt.clear()

    @ErrorHandler.handle_exception
    def _generar(self):
        servicio = self.servicio_txt.text().strip()
        total = self.total_spin.value()

        if not servicio:
            show_warning(self,
                         f"{ICONS['warning']} Error",
                         "Ingrese el concepto")
            return
        if total <= 0:
            show_warning(self,
                         f"{ICONS['warning']} Error",
                         "Ingrese un total válido")
            return

        datos = {
            'fecha': QDate.currentDate().toString("dd/MM/yyyy"),
            'cliente': self.cliente_txt.text().strip() or "Consumidor Final",
            'paciente': self.paciente_combo.currentText(),
            'servicio': servicio,
            'metodo_pago': self.metodo_pago.currentText(),
            'total': total
        }

        import os
        from datetime import datetime
        nombre_archivo = f"recibo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.pdf_service.guardar_recibo(datos, nombre_archivo)

        reply = QMessageBox.question(
            self,
            f"{ICONS['success']} Éxito",
            "Recibo generado. ¿Desea abrirlo?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(filepath)))

        self.accept()
