from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QLineEdit,
                               QComboBox, QTextEdit, QPushButton, QMessageBox,
                               QFormLayout, QGroupBox, QDateTimeEdit)
from PySide6.QtCore import Qt, QDateTime

from gui_pyside.dialogs.base_dialog import BaseDialog
from gui_pyside.dialogs.animal_dialog import NuevoAnimalDialog
from gui_pyside.components.components import ErrorHandler
from gui_pyside.utils.messages import show_warning
from services.recepcion_service import RecepcionService
from services.animal_service import AnimalService
from config import QT_STYLES, ESTADOS_RECEPCION, MOTIVOS_CONSULTA
from gui_pyside.styles import style_button
from utils.logger import setup_logger

logger = setup_logger()

# Estilos CSS modernos
MODERN_STYLES = """
    QLineEdit, QComboBox, QTextEdit, QDateTimeEdit {
        border: 2px solid #E2E8F0;
        border-radius: 8px;
        padding: 10px 12px;
        background-color: white;
        color: #1E293B;
        font-size: 13px;
        min-height: 20px;
    }
    QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateTimeEdit:focus {
        border: 2px solid #3BADE5;
        background-color: #F0F9FF;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 30px;
        border-left: 2px solid #E2E8F0;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }
    QComboBox QAbstractItemView {
        border: 2px solid #E2E8F0;
        border-radius: 8px;
        background-color: white;
        selection-background-color: #3BADE5;
        selection-color: white;
        padding: 4px;
    }
    QComboBox QAbstractItemView::item {
        padding: 8px 12px;
        border-radius: 4px;
        min-height: 20px;
    }
    QTextEdit {
        line-height: 1.5;
    }
    QDateTimeEdit::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 30px;
        border-left: 2px solid #E2E8F0;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }
"""


