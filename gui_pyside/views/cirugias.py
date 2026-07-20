# gui_pyside/views/cirugias.py
"""Vista de cirugías para PySide6"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QFrame, QComboBox)
from PySide6.QtCore import Signal

from gui_pyside.components.components import DataTable, SearchBar, ErrorHandler
from gui_pyside.utils.messages import show_error, show_warning
from gui_pyside.dialogs.cirugia_dialog import NuevaCirugiaDialog, EstadoCirugiaDialog, DetalleCirugiaDialog
from services.cirugia_service import CirugiaService
from config import QT_STYLES, ESTADOS_CIRUGIA
from utils.logger import setup_logger

logger = setup_logger()


class CirugiasView(QWidget):
    """Vista principal de cirugías"""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = CirugiaService()
        self.current_filtros = {}
        self._all_data = []  # Para filtrado en memoria
        self.setObjectName("cirugiasView")

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

        titulo = QLabel("Registro de Cirugías")
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
        btn_nueva = QPushButton("➕ Programar Cirugía")
        btn_nueva.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['accent']};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 180px;
            }}
            QPushButton:hover {{
                background-color: #256B5E;
            }}
        """)
        btn_nueva.clicked.connect(self._nueva_cirugia)
        header_layout.addWidget(btn_nueva)

        btn_estado = QPushButton("✎ Actualizar Estado")
        btn_estado.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['primary']};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 160px;
            }}
            QPushButton:hover {{
                background-color: {QT_STYLES['secondary']};
            }}
        """)
        btn_estado.clicked.connect(self._cambiar_estado)
        header_layout.addWidget(btn_estado)

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

        filtros_layout.addSpacing(20)

        # Filtro por estado
        lbl_estado = QLabel("Estado:")
        lbl_estado.setStyleSheet(f"color: {QT_STYLES['gray']};")
        filtros_layout.addWidget(lbl_estado)

        self.estado_filter = QComboBox()
        self.estado_filter.addItems(['Todos'] + ESTADOS_CIRUGIA)
        self.estado_filter.setFixedWidth(150)
        self.estado_filter.currentTextChanged.connect(self._filtrar_estado)
        filtros_layout.addWidget(self.estado_filter)

        filtros_layout.addStretch()

        parent_layout.addWidget(filtros_widget)

    def _crear_tabla(self, parent_layout):
        """Crea la tabla de cirugías"""
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
            }
        """)
        table_layout = QVBoxLayout(table_container)

        # Columnas: ID, Código, Paciente, Cód. Animal, Especie, Fecha, Tipo
        # Cirugía, Anestesia, Cirujano, Duración, Estado
        columns = [
            'ID',
            'Código',
            'Paciente',
            'Cód. Animal',
            'Especie',
            'Fecha',
            'Tipo Cirugía',
            'Anestesia',
            'Cirujano',
            'Duración',
            'Estado']
        col_widths = [45, 90, 120, 90, 80, 100, 170, 130, 130, 80, 100]

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

        btn_estado = QPushButton("✎ Cambiar Estado")
        btn_estado.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['warning']};
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: #B45309;
            }}
        """)
        btn_estado.clicked.connect(self._cambiar_estado)
        action_layout.addWidget(btn_estado)

        action_layout.addStretch()

        parent_layout.addWidget(action_bar)

    @ErrorHandler.handle_exception
    def _cargar_datos(self):
        """Carga los datos en la tabla"""
        try:
            # Construir filtros
            filtros = self.current_filtros.copy()

            # Obtener datos
            self._all_data = self.service.listar_cirugias(filtros)
            logger.debug(
                f"CirugiasView: {len(self._all_data)} registros recibidos")

            self._render(self._all_data)

        except Exception as e:
            show_error(self, "No se pudieron cargar los datos.", e)

    def _render(self, data):
        """Renderiza los datos en la tabla"""
        def row_getter(cg):
            return [
                str(cg.id),
                cg.codigo or '',
                cg.animal_nombre or '—',
                cg.animal_codigo or '—',
                cg.especie or '—',
                cg.fecha or '',
                cg.tipo_cirugia or '',
                cg.anestesia or '—',
                cg.cirujano or '—',
                f"{cg.duracion_min} min" if cg.duracion_min else '—',
                cg.estado or ''
            ]

        def tag_getter(cg):
            return (cg.estado,)

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
            cg for cg in self._all_data
            if (t in (cg.animal_nombre or '').lower() or
                t in (cg.codigo or '').lower() or
                t in (cg.tipo_cirugia or '').lower() or
                t in (cg.cirujano or '').lower())
        ]
        self._render(filtrados)

    def _filtrar_estado(self, estado: str):
        """Filtra por estado"""
        if estado != 'Todos':
            self.current_filtros['estado'] = estado
        elif 'estado' in self.current_filtros:
            del self.current_filtros['estado']
        self._cargar_datos()

    def _get_selected_id(self):
        """Obtiene el ID de la cirugía seleccionada"""
        cirugia_id = self.table.get_selected_id()
        if not cirugia_id:
            show_warning(self, "Selección", "Por favor seleccione una cirugía")
        return cirugia_id

    def _nueva_cirugia(self):
        """Abre diálogo para nueva cirugía"""
        dialog = NuevaCirugiaDialog(self, self._cargar_datos)
        dialog.exec()

    def _cambiar_estado(self):
        """Abre diálogo para cambiar estado"""
        cirugia_id = self._get_selected_id()
        if cirugia_id:
            dialog = EstadoCirugiaDialog(self, cirugia_id, self._cargar_datos)
            dialog.exec()

    def _ver_detalle(self):
        """Abre diálogo de detalle"""
        cirugia_id = self._get_selected_id()
        if cirugia_id:
            dialog = DetalleCirugiaDialog(self, cirugia_id)
            dialog.exec()

    def refresh(self):
        """Refresca los datos"""
        self._cargar_datos()
