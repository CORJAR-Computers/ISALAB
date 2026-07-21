# gui_pyside/app.py
"""Aplicación principal IsaLab con PySide6 - FLUJO CORREGIDO Y SIDEBAR CON SCROLL"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel,
                               QFrame, QStackedWidget, QMessageBox,
                               QScrollArea)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QShortcut, QKeySequence
from gui_pyside.utils.settings import AppSettings

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
# Fase 5 (H-G2): WindowManager eliminado — era dead code. Ningún view ni
# dialog lo usaba: ``open_dialog`` / ``close_all_dialogs`` / etc. nunca
# eran invocados; todos los diálogos se ejecutaban con ``dialog.exec()``
# directo. Su único uso aquí era ``WindowManager.set_main_window(self)``
# que no hacía nada útil porque nadie consultaba esa referencia.

# Fase 5 (H-G5): logger a nivel de módulo, para que ``_on_theme_changed``
# y otros métodos puedan loguear sin tener que re-obtener el logger cada
# vez (como hacía ``__init__`` con ``from utils.logger import setup_logger``
# dentro del método).
from utils.logger import setup_logger
logger = setup_logger()


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
    # Fase 6 (G-L8): antes ``setMinimumSize(1200, 700)`` y
    # ``_center_window`` hacían ``self.resize(1200, 768)`` — dos
    # constantes distintas para la misma idea ("tamaño inicial de la
    # ventana principal"). Ahora hay una sola constante
    # ``DEFAULT_WINDOW_SIZE`` y ``_center_window`` la usa, así como
    # ``setMinimumSize`` (con un poco de margen para que el usuario
    # pueda encoger la ventana sin perder el header).
    DEFAULT_WINDOW_SIZE = (1280, 800)

    def __init__(self, usuario: dict = None):
        super().__init__()
        self.usuario = usuario or {}
        self.settings = AppSettings()
        self._current_theme = self.settings.get_theme()
        # Fase 5 (H-G5): logger ahora es module-level (no hace falta
        # re-obtenerlo en cada __init__).
        logger.info(f"LabVetApp inicializado con usuario: {self.usuario}")
        self.setWindowTitle("IsaLab - Centro Diagnóstico Veterinario")
        # Fase 6 (G-L8): mínimo consistente con el tamaño inicial.
        min_w, min_h = 1200, 700
        self.setMinimumSize(min_w, min_h)
        self.setStyleSheet(GLOBAL_STYLESHEET)
        self._center_window()
        # Fase 6 (G-M2): ``self.views`` ya se usaba como cache de
        # vistas instanciadas (dict ``name -> view``). El handler
        # ``_on_theme_changed`` ahora lo recorre para refrescar tema
        # en TODAS las vistas, no solo el dashboard.
        self.views = {}
        self.active_button = None

        # Fase 5 (H-G2): WindowManager.set_main_window(self) eliminado —
        # era la única llamada y el singleton nunca se consultaba.

        self._build_layout()
        self._setup_keyboard_shortcuts()
        self._show_dashboard()

    def _center_window(self):
        # Fase 6 (G-L8): usa ``DEFAULT_WINDOW_SIZE`` (constante de
        # clase) en lugar de un literal ``1200, 768`` hardcodeado
        # distinto del ``setMinimumSize(1200, 700)``.
        w, h = self.DEFAULT_WINDOW_SIZE
        self.resize(w, h)
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

    def _setup_keyboard_shortcuts(self):
        """Configure global keyboard shortcuts for the application.

        Shortcuts:
            Ctrl+S: Save current form (delegates to active view)
            Ctrl+F: Focus search bar in active view
            Ctrl+N: Open new record dialog (context-dependent)
            Escape: Close active dialog or return to dashboard
        """
        # Ctrl+S — Save
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self._on_save_shortcut)

        # Ctrl+F — Search/Focus
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self._on_search_shortcut)

        # Ctrl+N — New record
        new_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_shortcut.activated.connect(self._on_new_shortcut)

        # Escape — Close/Back
        esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        esc_shortcut.activated.connect(self._on_escape_shortcut)

        logger.info("Keyboard shortcuts configured: Ctrl+S, Ctrl+F, Ctrl+N, Escape")

    def _on_save_shortcut(self):
        """Delegate save to the currently active view."""
        current = self.content_area.currentWidget()
        if current and hasattr(current, 'save'):
            try:
                current.save()
            except Exception as e:
                logger.warning(f"Save shortcut failed: {e}")
        else:
            logger.debug("No save handler in current view")

    def _on_search_shortcut(self):
        """Focus the search bar in the currently active view."""
        current = self.content_area.currentWidget()
        if current:
            # Try common search widget names
            for attr_name in ('search_bar', 'search_input', 'txt_buscar'):
                widget = getattr(current, attr_name, None)
                if widget and hasattr(widget, 'setFocus'):
                    widget.setFocus()
                    return
            # Try to find QLineEdit descendants
            from PySide6.QtWidgets import QLineEdit
            for child in current.findChildren(QLineEdit):
                if hasattr(child, 'placeholderText') and 'buscar' in (child.placeholderText() or '').lower():
                    child.setFocus()
                    return

    def _on_new_shortcut(self):
        """Open new record dialog based on current view context."""
        current = self.content_area.currentWidget()
        view_name = None
        for name, view in self.views.items():
            if view is current:
                view_name = name
                break

        actions = {
            'animales': self._nuevo_animal,
            'recepcion': self._nueva_recepcion,
            'historia': self._nueva_historia,
            'muestras': self._nueva_muestra,
        }
        if view_name and view_name in actions:
            actions[view_name]()

    def _on_escape_shortcut(self):
        """Close active dialog or navigate to dashboard."""
        from PySide6.QtWidgets import QApplication, QLineEdit
        focused = QApplication.focusWidget()
        if isinstance(focused, QLineEdit) and focused.text():
            focused.clear()
            return
        self._show_dashboard()

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

    # Fase 6 (G-M1): antes existían 9 métodos ``_show_X`` casi idénticos
    # (dashboard, recepcion, animales, historia, consultas, cirugias,
    # vacunacion, muestras, reportes) cada uno repitiendo el patrón:
    #
    #   if name not in self.views:
    #       self.views[name] = ViewClass(self.content_area)
    #       self.content_area.addWidget(self.views[name])
    #   else:
    #       self.views[name].refresh()
    #   self.content_area.setCurrentWidget(self.views[name])
    #
    # Eran ~60-80 líneas de duplicación. Ahora hay un único método
    # genérico ``_show_view(name, factory)`` que encapsula ese patrón,
    # y los 9 wrappers públicos solo pasan la clase correspondiente.
    # Los nombres públicos se conservan para que los ``connect`` del
    # sidebar no cambien.

    def _show_view(self, name: str, factory):
        """Patrón único para mostrar una vista (lazy-init + refresh).

        Args:
            name: clave en ``self.views`` (str).
            factory: callable ``parent -> QWidget`` que instancia la
                vista la primera vez. En llamadas subsiguientes se
                invoca ``view.refresh()`` si existe (la mayoría lo
                implementan para actualizar datos sin reconstruir el
                layout).
        """
        if name not in self.views:
            view = factory(self.content_area)
            self.views[name] = view
            self.content_area.addWidget(view)
        else:
            view = self.views[name]
            # Fase 6 (G-M2): ``refresh`` es opcional — algunos views
            # (ReportesView) pueden no implementarlo todavía. Si no
            # existe, simplemente traemos la vista al frente sin
            # recargar datos (antes estos métodos asumían que siempre
            # existía ``refresh``).
            if hasattr(view, 'refresh'):
                try:
                    view.refresh()
                except Exception as e:
                    logger.warning(
                        f"Error refrescando vista '{name}': {e}")
        self.content_area.setCurrentWidget(view)

    def _show_dashboard(self):
        # El dashboard es especial: su señal ``theme_changed`` debe
        # conectarse una sola vez (al crear la instancia), así que no
        # podemos usar ``_show_view`` directamente sin perder esa lógica.
        # Mantenemos el patrón explícito solo para este view.
        if 'dashboard' not in self.views:
            self.views['dashboard'] = DashboardView(self.content_area)
            # Fase 5 (H-G5): antes la señal ``theme_changed`` del Dashboard
            # NUNCA se conectaba, por lo que al cambiar el tema solo se
            # refrescaba el dashboard; las demás vistas (animales, muestras,
            # etc.) permanecían con el tema anterior hasta que se
            # reiniciara la app. Ahora, al construir el dashboard,
            # conectamos la señal a un handler que reconstruye cada vista
            # activa para que tome los nuevos colores.
            self.views['dashboard'].theme_changed.connect(
                self._on_theme_changed)
            self.content_area.addWidget(self.views['dashboard'])
        else:
            # ✅ CORRECCIÓN: Refrescar el dashboard para actualizar estadísticas
            self.views['dashboard'].refresh()
        self.content_area.setCurrentWidget(self.views['dashboard'])

    def _on_theme_changed(self):
        """Persiste el tema y re-aplica a todas las vistas activas.

        Guarda la preferencia del tema en QSettings para que se
        restaure en la próxima ejecución.
        """
        # Toggle and persist theme
        self._current_theme = 'light' if self._current_theme == 'dark' else 'dark'
        self.settings.set_theme(self._current_theme)
        logger.info(f"Theme persisted: {self._current_theme}")

        # Re-aplica el tema a todas las vistas activas.

        Fase 5 (H-G5): handler conectado a ``DashboardView.theme_changed``.
        Antes, el toggle de tema solo refrescaba el dashboard y el
        ``QApplication`` stylesheet, pero las vistas ya instanciadas en
        el ``QStackedWidget`` conservaban sus estilos inline (basados en
        el tema anterior). Resultado: la mitad de la pantalla en claro
        y la otra en oscuro tras un toggle.

        Fase 6 (G-M2): antes el handler solo recorría ``self.views``
        llamando ``rebuild_layout()``/``refresh()`` — pero solo lo
        hacía en vistas EXCEPTO el dashboard. Eso significaba que si el
        usuario había abierto ``recepcion`` y ``animales`` pero NO
        ``vacunacion``, esa última no se actualizaba al cambiar de
        tema. Ahora iteramos sobre TODAS las vistas instanciadas
        (incluyendo el dashboard) y:
          1. Si tiene ``apply_theme()`` (método nuevo recomendado para
             este propósito), lo llamamos.
          2. Si no, intentamos ``rebuild_layout()`` (lo implementan
             vistas que ya tienen soporte de tema).
          3. Como último recurso, ``refresh()``.
        Cualquier excepción se loguea pero no rompe el toggle.
        """
        for name, view in list(self.views.items()):
            try:
                # ``apply_theme`` es la API preferida (G-M2) — no
                # re-fetcha datos, solo re-aplica estilos inline.
                if hasattr(view, 'apply_theme'):
                    view.apply_theme()
                elif hasattr(view, 'rebuild_layout'):
                    view.rebuild_layout()
                elif hasattr(view, 'refresh'):
                    # Skip dashboard: ya se reconstruyó a sí mismo
                    # dentro de ``_toggle_theme`` (emite la señal
                    # DESPUÉS de rebuild_layout).
                    if name == 'dashboard':
                        continue
                    view.refresh()
            except Exception as e:
                logger.warning(
                    f"No se pudo re-aplicar tema a la vista '{name}': {e}")

    def _show_recepcion(self):
        self._show_view('recepcion',
                        lambda parent: RecepcionView(parent))

    def _show_animales(self):
        self._show_view('animales',
                        lambda parent: AnimalesView(parent))

    def _show_historia(self):
        self._show_view('historia',
                        lambda parent: HistoriaView(parent))

    def _show_consultas(self):
        self._show_view('consultas',
                        lambda parent: ConsultasView(parent))

    def _show_cirugias(self):
        self._show_view('cirugias',
                        lambda parent: CirugiasView(parent))

    def _show_vacunacion(self):
        self._show_view('vacunacion',
                        lambda parent: VacunacionView(parent))

    def _show_muestras(self):
        self._show_view('muestras',
                        lambda parent: MuestrasView(parent))

    def _show_reportes(self):
        self._show_view('reportes',
                        lambda parent: ReportesView(parent))

    def _show_usuarios(self):
        # ``UsuariosView`` requiere ``usuario_actual`` (para RBAC y
        # para mostrar/ocultar acciones). Los demás views no lo
        # necesitan. Por eso no usa ``_show_view`` directo — pero el
        # patrón interno es idéntico.
        from gui_pyside.views.usuarios import UsuariosView
        logger.info(f"_show_usuarios: self.usuario = {self.usuario}")
        self._show_view(
            'usuarios',
            lambda parent: UsuariosView(parent, self.usuario))

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
