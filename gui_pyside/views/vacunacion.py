# gui_pyside/views/vacunacion.py
"""Vista de vacunación y desparasitación para PySide6"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QFrame, QMessageBox,
                               QComboBox)
from PySide6.QtCore import Signal

from gui_pyside.components.components import DataTable, SearchBar, ErrorHandler
from gui_pyside.dialogs.vacuna_dialog import NuevaVacunacionDialog, DetalleVacunacionDialog
from gui_pyside.utils.messages import show_error, show_warning
from services.vacuna_service import VacunaService
from config import QT_STYLES
from utils.logger import setup_logger

logger = setup_logger()


class VacunacionView(QWidget):
    """Vista principal de vacunación y desparasitación"""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = VacunaService()
        self.current_filtros = {}
        self._all_data = []  # Para filtrado en memoria
        self.setObjectName("vacunacionView")

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

        titulo = QLabel("Vacunación y Desparasitación")
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
        btn_nueva = QPushButton("➕ Registrar")
        btn_nueva.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['accent']};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: #256B5E;
            }}
        """)
        btn_nueva.clicked.connect(self._nueva_vacunacion)
        header_layout.addWidget(btn_nueva)

        btn_proximas = QPushButton("🔔 Próximas")
        btn_proximas.setStyleSheet("""
            QPushButton {{
                background-color: #7F77DD;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 110px;
            }}
            QPushButton:hover {{
                background-color: #534AB7;
            }}
        """)
        btn_proximas.clicked.connect(self._ver_proximas)
        header_layout.addWidget(btn_proximas)

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

        # Filtro por tipo
        lbl_tipo = QLabel("Tipo:")
        lbl_tipo.setStyleSheet(f"color: {QT_STYLES['gray']};")
        filtros_layout.addWidget(lbl_tipo)

        self.tipo_filter = QComboBox()
        self.tipo_filter.addItems(['Todos', 'Vacuna', 'Desparasitación'])
        self.tipo_filter.setFixedWidth(150)
        self.tipo_filter.currentTextChanged.connect(self._filtrar_tipo)
        filtros_layout.addWidget(self.tipo_filter)

        filtros_layout.addStretch()

        # Label para próximas
        self.lbl_proximas = QLabel("")
        self.lbl_proximas.setStyleSheet(
            f"color: {QT_STYLES['danger']}; font-weight: bold;")
        filtros_layout.addWidget(self.lbl_proximas)

        parent_layout.addWidget(filtros_widget)

    def _crear_tabla(self, parent_layout):
        """Crea la tabla de vacunaciones"""
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
            }
        """)
        table_layout = QVBoxLayout(table_container)

        # Columnas: ID, Código, Paciente, Cód. Animal, Especie, Tipo, Producto,
        # Lote, Dosis, Vía, F. Aplicación, F. Próxima, Veterinario
        columns = ['ID', 'Código', 'Paciente', 'Cód. Animal', 'Especie',
                   'Tipo', 'Producto', 'Lote', 'Dosis', 'Vía',
                   'F. Aplicación', 'F. Próxima', 'Veterinario']
        col_widths = [45, 80, 120, 90, 80, 100, 160, 80, 80, 70, 110, 110, 120]

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

        action_layout.addStretch()

        parent_layout.addWidget(action_bar)

    @ErrorHandler.handle_exception
    def _cargar_datos(self):
        """Carga los datos en la tabla"""
        try:
            # Construir filtros
            filtros = self.current_filtros.copy()

            # Obtener datos
            self._all_data = self.service.listar(filtros)
            logger.debug(
                f"VacunacionView: {len(self._all_data)} registros recibidos")

            self._render(self._all_data)

            # Actualizar aviso de próximas
            self._actualizar_proximas()

        except Exception as e:
            show_error(self, "No se pudieron cargar los datos.", e)

    def _render(self, data):
        """Renderiza los datos en la tabla"""
        def row_getter(v):
            return [
                str(v.id),
                v.codigo or '',
                v.animal_nombre or '—',
                v.animal_codigo or '—',
                v.especie or '—',
                v.tipo or '',
                v.producto or '',
                v.lote or '—',
                v.dosis or '—',
                v.via or '—',
                v.fecha_aplicacion or '',
                v.fecha_proxima or '—',
                v.veterinario or '—'
            ]

        def tag_getter(v):
            return (v.tipo,)

        self.table.populate(
            data=data,
            row_getter=row_getter,
            tag_getter=tag_getter
        )

    def _actualizar_proximas(self):
        """Actualiza el aviso de próximas vacunaciones"""
        try:
            proximas = self.service.proximas_a_vencer(30)
            if proximas:
                self.lbl_proximas.setText(
                    f"⚠ {len(proximas)} vencen en 30 días")
            else:
                self.lbl_proximas.setText("")
        except Exception:
            self.lbl_proximas.setText("")

    def _buscar(self, texto: str):
        """Filtra por búsqueda en memoria"""
        if not texto:
            self._render(self._all_data)
            return

        t = texto.lower()
        filtrados = [
            v for v in self._all_data
            if (t in (v.animal_nombre or '').lower() or
                t in (v.codigo or '').lower() or
                t in (v.producto or '').lower() or
                t in (v.veterinario or '').lower())
        ]
        self._render(filtrados)

    def _filtrar_tipo(self, tipo: str):
        """Filtra por tipo"""
        if tipo != 'Todos':
            self.current_filtros['tipo'] = tipo
        elif 'tipo' in self.current_filtros:
            del self.current_filtros['tipo']
        self._cargar_datos()

    def _get_selected_id(self):
        """Obtiene el ID del registro seleccionado"""
        vacuna_id = self.table.get_selected_id()
        if not vacuna_id:
            show_warning(self, "Selección", "Por favor seleccione un registro")
        return vacuna_id

    def _nueva_vacunacion(self):
        """Abre diálogo para nueva vacunación"""
        dialog = NuevaVacunacionDialog(self, self._cargar_datos)
        dialog.exec()

    def _ver_proximas(self):
        """Muestra las próximas vacunaciones"""
        try:
            proximas = self.service.proximas_a_vencer(30)
            if not proximas:
                QMessageBox.information(
                    self,
                    "Próximas",
                    "No hay vacunas/desparasitaciones próximas a vencer en 30 días.")
                return
            self._render(proximas)
            self.lbl_proximas.setText(f"Mostrando {len(proximas)} próximas")
        except Exception as e:
            show_error(
                self,
                "No se pudieron cargar las próximas vacunaciones.",
                e)

    def _ver_detalle(self):
        """Abre diálogo de detalle"""
        vacuna_id = self._get_selected_id()
        if vacuna_id:
            dialog = DetalleVacunacionDialog(self, vacuna_id)
            dialog.exec()

    def refresh(self):
        """Refresca los datos"""
        self._cargar_datos()
