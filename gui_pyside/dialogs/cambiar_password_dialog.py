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
        # Fase 5 (H-S2): antes decía "Mínimo 6 caracteres" pero el
        # servicio ``validar_fortaleza_password`` exige 8. Mostramos el
        # requisito real para no confundir al usuario.
        self.txt_nueva.setPlaceholderText("Mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número")
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
        # Fase 5 (H-S2): el umbral visual ahora es 8 (consistente con
        # ``validar_fortaleza_password``). Antes era 6, lo que mostraba
        # "Aceptable" para contraseñas que el servicio iba a rechazar.
        if len(text) < 8:
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
        # Fase 5 (H-S2): NO hacemos ``.strip()`` sobre las contraseñas.
        # Antes, ``self.txt_nueva.text().strip()`` eliminaba espacios en
        # blanco a los lados, lo que significa que un usuario que
        # intencionalmente incluyera un espacio al inicio/final de su
        # contraseña NO podía loguearse después (el formulario de login
        # tampoco hace strip, así que la contraseña no coincidía).
        # Peor aún: el servicio ``cambiar_password`` SÍ recibe la
        # contraseña sin strip y la valida con ``validar_fortaleza_password``,
        # por lo que un espacio al final que el usuario vio en el campo
        # se eliminaba silenciosamente aquí.
        actual = self.txt_actual.text()
        nueva = self.txt_nueva.text()
        confirmar = self.txt_confirmar.text()

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

        # Fase 5 (H-S2): umbral consistent con ``validar_fortaleza_password``
        # (8 caracteres mínimo, antes era 6 aquí).
        if len(nueva) < 8:
            errores.append(
                "La nueva contraseña debe tener al menos 8 caracteres")

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
