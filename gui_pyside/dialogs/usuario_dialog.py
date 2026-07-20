# gui_pyside/dialogs/usuario_dialog.py
from PySide6.QtWidgets import (QLineEdit, QMessageBox, QComboBox,
                               QFormLayout, QVBoxLayout)

from gui_pyside.dialogs.base_dialog import BaseDialog
from services.usuario_service import UsuarioService
from utils.exceptions import DuplicateError
from gui_pyside.styles import IsaStyles, style_input, style_button
from gui_pyside.utils.messages import show_error, show_warning
from config import ICONS, DIALOG_SIZES


class UsuarioDialog(BaseDialog):
    def __init__(self, parent=None, usuario=None, usuario_actual=None):
        self.usuario = usuario
        self.usuario_actual = usuario_actual
        width, height = DIALOG_SIZES['medium']
        title = f"{
            ICONS['edit']} Editar Usuario" if usuario else f"{
            ICONS['add']} Nuevo Usuario"
        super().__init__(parent, title, width, height)

        self.service = UsuarioService(usuario_actual)
        self._build()

    def _build(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Formulario
        form = QFormLayout()
        form.setSpacing(14)

        # Nombre completo
        self.nombre = QLineEdit()
        self.nombre.setPlaceholderText("Nombre completo del usuario")
        style_input(self.nombre)
        if self.usuario:
            self.nombre.setText(self.usuario['nombre'])
        form.addRow("Nombre Completo *:", self.nombre)

        # Username
        self.username = QLineEdit()
        self.username.setPlaceholderText("Nombre de usuario único")
        style_input(self.username)
        if self.usuario:
            self.username.setText(self.usuario['username'])
            self.username.setEnabled(False)
            self.username.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {IsaStyles.LIGHT_BG};
                    color: {IsaStyles.GRAY};
                    border: 2px solid {IsaStyles.BORDER};
                    border-radius: 6px;
                    padding: 6px 10px;
                }}
            """)
        form.addRow("Usuario *:", self.username)

        # Contraseñas (solo para nuevo)
        if not self.usuario:
            self.password = QLineEdit()
            self.password.setEchoMode(QLineEdit.Password)
            self.password.setPlaceholderText("Mínimo 6 caracteres")
            style_input(self.password)
            form.addRow("Contraseña *:", self.password)

            self.password2 = QLineEdit()
            self.password2.setEchoMode(QLineEdit.Password)
            self.password2.setPlaceholderText("Repita la contraseña")
            style_input(self.password2)
            form.addRow("Confirmar *:", self.password2)

        # Rol
        self.rol = QComboBox()
        self.rol.addItems(["usuario", "admin"])
        self.rol.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        if self.usuario:
            self.rol.setCurrentText(self.usuario['rol'])
        style_input(self.rol)
        form.addRow("Rol *:", self.rol)

        layout.addLayout(form)
        layout.addStretch()
        self.content_layout.addLayout(layout)

        # Botones
        self.btn_guardar.setText(f"{ICONS['save']} Guardar")
        style_button(self.btn_guardar, 'primary')
        self.btn_cancelar.setText(f"{ICONS['cancel']} Cancelar")
        style_button(self.btn_cancelar, 'ghost')

        self.set_save_callback(self.guardar)

    def guardar(self):
        nombre = self.nombre.text().strip()

        if not nombre:
            show_warning(self,
                         f"{ICONS['warning']} Error",
                         "El nombre es obligatorio")
            return

        try:
            if self.usuario:
                # Editar
                data = {'nombre': nombre, 'rol': self.rol.currentText()}
                self.service.actualizar_usuario(self.usuario['id'], data)
                QMessageBox.information(self,
                                        f"{ICONS['success']} Éxito",
                                        "Usuario actualizado")
                self.accept()
            else:
                # Nuevo
                username = self.username.text().strip()
                pwd = self.password.text()
                pwd2 = self.password2.text()

                if not username:
                    show_warning(self,
                                 f"{ICONS['warning']} Error",
                                 "El usuario es obligatorio")
                    return
                if not pwd or len(pwd) < 6:
                    show_warning(self,
                                 f"{ICONS['warning']} Error",
                                 "La contraseña debe tener al menos 6 caracteres")
                    return
                if pwd != pwd2:
                    show_warning(self,
                                 f"{ICONS['warning']} Error",
                                 "Las contraseñas no coinciden")
                    return

                self.service.crear_usuario(
                    username, pwd, nombre, self.rol.currentText())
                QMessageBox.information(self,
                                        f"{ICONS['success']} Éxito",
                                        "Usuario creado correctamente")
                self.accept()

        except DuplicateError as e:
            show_warning(self, f"{ICONS['warning']} Duplicado", str(e))
        except Exception as e:
            show_error(self, "No se pudo guardar el usuario.", e)
