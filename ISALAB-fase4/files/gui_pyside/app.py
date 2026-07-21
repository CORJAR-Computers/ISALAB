# gui_pyside/app.py
"""Aplicación principal IsaLab con PySide6 - FLUJO CORREGIDO Y SIDEBAR CON SCROLL"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel,
                               QFrame, QStackedWidget, QMessageBox,
                               QScrollArea)
from PySide6.QtCore import Qt

from config import QT_STYLES, GLOBAL_STYLESHEET
from gui_pyside.views.dashboard import DashboardView
from gui_pyside.views.recepcion import RecepcionView
from gui_pyside.views.animales import AnimalesView
from gui_pyside.views.historia import HistoriaView
from gui_pyside.views.consultas import ConsultasView
from gui_pyside.views.cirugias import CirugiasView
from gui_pyside.views.vacunacion import VacunacionView
from gui_pyside.views.muestras import MuestrasView
from gui_pyside.views.reportes import ReportesView
from gui_pyside.utils.window_manager import WindowManager


class SidebarButton(QPushButton):
    """Botón personalizado para la barra lateral"""

    def __init__(self, text, icon_text="", parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(45)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #CBD5E1;
                text-align: left;
                padding-left: 20px;
                border: none;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #2D4A6B;
                color: white;
            }}
            QPushButton:checked {{
                background-color: {QT_STYLES['secondary']};
                color: white;
                border-left: 4px solid {QT_STYLES['primary']};
            }}
        """)


