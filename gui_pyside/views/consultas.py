# gui_pyside/views/consultas.py
"""Vista de consultas ambulatorias para PySide6"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QFrame)
from PySide6.QtCore import Signal

from gui_pyside.components.components import DataTable, SearchBar, ErrorHandler
from gui_pyside.utils.messages import show_error, show_warning
from gui_pyside.dialogs.consulta_dialog import NuevaConsultaDialog, EditarConsultaDialog, DetalleConsultaDialog
from services.consulta_service import ConsultaService
from config import QT_STYLES
from utils.logger import setup_logger

logger = setup_logger()


class ConsultasView(QWidget):
    """Vista principal de consultas ambulatorias"""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = ConsultaService()
        self.current_filtros = {}
        self._all_data = []  # Para filtrado en memoria
        self.setObjectName("consultasView")

        self._build_layout()
        self._cargar_datos()

    def _build_layout(self):
        """Construye el layout de la vista"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header
        self._crear_header(main_layout)

        # Filtros
        self._crear_filtros(main_layout)

        # Tabla
        self._crear_tabla(main_layout)

    def _crear_header(self, parent_layout):
        """Crea el header con título y botones"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Consultas Ambulatorias")
        titulo.setStyleSheet(f"""
            QLabel {{
                color: {QT_STYLES['secondary']};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(titulo)

        header_layout.addStretch()

        # Botones
        btn_nueva = QPushButton("➕ Nueva Consulta")
        btn_nueva.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['accent']};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 160px;
            }}
            QPushButton:hover {{
                background-color: #256B5E;
            }}
        """)
        btn_nueva.clicked.connect(self._nueva_consulta)
        header_layout.addWidget(btn_nueva)

        btn_editar = QPushButton("✎ Editar")
        btn_editar.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['primary']};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {QT_STYLES['secondary']};
            }}
        """)
        btn_editar.clicked.connect(self._editar_consulta)
        header_layout.addWidget(btn_editar)

        btn_refresh = QPushButton("🔄 Refrescar")
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['gray']};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 110px;
            }}
            QPushButton:hover {{
                background-color: {QT_STYLES['secondary']};
            }}
        """)
        btn_refresh.clicked.connect(self._cargar_datos)
        header_layout.addWidget(btn_refresh)

        parent_layout.addWidget(header)

    def _crear_filtros(self, parent_layout):
        """Crea los filtros de búsqueda"""
        filtros_widget = QWidget()
        filtros_layout = QHBoxLayout(filtros_widget)
        filtros_layout.setContentsMargins(0, 0, 0, 0)

        # Barra de búsqueda
        self.search_bar = SearchBar()
        self.search_bar.search_changed.connect(self._buscar)
        filtros_layout.addWidget(self.search_bar)

        filtros_layout.addStretch()

        parent_layout.addWidget(filtros_widget)

    def _crear_tabla(self, parent_layout):
        """Crea la tabla de consultas"""
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
            }
        """)
        table_layout = QVBoxLayout(table_container)

        # Columnas: ID, Código, Paciente, Cód. Animal, Especie, Fecha, Motivo,
        # Tratamiento, Veterinario, Próx. Consulta
        columns = [
            'ID',
            'Código',
            'Paciente',
            'Cód. Animal',
            'Especie',
            'Fecha',
            'Motivo',
            'Tratamiento',
            'Veterinario',
            'Próx. Consulta']
        col_widths = [45, 90, 130, 90, 80, 100, 160, 180, 120, 110]

        self.table = DataTable()
        self.table.setup_columns(columns, col_widths)
        self.table.setMinimumHeight(450)
        self.table.doubleClicked.connect(self._ver_detalle)
        table_layout.addWidget(self.table)

        parent_layout.addWidget(table_container, 1)

        # Botones de acción
        action_bar = QWidget()
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(0, 10, 0, 0)

        btn_detalle = QPushButton("👁 Ver Detalle")
        btn_detalle.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['primary']};
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 120px;
            }}
        """)
        btn_detalle.clicked.connect(self._ver_detalle)
        action_layout.addWidget(btn_detalle)

        btn_editar = QPushButton("✎ Editar")
        btn_editar.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['warning']};
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: #B45309;
            }}
        """)
        btn_editar.clicked.connect(self._editar_consulta)
        action_layout.addWidget(btn_editar)

        action_layout.addStretch()

        parent_layout.addWidget(action_bar)

    @ErrorHandler.handle_exception
    def _cargar_datos(self):
        """Carga los datos en la tabla"""
        try:
            # Obtener datos
            self._all_data = self.service.listar_consultas(
                self.current_filtros)
            logger.debug(
                f"ConsultasView: {len(self._all_data)} registros recibidos")

            self._render(self._all_data)

        except Exception as e:
            show_error(self, "No se pudieron cargar los datos.", e)

    def _render(self, data):
        """Renderiza los datos en la tabla"""
        def row_getter(c):
            return [
                str(c.id),
                c.codigo or '',
                c.animal_nombre or '—',
                c.animal_codigo or '—',
                c.especie or '—',
                c.fecha or '',
                c.motivo or '',
                c.tratamiento or '—',
                c.veterinario or '—',
                c.proxima_consulta or '—'
            ]

        def tag_getter(c):
            tags = []
            if c.proxima_consulta:
                tags.append('proxima')
            return tuple(tags)

        self.table.populate(
            data=data,
            row_getter=row_getter,
            tag_getter=tag_getter
        )

    def _buscar(self, texto: str):
        """Filtra por búsqueda en memoria"""
        if not texto:
            self._render(self._all_data)
            return

        t = texto.lower()
        filtrados = [
            c for c in self._all_data
            if (t in (c.animal_nombre or '').lower() or
                t in (c.codigo or '').lower() or
                t in (c.motivo or '').lower() or
                t in (c.veterinario or '').lower())
        ]
        self._render(filtrados)

    def _get_selected_id(self):
        """Obtiene el ID de la consulta seleccionada"""
        consulta_id = self.table.get_selected_id()
        if not consulta_id:
            show_warning(
                self,
                "Selección",
                "Por favor seleccione una consulta")
        return consulta_id

    def _nueva_consulta(self):
        """Abre diálogo para nueva consulta"""
        dialog = NuevaConsultaDialog(self, self._cargar_datos)
        dialog.exec()

    def _editar_consulta(self):
        """Abre diálogo para editar consulta"""
        consulta_id = self._get_selected_id()
        if consulta_id:
            dialog = EditarConsultaDialog(
                self, consulta_id, self._cargar_datos)
            dialog.exec()

    def _ver_detalle(self):
        """Abre diálogo de detalle"""
        consulta_id = self._get_selected_id()
        if consulta_id:
            dialog = DetalleConsultaDialog(self, consulta_id)
            dialog.exec()

    def refresh(self):
        """Refresca los datos"""
        self._cargar_datos()
