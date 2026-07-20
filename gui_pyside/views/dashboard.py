# gui_pyside/views/dashboard.py
"""Vista de Dashboard para PySide6"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QFrame)
from PySide6.QtCore import Qt

from config import get_theme_colors, CURRENT_THEME, toggle_theme, generate_qt_stylesheet
from gui_pyside.components.components import ErrorHandler
from PySide6.QtCore import Signal


class DashboardView(QWidget):
    """Vista principal del dashboard"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_btn = None
        self.current_theme = None
        self.setObjectName("dashboardView")
        self._build_layout()

    def _get_theme(self):
        return get_theme_colors()

    def _update_theme_btn(self):
        """Actualiza el texto del botón según el tema actual"""
        if self.theme_btn:
            icon = "☀️" if CURRENT_THEME == "dark" else "🌙"
            self.theme_btn.setText(
                f"{icon} Modo {
                    'Claro' if CURRENT_THEME == 'dark' else 'Oscuro'}")

    def rebuild_layout(self):
        """Reconstruye el layout completamente para aplicar nuevo tema"""
        # Save current theme
        self.current_theme = CURRENT_THEME

        # Clear existing layout
        if self.layout():
            QWidget().setLayout(self.layout())

        # Rebuild with new theme colors
        self._build_layout()

    def _toggle_theme(self):
        """Cambia entre temas light/dark"""

        # Toggle theme
        new_theme = toggle_theme()

        # Rebuild entire layout for fresh styles (uses current theme)
        self.rebuild_layout()

        # Apply global stylesheet to app
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            new_stylesheet = generate_qt_stylesheet(new_theme)
            app.setStyleSheet(new_stylesheet)

        # Emit signal for other views
        self.theme_changed.emit()

    # Señal para notificar a las vistas del cambio de tema
    theme_changed = Signal()

    def _build_layout(self):
        """Construye el layout del dashboard"""
        theme = self._get_theme()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header con toggle de tema
        header_layout = QHBoxLayout()

        header = QLabel("Panel de Control")
        header.setAlignment(Qt.AlignLeft)
        header.setStyleSheet(f"""
            QLabel {{
                color: {theme['secondary']};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(header)

        # Botón de cambio de tema
        self.theme_btn = QPushButton(
            f"{
                '☀️' if CURRENT_THEME == 'light' else '🌙'} {
                'Oscuro' if CURRENT_THEME == 'light' else 'Claro'}")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['secondary']};
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {theme['primary']};
            }}
        """)
        self.theme_btn.clicked.connect(self._toggle_theme)
        header_layout.addStretch()
        header_layout.addWidget(self.theme_btn)

        layout.addLayout(header_layout)

        # Cards de estadísticas
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        card1 = self._create_stat_card(
            "Total Pacientes", "0", theme['primary'])
        cards_layout.addWidget(card1)

        card2 = self._create_stat_card(
            "Muestras Pendientes", "0", theme['warning'])
        cards_layout.addWidget(card2)

        card3 = self._create_stat_card("Consultas Hoy", "0", theme['accent'])
        cards_layout.addWidget(card3)

        card4 = self._create_stat_card("Urgentes", "0", theme['danger'])
        cards_layout.addWidget(card4)

        layout.addLayout(cards_layout)

        # Mensaje de bienvenida
        welcome = QLabel(
            "¡Bienvenido a IsaLab! Seleccione una opción del menú lateral.")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet(f"""
            QLabel {{
                color: {theme['gray']};
                font-size: 16px;
                padding: 40px;
                background-color: {theme['white']};
                border-radius: 8px;
                border: 1px solid {theme['border']};
            }}
        """)
        layout.addWidget(welcome)

        layout.addStretch()

    def _create_stat_card(self, title, value, color):
        """Crea una tarjeta de estadística"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 15px;
            }}
        """)

        layout = QVBoxLayout(card)

        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: bold;
            }
        """)
        layout.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
            }
        """)
        layout.addWidget(title_label)

        return card

    @ErrorHandler.handle_exception
    def refresh(self):
        """Refresca los datos del dashboard"""
        # Aquí cargarías datos reales desde los servicios
