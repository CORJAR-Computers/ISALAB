# gui_pyside/dialogs/cirugia_dialog.py
"""Diálogos de cirugías para PySide6 - VERSIÓN MEJORADA"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel,
                               QLineEdit, QComboBox, QTextEdit,
                               QMessageBox, QFormLayout, QGroupBox,
                               QSpinBox, QDateEdit, QPushButton, QVBoxLayout)
from PySide6.QtCore import Qt, QDate

from gui_pyside.dialogs.base_dialog import BaseDialog
from gui_pyside.dialogs.animal_dialog import NuevoAnimalDialog
from gui_pyside.utils.messages import show_error, show_warning
from gui_pyside.styles import IsaStyles, style_button, style_group, style_input
from gui_pyside.components.components import ErrorHandler, StatusBadge
from services.cirugia_service import CirugiaService
from services.animal_service import AnimalService
from config import ESTADOS_CIRUGIA, TIPOS_CIRUGIA, TIPOS_ANESTESIA, ICONS, DIALOG_SIZES
from utils.logger import setup_logger

logger = setup_logger()


class NuevaCirugiaDialog(BaseDialog):
    def __init__(self, parent=None, on_save=None):
        width, height = DIALOG_SIZES['xlarge']
        super().__init__(
            parent, f"{
                ICONS['add']} Programar Cirugía", width, height)
        self.on_save = on_save
        self.service = CirugiaService()
        self.animal_service = AnimalService()
        self._build()

    def _build(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        self.content_layout.addLayout(main_layout)

        # --- CARD IZQUIERDA ---
        left_card = QGroupBox("Datos del Procedimiento")
        style_group(left_card, IsaStyles.ACCENT)
        left_layout = QFormLayout(left_card)
        left_layout.setSpacing(14)

        # Paciente
        paciente_widget = QWidget()
        pac_layout = QHBoxLayout(paciente_widget)
        pac_layout.setContentsMargins(0, 0, 0, 0)

        self.animal_combo = QComboBox()
        self._cargar_animales()
        style_input(self.animal_combo)
        pac_layout.addWidget(self.animal_combo, 1)

        btn_nuevo = QPushButton(f"{ICONS['add']}")
        btn_nuevo.setFixedSize(36, IsaStyles.INPUT_HEIGHT)
        btn_nuevo.setCursor(Qt.PointingHandCursor)
        btn_nuevo.setToolTip("Nuevo paciente")
        btn_nuevo.clicked.connect(self._abrir_nuevo_paciente)
        style_button(btn_nuevo, 'secondary')
        pac_layout.addWidget(btn_nuevo)

        left_layout.addRow("Paciente *:", paciente_widget)

        self.tipo_cirugia = QComboBox()
        self.tipo_cirugia.addItems(TIPOS_CIRUGIA)
        style_input(self.tipo_cirugia)
        left_layout.addRow("Procedimiento *:", self.tipo_cirugia)

        # Fecha y duración en fila
        fechas = QWidget()
        f_layout = QHBoxLayout(fechas)
        f_layout.setContentsMargins(0, 0, 0, 0)

        self.fecha = QDateEdit(QDate.currentDate())
        self.fecha.setCalendarPopup(True)
        style_input(self.fecha)

        self.duracion = QSpinBox()
        self.duracion.setSuffix(" min")
        self.duracion.setRange(0, 720)

        f_layout.addWidget(QLabel("Fecha:"))
        f_layout.addWidget(self.fecha)
        f_layout.addWidget(QLabel("Duración:"))
        f_layout.addWidget(self.duracion)

        left_layout.addRow(fechas)

        self.cirujano = QLineEdit()
        self.cirujano.setPlaceholderText("Dr(a). Principal")
        style_input(self.cirujano)
        left_layout.addRow("Cirujano:", self.cirujano)

        self.asistente = QLineEdit()
        self.asistente.setPlaceholderText("Asistente")
        style_input(self.asistente)
        left_layout.addRow("Asistente:", self.asistente)

        self.descripcion = QTextEdit()
        self.descripcion.setPlaceholderText(
            "Detalles del abordaje quirúrgico, técnica a utilizar...")
        self.descripcion.setMaximumHeight(100)
        self.descripcion.setStyleSheet(IsaStyles.get_textarea_style())
        left_layout.addRow("Descripción:", self.descripcion)

        # --- CARD DERECHA ---
        right_card = QGroupBox("Anestesia y Postoperatorio")
        style_group(right_card, IsaStyles.PRIMARY)
        right_layout = QFormLayout(right_card)
        right_layout.setSpacing(14)

        self.anestesiologo = QLineEdit()
        self.anestesiologo.setPlaceholderText("Anestesiólogo")
        style_input(self.anestesiologo)
        right_layout.addRow("Anestesiólogo:", self.anestesiologo)

        self.anestesia = QComboBox()
        self.anestesia.addItems(TIPOS_ANESTESIA)
        style_input(self.anestesia)
        right_layout.addRow("Tipo Anestesia:", self.anestesia)

        self.protocolo = QTextEdit()
        self.protocolo.setPlaceholderText("Fármacos, dosis, inducción...")
        self.protocolo.setMaximumHeight(80)
        self.protocolo.setStyleSheet(IsaStyles.get_textarea_style())
        right_layout.addRow("Protocolo:", self.protocolo)

        self.complicaciones = QTextEdit()
        self.complicaciones.setPlaceholderText(
            "Si no hubo complicaciones, dejar en blanco...")
        self.complicaciones.setMaximumHeight(80)
        self.complicaciones.setStyleSheet(IsaStyles.get_textarea_style())
        right_layout.addRow("Complicaciones:", self.complicaciones)

        self.cuidados = QTextEdit()
        self.cuidados.setPlaceholderText(
            "Reposo, limpieza de herida, medicamentos...")
        self.cuidados.setMaximumHeight(80)
        self.cuidados.setStyleSheet(IsaStyles.get_textarea_style())
        right_layout.addRow("Cuidados Post:", self.cuidados)

        main_layout.addWidget(left_card, 1)
        main_layout.addWidget(right_card, 1)

        self.btn_guardar.setText(f"{ICONS['save']} Programar Cirugía")
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
                f"No se pudieron cargar pacientes para cirugía: {e}")

    def _abrir_nuevo_paciente(self):
        dialog = NuevoAnimalDialog(
            parent=self.parent(),
            on_save=self._cargar_animales)
        dialog.exec()

    def _validate(self) -> bool:
        if not self.animal_combo.currentData():
            show_warning(self,
                         f"{ICONS['warning']} Error",
                         "Seleccione un paciente")
            return False
        return True

    @ErrorHandler.handle_exception
    def _guardar(self):
        if not self._validate():
            return

        data = {
            'animal_id': self.animal_combo.currentData(),
            'fecha': self.fecha.date().toString("yyyy-MM-dd"),
            'tipo_cirugia': self.tipo_cirugia.currentText(),
            'descripcion': self.descripcion.toPlainText().strip(),
            'anestesia': self.anestesia.currentText(),
            'protocolo_anestesico': self.protocolo.toPlainText().strip(),
            'duracion_min': self.duracion.value() or None,
            'cirujano': self.cirujano.text().strip(),
            'anestesiologo': self.anestesiologo.text().strip(),
            'asistente': self.asistente.text().strip(),
            'complicaciones': self.complicaciones.toPlainText().strip(),
            'cuidados_post': self.cuidados.toPlainText().strip(),
            'estado': 'Programada'
        }

        self.service.programar_cirugia(data)
        QMessageBox.information(self,
                                f"{ICONS['success']} Éxito",
                                "Cirugía programada correctamente")

        if self.on_save:
            self.on_save()
        self.accept()


class EditarCirugiaDialog(NuevaCirugiaDialog):
    """Hereda de NuevaCirugiaDialog para reutilizar la interfaz"""

    def __init__(self, parent=None, cirugia_id=None, on_save=None):
        self.cirugia_id = cirugia_id
        super().__init__(parent, on_save)
        self.setWindowTitle(f"{ICONS['edit']} Editar Cirugía")
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
            c = self.service.obtener_cirugia(self.cirugia_id)

            idx = self.animal_combo.findData(c.animal_id)
            if idx >= 0:
                self.animal_combo.setCurrentIndex(idx)

            self.tipo_cirugia.setCurrentText(c.tipo_cirugia)

            if c.fecha:
                qdate = QDate.fromString(c.fecha[:10], "yyyy-MM-dd")
                if qdate.isValid():
                    self.fecha.setDate(qdate)

            self.duracion.setValue(c.duracion_min or 0)
            self.cirujano.setText(c.cirujano or "")
            self.asistente.setText(c.asistente or "")
            self.descripcion.setPlainText(c.descripcion or "")
            self.anestesiologo.setText(c.anestesiologo or "")
            self.anestesia.setCurrentText(c.anestesia or TIPOS_ANESTESIA[0])
            self.protocolo.setPlainText(c.protocolo_anestesico or "")
            self.complicaciones.setPlainText(c.complicaciones or "")
            self.cuidados.setPlainText(c.cuidados_post or "")

        except Exception as e:
            show_error(self, "No se pudo cargar la cirugía.", e)
            self.reject()

    @ErrorHandler.handle_exception
    def _guardar(self):
        data = {
            'fecha': self.fecha.date().toString("yyyy-MM-dd"),
            'tipo_cirugia': self.tipo_cirugia.currentText(),
            'descripcion': self.descripcion.toPlainText().strip(),
            'anestesia': self.anestesia.currentText(),
            'protocolo_anestesico': self.protocolo.toPlainText().strip(),
            'duracion_min': self.duracion.value() or None,
            'cirujano': self.cirujano.text().strip(),
            'anestesiologo': self.anestesiologo.text().strip(),
            'asistente': self.asistente.text().strip(),
            'complicaciones': self.complicaciones.toPlainText().strip(),
            'cuidados_post': self.cuidados.toPlainText().strip()
        }

        self.service.actualizar_cirugia(self.cirugia_id, data)
        QMessageBox.information(self,
                                f"{ICONS['success']} Éxito",
                                "Cirugía actualizada")

        if self.on_save:
            self.on_save()
        self.accept()


class EstadoCirugiaDialog(BaseDialog):
    """Diálogo para cambiar el estado de una cirugía"""

    def __init__(self, parent=None, cirugia_id=None, on_save=None):
        width, height = DIALOG_SIZES['small']
        super().__init__(
            parent, f"{
                ICONS['edit']} Actualizar Estado", width, height)
        self.cirugia_id = cirugia_id
        self.on_save = on_save
        self.service = CirugiaService()
        self._build()

    def _build(self):
        layout = QFormLayout()
        layout.setSpacing(16)

        # Info actual
        try:
            c = self.service.obtener_cirugia(self.cirugia_id)
            info = QLabel(
                f"Cirugía: <b>{c.codigo}</b><br>Paciente: {c.animal_nombre}")
            info.setStyleSheet(f"""
                color: {IsaStyles.SECONDARY};
                padding: 10px;
                background-color: {IsaStyles.LIGHT_BG};
                border-radius: 6px;
                margin-bottom: 10px;
            """)
            layout.addRow(info)
        except Exception:
            pass

        # Estado
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(ESTADOS_CIRUGIA)
        style_input(self.estado_combo)
        layout.addRow("Nuevo Estado:", self.estado_combo)

        # Complicaciones (si aplica)
        self.complicaciones = QTextEdit()
        self.complicaciones.setPlaceholderText(
            "Registrar complicaciones si las hubo...")
        self.complicaciones.setMaximumHeight(80)
        self.complicaciones.setStyleSheet(IsaStyles.get_textarea_style())
        layout.addRow("Complicaciones:", self.complicaciones)

        self.content_layout.addLayout(layout)

        self.btn_guardar.setText(f"{ICONS['save']} Actualizar")
        style_button(self.btn_guardar, 'primary')
        self.btn_cancelar.setText(f"{ICONS['cancel']} Cancelar")
        style_button(self.btn_cancelar, 'ghost')

        self.set_save_callback(self._guardar)

    @ErrorHandler.handle_exception
    def _guardar(self):
        nuevo_estado = self.estado_combo.currentText()
        complicaciones = self.complicaciones.toPlainText().strip()

        self.service.actualizar_estado(
            self.cirugia_id, nuevo_estado, complicaciones)
        QMessageBox.information(self,
                                f"{ICONS['success']} Éxito",
                                "Estado actualizado")

        if self.on_save:
            self.on_save()
        self.accept()


class DetalleCirugiaDialog(BaseDialog):
    """Diálogo para ver detalles de una cirugía"""

    def __init__(self, parent=None, cirugia_id=None):
        width, height = DIALOG_SIZES['xlarge']
        super().__init__(
            parent, f"{
                ICONS['view']} Reporte Quirúrgico", width, height)
        self.cirugia_id = cirugia_id
        self.service = CirugiaService()
        self._build()

    def _build(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        self.content_layout.addLayout(main_layout)

        try:
            c = self.service.obtener_cirugia(self.cirugia_id)
            self.c = c  # Guardamos el objeto para el Worker

            # --- CARD IZQUIERDA ---
            izq_card = QGroupBox("Información del Procedimiento")
            style_group(izq_card, IsaStyles.ACCENT)
            izq_layout = QFormLayout(izq_card)

            izq_layout.addRow("Código:", QLabel(
                f"<b style='font-size:16px;'>{c.codigo}</b>"))
            izq_layout.addRow("Paciente:", QLabel(
                f"{c.animal_nombre} ({c.animal_codigo})"))
            izq_layout.addRow(
                "Procedimiento:", QLabel(
                    f"<b>{
                        c.tipo_cirugia}</b>"))
            izq_layout.addRow("Fecha:", QLabel(c.fecha))
            izq_layout.addRow("Duración:",
                              QLabel(f"{c.duracion_min or 0} min"))

            # Badge de estado
            estado_badge = StatusBadge(c.estado)
            izq_layout.addRow("Estado:", estado_badge)

            # Equipo médico
            equipo = f"<b>Cirujano:</b> {c.cirujano or 'N/A'}<br>"
            equipo += f"<b>Anestesiólogo:</b> {c.anestesiologo or 'N/A'}<br>"
            equipo += f"<b>Asistente:</b> {c.asistente or 'N/A'}"
            izq_layout.addRow("Equipo:", QLabel(equipo))

            main_layout.addWidget(izq_card, 0)

            # --- CARD DERECHA ---
            der_card = QGroupBox("Reporte Clínico")
            style_group(der_card, IsaStyles.PRIMARY)
            der_layout = QVBoxLayout(der_card)

            # Anestesia
            der_layout.addWidget(QLabel(f"<b>Anestesia ({c.anestesia}):</b>"))
            lbl_prot = QLabel(
                c.protocolo_anestesico or "<i>Sin protocolo registrado</i>")
            lbl_prot.setWordWrap(True)
            lbl_prot.setStyleSheet(f"""
                color: {IsaStyles.DARK};
                padding: 8px;
                background-color: {IsaStyles.LIGHT_BG};
                border-radius: 4px;
            """)
            der_layout.addWidget(lbl_prot)
            der_layout.addSpacing(10)

            # Descripción
            der_layout.addWidget(QLabel("<b>Descripción Quirúrgica:</b>"))
            lbl_desc = QLabel(c.descripcion or "<i>Sin descripción</i>")
            lbl_desc.setWordWrap(True)
            der_layout.addWidget(lbl_desc)

            # Complicaciones
            if c.complicaciones:
                der_layout.addSpacing(10)
                lbl_comp = QLabel(
                    f"<b style='color:{IsaStyles.DANGER};'>Complicaciones:</b><br>{c.complicaciones}")
                lbl_comp.setWordWrap(True)
                lbl_comp.setStyleSheet(f"""
                    color: {IsaStyles.DANGER};
                    background-color: #FEE2E2;
                    padding: 10px;
                    border-radius: 6px;
                """)
                der_layout.addWidget(lbl_comp)

            # Cuidados post
            if c.cuidados_post:
                der_layout.addSpacing(10)
                lbl_cuid = QLabel(
                    f"<b>Cuidados Postoperatorios:</b><br>{c.cuidados_post}")
                lbl_cuid.setWordWrap(True)
                lbl_cuid.setStyleSheet("""
                    background-color: #F0FDF4;
                    padding: 10px;
                    border-radius: 6px;
                    color: #166534;
                """)
                der_layout.addWidget(lbl_cuid)

            der_layout.addStretch()

            # --- NUEVO BOTÓN DE IMPRIMIR ---
            self.btn_imprimir = QPushButton("🖨️ Imprimir Registro Quirúrgico")
            style_button(self.btn_imprimir, 'primary')
            self.btn_imprimir.clicked.connect(self._imprimir_pdf)
            der_layout.addWidget(self.btn_imprimir)

            main_layout.addWidget(der_card, 1)

        except Exception as e:
            main_layout.addWidget(
                QLabel(f"<span style='color:red;'>Error: {e}</span>"))

        # Botón cerrar (Limpiado para evitar el RuntimeWarning)
        self.btn_guardar.setText(f"{ICONS['success']} Cerrar")
        style_button(self.btn_guardar, 'secondary')
        self.set_save_callback(self.accept)
        self.btn_cancelar.hide()

    # =================================================================
    # FUNCIONES DEL WORKER (¡Asegúrate de que mantengan esta sangría!)
    # =================================================================
    def _imprimir_pdf(self):
        self.btn_imprimir.setText("Generando PDF... ⏳")
        self.btn_imprimir.setEnabled(False)

        from gui_pyside.dialogs.dialogo_generar_reporte import DialogoGenerarReporte

        # Usar el diálogo reutilizable
        dlg = DialogoGenerarReporte(self)
        dlg.generar_cirugia(cirugia_id=self.cirugia_id)
        dlg.exec()

        self.btn_imprimir.setText("🖨️ Imprimir Registro Quirúrgico")
        self.btn_imprimir.setEnabled(True)