class LabVetApp(QMainWindow):
    def __init__(self, usuario: dict = None):
        super().__init__()
        self.usuario = usuario or {}
        from utils.logger import setup_logger
        logger = setup_logger()
        logger.info(f"LabVetApp inicializado con usuario: {self.usuario}")
        self.setWindowTitle("IsaLab - Centro Diagnóstico Veterinario")
        self.setMinimumSize(1200, 700)
        self.setStyleSheet(GLOBAL_STYLESHEET)
        self._center_window()
        self.views = {}
        self.active_button = None

        # Registrar esta ventana como la principal en el WindowManager
        WindowManager.set_main_window(self)

        self._build_layout()
        self._show_dashboard()

    def _center_window(self):
        self.resize(1200, 768)
        screen_geo = self.screen().availableGeometry()
        frame_geo = self.frameGeometry()
        center_point = screen_geo.center()
        frame_geo.moveCenter(center_point)
        self.move(frame_geo.topLeft())

    def _build_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- SIDEBAR ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet(
            f"QFrame {{ background-color: {QT_STYLES['secondary']}; border: none; }}"
        )
        sidebar_main_layout = QVBoxLayout(self.sidebar)
        sidebar_main_layout.setContentsMargins(0, 20, 0, 10)
        sidebar_main_layout.setSpacing(0)

        # Logo (Tu código original perfecto)
        try:
            from PySide6.QtGui import QPixmap
            import os
            from config import BASE_DIR
            # Fase 4 (C3): el archivo real en el repositorio es
            # `Logo_Sidebar.png` (PascalCase). En filesystems
            # case-sensitive (Linux/macOS) la referencia lowercase
            # `logo_sidebar.png` no resolvía y el logo caía al fallback
            # de texto "IsaLab". Usamos el nombre exacto del asset.
            logo_path = os.path.join(BASE_DIR, "assets", "Logo_Sidebar.png")
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                scaled_pixmap = pixmap.scaledToWidth(
                    200, Qt.SmoothTransformation)
                logo_label = QLabel()
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignCenter)
                logo_label.setFixedHeight(97)
            else:
                logo_label = QLabel("IsaLab")
                logo_label.setAlignment(Qt.AlignCenter)
                logo_label.setStyleSheet(
                    f"color: {
                        QT_STYLES['primary']}; font-size: 24px; font-weight: bold; padding: 20px;")
        except Exception:
            logo_label = QLabel("IsaLab")
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet(
                f"color: {
                    QT_STYLES['primary']}; font-size: 24px; font-weight: bold; padding: 20px;")

        sidebar_main_layout.addWidget(logo_label)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #2D4A6B;")
        separator.setFixedHeight(1)
        sidebar_main_layout.addWidget(separator)

        # Scroll Area (Tu código original perfecto)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("background-color: transparent;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 10, 0, 10)
        scroll_layout.setSpacing(5)

        nav_items = [
            ("🏠  Dashboard", self._show_dashboard),
            ("📋  Recepción", self._show_recepcion),
            ("🐾  Pacientes", self._show_animales),
            ("📁  Historia Clínica", self._show_historia),
            ("🩺  Consultas", self._show_consultas),
            ("🔪  Cirugías", self._show_cirugias),
            ("💉  Vacunación", self._show_vacunacion),
            ("🧪  Muestras", self._show_muestras),
            ("📊  Reportes", self._show_reportes),
        ]

        self.nav_buttons = {}
        for text, callback in nav_items:
            btn = SidebarButton(text)
            btn.clicked.connect(
                lambda checked,
                cb=callback,
                t=text: self._navigate(
                    cb,
                    t))
            scroll_layout.addWidget(btn)
            self.nav_buttons[text] = btn

        if self.usuario and isinstance(
                self.usuario,
                dict) and self.usuario.get('rol') == 'admin':
            btn_usuarios = SidebarButton("👥  Usuarios")
            btn_usuarios.clicked.connect(lambda checked: self._show_usuarios())
            scroll_layout.addWidget(btn_usuarios)
            self.nav_buttons["👥  Usuarios"] = btn_usuarios

        scroll_layout.addSpacing(20)

        acciones_label = QLabel("ACCIONES RÁPIDAS")
        acciones_label.setStyleSheet(
            "color: #475569; font-size: 10px; font-weight: bold; padding-left: 20px;")
        scroll_layout.addWidget(acciones_label)

        btn_nuevo = QPushButton("➕ Nuevo Paciente")
        btn_nuevo.setStyleSheet(
            f"background-color: {
                QT_STYLES['accent']}; color: white; padding: 8px; margin: 5px 20px; border-radius: 4px;")
        btn_nuevo.clicked.connect(self._nuevo_animal)
        scroll_layout.addWidget(btn_nuevo)

        btn_recepcion = QPushButton("📋 Nueva Recepción")
        btn_recepcion.setStyleSheet(
            "background-color: #7F77DD; color: white; padding: 8px; margin: 5px 20px; border-radius: 4px;")
        btn_recepcion.clicked.connect(self._nueva_recepcion)
        scroll_layout.addWidget(btn_recepcion)

        btn_historia = QPushButton("📁 Nueva Historia")
        btn_historia.setStyleSheet(
            f"background-color: {
                QT_STYLES['primary']}; color: white; padding: 8px; margin: 5px 20px; border-radius: 4px;")
        btn_historia.clicked.connect(self._nueva_historia)
        scroll_layout.addWidget(btn_historia)

        btn_muestra = QPushButton("🧪 Nueva Muestra")
        btn_muestra.setStyleSheet(
            f"background-color: {
                QT_STYLES['primary']}; color: white; padding: 8px; margin: 5px 20px; border-radius: 4px;")
        btn_muestra.clicked.connect(self._nueva_muestra)
        scroll_layout.addWidget(btn_muestra)

        btn_recibo = QPushButton("🧾 Generar Recibo")
        btn_recibo.setStyleSheet(
            f"background-color: {
                QT_STYLES['warning']}; color: white; padding: 8px; margin: 5px 20px; border-radius: 4px;")
        btn_recibo.clicked.connect(self._nuevo_recibo)
        scroll_layout.addWidget(btn_recibo)

        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        sidebar_main_layout.addWidget(scroll_area)

        # Footer
        footer_widget = QWidget()
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(10, 5, 10, 5)

        version_label = QLabel("IsaLab v1.0.0")
        version_label.setStyleSheet("color: #64748B; font-size: 10px;")
        footer_layout.addWidget(version_label)
        footer_layout.addStretch()

        btn_cambiar_password = QPushButton("🔐 Contraseña")
        btn_cambiar_password.setCursor(Qt.PointingHandCursor)
        btn_cambiar_password.setFixedHeight(25)
        btn_cambiar_password.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {QT_STYLES['gray']};
                border: 1px solid {QT_STYLES['gray']};
                border-radius: 4px;
                font-size: 10px;
                padding: 2px 8px;
            }}
            QPushButton:hover {{
                background-color: {QT_STYLES['gray']};
                color: white;
            }}
        """)
        btn_cambiar_password.clicked.connect(self._cambiar_password)
        footer_layout.addWidget(btn_cambiar_password)

        sidebar_main_layout.addWidget(footer_widget)

        # Contenido Central
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("background-color: #F1F5F9;")

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area, 1)

    def _navigate(self, callback, button_text):
        if self.active_button:
            self.active_button.setChecked(False)
        btn = self.nav_buttons.get(button_text)
        if btn:
            btn.setChecked(True)
            self.active_button = btn
        callback()

    # ======================================================================
    # VISTAS
    # ======================================================================

    def _show_dashboard(self):
        if 'dashboard' not in self.views:
            self.views['dashboard'] = DashboardView(self.content_area)
            self.content_area.addWidget(self.views['dashboard'])
        else:
            # ✅ CORRECCIÓN: Refrescar el dashboard para actualizar estadísticas
            self.views['dashboard'].refresh()
        self.content_area.setCurrentWidget(self.views['dashboard'])

    def _show_recepcion(self):
        if 'recepcion' not in self.views:
            self.views['recepcion'] = RecepcionView(self.content_area)
            self.content_area.addWidget(self.views['recepcion'])
        else:
            self.views['recepcion'].refresh()
        self.content_area.setCurrentWidget(self.views['recepcion'])

    def _show_animales(self):
        if 'animales' not in self.views:
            self.views['animales'] = AnimalesView(self.content_area)
            self.content_area.addWidget(self.views['animales'])
        else:
            self.views['animales'].refresh()
        self.content_area.setCurrentWidget(self.views['animales'])

    def _show_historia(self):
        if 'historia' not in self.views:
            self.views['historia'] = HistoriaView(self.content_area)
            self.content_area.addWidget(self.views['historia'])
        else:
            self.views['historia'].refresh()
        self.content_area.setCurrentWidget(self.views['historia'])

    def _show_consultas(self):
        if 'consultas' not in self.views:
            self.views['consultas'] = ConsultasView(self.content_area)
            self.content_area.addWidget(self.views['consultas'])
        else:
            self.views['consultas'].refresh()
        self.content_area.setCurrentWidget(self.views['consultas'])

    def _show_cirugias(self):
        if 'cirugias' not in self.views:
            self.views['cirugias'] = CirugiasView(self.content_area)
            self.content_area.addWidget(self.views['cirugias'])
        else:
            self.views['cirugias'].refresh()
        self.content_area.setCurrentWidget(self.views['cirugias'])

    def _show_vacunacion(self):
        if 'vacunacion' not in self.views:
            self.views['vacunacion'] = VacunacionView(self.content_area)
            self.content_area.addWidget(self.views['vacunacion'])
        else:
            self.views['vacunacion'].refresh()
        self.content_area.setCurrentWidget(self.views['vacunacion'])

    def _show_muestras(self):
        if 'muestras' not in self.views:
            self.views['muestras'] = MuestrasView(self.content_area)
            self.content_area.addWidget(self.views['muestras'])
        else:
            self.views['muestras'].refresh()
        self.content_area.setCurrentWidget(self.views['muestras'])

    def _show_reportes(self):
        if 'reportes' not in self.views:
            self.views['reportes'] = ReportesView(self.content_area)
            self.content_area.addWidget(self.views['reportes'])
        else:
            self.views['reportes'].refresh()
        self.content_area.setCurrentWidget(self.views['reportes'])

    def _show_usuarios(self):
        from gui_pyside.views.usuarios import UsuariosView
        from utils.logger import setup_logger
        logger = setup_logger()
        logger.info(f"_show_usuarios: self.usuario = {self.usuario}")
        if 'usuarios' not in self.views:
            self.views['usuarios'] = UsuariosView(
                self.content_area, self.usuario)
            self.content_area.addWidget(self.views['usuarios'])
        else:
            self.views['usuarios'].refresh()
        self.content_area.setCurrentWidget(self.views['usuarios'])

    def _cambiar_password(self):
        if not self.usuario:
            QMessageBox.warning(self, "Error", "No hay usuario autenticado")
            return
        from gui_pyside.dialogs.cambiar_password_dialog import CambiarPasswordDialog

        user_id = self.usuario.get('id') if isinstance(
            self.usuario, dict) else None
        if not user_id:
            QMessageBox.warning(
                self, "Error", "Error recuperando ID de usuario.")
            return

        dialog = CambiarPasswordDialog(self, user_id)
        dialog.exec()

    # ======================================================================
    # ACCIONES RÁPIDAS
    # ======================================================================

    def _nuevo_animal(self):
        from gui_pyside.dialogs.animal_dialog import NuevoAnimalDialog
        dialog = NuevoAnimalDialog(self, self._show_animales)
        dialog.exec()

    def _nueva_recepcion(self):
        from gui_pyside.dialogs.recepcion_dialog import NuevaRecepcionDialog
        dialog = NuevaRecepcionDialog(self, self._show_recepcion)
        dialog.exec()

    def _nueva_historia(self):
        from gui_pyside.dialogs.historia_dialog import NuevaHistoriaDialog
        dialog = NuevaHistoriaDialog(self, self._show_historia)
        dialog.exec()

    def _nueva_muestra(self):
        from gui_pyside.dialogs.muestra_dialog import NuevaMuestraDialog
        dialog = NuevaMuestraDialog(self, self._show_muestras)
        dialog.exec()

    def _nuevo_recibo(self):
        from gui_pyside.dialogs.recibo_dialog import GenerarReciboDialog
        dialog = GenerarReciboDialog(self)
        dialog.exec()

    # ======================================================================
    # CIERRE DE APLICACIÓN
    # ======================================================================

    def closeEvent(self, event):
        """Intercepta la 'X' con un diálogo con estilos personalizados"""

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Confirmar salida")
        msg.setText("¿Está seguro que desea salir de IsaLab?")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        # Estilos robustos para los botones del messagebox
        msg.setStyleSheet("""
            QMessageBox {{
                background-color: white;
            }}
            QLabel {{
                color: #0F172A;
                font-size: 14px;
            }}
            QMessageBox QPushButton {{
                background-color: #0E7490;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: #134E4A;
            }}
            QMessageBox QPushButton:pressed {{
                background-color: #0F172A;
            }}
            QMessageBox QPushButton[text="No"] {{
                background-color: #F1F5F9;
                color: #0F172A;
                border: 1px solid #CBD5E1;
            }}
            QMessageBox QPushButton[text="No"]:hover {{
                background-color: #E2E8F0;
            }}
        """)

        respuesta = msg.exec()

        if respuesta == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