class NuevaRecepcionDialog(BaseDialog):
    """Diálogo para nueva recepción - VERSIÓN MEJORADA"""

    def __init__(self, parent=None, on_save=None):
        super().__init__(parent, "Nueva Recepción", 900, 480)
        self.on_save = on_save
        self.service = RecepcionService()
        self.animal_service = AnimalService()
        self._build()

    def _build(self):
        """Construye el formulario con diseño moderno de 2 cards"""
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.addLayout(main_layout)

        # Aplicar estilos globales
        self.setStyleSheet(MODERN_STYLES)

        # --- CARD IZQUIERDA: Selección de Paciente ---
        left_card = QGroupBox("🐾  Selección del Paciente")
        left_card.setStyleSheet("""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                margin-top: 16px;
                padding: 16px;
                background-color: white;
                font-size: 14px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 4px 12px;
                color: #1E3A5F;
                background-color: #E8F4F8;
                border-radius: 6px;
            }}
        """)
        left_layout = QFormLayout(left_card)
        left_layout.setSpacing(14)
        left_layout.setLabelAlignment(Qt.AlignLeft)
        left_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # Combo de pacientes con estilo mejorado
        self.animal_combo = QComboBox()
        self.animal_combo.setMinimumHeight(42)
        self._cargar_animales()
        self.animal_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #E2E8F0;
                border-left: 4px solid #EF4444;
                border-radius: 8px;
                padding: 10px 12px;
                padding-right: 30px;
                background-color: white;
                font-size: 13px;
                min-height: 20px;
            }
            QComboBox:focus {
                border: 2px solid #3BADE5;
                border-left: 4px solid #EF4444;
                background-color: #F0F9FF;
            }
        """)
        left_layout.addRow("Paciente *:", self.animal_combo)

        # Botón de nuevo paciente con mejor diseño
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 8, 0, 0)
        btn_layout.setSpacing(0)

        btn_nuevo = QPushButton("➕  Registrar Nuevo Paciente")
        btn_nuevo.setMinimumHeight(40)
        btn_nuevo.setCursor(Qt.PointingHandCursor)
        btn_nuevo.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 16px;
            }}
            QPushButton:hover {{
                background-color: {QT_STYLES['secondary']};
            }}
            QPushButton:pressed {{
                background-color: #0F172A;
            }}
        """)
        btn_nuevo.clicked.connect(self._abrir_nuevo_paciente)
        btn_layout.addWidget(btn_nuevo)
        btn_layout.addStretch()

        left_layout.addRow("", btn_container)

        # Información del paciente seleccionado (dinámica)
        self.info_paciente = QLabel(
            "Seleccione un paciente para ver sus datos")
        self.info_paciente.setStyleSheet("""
            color: #64748B;
            font-size: 12px;
            padding: 12px;
            background-color: #F8FAFC;
            border-radius: 8px;
            margin-top: 8px;
        """)
        self.info_paciente.setWordWrap(True)
        self.info_paciente.setMinimumHeight(60)
        left_layout.addRow("Info:", self.info_paciente)

        # Conectar cambio de selección para actualizar info
        self.animal_combo.currentIndexChanged.connect(
            self._actualizar_info_paciente)

        # --- CARD DERECHA: Detalles de la Visita ---
        right_card = QGroupBox("📋  Detalles de la Visita")
        right_card.setStyleSheet(left_card.styleSheet())
        right_layout = QFormLayout(right_card)
        right_layout.setSpacing(14)
        right_layout.setLabelAlignment(Qt.AlignLeft)
        right_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        # Motivo de consulta
        self.motivo_combo = QComboBox()
        self.motivo_combo.addItems(MOTIVOS_CONSULTA)
        self.motivo_combo.setMinimumHeight(42)
        self.motivo_combo.setEditable(True)
        self.motivo_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #E2E8F0;
                border-left: 4px solid #EF4444;
                border-radius: 8px;
                padding: 10px 12px;
                padding-right: 30px;
                background-color: white;
            }
            QComboBox:focus {
                border: 2px solid #3BADE5;
                border-left: 4px solid #EF4444;
                background-color: #F0F9FF;
            }
        """)
        right_layout.addRow("Motivo *:", self.motivo_combo)

        # Veterinario
        self.veterinario = QLineEdit()
        self.veterinario.setPlaceholderText("Dr(a). Encargado (opcional)")
        self.veterinario.setMinimumHeight(42)
        right_layout.addRow("Veterinario:", self.veterinario)

        # Fecha y hora
        self.fecha_hora = QDateTimeEdit()
        self.fecha_hora.setDateTime(QDateTime.currentDateTime())
        self.fecha_hora.setCalendarPopup(True)
        self.fecha_hora.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.fecha_hora.setMinimumHeight(42)
        self.fecha_hora.setStyleSheet("""
            QDateTimeEdit {
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px 12px;
                background-color: white;
            }
            QDateTimeEdit:focus {
                border: 2px solid #3BADE5;
                background-color: #F0F9FF;
            }
        """)
        right_layout.addRow("Fecha/Hora:", self.fecha_hora)

        # Observaciones
        self.observaciones = QTextEdit()
        self.observaciones.setPlaceholderText(
            "Notas adicionales sobre la recepción...")
        self.observaciones.setMaximumHeight(100)
        self.observaciones.setStyleSheet("""
            QTextEdit {
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px 12px;
                background-color: white;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border: 2px solid #3BADE5;
                background-color: #F0F9FF;
            }
        """)
        right_layout.addRow("Notas:", self.observaciones)

        main_layout.addWidget(left_card, 1)
        main_layout.addWidget(right_card, 1)

        # Tooltips informativos
        self.animal_combo.setToolTip(
            "Seleccione el paciente que está siendo recibido")
        btn_nuevo.setToolTip("Crear un nuevo paciente si no está en la lista")
        self.motivo_combo.setToolTip(
            "Motivo principal de la visita. Puede escribir uno personalizado.")
        self.veterinario.setToolTip(
            "Nombre del médico veterinario que atenderá al paciente")
        self.fecha_hora.setToolTip("Fecha y hora de la recepción")

        self.set_save_callback(self._guardar)

    def _cargar_animales(self):
        """Carga la lista de pacientes activos"""
        self.animal_combo.clear()
        try:
            animales = self.animal_service.listar_animales(
                {'estado': 'Activo'})
            self.animales_data = {}
            for a in animales:
                display_text = f"{a.nombre} ({a.codigo}) - {a.especie}"
                self.animal_combo.addItem(display_text, a.id)
                self.animales_data[a.id] = a
        except Exception as e:
            logger.warning(
                f"No se pudieron cargar pacientes para recepción: {e}")

    def _actualizar_info_paciente(self):
        """Actualiza la información mostrada del paciente seleccionado"""
        animal_id = self.animal_combo.currentData()
        if animal_id and hasattr(
                self, 'animales_data') and animal_id in self.animales_data:
            a = self.animales_data[animal_id]
            info_text = f"""
                <b>{a.nombre}</b><br>
                <span style='color: #64748B;'>Código: {a.codigo} | Especie: {a.especie}</span><br>
                <span style='color: #64748B;'>Propietario: {a.propietario or 'No registrado'}</span>
            """
            self.info_paciente.setText(info_text)
            self.info_paciente.setStyleSheet("""
                color: #1E293B;
                font-size: 12px;
                padding: 12px;
                background-color: #E8F4F8;
                border-radius: 8px;
                margin-top: 8px;
                border-left: 4px solid #3BADE5;
            """)
        else:
            self.info_paciente.setText(
                "Seleccione un paciente para ver sus datos")
            self.info_paciente.setStyleSheet("""
                color: #64748B;
                font-size: 12px;
                padding: 12px;
                background-color: #F8FAFC;
                border-radius: 8px;
                margin-top: 8px;
            """)

    def _abrir_nuevo_paciente(self):
        """Abre diálogo para crear nuevo paciente"""
        dialog = NuevoAnimalDialog(
            parent=self.parent(),
            on_save=self._cargar_animales)
        dialog.exec()

    @ErrorHandler.handle_exception
    def _guardar(self):
        """Valida y guarda la recepción"""
        animal_id = self.animal_combo.currentData()
        motivo = self.motivo_combo.currentText().strip()

        errores = []

        if not animal_id:
            errores.append("• Debe seleccionar un paciente")
            self.animal_combo.setStyleSheet("""
                QComboBox {
                    border: 2px solid #EF4444;
                    border-radius: 8px;
                    padding: 10px 12px;
                    background-color: #FEF2F2;
                }
            """)

        if not motivo:
            errores.append("• El motivo de consulta es obligatorio")
            self.motivo_combo.setStyleSheet("""
                QComboBox {
                    border: 2px solid #EF4444;
                    border-radius: 8px;
                    padding: 10px 12px;
                    background-color: #FEF2F2;
                }
            """)

        if errores:
            show_warning(
                self,
                "Campos Requeridos",
                "Por favor complete los siguientes campos:\n\n" +
                "\n".join(errores))
            return

        data = {
            'animal_id': animal_id,
            'motivo': motivo,
            'veterinario': self.veterinario.text().strip(),
            'observaciones': self.observaciones.toPlainText().strip(),
            'fecha_hora': self.fecha_hora.dateTime().toString("yyyy-MM-dd HH:mm")}

        self.service.registrar_recepcion(data)
        QMessageBox.information(
            self, "Éxito", "Recepción registrada correctamente")

        if self.on_save:
            self.on_save()
        self.accept()


class EstadoRecepcionDialog(BaseDialog):
    """Diálogo para cambiar estado de recepción"""

    def __init__(self, parent=None, recepcion_id=None, on_save=None):
        super().__init__(parent, "Cambiar Estado de Recepción", 400, 220)
        self.recepcion_id = recepcion_id
        self.on_save = on_save
        self.service = RecepcionService()
        self._build()

    def _build(self):
        layout = QFormLayout()
        layout.setSpacing(14)

        self.estado_combo = QComboBox()
        self.estado_combo.addItems(ESTADOS_RECEPCION)
        self.estado_combo.setMinimumHeight(42)
        self.estado_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px 12px;
                padding-right: 30px;
                background-color: white;
                font-size: 13px;
            }
            QComboBox:focus {
                border: 2px solid #3BADE5;
                background-color: #F0F9FF;
            }
        """)
        layout.addRow("Nuevo Estado:", self.estado_combo)

        self.content_layout.addLayout(layout)
        self.set_save_callback(self._guardar)

    @ErrorHandler.handle_exception
    def _guardar(self):
        nuevo_estado = self.estado_combo.currentText()
        self.service.actualizar_estado(self.recepcion_id, nuevo_estado)
        QMessageBox.information(
            self, "Éxito", "Estado actualizado correctamente")
        if self.on_save:
            self.on_save()
        self.accept()


