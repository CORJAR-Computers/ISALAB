"""
Sistema de estilos centralizado para IsaLab
Elimina la duplicación de CSS inline en todos los diálogos
"""

from PySide6.QtCore import Qt
from config import QT_STYLES


class IsaStyles:
    """Clase centralizada de estilos para mantener consistencia visual"""

    # ── Paleta de colores extendida - Healthcare Professional WCAG ──────────
    PRIMARY = QT_STYLES['primary']      # Cyan-700 #0E7490
    SECONDARY = QT_STYLES['secondary']  # Dark Teal #134E4A
    ACCENT = QT_STYLES['accent']     # Green-700 #15803D
    SUCCESS = QT_STYLES['success']   # Green-700 #15803D
    WARNING = QT_STYLES['warning']    # Amber-700 #B45309
    DANGER = QT_STYLES['danger']     # Red-700 #B91C1C
    GRAY = QT_STYLES['gray']          # Slate-600 #475569
    DARK = QT_STYLES['dark']         # Slate-900 #0F172A
    LIGHT_BG = QT_STYLES['light_bg']  # Mint White #F0FDFA
    BORDER = '#CBD5E1'

    # ── Dimensiones estándar ────────────────────────────────────────────
    INPUT_HEIGHT = 32  # Altura consistente para todos los inputs
    BUTTON_HEIGHT = 34  # Altura de botones principales
    SMALL_BUTTON_HEIGHT = 32  # Botones secundarios
    SPACING_SMALL = 8
    SPACING_MEDIUM = 12
    SPACING_LARGE = 20

    # ── Estilos base para QSS ───────────────────────────────────────────
    @classmethod
    def get_input_style(cls, has_error=False, is_disabled=False) -> str:
        """Estilo base para inputs con estados visuales"""
        border_color = cls.DANGER if has_error else cls.BORDER
        bg_color = '#F1F5F9' if is_disabled else 'white'

        return f"""
            QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {{
                min-height: {cls.INPUT_HEIGHT}px;
                max-height: {cls.INPUT_HEIGHT + 4}px;
                padding: 6px 10px;
                border: 2px solid {border_color};
                border-radius: 6px;
                background-color: {bg_color};
                font-size: 13px;
                color: {cls.DARK};
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 2px solid {cls.PRIMARY};
                background-color: #F0F9FF;
            }}
            /* 👇 FORZAR COLOR OSCURO EN CAMPOS DESHABILITADOS 👇 */
            QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled {{
                background-color: #F1F5F9;
                color: {cls.DARK};
                border-color: #E2E8F0;
            }}
            /* 👇 FORZAR COLOR OSCURO EN CAMPOS DE SOLO LECTURA 👇 */
            QLineEdit[readOnly="true"], QTextEdit[readOnly="true"] {{
                background-color: #F1F5F9;
                color: {cls.DARK};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {cls.GRAY};
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {cls.BORDER};
                border-radius: 4px;
                background-color: white;
                selection-background-color: {cls.PRIMARY};
                selection-color: white;
                padding: 4px;
            }}
        """

    @classmethod
    def get_textarea_style(cls, has_error=False) -> str:
        """Estilo para áreas de texto"""
        border_color = cls.DANGER if has_error else cls.BORDER
        return f"""
                QTextEdit {{
                    border: 2px solid {border_color};
                    border-radius: 6px;
                    padding: 8px;
                    background-color: white;  /* <--- CORREGIDO DE 'black' A 'white' */
                    font-size: 13px;
                    color: {cls.DARK};
                    line-height: 1.4;
                }}
                QTextEdit:focus {{
                    border: 2px solid {cls.PRIMARY};
                    background-color: #F0F9FF;
                }}
            """

    @classmethod
    def get_button_style(cls, variant='primary', size='normal') -> str:
        """Estilos de botones con variantes"""
        styles = {
            'primary': {
                'bg': cls.ACCENT,
                'hover': '#256B5E',
                'text': 'white'
            },
            'secondary': {
                'bg': cls.PRIMARY,
                'hover': cls.SECONDARY,
                'text': 'white'
            },
            'danger': {
                'bg': cls.DANGER,
                'hover': '#B91C1C',
                'text': 'white'
            },
            'ghost': {
                'bg': 'transparent',
                'hover': '#F1F5F9',
                'text': cls.DARK,
                'border': cls.BORDER
            }
        }

        height = cls.BUTTON_HEIGHT if size == 'normal' else cls.SMALL_BUTTON_HEIGHT
        style_config = styles.get(variant, styles['primary'])

        border_part = f"border: 1px solid {
            style_config.get(
                'border',
                'none')};" if 'border' in style_config else "border: none;"

        return f"""
            QPushButton {{
                background-color: {style_config['bg']};
                color: {style_config['text']};
                {border_part}
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: {13 if size == 'normal' else 12}px;
                min-height: {height}px;
            }}
            QPushButton:hover {{
                background-color: {style_config['hover']};
            }}
            QPushButton:pressed {{
                background-color: {cls.DARK};
                padding-top: 10px;
                padding-bottom: 6px;
            }}
            QPushButton:disabled {{
                background-color: #CBD5E1;
                color: #94A3B8;
            }}
        """

    @classmethod
    def get_group_style(cls, accent_color=None) -> str:
        """Estilo para QGroupBox con acento de color opcional"""
        color = accent_color or cls.PRIMARY
        return f"""
                QGroupBox {{
                    font-weight: bold;
                    border: 1px solid {cls.BORDER};
                    border-radius: 8px;
                    margin-top: 16px;
                    padding-top: 16px;
                    background-color: white;
                    color: {cls.DARK};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 4px 12px;
                    color: white;
                    background-color: {color};
                    border-radius: 4px;
                    font-size: 12px;
                }}
                /* 👇 ESTA ES LA MAGIA PARA LOS TEXTOS (LABELS) 👇 */
                QGroupBox QLabel {{
                    color: {cls.DARK};
                }}
            """

    @classmethod
    def get_card_style(cls) -> str:
        """Estilo para tarjetas/contenedores"""
        return f"""
                QFrame {{
                    background-color: white;
                    color: {cls.DARK};  /* <--- ESTA LÍNEA SOLUCIONA EL TEXTO BLANCO */
                    border: 1px solid {cls.BORDER};
                    border-radius: 8px;
                    padding: 16px;
                }}
            """

    @classmethod
    def get_error_indicator(cls) -> str:
        """Estilo para indicadores de error en campos"""
        return f"""
            color: {cls.DANGER};
            font-size: 11px;
            font-weight: bold;
            padding-left: 4px;
        """

    @classmethod
    def get_tooltip_style(cls) -> str:
        """Estilo para tooltips"""
        return f"""
            QToolTip {{
                background-color: {cls.DARK};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }}
        """


