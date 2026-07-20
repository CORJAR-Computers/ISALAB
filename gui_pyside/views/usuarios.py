# gui_pyside/views/usuarios.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox)
from PySide6.QtCore import Qt, Signal
from services.usuario_service import UsuarioService
from gui_pyside.dialogs.usuario_dialog import UsuarioDialog
from gui_pyside.components.components import ErrorHandler
from config import QT_STYLES


class UsuariosView(QWidget):
    data_changed = Signal()

    def __init__(self, parent=None, usuario_actual=None):
        super().__init__(parent)
        self.service = UsuarioService(usuario_actual)
        self.usuario_actual = usuario_actual
        self.setObjectName("usuariosView")
        self._build_layout()
        self._cargar_datos()

    def _build_layout(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Gestión de Usuarios")
        titulo.setStyleSheet(
            f"color: {
                QT_STYLES['secondary']}; font-size: 24px; font-weight: bold;")
        header_layout.addWidget(titulo)

        header_layout.addStretch()

        btn_nuevo = QPushButton("➕ Nuevo Usuario")
        btn_nuevo.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['accent']};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
        """)
        btn_nuevo.clicked.connect(self._nuevo_usuario)
        header_layout.addWidget(btn_nuevo)

        btn_refresh = QPushButton("🔄 Refrescar")
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['gray']};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }}
        """)
        btn_refresh.clicked.connect(self._cargar_datos)
        header_layout.addWidget(btn_refresh)

        layout.addWidget(header)

        # Checkbox para mostrar inactivos
        self.mostrar_inactivos = QCheckBox("Mostrar usuarios inactivos")
        self.mostrar_inactivos.stateChanged.connect(self._cargar_datos)
        layout.addWidget(self.mostrar_inactivos)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Usuario", "Nombre", "Rol", "Estado", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    @ErrorHandler.handle_exception
    def _cargar_datos(self, *args):
        solo_activos = not self.mostrar_inactivos.isChecked()
        usuarios = self.service.listar_usuarios(solo_activos)
        self.table.setRowCount(len(usuarios))

        for row, user in enumerate(usuarios):
            self.table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(user['username']))
            self.table.setItem(row, 2, QTableWidgetItem(user['nombre']))
            self.table.setItem(row, 3, QTableWidgetItem(user['rol']))

            estado = "Activo" if user['activo'] else "Inactivo"
            estado_item = QTableWidgetItem(estado)
            if not user['activo']:
                estado_item.setForeground(Qt.red)
            self.table.setItem(row, 4, estado_item)

            # Botones de acción (editar y activar/desactivar)
            acciones_widget = QWidget()
            acciones_layout = QHBoxLayout(acciones_widget)
            acciones_layout.setContentsMargins(5, 2, 5, 2)

            btn_editar = QPushButton("✎")
            btn_editar.setFixedSize(30, 25)
            btn_editar.clicked.connect(
                lambda _, uid=user['id']: self._editar_usuario(uid))
            acciones_layout.addWidget(btn_editar)

            if user['activo']:
                btn_toggle = QPushButton("🔴 Desactivar")
                btn_toggle.clicked.connect(
                    lambda _, uid=user['id']: self._desactivar_usuario(uid))
            else:
                btn_toggle = QPushButton("🟢 Activar")
                btn_toggle.clicked.connect(
                    lambda _, uid=user['id']: self._activar_usuario(uid))
            acciones_layout.addWidget(btn_toggle)

            acciones_layout.addStretch()
            self.table.setCellWidget(row, 5, acciones_widget)

    def _nuevo_usuario(self):
        dialog = UsuarioDialog(self, usuario_actual=self.usuario_actual)
        if dialog.exec():
            self._cargar_datos()

    def _editar_usuario(self, usuario_id):
        try:
            usuario = self.service.obtener_usuario(usuario_id)
            dialog = UsuarioDialog(self, usuario, self.usuario_actual)
            if dialog.exec():
                self._cargar_datos()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _desactivar_usuario(self, usuario_id):
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "¿Desactivar este usuario?",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.service.desactivar_usuario(usuario_id)
                self._cargar_datos()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _activar_usuario(self, usuario_id):
        try:
            self.service.activar_usuario(usuario_id)
            self._cargar_datos()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def refresh(self):
        self._cargar_datos()