class DetalleRecepcionDialog(BaseDialog):
    """Diálogo para ver detalles de recepción"""

    def __init__(self, parent=None, recepcion_id=None):
        super().__init__(parent, "Detalles de la Recepción", 500, 420)
        self.recepcion_id = recepcion_id
        self.service = RecepcionService()
        self._build()

    def _build(self):
        try:
            recepcion = self.service.obtener_recepcion(self.recepcion_id)

            # Card de información
            info_group = QGroupBox("📋  Información de la Recepción")
            info_group.setStyleSheet("""
                QGroupBox {{
                    font-weight: bold;
                    border: 2px solid #E2E8F0;
                    border-radius: 12px;
                    margin-top: 16px;
                    padding: 16px;
                    background-color: white;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 4px 12px;
                    color: #1E3A5F;
                    background-color: #E8F4F8;
                    border-radius: 6px;
                }}
            """)
            layout = QFormLayout(info_group)
            layout.setSpacing(12)

            layout.addRow("Código:", QLabel(
                f"<b style='font-size:14px;'>{recepcion.codigo}</b>"))
            layout.addRow("Paciente:", QLabel(
                f"{recepcion.animal_nombre} ({recepcion.animal_codigo})"))
            layout.addRow("Motivo:", QLabel(recepcion.motivo))

            # Estado con color
            estado_label = QLabel(recepcion.estado)
            estado_colors = {
                'En espera': '#F59E0B',
                'En consulta': '#3BADE5',
                'Finalizado': '#22C55E',
                'Cancelado': '#EF4444'
            }
            color = estado_colors.get(recepcion.estado, '#64748B')
            estado_label.setStyleSheet(f"""
                color: {color};
                font-weight: bold;
                padding: 4px 12px;
                background-color: {color}15;
                border-radius: 6px;
                display: inline-block;
            """)
            layout.addRow("Estado:", estado_label)

            layout.addRow("Fecha/Hora:", QLabel(recepcion.fecha_hora))
            layout.addRow(
                "Veterinario:", QLabel(
                    recepcion.veterinario or 'No asignado'))

            if recepcion.observaciones:
                obs_label = QLabel(recepcion.observaciones)
                obs_label.setWordWrap(True)
                obs_label.setStyleSheet("color: #475569; padding-top: 8px;")
                layout.addRow("Observaciones:", obs_label)

            self.content_layout.addWidget(info_group)

        except Exception as e:
            self.content_layout.addWidget(
                QLabel(f"Error cargando detalles: {e}"))

        self.btn_guardar.setText("✅ Cerrar")
        style_button(self.btn_guardar, 'secondary')

        self.set_save_callback(self.accept)

        self.btn_cancelar.hide()
