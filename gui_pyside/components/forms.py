"""
Componentes de formulario reutilizables para IsaLab
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                               QLineEdit, QComboBox, QTextEdit, QDateEdit,
                               QSpinBox, QDoubleSpinBox, QCheckBox, QFrame)
from PySide6.QtCore import Qt, Signal

from gui_pyside.styles import IsaStyles, style_input, style_textarea


class FormField(QWidget):
    """Campo de formulario con label, input e indicador de error"""

    value_changed = Signal()
    validation_error = Signal(str)

    def __init__(self, label_text, widget_type='lineedit', required=False,
                 parent=None, **kwargs):
        super().__init__(parent)

        self.required = required
        self.widget_type = widget_type
        self._setup_ui(label_text, **kwargs)

    def _setup_ui(self, label_text, **kwargs):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Label con indicador de obligatorio
        label_text_full = f"{label_text} {'*' if self.required else ''}"
        self.label = QLabel(label_text_full)
        self.label.setStyleSheet(f"""
            color: {IsaStyles.DARK};
            font-weight: bold;
            font-size: 12px;
        """)
        layout.addWidget(self.label)

        # Widget según tipo
        if self.widget_type == 'lineedit':
            self.input = QLineEdit()
            if 'placeholder' in kwargs:
                self.input.setPlaceholderText(kwargs['placeholder'])
        elif self.widget_type == 'combo':
            self.input = QComboBox()
            if 'items' in kwargs:
                self.input.addItems(kwargs['items'])
            if 'editable' in kwargs:
                self.input.setEditable(kwargs['editable'])
        elif self.widget_type == 'textarea':
            self.input = QTextEdit()
            self.input.setMaximumHeight(kwargs.get('max_height', 80))
        elif self.widget_type == 'date':
            self.input = QDateEdit()
            self.input.setCalendarPopup(True)
        elif self.widget_type == 'spin':
            self.input = QSpinBox()
            if 'suffix' in kwargs:
                self.input.setSuffix(kwargs['suffix'])
            if 'range' in kwargs:
                self.input.setRange(*kwargs['range'])
        elif self.widget_type == 'doublespin':
            self.input = QDoubleSpinBox()
            if 'suffix' in kwargs:
                self.input.setSuffix(kwargs['suffix'])
            if 'decimals' in kwargs:
                self.input.setDecimals(kwargs['decimals'])
        elif self.widget_type == 'check':
            self.input = QCheckBox(kwargs.get('check_text', ''))

        # Aplicar estilo base
        if self.widget_type in [
            'lineedit',
            'combo',
            'date',
            'spin',
                'doublespin']:
            style_input(self.input)
        elif self.widget_type == 'textarea':
            style_textarea(self.input)

        # Conectar señales para validación en tiempo real
        if hasattr(self.input, 'textChanged'):
            self.input.textChanged.connect(self._on_value_changed)
        elif hasattr(self.input, 'currentTextChanged'):
            self.input.currentTextChanged.connect(self._on_value_changed)

        layout.addWidget(self.input)

        # Label de error (inicialmente oculto)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(
            f"color: {IsaStyles.DANGER}; font-size: 11px;")
        self.error_label.hide()
        layout.addWidget(self.error_label)

    def _on_value_changed(self):
        self.value_changed.emit()
        self.clear_error()

    def set_error(self, message):
        """Muestra error visual y mensaje"""
        self.error_label.setText(f"⚠ {message}")
        self.error_label.show()
        style_input(self.input, has_error=True)

    def clear_error(self):
        """Limpia indicador de error"""
        self.error_label.hide()
        style_input(self.input, has_error=False)

    def get_value(self):
        """Obtiene el valor según tipo de widget"""
        if self.widget_type == 'lineedit':
            return self.input.text().strip()
        elif self.widget_type == 'combo':
            return self.input.currentText()
        elif self.widget_type == 'textarea':
            return self.input.toPlainText().strip()
        elif self.widget_type == 'date':
            return self.input.date().toString("yyyy-MM-dd")
        elif self.widget_type in ['spin', 'doublespin']:
            return self.input.value()
        elif self.widget_type == 'check':
            return self.input.isChecked()
        return None

    def set_value(self, value):
        """Establece valor según tipo"""
        if self.widget_type == 'lineedit':
            self.input.setText(str(value) if value else "")
        elif self.widget_type == 'combo':
            idx = self.input.findText(str(value))
            if idx >= 0:
                self.input.setCurrentIndex(idx)
        elif self.widget_type == 'textarea':
            self.input.setPlainText(str(value) if value else "")
        elif self.widget_type in ['spin', 'doublespin']:
            self.input.setValue(value or 0)

    def validate(self):
        """Valida campo obligatorio"""
        if self.required and not self.get_value():
            self.set_error("Este campo es obligatorio")
            return False
        return True


class FormRow(QWidget):
    """Fila de formulario con múltiples campos en horizontal"""

    def __init__(self, fields, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        for field in fields:
            layout.addWidget(field, 1)

        self.fields = fields

    def validate(self):
        """Valida todos los campos de la fila"""
        valid = True
        for field in self.fields:
            if not field.validate():
                valid = False
        return valid


class LoadingOverlay(QFrame):
    """Overlay de carga para operaciones largas"""

    def __init__(self, parent=None, message="Procesando..."):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.85);
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Spinner animado (usando label con emoji por simplicidad)
        self.spinner = QLabel("⏳")
        self.spinner.setStyleSheet("font-size: 48px;")
        self.spinner.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.spinner)

        self.message = QLabel(message)
        self.message.setStyleSheet(f"""
            color: {IsaStyles.SECONDARY};
            font-size: 14px;
            font-weight: bold;
        """)
        self.message.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message)

        self.hide()

    def showEvent(self, event):
        self.resize(self.parent().size())
        super().showEvent(event)

    def start(self, message=None):
        if message:
            self.message.setText(message)
        self.show()
        self.raise_()

    def stop(self):
        self.hide()
