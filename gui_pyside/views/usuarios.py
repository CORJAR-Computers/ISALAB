# gui_pyside/views/usuarios.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QDialog)
from PySide6.QtCore import Qt, Signal
from services.usuario_service import UsuarioService
from gui_pyside.dialogs.usuario_dialog import UsuarioDialog
from gui_pyside.components.components import ErrorHandler, DataTable
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
        # Fase 6 (G-M10): antes se conectaba ``stateChanged`` directo
        # a ``self._cargar_datos``, que tenía que aceptar ``*args``
        # para tragarse el ``int`` (0/2) que emite ``stateChanged``.
        # Esto es anti-idiomático: la firma del método quedaba
        # sucia para todos los callers internos. Ahora el lambda
        # descarta el argumento y ``_cargar_datos`` vuelve a ser
        # una firma limpia sin ``*args``.
        self.mostrar_inactivos.stateChanged.connect(
            lambda _: self._cargar_datos())
        layout.addWidget(self.mostrar_inactivos)

        # Tabla. Fase 6 (G-L9): antes se instanciaba ``QTableWidget``
        # directo y se configuraba a mano (columnCount, headers,
        # resize mode, selection behavior, edit triggers, vertical
        # header). El resto del codebase usa ``DataTable`` que ya
        # encapsula todo eso en ``__init__`` + ``setup_columns``.
        # Ahora usamos ``DataTable`` para consistencia visual y de
        # código. La API es ligeramente distinta (``setup_columns``
        # en lugar de ``setColumnCount`` + ``setHorizontalHeaderLabels``)
        # pero el resultado es equivalente.
        self.table = DataTable()
        self.table.setup_columns(
            ["ID", "Usuario", "Nombre", "Rol", "Estado", "Acciones"],
            col_widths=[60, 140, None, 100, 100, 220]
        )
        # La columna "Nombre" (índice 2) se estira para rellenar el
        # ancho disponible. ``setup_columns`` con ``col_widths=None``
        # estira TODAS las columnas; aquí queremos que solo "Nombre"
        # lo haga, así que seteamos el modo manualmente después.
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        # Las columnas con ancho fijo (0,1,3,4,5) ya las configuró
        # ``setup_columns`` via ``setColumnWidth``.
        layout.addWidget(self.table)

    @ErrorHandler.handle_exception
    def _cargar_datos(self):
        # Fase 6 (G-M10): firma limpia sin ``*args``. El lambda en
        # el ``connect`` descarta el int del ``stateChanged``.
        solo_activos = not self.mostrar_inactivos.isChecked()
        usuarios = self.service.listar_usuarios(solo_activos)
        self.table.setRowCount(len(usuarios))

        # Fase 6 (G-L9): como esta tabla tiene widgets interactivos
        # (botones Editar/Activar/Desactivar) en la columna 5, no
        # podemos usar ``DataTable.populate()`` (que solo setea texto).
        # Llenamos las celdas manualmente con ``setItem`` para las
        # columnas de texto y ``setCellWidget`` para los botones.
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
        # Fase 5 (H-G6): ``QDialog.exec()`` retorna un ``int`` (0 para
        #Rejected, 1 para Accepted). ``if dialog.exec():`` funciona por
        # accidente porque 1 es truthy, pero es frágil y no idiomático.
        # Comparar contra ``QDialog.Accepted`` es el patrón correcto.
        if dialog.exec() == QDialog.Accepted:
            self._cargar_datos()

    def _editar_usuario(self, usuario_id):
        try:
            usuario = self.service.obtener_usuario(usuario_id)
            dialog = UsuarioDialog(self, usuario, self.usuario_actual)
            # Fase 5 (H-G6): mismo patrón que en ``_nuevo_usuario``.
            if dialog.exec() == QDialog.Accepted:
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
