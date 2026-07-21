# gui_pyside/dialogs/login_dialog.py
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QCheckBox,
    QApplication,
    QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal, QPoint
from config import QT_STYLES
from services.usuario_service import UsuarioService
from utils.logger import setup_logger

logger = setup_logger()


class LoginDialog(QDialog):
    login_successful = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Configuración de la ventana sin marco ---
        self.setWindowFlags(Qt.FramelessWindowHint)
        # Fondo transparente para redondear
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Tamaño un poco mayor para la barra de título. Fase 6 (G-L2):
        # aumentado de 400 a 440 para acomodar la nueva fila con
        # checkbox "Mostrar contraseña" + advertencia de Bloq Mayús.
        self.setFixedSize(420, 440)

        # Fase 5 (issue HIGH): lazy-init — no instanciar en __init__
        self._usuario_service = None
        self.drag_position = QPoint()  # Para arrastrar la ventana

        self._build_ui()
        self._center()
        self.username.setFocus()

    def _build_ui(self):
        # --- Layout principal con fondo transparente ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Contenedor principal con fondo blanco y esquinas redondeadas ---
        self.container = QFrame()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QFrame#container {{
                background-color: white;
                border-radius: 16px;
            }}
        """)
        # Sombra para el contenedor (opcional, da profundidad)
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
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                min-height: 40px;
            }}
        """)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(15, 0, 15, 0)

        # Título de la barra
        title_label = QLabel("Iniciar Sesión - IsaLab")
        title_label.setStyleSheet(
            "color: white; font-size: 14px; font-weight: bold;")
        title_bar_layout.addWidget(title_label)

        # Botón de cerrar
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E81123;
                border-radius: 4px;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        title_bar_layout.addWidget(self.close_btn, alignment=Qt.AlignRight)

        # Hacer que la barra de título sea arrastrable
        title_bar.mousePressEvent = self.mousePressEvent
        title_bar.mouseMoveEvent = self.mouseMoveEvent

        container_layout.addWidget(title_bar)

        # --- Cuerpo del diálogo (contenido original) ---
        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 25, 30, 30)
        content_layout.setSpacing(20)

        # Título principal
        titulo = QLabel("IsaLab")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {QT_STYLES['primary']};
            letter-spacing: 1px;
        """)
        content_layout.addWidget(titulo)

        subtitulo = QLabel("Centro Diagnóstico Veterinario")
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setStyleSheet(f"""
            font-size: 12px;
            color: {QT_STYLES['gray']};
        """)
        content_layout.addWidget(subtitulo)

        # Campos de texto
        self.username = QLineEdit()
        self.username.setPlaceholderText("Usuario")
        self.username.setMinimumHeight(38)
        self.username.setStyleSheet(self._input_style())
        content_layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Contraseña")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(38)
        self.password.setStyleSheet(self._input_style())
        # Fase 6 (G-L2): detectar Bloq Mayús mientras el usuario escribe
        # la contraseña. Es una pista útil (las contraseñas se ven como
        # puntos) y evita el clásico "¿por qué no me deja entrar?".
        # Se actualiza también en focusIn, por si el usuario entra al
        # campo con Bloq Mayús ya activado.
        self.password.textChanged.connect(self._check_caps_lock)
        self.password.installEventFilter(self)
        content_layout.addWidget(self.password)

        # Fase 6 (G-L2): fila con checkbox "Mostrar contraseña" y
        # advertencia de Bloq Mayús. Antes, si el usuario activaba
        # Bloq Mayús sin darse cuenta, no había feedback visual y la
        # contraseña se rechazaba sin explicación clara.
        extras_layout = QHBoxLayout()
        extras_layout.setContentsMargins(0, 0, 0, 0)
        extras_layout.setSpacing(8)

        self.show_password_chk = QCheckBox("👁 Mostrar contraseña")
        self.show_password_chk.setStyleSheet(
            f"color: {QT_STYLES['gray']}; font-size: 11px;")
        self.show_password_chk.toggled.connect(self._toggle_password_echo)
        extras_layout.addWidget(self.show_password_chk)
        extras_layout.addStretch()

        self.lbl_caps_warning = QLabel("⚠ Bloq Mayús está activado")
        self.lbl_caps_warning.setStyleSheet(
            f"color: {QT_STYLES['warning']}; font-size: 11px; font-weight: bold;")
        self.lbl_caps_warning.hide()
        extras_layout.addWidget(self.lbl_caps_warning)

        extras_widget = QFrame()
        extras_widget.setLayout(extras_layout)
        content_layout.addWidget(extras_widget)

        # Mensaje de error
        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setStyleSheet(
            f"color: {QT_STYLES['danger']}; font-size: 11px;")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()
        content_layout.addWidget(self.lbl_error)

        # Botón de login
        self.btn_login = QPushButton("Ingresar al Sistema")
        self.btn_login.setMinimumHeight(42)
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setStyleSheet(self._button_style())
        self.btn_login.clicked.connect(self._do_login)
        self.password.returnPressed.connect(self._do_login)
        content_layout.addWidget(self.btn_login)

        content_layout.addStretch()

        container_layout.addWidget(content)
        main_layout.addWidget(self.container)

    def _input_style(self):
        """Estilo para los campos de texto"""
        return f"""
            QLineEdit {{
                border: 1px solid {QT_STYLES['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                background-color: white;
            }}
            QLineEdit:focus {{
                border: 2px solid {QT_STYLES['primary']};
                background-color: #F0F9FF;
            }}
        """

    def _button_style(self):
        """Estilo para el botón principal"""
        return f"""
            QPushButton {{
                background-color: {QT_STYLES['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {QT_STYLES['secondary']};
            }}
            QPushButton:pressed {{
                background-color: {QT_STYLES['dark']};
            }}
        """

    # --- Métodos para arrastrar la ventana ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - \
                self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    # --- Método original _center ajustado ---
    def _center(self):
        if self.parent():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)

    # --- Lógica de autenticación ---
    # Fase 6 (G-L1): antes el ``except Exception`` mostraba ``str(e)``
    # directamente en ``lbl_error``. Eso filtraba información interna
    # (nombres de tablas, rutas, mensajes SQL) y creaba un oráculo de
    # timing: el usuario podía distinguir "usuario no existe" (rápido)
    # de "contraseña incorrecta" (lento, por el bcrypt verify dummy).
    # Ahora: log completo vía ``logger.error`` (para debugging), pero
    # al usuario solo se le muestra un mensaje genérico idéntico en
    # ambos casos. Cierra el vector de enumeración de usuarios.

    @property
    def usuario_service(self):
        """Lazy-init de UsuarioService."""
        if self._usuario_service is None:
            self._usuario_service = UsuarioService()
        return self._usuario_service

    @usuario_service.setter
    def usuario_service(self, value):
        """Permite inyectar un servicio (para tests/mocking)."""
        self._usuario_service = value

    def _do_login(self):
        username = self.username.text().strip()
        password = self.password.text()

        self.lbl_error.hide()

        if not username or not password:
            self.lbl_error.setText("⚠️ Ingrese usuario y contraseña")
            self.lbl_error.show()
            return

        try:
            usuario_data = self.usuario_service.autenticar(username, password)
            self.usuario = usuario_data
            self.login_successful.emit(usuario_data)
            self.accept()
        except Exception as e:
            # Log completo (con stacktrace) para debugging interno.
            logger.error(
                f"Fallo de autenticación para usuario '{username}': {e}",
                exc_info=True)
            # Mensaje sanitizado y uniforme (no distingue "usuario no
            # encontrado" de "contraseña incorrecta" — cierra el
            # oráculo de timing que tendría un atacante midiendo la
            # latencia de la respuesta).
            self.lbl_error.setText("❌ Usuario o contraseña incorrectos")
            self.lbl_error.show()
            # Limpia el campo de contraseña para evitar re-submit
            # accidental del mismo valor.
            self.password.clear()
            self.password.setFocus()

    # --- Fase 6 (G-L2): helpers para mostrar/ocultar contraseña y
    # detectar Bloq Mayús ---

    def _toggle_password_echo(self, checked: bool):
        """Alterna entre ``Password`` (oculto) y ``Normal`` (visible)."""
        if checked:
            self.password.setEchoMode(QLineEdit.Normal)
        else:
            self.password.setEchoMode(QLineEdit.Password)

    def _check_caps_lock(self):
        """Muestra/oculta la advertencia de Bloq Mayús.

        Qt no tiene un accessor directo para el estado de Caps Lock
        (es un estado global del teclado, no de Qt). Lo inferimos
        comparando el último caracter tipeado con/sin Shift: si es
        uppercase y Shift NO está presionado, o es lowercase y Shift
        SÍ está presionado, entonces Caps Lock está activado.
        ``QApplication.queryKeyboardModifiers()`` devuelve los
        modificadores activos al momento de la llamada.
        """
        text = self.password.text()
        if not text:
            self.lbl_caps_warning.hide()
            return
        last_char = text[-1]
        if not last_char.isalpha():
            # No es letra — no podemos inferir Caps Lock.
            return
        shift = bool(QApplication.queryKeyboardModifiers() & Qt.ShiftModifier)
        caps_on = (last_char.isupper() and not shift) or \
                  (last_char.islower() and shift)
        self.lbl_caps_warning.setVisible(caps_on)

    def eventFilter(self, obj, event):
        """Interceptor de eventos para el campo de contraseña.

        Fase 6 (G-L2): captura ``KeyPress`` y ``FocusIn`` sobre
        ``self.password`` para refrescar el indicador de Bloq Mayús.
        ``textChanged`` solo dispara cuando el texto cambia; si el
        usuario entra al campo con Bloq Mayús ya activado (sin haber
        tipeado nada nuevo), el warning no aparecería sin este filter.
        """
        from PySide6.QtCore import QEvent
        if obj is self.password:
            if event.type() in (QEvent.KeyPress, QEvent.FocusIn,
                                 QEvent.KeyRelease):
                self._check_caps_lock()
        return super().eventFilter(obj, event)
