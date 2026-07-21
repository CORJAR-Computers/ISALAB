# gui_pyside/views/recepcion.py
"""Vista de recepción de pacientes para PySide6 - MEJORADA"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QFrame, QComboBox)
from PySide6.QtCore import Qt, Signal

from gui_pyside.components.components import DataTable, SearchBar, ErrorHandler
from gui_pyside.dialogs.recepcion_dialog import NuevaRecepcionDialog, EstadoRecepcionDialog, DetalleRecepcionDialog
from gui_pyside.dialogs.historia_dialog import NuevaHistoriaDialog
from gui_pyside.dialogs.consentimiento_dialog import ConsentimientoInformadoDialog
from gui_pyside.utils.messages import show_error, show_warning
from services.recepcion_service import RecepcionService
from services.historia_service import HistoriaService
from config import QT_STYLES, ESTADOS_RECEPCION
from utils.logger import setup_logger

logger = setup_logger()


class RecepcionView(QWidget):
    """Vista principal de recepción de pacientes - CON ACCIONES MEJORADAS"""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = RecepcionService()
        self.historia_service = HistoriaService()
        self.current_filtros = {}
        self.setObjectName("recepcionView")

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

        # Estadísticas
        self._crear_stats(main_layout)

    def _crear_header(self, parent_layout):
        """Crea el header con título y botones"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Recepción de Pacientes")
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
        btn_nueva = QPushButton("📋 Nueva Recepción")
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
        btn_nueva.clicked.connect(self._nueva_recepcion)
        header_layout.addWidget(btn_nueva)

        btn_estado = QPushButton("✎ Actualizar Estado")
        btn_estado.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['primary']};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 150px;
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
        self.estado_filter.addItems(['Todos'] + ESTADOS_RECEPCION)
        self.estado_filter.setFixedWidth(150)
        self.estado_filter.currentTextChanged.connect(self._filtrar_estado)
        filtros_layout.addWidget(self.estado_filter)

        filtros_layout.addStretch()

        # Contador de hoy
        self.lbl_hoy = QLabel("Hoy: —")
        self.lbl_hoy.setStyleSheet(
            f"color: {QT_STYLES['accent']}; font-weight: bold;")
        filtros_layout.addWidget(self.lbl_hoy)

        parent_layout.addWidget(filtros_widget)

    def _crear_tabla(self, parent_layout):
        """Crea la tabla de recepciones"""
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
            }
        """)
        table_layout = QVBoxLayout(table_container)

        # Columnas: ID, Código, Paciente, Cód. Animal, Especie, Propietario,
        #           Fecha/Hora, Motivo, Veterinario, Estado, Próx. Cita, Historia
        columns = ['ID', 'Código', 'Paciente', 'Cód. Animal', 'Especie',
                   'Propietario', 'Fecha/Hora', 'Motivo', 'Veterinario',
                   'Estado', 'Próx. Cita', 'Historia']
        col_widths = [45, 90, 120, 90, 80, 130, 130, 150, 120, 100, 100, 70]

        self.table = DataTable()
        self.table.setup_columns(columns, col_widths)
        self.table.setMinimumHeight(400)
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

        btn_historia = QPushButton("📁 Crear Historia")
        btn_historia.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['accent']};
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: #256B5E;
            }}
        """)
        btn_historia.clicked.connect(self._crear_historia_desde_recepcion)
        action_layout.addWidget(btn_historia)

        btn_consentimiento = QPushButton("📄 Imprimir Consentimiento")
        btn_consentimiento.setStyleSheet("""
            QPushButton {{
                background-color: #7C3AED;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 160px;
            }}
            QPushButton:hover {{
                background-color: #6D28D9;
            }}
        """)
        btn_consentimiento.clicked.connect(self._imprimir_consentimiento)
        action_layout.addWidget(btn_consentimiento)

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

        # Estadísticas
        self.stats_labels = {}
        stats_data = [
            ("total", "Total", QT_STYLES['secondary']),
            ("espera", "En espera", QT_STYLES['warning']),
            ("consulta", "En consulta", QT_STYLES['primary']),
            ("finalizado", "Finalizado", QT_STYLES['success']),
        ]

        for key, label, color in stats_data:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            card_layout = QVBoxLayout(card)

            value_label = QLabel("0")
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 20px;
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
            # Construir filtros
            filtros = self.current_filtros.copy()

            # Obtener datos
            recepciones = self.service.listar_recepciones(filtros)
            logger.debug(
                f"RecepcionView: {
                    len(recepciones)} registros recibidos")

            def row_getter(r):
                # Verificar si tiene historia clínica
                tiene_historia = self._tiene_historia(r.animal_id)

                return [
                    str(r.id),
                    r.codigo or '',
                    r.animal_nombre or '—',
                    r.animal_codigo or '—',
                    r.especie or '—',
                    r.propietario or '—',
                    r.fecha_hora or '',
                    r.motivo or '',
                    r.veterinario or '—',
                    r.estado or '',
                    r.proxima_cita or '—',
                    '📋' if not tiene_historia else '✅'  # Indicador visual
                ]

            def tag_getter(r):
                return (r.estado,)

            self.table.populate(
                data=recepciones,
                row_getter=row_getter,
                tag_getter=tag_getter
            )

            # Actualizar estadísticas
            self._actualizar_stats(recepciones)

            # Actualizar contador de hoy
            hoy = self.service.recepciones_hoy()
            self.lbl_hoy.setText(f"Hoy: {len(hoy)}")

        except Exception as e:
            show_error(self, "No se pudieron cargar los datos.", e)

    def _tiene_historia(self, animal_id):
        """Verifica si un animal tiene historia clínica"""
        try:
            historias = self.historia_service.historias_por_paciente(animal_id)
            return len(historias) > 0
        except Exception:
            return False

    def _actualizar_stats(self, recepciones):
        """Actualiza el panel de estadísticas"""
        total = len(recepciones)
        espera = len([r for r in recepciones if r.estado == 'En espera'])
        consulta = len([r for r in recepciones if r.estado == 'En consulta'])
        finalizado = len([r for r in recepciones if r.estado == 'Finalizado'])

        self.stats_labels['total'].setText(str(total))
        self.stats_labels['espera'].setText(str(espera))
        self.stats_labels['consulta'].setText(str(consulta))
        self.stats_labels['finalizado'].setText(str(finalizado))

    def _buscar(self, texto: str):
        """Filtra por búsqueda"""
        if texto:
            self.current_filtros['busqueda'] = texto
        elif 'busqueda' in self.current_filtros:
            del self.current_filtros['busqueda']
        self._cargar_datos()

    def _filtrar_estado(self, estado: str):
        """Filtra por estado"""
        if estado != 'Todos':
            self.current_filtros['estado'] = estado
        elif 'estado' in self.current_filtros:
            del self.current_filtros['estado']
        self._cargar_datos()

    def _get_selected_id(self):
        """Obtiene el ID de la recepción seleccionada"""
        recepcion_id = self.table.get_selected_id()
        if not recepcion_id:
            show_warning(
                self,
                "Selección",
                "Por favor seleccione una recepción")
        return recepcion_id

    def _get_selected_animal_id(self):
        """Obtiene el ID del animal de la recepción seleccionada"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            # La columna 3 es el código del animal
            item = self.table.item(current_row, 3)
            if item and item.text() and item.text() != '—':
                # El código está en formato "CODIGO", necesitamos obtener el ID
                # Por ahora retornamos None, pero idealmente deberíamos tener
                # el ID
                pass
        return None

    def _nueva_recepcion(self):
        """Abre diálogo para nueva recepción"""
        dialog = NuevaRecepcionDialog(self, self._cargar_datos)
        dialog.exec()

    def _cambiar_estado(self):
        """Abre diálogo para cambiar estado"""
        recepcion_id = self._get_selected_id()
        if recepcion_id:
            dialog = EstadoRecepcionDialog(
                self, recepcion_id, self._cargar_datos)
            dialog.exec()

    def _ver_detalle(self):
        """Abre diálogo de detalle"""
        recepcion_id = self._get_selected_id()
        if recepcion_id:
            dialog = DetalleRecepcionDialog(self, recepcion_id)
            dialog.exec()

    def _crear_historia_desde_recepcion(self):
        """Crea una historia clínica desde la recepción seleccionada"""
        recepcion_id = self._get_selected_id()
        if recepcion_id:
            dialog = NuevaHistoriaDialog(
                self, self._cargar_datos, recepcion_id)
            dialog.exec()

    def _imprimir_consentimiento(self):
        """Abre diálogo para generar consentimiento informado"""
        recepcion_id = self._get_selected_id()
        if not recepcion_id:
            return

        try:
            # Obtener datos de la recepción
            recepcion = self.service.obtener_recepcion(recepcion_id)

            recepcion_data = {
                'id': recepcion.id,
                'codigo': recepcion.codigo,
                'animal_nombre': recepcion.animal_nombre,
                'animal_codigo': recepcion.animal_codigo,
                'especie': recepcion.especie,
                'raza': recepcion.raza if hasattr(
                    recepcion,
                    'raza') else '',
                'propietario': recepcion.propietario,
                'telefono': recepcion.telefono if hasattr(
                    recepcion,
                    'telefono') else '',
                'veterinario': recepcion.veterinario,
            }

            dialog = ConsentimientoInformadoDialog(
                self, recepcion_data=recepcion_data)
            dialog.exec()

        except Exception as e:
            show_error(self, "No se pudo generar el consentimiento.", e)

    def refresh(self):
        """Refresca los datos"""
        self._cargar_datos()