# ── Funciones helper para aplicar estilos rápidamente ───────────────────

def style_input(widget, has_error=False, placeholder=""):
    """Aplica estilo consistente a un input"""
    from PySide6.QtWidgets import QLineEdit

    widget.setStyleSheet(IsaStyles.get_input_style(has_error=has_error))
    if placeholder and isinstance(widget, QLineEdit):
        widget.setPlaceholderText(placeholder)
    widget.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
    widget.setMaximumHeight(IsaStyles.INPUT_HEIGHT + 4)


def style_textarea(widget, has_error=False, max_height=100):
    """Aplica estilo consistente a un QTextEdit"""
    widget.setStyleSheet(IsaStyles.get_textarea_style(has_error=has_error))
    widget.setMaximumHeight(max_height)


def style_button(widget, variant='primary', tooltip=""):
    """Aplica estilo de botón con tooltip opcional"""
    widget.setStyleSheet(IsaStyles.get_button_style(variant=variant))
    widget.setCursor(Qt.PointingHandCursor)
    widget.setMinimumHeight(IsaStyles.BUTTON_HEIGHT)
    if tooltip:
        widget.setToolTip(tooltip)


def style_group(widget, title_color=None):
    """Aplica estilo a un QGroupBox"""
    widget.setStyleSheet(IsaStyles.get_group_style(accent_color=title_color))
