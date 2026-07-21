# gui_pyside/dialogs/instalador_dialog.py
"""Diálogo de instalación inicial - Primera ejecución del sistema"""

from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from gui_pyside.dialogs.base_dialog import BaseDialog
from gui_pyside.styles import IsaStyles
from gui_pyside.utils.services import LazyService
from services.usuario_service import UsuarioService
from services.configuracion_service import ConfiguracionService
from utils.security import validar_fortaleza_password
from gui_pyside.components.components import ErrorHandler

class InstaladorDialog(BaseDialog):
    """Wizard de instalación inicial para crear el primer usuario administrador y configurar el laboratorio."""
    service = LazyService(UsuarioService)
    config_service = LazyService(ConfiguracionService)

    def __init__(self, parent=None):
        super().__init__(parent, "🐾 IsaLab - Instalación Inicial", 500, 680)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.content_layout.setSpacing(12)

        icono_label = QLabel("🔐")
        icono_label.setAlignment(Qt.AlignCenter)
        icono_label.setStyleSheet("font-size: 48px;")
        self.content_layout.addWidget(icono_label)

        titulo = QLabel("Configuración del Administrador")
        titulo.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1E3A5F; text-align: center;")
        titulo.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(titulo)

        descripcion = QLabel(
            "Esta es la primera ejecución de IsaLab.<br>"
            "Configure las credenciales del administrador del sistema."
        )
        descripcion.setStyleSheet(
            "color: #666; font-size: 12px; text-align: center;")
        descripcion.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(descripcion)

        separador = QFrame()
        separador.setFrameShape(QFrame.HLine)
        separador.setStyleSheet("background-color: #E0E0E0; margin: 10px 0;")
        self.content_layout.addWidget(separador)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(16)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nombre de usuario")
        self.username_input.setMinimumHeight(40)
        self.username_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {IsaStyles.BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                background: white;
            }}
            QLineEdit:focus {{
                border-color: {IsaStyles.PRIMARY};
            }}
        """)

        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Nombre completo")
        self.nombre_input.setMinimumHeight(40)
        self.nombre_input.setStyleSheet(self.username_input.styleSheet())

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña segura")
        self.password_input.setMinimumHeight(40)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self.username_input.styleSheet())

        self.confirmar_input = QLineEdit()
        self.confirmar_input.setPlaceholderText("Confirmar contraseña")
        self.confirmar_input.setMinimumHeight(40)
        self.confirmar_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirmar_input.setStyleSheet(self.username_input.styleSheet())

        requisitos_label = QLabel(
            "<b>Requisitos de contraseña:</b><br>"
            "• Mínimo 8 caracteres<br>"
            "• Al menos una mayúscula<br>"
            "• Al menos una minúscula<br>"
            "• Al menos un número<br>"
            "• Al menos un símbolo"
        )
        requisitos_label.setStyleSheet(
            "color: #888; font-size: 11px; padding: 8px; background: #F5F5F5; border-radius: 4px;")
        requisitos_label.setWordWrap(True)

        form_layout.addWidget(QLabel("Usuario:"))
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(QLabel("Nombre completo:"))
        form_layout.addWidget(self.nombre_input)
        form_layout.addWidget(QLabel("Contraseña:"))
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(QLabel("Confirmar contraseña:"))
        form_layout.addWidget(self.confirmar_input)
        form_layout.addWidget(requisitos_label)

        # ---- SECCIÓN LABORATORIO ----
        separador_lab = QFrame()
        separador_lab.setFrameShape(QFrame.HLine)
        separador_lab.setStyleSheet("background-color: #E0E0E0; margin: 10px 0;")
        form_layout.addWidget(separador_lab)

        titulo_lab = QLabel("Datos del Laboratorio (Para Reportes)")
        titulo_lab.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E3A5F;")
        form_layout.addWidget(titulo_lab)

        self.lab_nit_input = QLineEdit()
        self.lab_nit_input.setPlaceholderText("NIT o Identificación")
        self.lab_nit_input.setMinimumHeight(40)
        self.lab_nit_input.setStyleSheet(self.username_input.styleSheet())

        self.lab_direccion_input = QLineEdit()
        self.lab_direccion_input.setPlaceholderText("Dirección completa")
        self.lab_direccion_input.setMinimumHeight(40)
        self.lab_direccion_input.setStyleSheet(self.username_input.styleSheet())

        self.lab_celular_input = QLineEdit()
        self.lab_celular_input.setPlaceholderText("Celular / Teléfono")
        self.lab_celular_input.setMinimumHeight(40)
        self.lab_celular_input.setStyleSheet(self.username_input.styleSheet())

        self.lab_slogan_input = QLineEdit()
        self.lab_slogan_input.setPlaceholderText("Slogan (Ej. Precisión y salud animal)")
        self.lab_slogan_input.setMinimumHeight(40)
        self.lab_slogan_input.setStyleSheet(self.username_input.styleSheet())

        form_layout.addWidget(self.lab_nit_input)
        form_layout.addWidget(self.lab_direccion_input)
        form_layout.addWidget(self.lab_celular_input)
        form_layout.addWidget(self.lab_slogan_input)

        self.label_error = QLabel("")
        self.label_error.setStyleSheet("color: #D32F2F; font-size: 12px;")
        self.label_error.setAlignment(Qt.AlignCenter)
        self.label_error.setVisible(False)
        form_layout.addWidget(self.label_error)

        # Como el contenido es más grande, lo metemos en un ScrollArea
        from PySide6.QtWidgets import QScrollArea, QWidget
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        container = QWidget()
        container.setLayout(form_layout)
        container.setStyleSheet("background-color: transparent;")
        scroll.setWidget(container)

        self.content_layout.addWidget(scroll)

        self.btn_crear = QPushButton("Crear Administrador")
        self.btn_crear.setMinimumHeight(44)
        self.btn_crear.setStyleSheet(f"""
            QPushButton {{
                background-color: {IsaStyles.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #15417A;
            }}
            QPushButton:disabled {{
                background-color: #B0BEC5;
            }}
        """)

        self.footer_layout.removeWidget(self.btn_cancelar)
        self.btn_cancelar.setVisible(False)
        self.footer_layout.removeWidget(self.btn_guardar)
        self.btn_guardar.setVisible(False)
        self.footer_layout.insertWidget(0, self.btn_crear)

    def _connect_signals(self):
        self.btn_crear.clicked.connect(self._crear_admin)

    def _validar_campos(self) -> tuple[bool, str]:
        username = self.username_input.text().strip()
        nombre = self.nombre_input.text().strip()
        password = self.password_input.text()
        confirmar = self.confirmar_input.text()

        if not username:
            return False, "El nombre de usuario es requerido"
        if len(username) < 3:
            return False, "El usuario debe tener al menos 3 caracteres"
        if not nombre:
            return False, "El nombre completo es requerido"
        if not password:
            return False, "La contraseña es requerida"

        es_valida, msg = validar_fortaleza_password(password)
        if not es_valida:
            return False, msg

        if password != confirmar:
            return False, "Las contraseñas no coinciden"

        # Validaciones laboratorio
        if not self.lab_nit_input.text().strip():
            return False, "El NIT o Identificación del laboratorio es requerido"
        if not self.lab_direccion_input.text().strip():
            return False, "La dirección del laboratorio es requerida"
        if not self.lab_celular_input.text().strip():
            return False, "El celular o teléfono es requerido"

        return True, ""

    @ErrorHandler.handle_exception
    def _crear_admin(self):
        es_valido, mensaje = self._validar_campos()

        if not es_valido:
            self.label_error.setText(mensaje)
            self.label_error.setVisible(True)
            return

        self.label_error.setVisible(False)
        self.btn_crear.setEnabled(False)
        self.btn_crear.setText("Creando...")

        try:
            # 1. Crear usuario administrador
            self.service.crear_usuario_inicial(
                username=self.username_input.text().strip(),
                password=self.password_input.text(),
                nombre=self.nombre_input.text().strip()
            )

            # 2. Guardar configuración del laboratorio
            lab_config = {
                "nit": self.lab_nit_input.text().strip(),
                "direccion": self.lab_direccion_input.text().strip(),
                "telefono_celular": self.lab_celular_input.text().strip(),
                "slogan": self.lab_slogan_input.text().strip()
            }
            self.config_service.guardar_configuracion(lab_config)

            QMessageBox.information(
                self,
                "Instalación Completa",
                "✓ Configuración completada exitosamente.\n\n"
                "Ahora puede iniciar sesión con sus credenciales."
            )

            self.accept()

        except Exception as e:
            self.label_error.setText(str(e))
            self.label_error.setVisible(True)
            self.btn_crear.setEnabled(True)
            self.btn_crear.setText("Crear Administrador")
