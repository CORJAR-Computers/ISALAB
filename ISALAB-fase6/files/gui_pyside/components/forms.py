"""
Componentes de formulario reutilizables para IsaLab
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                               QLineEdit, QComboBox, QTextEdit, QDateEdit,
                               QSpinBox, QDoubleSpinBox, QCheckBox, QFrame)
from PySide6.QtCore import Qt, Signal

from gui_pyside.styles import IsaStyles, style_input, style_textarea

# Fase 6 (G-M7): importamos ``re`` solo cuando se necesita (lazy) para
# no penalizar el import del módulo si nadie usa regex. En la práctica
# es un módulo stdlib y el costo es mínimo, pero por consistencia con
# el resto del códigobase:
import re as _re


class FormField(QWidget):
    """Campo de formulario con label, input e indicador de error"""

    value_changed = Signal()
    validation_error = Signal(str)

    def __init__(self, label_text, widget_type='lineedit', required=False,
                 parent=None, **kwargs):
        super().__init__(parent)

        self.required = required
        self.widget_type = widget_type
        # Fase 6 (G-M7): constraints de validación adicionales.
        # Todos son opcionales (default ``None`` = no se aplica esa
        # validación) para mantener compatibilidad con callers
        # existentes que solo pasan ``required=True``.
        #
        # - ``max_length`` / ``min_length``: aplican solo a widgets de
        #   texto (lineedit, textarea). ``min_length`` cuenta después
        #   de ``strip()`` para no confundir con espacios.
        # - ``regex``: string compilado con ``re.compile`` o string
        #   crudo. Se aplica al ``get_value()`` con ``re.search``
        #   (más permisivo que ``fullmatch``).
        # - ``validator``: callable ``(value) -> Optional[str]``.
        #   Retorna ``None`` si válido, o un mensaje de error si no.
        #   Útil para validaciones de negocio (ej: "que exista en
        #   tabla X").
        self.max_length = kwargs.pop('max_length', None)
        self.min_length = kwargs.pop('min_length', None)
        self.regex = kwargs.pop('regex', None)
        self.validator = kwargs.pop('validator', None)
        # Pre-compilar regex si vino como string (más eficiente en
        # llamadas repetidas a ``validate``).
        if isinstance(self.regex, str):
            self.regex = _re.compile(self.regex)
        # Si ``max_length`` está seteado, también limitamos el input
        # en el widget (no solo validación post-hoc).
        self._setup_ui(label_text, **kwargs)
        if self.max_length is not None and self.widget_type == 'lineedit':
            try:
                self.input.setMaxLength(self.max_length)
            except Exception:
                # ``setMaxLength`` solo existe en QLineEdit/QTextEdit.
                pass

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
        """Valida el campo aplicando todos los constraints configurados.

        Fase 6 (G-M7): antes solo verificaba ``required``. Ahora corre
        una cadena de checks en orden: required → min_length →
        max_length → regex → validator (callable). Si cualquiera falla,
        setea el primer error encontrado y retorna ``False``.

        Returns:
            bool: ``True`` si el campo pasa todas las validaciones.
        """
        value = self.get_value()
        # ``get_value`` para checkbox retorna ``bool``, para spinbox
        # retorna número, etc. Solo aplicamos length/regex a strings.
        is_text = isinstance(value, str)

        # 1. Required (aplica a cualquier tipo).
        if self.required:
            # Para texto: vacío después de strip().
            # Para número: 0 se considera válido (no es "ausente").
            # Para checkbox: False se considera "no llenado" si required.
            if is_text:
                if not value.strip():
                    self.set_error("Este campo es obligatorio")
                    return False
            elif value in (None, False):
                self.set_error("Este campo es obligatorio")
                return False

        # 2. min_length (solo texto, después del strip).
        if is_text and self.min_length is not None:
            if len(value.strip()) < self.min_length:
                self.set_error(
                    f"Mínimo {self.min_length} caracteres")
                return False

        # 3. max_length (solo texto).
        if is_text and self.max_length is not None:
            if len(value) > self.max_length:
                self.set_error(
                    f"Máximo {self.max_length} caracteres")
                return False

        # 4. regex (solo texto, no vacío — required ya cubrió vacío).
        if is_text and value and self.regex is not None:
            # ``regex`` puede ser string o compiled pattern. Pre-compilamos
            # en __init__ si vino como string.
            pattern = self.regex
            if isinstance(pattern, str):
                pattern = _re.compile(pattern)
            if not pattern.search(value):
                self.set_error("Formato no válido")
                return False

        # 5. validator callable (para validaciones de negocio).
        if self.validator is not None:
            try:
                err = self.validator(value)
            except Exception as e:
                # Si el validator levanta excepción, la tratamos como
                # error de validación con el mensaje de la excepción.
                err = str(e)
            if err:
                self.set_error(err)
                return False

        # Todos los checks pasaron.
        self.clear_error()
        return True

    def get_errors(self):
        """Retorna lista de errores de validación sin setear UI.

        Fase 6 (G-M7): utilidad para validators que quieren inspeccionar
        todos los errores de un form sin disparar side-effects visuales.
        """
        value = self.get_value()
        is_text = isinstance(value, str)
        errors = []
        if self.required:
            if is_text and not value.strip():
                errors.append("Este campo es obligatorio")
            elif value in (None, False):
                errors.append("Este campo es obligatorio")
        if is_text and self.min_length is not None \
                and len(value.strip()) < self.min_length:
            errors.append(f"Mínimo {self.min_length} caracteres")
        if is_text and self.max_length is not None \
                and len(value) > self.max_length:
            errors.append(f"Máximo {self.max_length} caracteres")
        if is_text and value and self.regex is not None:
            pattern = self.regex
            if isinstance(pattern, str):
                pattern = _re.compile(pattern)
            if not pattern.search(value):
                errors.append("Formato no válido")
        if self.validator is not None:
            try:
                err = self.validator(value)
            except Exception as e:
                err = str(e)
            if err:
                errors.append(err)
        return errors


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
        # Fase 6 (G-L6): antes hacía ``self.resize(self.parent().size())``
        # sin chequear si ``parent()`` es ``None``. Si se llamaba
        # ``show()`` sobre un overlay sin parent (por ejemplo, en tests
        # unitarios o si el caller olvidó pasar ``parent=``), rompía
        # con ``AttributeError: 'NoneType' object has no attribute
        # 'size'``. Ahora guardamos contra ``None`` y, si no hay
        # parent, simplemente no resizeamos (el overlay queda con su
        # tamaño por defecto — feo pero no crashea).
        parent = self.parent()
        if parent is not None:
            self.resize(parent.size())
        super().showEvent(event)

    def start(self, message=None):
        if message:
            self.message.setText(message)
        self.show()
        self.raise_()

    def stop(self):
        self.hide()
