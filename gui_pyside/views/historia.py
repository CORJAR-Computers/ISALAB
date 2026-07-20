# gui_pyside/views/historia.py
"""Vista de historias clínicas para PySide6"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QFrame)
from PySide6.QtCore import Signal

from gui_pyside.components.components import DataTable, SearchBar, ErrorHandler
from gui_pyside.utils.messages import show_error, show_warning
from services.historia_service import HistoriaService
from config import QT_STYLES
from utils.logger import setup_logger

logger = setup_logger()


class HistoriaView(QWidget):
    """Vista principal de historias clínicas"""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = HistoriaService()
        self.current_filtros = {}
        self._all_data = []
        self.setObjectName("historiaView")

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

        titulo = QLabel("Historias Clínicas")
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
        btn_nueva = QPushButton("➕ Nueva Historia")
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
        btn_nueva.clicked.connect(self._nueva_historia)
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
        btn_editar.clicked.connect(self._editar_historia)
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
        """Crea la tabla de historias"""
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
            }
        """)
        table_layout = QVBoxLayout(table_container)

        # Columnas: ID, Recepción, Paciente, Cód. Animal, Especie, Fecha,
        # Diagnóstico, Pronóstico, Veterinario
        columns = ['ID', 'Recepción', 'Paciente', 'Cód. Animal', 'Especie',
                   'Fecha', 'Diagnóstico', 'Pronóstico', 'Veterinario']
        col_widths = [45, 90, 130, 90, 80, 100, 200, 100, 130]

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
        btn_editar.clicked.connect(self._editar_historia)
        action_layout.addWidget(btn_editar)

        action_layout.addStretch()

        parent_layout.addWidget(action_bar)

    @ErrorHandler.handle_exception
    def _cargar_datos(self):
        """Carga los datos en la tabla"""
        try:
            # Obtener datos del servicio
            from database.repositories import HistoriaClinicaRepository
            repo = HistoriaClinicaRepository()
            rows = repo.db.fetch_all('''
                SELECT h.*, a.nombre as animal_nombre, a.codigo as animal_codigo,
                       a.especie, r.codigo as recepcion_codigo
                FROM historias_clinicas h
                LEFT JOIN animales a ON h.animal_id = a.id
                LEFT JOIN recepciones r ON h.recepcion_id = r.id
                ORDER BY h.fecha DESC
            ''')

            from database.models import HistoriaClinica
            self._all_data = [HistoriaClinica.from_row(row) for row in rows]

            logger.debug(
                f"HistoriaView: {len(self._all_data)} registros recibidos")

            self._render(self._all_data)

        except Exception as e:
            show_error(self, "No se pudieron cargar los datos.", e)

    def _render(self, data):
        """Renderiza los datos en la tabla"""
        def row_getter(h):
            return [
                str(h.id),
                h.recepcion_codigo or '—',
                h.animal_nombre or '—',
                h.animal_codigo or '—',
                h.especie or '—',
                h.fecha or '',
                h.diagnostico or '—',
                h.pronostico or '—',
                h.veterinario or '—'
            ]

        def tag_getter(h):
            return (h.pronostico or '',)

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
            h for h in self._all_data
            if (t in (h.animal_nombre or '').lower() or
                t in (h.animal_codigo or '').lower() or
                t in (h.diagnostico or '').lower() or
                t in (h.veterinario or '').lower())
        ]
        self._render(filtrados)

    def _get_selected_id(self):
        """Obtiene el ID de la historia seleccionada"""
        historia_id = self.table.get_selected_id()
        if not historia_id:
            show_warning(
                self,
                "Selección",
                "Por favor seleccione una historia clínica")
        return historia_id

    def _nueva_historia(self):
        """Abre diálogo para nueva historia"""
        from gui_pyside.dialogs.historia_dialog import NuevaHistoriaDialog
        dialog = NuevaHistoriaDialog(self, self._cargar_datos)
        dialog.exec()

    def _editar_historia(self):
        """Abre diálogo para editar historia"""
        historia_id = self._get_selected_id()
        if historia_id:
            from gui_pyside.dialogs.historia_dialog import EditarHistoriaDialog
            dialog = EditarHistoriaDialog(
                self, historia_id, self._cargar_datos)
            dialog.exec()

    def _ver_detalle(self):
        """Abre diálogo de detalle"""
        historia_id = self._get_selected_id()
        if historia_id:
            from gui_pyside.dialogs.historia_dialog import DetalleHistoriaDialog
            dialog = DetalleHistoriaDialog(self, historia_id)
            dialog.exec()

    def refresh(self):
        """Refresca los datos"""
        self._cargar_datos()
