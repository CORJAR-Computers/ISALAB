# gui_pyside/dialogs/base_dialog.py
"""Diálogo base con ventana moderna, esquinas redondeadas y barra personalizada"""

from typing import Callable, Optional
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QGraphicsDropShadowEffect,
                               QMainWindow)
from PySide6.QtGui import QCloseEvent
from PySide6.QtCore import Qt, QPoint

from config import QT_STYLES, ICONS


class BaseDialog(QDialog):
    """Diálogo base con esquinas redondeadas, sombra y barra de título personalizada"""

    def __init__(
            self,
            parent: Optional[QMainWindow] = None,
            title: str = "",
            width: int = 600,
            height: int = 450) -> None:
        super().__init__(parent)

        # --- Configuración de la ventana sin marco ---
        # Dialog: ventana de diálogo (no siempre encima)
        # FramelessWindowHint: sin bordes del sistema operativo
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(width, height)
        # Limpiar automáticamente al cerrar
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.drag_position = QPoint()  # Para arrastrar la ventana

        # --- Layout principal transparente ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Contenedor principal con fondo blanco y esquinas redondeadas ---
        self.container = QFrame()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QFrame#container {{
                background-color: white;
                border-radius: 12px;
            }}
        """)
        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(Qt.gray)
        self.container.setGraphicsEffect(shadow)

        # Layout interno del contenedor
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # --- Barra de título personalizada ---
        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        title_bar.setStyleSheet(f"""
            QFrame#titleBar {{
                background-color: {QT_STYLES['primary']};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                min-height: 44px;
            }}
        """)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(15, 0, 15, 0)

        # Título de la barra
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: white;
            font-size: 14px;
            font-weight: bold;
            background-color: transparent;
        """)
        title_bar_layout.addWidget(title_label)

        # Espaciador para empujar los botones a la derecha
        title_bar_layout.addStretch()

        # Botón de cerrar
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 18px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #E81123;
                border-radius: 4px;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        title_bar_layout.addWidget(self.close_btn)

        # Hacer que la barra de título sea arrastrable
        title_bar.mousePressEvent = self.mousePressEvent
        title_bar.mouseMoveEvent = self.mouseMoveEvent

        container_layout.addWidget(title_bar)

        # --- Contenido (lo usarán las subclases) ---
        self.content_widget = QFrame()
        self.content_widget.setObjectName("dialogContent")
        self.content_widget.setStyleSheet("""
            QFrame#dialogContent {
                background-color: white;
                padding: 0px;
            }
        """)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(16)

        container_layout.addWidget(self.content_widget, 1)

        # --- Footer con botones (creados siempre) ---
        self.footer = QFrame()
        self.footer.setFixedHeight(60)
        self.footer.setStyleSheet(f"""
            QFrame {{
                background-color: {QT_STYLES['primary']};
                border-top: 1px solid {QT_STYLES['border']};
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
        """)
        self.footer_layout = QHBoxLayout(self.footer)
        self.footer_layout.setContentsMargins(20, 0, 20, 0)

        self.footer_layout.addStretch()

        self.btn_cancelar = QPushButton(f"{ICONS.get('cancel', '❌')} Cancelar")
        self.btn_cancelar.setMinimumHeight(38)
        self.btn_cancelar.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['gray']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {QT_STYLES['secondary']};
            }}
        """)
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_guardar = QPushButton(f"{ICONS.get('save', '💾')} Guardar")
        self.btn_guardar.setMinimumHeight(38)
        self.btn_guardar.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #256B5E;
            }}
        """)

        self.footer_layout.addWidget(self.btn_cancelar)
        self.footer_layout.addWidget(self.btn_guardar)

        container_layout.addWidget(self.footer)

        # Agregar el contenedor principal al layout
        main_layout.addWidget(self.container)

        # Centrar en pantalla (después de construir)
        self._center()

        # Guardar callback para el botón guardar (inicialmente None)
        self._save_callback = None

        # --- OPCIÓN NUCLEAR CONTRA EL MODO OSCURO DE WINDOWS ---
        from gui_pyside.styles import IsaStyles

        # Le aplicamos la regla a la ventana completa, forzando a TODOS los
        # elementos internos
        estilo_actual = self.styleSheet()
        self.setStyleSheet(estilo_actual + f"""
                    /* Forzar todos los labels a color oscuro */
                    QLabel {{
                        color: {IsaStyles.DARK} !important;
                    }}
                    /* Forzar las cajas deshabilitadas o de lectura */
                    QLineEdit:disabled, QLineEdit[readOnly="true"],
                    QTextEdit:disabled, QTextEdit[readOnly="true"],
                    QComboBox:disabled {{
                        color: {IsaStyles.DARK} !important;
                        background-color: #F1F5F9 !important;
                    }}
                """)

    def set_save_callback(self, callback: Callable[[], None]) -> None:
        """Asigna la función que se ejecutará al hacer clic en Guardar"""
        # Si ya hay un callback guardado, desconectar esa función específica
        if self._save_callback is not None:
            try:
                self.btn_guardar.clicked.disconnect(self._save_callback)
            except (RuntimeError, TypeError):
                # Si no estaba conectada o error de tipo, ignoramos
                pass
        self._save_callback = callback
        self.btn_guardar.clicked.connect(callback)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Asegurar cierre limpio del diálogo"""
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        event.accept()

    # --- Métodos para arrastrar la ventana ---
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - \
                self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def exec(self) -> int:
        """
        Ejecuta el diálogo de manera modal.
        exec() ya es bloqueante por naturaleza de Qt.
        """
        # Centrar respecto al padre si existe
        if self.parent():
            self._center()

        # Asegurar foco al abrir
        self.raise_()
        self.activateWindow()

        return super().exec()

    def show_dialog(self):
        """
        Alternativa non-blocking para mostrar el diálogo.
        Útil cuando no necesitas esperar el resultado.
        """
        if self.parent():
            self._center()

        self.raise_()
        self.activateWindow()
        self.show()

    def _center(self):
        """Centrar el diálogo respecto al padre"""
        if self.parent():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)

    # Métodos vacíos para compatibilidad con código antiguo (por si se llaman)
    def _crear_header(self, title):
        pass

    def _crear_footer(self):
        pass
