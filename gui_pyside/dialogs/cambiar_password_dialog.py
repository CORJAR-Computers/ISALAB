# gui_pyside/dialogs/cambiar_password_dialog.py
from PySide6.QtWidgets import (QLabel, QLineEdit, QMessageBox,
                               QFormLayout, QGroupBox, QVBoxLayout)

from gui_pyside.dialogs.base_dialog import BaseDialog
from gui_pyside.utils.messages import show_error, show_warning
from services.usuario_service import UsuarioService
from gui_pyside.styles import IsaStyles, style_input, style_button
from config import ICONS, DIALOG_SIZES, VALIDACION_VISUAL


class CambiarPasswordDialog(BaseDialog):
    def __init__(self, parent=None, usuario_id=None):
        width, height = DIALOG_SIZES['medium']
        super().__init__(
            parent, f"{
                ICONS['password']} Cambiar Contraseña", width, height)
        self.usuario_id = usuario_id
        self.service = UsuarioService()
        self._build()

    def _build(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Grupo estilizado
        group = QGroupBox("Seguridad de la Cuenta")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {IsaStyles.BORDER};
                border-radius: 8px;
                margin-top: 16px;
                padding: 20px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px;
                color: {IsaStyles.PRIMARY};
            }}
        """)

        form = QFormLayout(group)
        form.setSpacing(16)

        # Contraseña actual
        self.txt_actual = QLineEdit()
        self.txt_actual.setEchoMode(QLineEdit.Password)
        self.txt_actual.setPlaceholderText("Contraseña actual")
        style_input(self.txt_actual)
        form.addRow("Contraseña Actual *:", self.txt_actual)

        # Nueva contraseña
        self.txt_nueva = QLineEdit()
        self.txt_nueva.setEchoMode(QLineEdit.Password)
        self.txt_nueva.setPlaceholderText("Mínimo 6 caracteres")
        style_input(self.txt_nueva)
        form.addRow("Nueva Contraseña *:", self.txt_nueva)

        # Confirmar
        self.txt_confirmar = QLineEdit()
        self.txt_confirmar.setEchoMode(QLineEdit.Password)
        self.txt_confirmar.setPlaceholderText("Repita la nueva contraseña")
        style_input(self.txt_confirmar)
        form.addRow("Confirmar Contraseña *:", self.txt_confirmar)

        # Indicador de seguridad
        self.lbl_seguridad = QLabel("")
        self.lbl_seguridad.setStyleSheet(
            f"font-size: 11px; color: {IsaStyles.GRAY};")
        form.addRow("", self.lbl_seguridad)

        layout.addWidget(group)
        layout.addStretch()
        self.content_layout.addLayout(layout)

        # Actualizar botones
        self.btn_guardar.setText(f"{ICONS['save']} Actualizar Contraseña")
        style_button(self.btn_guardar, 'primary')
        self.btn_cancelar.setText(f"{ICONS['cancel']} Cancelar")
        style_button(self.btn_cancelar, 'ghost')

        self.set_save_callback(self._guardar)

        # Validación en tiempo real
        self.txt_nueva.textChanged.connect(self._check_seguridad)

    def _check_seguridad(self, text):
        if len(text) < 6:
            self.lbl_seguridad.setText(f"{ICONS['warning']} Muy débil")
            self.lbl_seguridad.setStyleSheet(
                f"color: {IsaStyles.DANGER}; font-size: 11px;")
        elif len(text) < 10:
            self.lbl_seguridad.setText(f"{ICONS['info']} Aceptable")
            self.lbl_seguridad.setStyleSheet(
                f"color: {IsaStyles.WARNING}; font-size: 11px;")
        else:
            self.lbl_seguridad.setText(f"{ICONS['success']} Segura")
            self.lbl_seguridad.setStyleSheet(
                f"color: {IsaStyles.SUCCESS}; font-size: 11px;")

    def _guardar(self):
        actual = self.txt_actual.text().strip()
        nueva = self.txt_nueva.text().strip()
        confirmar = self.txt_confirmar.text().strip()

        errores = []

        if not all([actual, nueva, confirmar]):
            errores.append("Todos los campos son obligatorios")

        if nueva != confirmar:
            errores.append("Las contraseñas nuevas no coinciden")
            self.txt_confirmar.setStyleSheet(f"""
                QLineEdit {{
                    border: 2px solid {VALIDACION_VISUAL['error_color']};
                    border-radius: 6px;
                    padding: 6px 10px;
                }}
            """)

        if len(nueva) < 6:
            errores.append(
                "La nueva contraseña debe tener al menos 6 caracteres")

        if errores:
            show_warning(self,
                         f"{ICONS['warning']} Validación",
                         "\n• ".join([""] + errores))
            return

        try:
            self.service.cambiar_password(self.usuario_id, actual, nueva)
            QMessageBox.information(self, f"{ICONS['success']} Éxito",
                                    "Contraseña actualizada correctamente")
            self.accept()
        except Exception as e:
            show_error(self, "No se pudo actualizar la contraseña.", e)
