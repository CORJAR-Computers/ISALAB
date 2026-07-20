# gui_pyside/views/animales.py
"""Vista de gestión de pacientes para PySide6"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QFrame, QComboBox)
from PySide6.QtCore import Qt, Signal

from gui_pyside.components.components import DataTable, SearchBar, ErrorHandler
from gui_pyside.utils.messages import show_error, show_warning
from gui_pyside.dialogs.animal_dialog import (
    NuevoAnimalDialog, EditarAnimalDialog,
    SalidaAnimalDialog, DetalleAnimalDialog
)
from services.animal_service import AnimalService
from config import QT_STYLES, ESTADOS_ANIMAL
from utils.logger import setup_logger

logger = setup_logger()


class AnimalesView(QWidget):
    """Vista principal de gestión de pacientes"""

    # Señal para notificar cuando hay cambios
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = AnimalService()
        self.current_filtros = {}
        self.setObjectName("animalesView")

        self._build_layout()
        self._cargar_datos()

    def _build_layout(self):
        """Construye el layout de la vista"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header con título y acciones
        self._crear_header(main_layout)

        # Filtros y búsqueda
        self._crear_filtros(main_layout)

        # Tabla de datos
        self._crear_tabla(main_layout)

        # Estadísticas
        self._crear_stats(main_layout)

    def _crear_header(self, parent_layout):
        """Crea el header con título y botones"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Gestión de Pacientes")
        titulo.setStyleSheet(f"""
            QLabel {{
                color: {QT_STYLES['secondary']};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(titulo)

        header_layout.addStretch()

        # Botones de acción
        btn_nuevo = QPushButton("➕ Nuevo Paciente")
        btn_nuevo.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['accent']};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: #256B5E;
            }}
        """)
        btn_nuevo.clicked.connect(self._nuevo_animal)
        header_layout.addWidget(btn_nuevo)

        btn_refresh = QPushButton("🔄 Refrescar")
        btn_refresh.setStyleSheet(f"""
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
        self.estado_filter.addItems(['Todos'] + ESTADOS_ANIMAL)
        self.estado_filter.setFixedWidth(150)
        self.estado_filter.currentTextChanged.connect(self._filtrar_por_estado)
        filtros_layout.addWidget(self.estado_filter)

        filtros_layout.addSpacing(20)

        # Filtro por especie
        lbl_especie = QLabel("Especie:")
        lbl_especie.setStyleSheet(f"color: {QT_STYLES['gray']};")
        filtros_layout.addWidget(lbl_especie)

        self.especie_filter = QComboBox()
        self.especie_filter.addItems(['Todas', 'Perro', 'Gato', 'Otro'])
        self.especie_filter.setFixedWidth(120)
        self.especie_filter.currentTextChanged.connect(
            self._filtrar_por_especie)
        filtros_layout.addWidget(self.especie_filter)

        filtros_layout.addStretch()

        parent_layout.addWidget(filtros_widget)

    def _crear_tabla(self, parent_layout):
        """Crea la tabla de pacientes"""
        # Frame contenedor
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
            }
        """)
        table_layout = QVBoxLayout(table_container)

        # Tabla
        columns = ['ID', 'Código', 'Nombre', 'Especie', 'Raza', 'Edad',
                   'Propietario', 'Teléfono', 'Estado', 'F. Ingreso']
        col_widths = [50, 90, 120, 80, 100, 50, 120, 100, 100, 90]

        self.table = DataTable()
        self.table.setup_columns(columns, col_widths)
        self.table.setMinimumHeight(400)
        table_layout.addWidget(self.table)

        parent_layout.addWidget(table_container, 1)  # 1 = expande

        # Botones de acción para fila seleccionada
        action_bar = QWidget()
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(0, 10, 0, 0)

        btn_ver = QPushButton("👁 Ver Detalle")
        btn_ver.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['primary']};
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 120px;
            }}
        """)
        btn_ver.clicked.connect(self._ver_detalle)
        action_layout.addWidget(btn_ver)

        btn_editar = QPushButton("✏ Editar")
        btn_editar.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['gray']};
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {QT_STYLES['secondary']};
            }}
        """)
        btn_editar.clicked.connect(self._editar_animal)
        action_layout.addWidget(btn_editar)

        btn_salida = QPushButton("📤 Registrar Salida")
        btn_salida.setStyleSheet(f"""
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
        btn_salida.clicked.connect(self._registrar_salida)
        action_layout.addWidget(btn_salida)

        action_layout.addStretch()

        parent_layout.addWidget(action_bar)

    def _crear_stats(self, parent_layout):
        """Crea panel de estadísticas"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {QT_STYLES['light_bg']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        stats_layout = QHBoxLayout(stats_frame)

        # Estas etiquetas se actualizarán en _cargar_datos
        self.stats_labels = {}
        stats_data = [
            ("total", "Total Pacientes", QT_STYLES['secondary']),
            ("activos", "Activos", QT_STYLES['success']),
            ("tratamiento", "En Tratamiento", QT_STYLES['warning']),
            ("cuarentena", "Cuarentena", QT_STYLES['danger']),
        ]

        for key, label, color in stats_data:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 10px;
                }}
            """)
            card_layout = QVBoxLayout(card)

            value_label = QLabel("0")
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 24px;
                    font-weight: bold;
                }}
            """)
            card_layout.addWidget(value_label)
            self.stats_labels[key] = value_label

            title_label = QLabel(label)
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("color: #64748B; font-size: 11px;")
            card_layout.addWidget(title_label)

            stats_layout.addWidget(card)

        parent_layout.addWidget(stats_frame)

    @ErrorHandler.handle_exception
    def _cargar_datos(self):
        """Carga los datos en la tabla"""
        try:
            # Obtener datos del servicio (limitado a 100 para optimizar carga)
            animales = self.service.listar_animales(self.current_filtros, limit=100)
            logger.debug(f"AnimalesView: {len(animales)} registros recibidos")

            # Definir función para obtener valores de fila
            def row_getter(animal):
                return [
                    str(animal.id),
                    animal.codigo or '',
                    animal.nombre or '',
                    animal.especie or '',
                    animal.raza or '—',
                    str(animal.edad) if animal.edad else '—',
                    animal.propietario or '—',
                    animal.telefono or '—',
                    animal.estado or '',
                    animal.fecha_ingreso or ''
                ]

            # Definir función para tags de color
            def tag_getter(animal):
                return (animal.estado,)

            # Poblar la tabla
            self.table.populate(
                data=animales,
                row_getter=row_getter,
                tag_getter=tag_getter
            )

            # Actualizar estadísticas
            self._actualizar_stats(animales)

        except Exception as e:
            show_error(self, "No se pudieron cargar los datos.", e)

    def _actualizar_stats(self, animales):
        """Actualiza el panel de estadísticas"""
        total = len(animales)
        activos = len([a for a in animales if a.estado == 'Activo'])
        tratamiento = len(
            [a for a in animales if a.estado == 'En Tratamiento'])
        cuarentena = len([a for a in animales if a.estado == 'Cuarentena'])

        self.stats_labels['total'].setText(str(total))
        self.stats_labels['activos'].setText(str(activos))
        self.stats_labels['tratamiento'].setText(str(tratamiento))
        self.stats_labels['cuarentena'].setText(str(cuarentena))

    def _buscar(self, texto: str):
        """Filtra por búsqueda"""
        if texto:
            self.current_filtros['busqueda'] = texto
        elif 'busqueda' in self.current_filtros:
            del self.current_filtros['busqueda']
        self._cargar_datos()

    def _filtrar_por_estado(self, estado: str):
        """Filtra por estado"""
        if estado != 'Todos':
            self.current_filtros['estado'] = estado
        elif 'estado' in self.current_filtros:
            del self.current_filtros['estado']
        self._cargar_datos()

    def _filtrar_por_especie(self, especie: str):
        """Filtra por especie"""
        if especie != 'Todas':
            self.current_filtros['especie'] = especie
        elif 'especie' in self.current_filtros:
            del self.current_filtros['especie']
        self._cargar_datos()

    def _get_selected_id(self):
        """Obtiene el ID del registro seleccionado"""
        animal_id = self.table.get_selected_id()
        if not animal_id:
            show_warning(self, "Selección", "Por favor seleccione un paciente")
        return animal_id

    def _nuevo_animal(self):
        """Abre diálogo para nuevo paciente"""
        dialog = NuevoAnimalDialog(self, self._cargar_datos)
        dialog.exec()

    def _ver_detalle(self):
        """Abre diálogo de detalle del paciente seleccionado"""
        animal_id = self._get_selected_id()
        if animal_id:
            dialog = DetalleAnimalDialog(self, animal_id)
            dialog.exec()

    def _editar_animal(self):
        """Abre diálogo para editar paciente"""
        animal_id = self._get_selected_id()
        if animal_id:
            dialog = EditarAnimalDialog(self, animal_id, self._cargar_datos)
            dialog.exec()

    def _registrar_salida(self):
        """Abre diálogo para registrar salida"""
        animal_id = self._get_selected_id()
        if animal_id:
            dialog = SalidaAnimalDialog(self, animal_id, self._cargar_datos)
            dialog.exec()

    def refresh(self):
        """Refresca los datos (llamado desde la app principal)"""
        self._cargar_datos()
