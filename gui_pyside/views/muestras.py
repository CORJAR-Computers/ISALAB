# gui_pyside/views/muestras.py
"""Vista de gestión de muestras para PySide6 - CORREGIDA"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QFrame, QMessageBox,
                               QComboBox, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, Signal

from gui_pyside.components.components import DataTable, SearchBar
from gui_pyside.utils.messages import show_error, show_warning
from gui_pyside.dialogs.muestra_dialog import NuevaMuestraDialog, ResultadoMuestraDialog, DetalleMuestraDialog
from services.muestra_service import MuestraService
from config import QT_STYLES, TIPOS_MUESTRA, ESTADOS_MUESTRA


class MuestrasView(QWidget):
    """Vista principal de gestión de muestras"""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = MuestraService()
        self.current_filtros = {}
        self._search_text = ""
        self.setObjectName("muestrasView")

        self._build_layout()
        self._cargar_datos()

    def _build_layout(self):
        """Construye el layout de la vista"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        self._crear_header(main_layout)
        self._crear_filtros_rapidos(main_layout)
        self._crear_filtros(main_layout)
        self._crear_tabla(main_layout)
        self._crear_stats(main_layout)

    def _crear_header(self, parent_layout):
        header_layout = QHBoxLayout()

        titulo = QLabel("Gestión de Muestras de Laboratorio")
        titulo.setStyleSheet(
            f"color: {
                QT_STYLES['secondary']}; font-size: 22px; font-weight: bold;")
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        btn_nueva = QPushButton("➕ Nueva Muestra")
        btn_nueva.setCursor(Qt.PointingHandCursor)
        btn_nueva.setStyleSheet(
            f"background-color: {
                QT_STYLES['primary']}; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        btn_nueva.clicked.connect(self._nueva_muestra)

        btn_resultados = QPushButton("🧪 Ingresar Resultados")
        btn_resultados.setCursor(Qt.PointingHandCursor)
        btn_resultados.setStyleSheet(
            f"background-color: {
                QT_STYLES['accent']}; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        btn_resultados.clicked.connect(self._ingresar_resultados)

        btn_detalle = QPushButton("🔍 Ver / Imprimir")
        btn_detalle.setCursor(Qt.PointingHandCursor)
        btn_detalle.setStyleSheet(
            f"background-color: {
                QT_STYLES['gray']}; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        btn_detalle.clicked.connect(self._ver_detalle)

        header_layout.addWidget(btn_nueva)
        header_layout.addWidget(btn_resultados)
        header_layout.addWidget(btn_detalle)

        parent_layout.addLayout(header_layout)

    def _crear_filtros_rapidos(self, parent_layout):
        filtros_widget = QWidget()
        filtros_layout = QHBoxLayout(filtros_widget)
        filtros_layout.setContentsMargins(0, 0, 0, 0)

        lbl_mostrar = QLabel("Mostrar:")
        lbl_mostrar.setStyleSheet(
            f"color: {QT_STYLES['gray']}; font-weight: bold;")
        filtros_layout.addWidget(lbl_mostrar)

        self.filtro_grupo = QButtonGroup(self)
        opciones = [
            "Todas",
            "Pendientes",
            "En Proceso",
            "Completadas",
            "Urgentes"]

        for opcion in opciones:
            radio = QRadioButton(opcion)
            radio.setStyleSheet(
                f"QRadioButton {{ color: {QT_STYLES['dark']}; }}")
            self.filtro_grupo.addButton(radio)
            filtros_layout.addWidget(radio)

        if self.filtro_grupo.buttons():
            self.filtro_grupo.buttons()[0].setChecked(True)

        self.filtro_grupo.buttonClicked.connect(self._filtrar_rapido)
        filtros_layout.addStretch()
        parent_layout.addWidget(filtros_widget)

    def _crear_filtros(self, parent_layout):
        filtros_widget = QWidget()
        filtros_layout = QHBoxLayout(filtros_widget)
        filtros_layout.setContentsMargins(0, 0, 0, 0)

        self.search_bar = SearchBar()
        self.search_bar.search_changed.connect(self._buscar)
        filtros_layout.addWidget(self.search_bar)

        filtros_layout.addSpacing(20)

        lbl_estado = QLabel("Estado:")
        lbl_estado.setStyleSheet(f"color: {QT_STYLES['gray']};")
        filtros_layout.addWidget(lbl_estado)

        self.estado_filter = QComboBox()
        self.estado_filter.addItems(['Todos'] + ESTADOS_MUESTRA)
        self.estado_filter.setFixedWidth(130)
        self.estado_filter.currentTextChanged.connect(self._filtrar_estado)
        filtros_layout.addWidget(self.estado_filter)

        filtros_layout.addSpacing(20)

        lbl_tipo = QLabel("Tipo:")
        lbl_tipo.setStyleSheet(f"color: {QT_STYLES['gray']};")
        filtros_layout.addWidget(lbl_tipo)

        self.tipo_filter = QComboBox()
        self.tipo_filter.addItems(['Todos'] + TIPOS_MUESTRA)
        self.tipo_filter.setFixedWidth(130)
        self.tipo_filter.currentTextChanged.connect(self._filtrar_tipo)
        filtros_layout.addWidget(self.tipo_filter)

        filtros_layout.addStretch()
        parent_layout.addWidget(filtros_widget)

    def _crear_tabla(self, parent_layout):
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
            }
        """)
        table_layout = QVBoxLayout(table_container)

        columns = ['ID', 'Código', 'Animal', 'Especie', 'Tipo',
                   'F. Recolección', 'Estado', 'Urgente', 'Técnico']
        col_widths = [50, 110, 130, 90, 100, 110, 100, 70, 120]

        self.table = DataTable()
        self.table.setup_columns(columns, col_widths)
        self.table.setMinimumHeight(400)

        # ✅ SOLUCIÓN AL CRASH: Usamos un lambda para ignorar el argumento 'index'
        self.table.doubleClicked.connect(
            lambda index: self._ingresar_resultados())

        table_layout.addWidget(self.table)
        parent_layout.addWidget(table_container, 1)

    def _crear_stats(self, parent_layout):
        stats_frame = QFrame()
        stats_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {QT_STYLES['light_bg']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        stats_layout = QHBoxLayout(stats_frame)

        self.stats_labels = {}
        stats_data = [
            ("total", "Total", QT_STYLES['secondary']),
            ("pendientes", "Pendientes", QT_STYLES['warning']),
            ("proceso", "En Proceso", QT_STYLES['primary']),
            ("completadas", "Completadas", QT_STYLES['success']),
            ("urgentes", "⚠ Urgentes", QT_STYLES['danger']),
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

    # ✅ SOLUCIÓN: Quitamos el decorador para evitar conflictos con el try/except interno
    def _cargar_datos(self):
        """Carga los datos en la tabla"""
        try:
            filtros = self.current_filtros.copy()
            muestras = self.service.listar_muestras(filtros)

            if self._search_text:
                q = self._search_text.lower()
                muestras = [
                    m for m in muestras
                    if (q in (m.codigo or '').lower() or
                        q in (m.animal_nombre or '').lower() or
                        q in (m.animal_codigo or '').lower() or
                        q in (m.tipo_muestra or '').lower() or
                        q in (m.tecnico or '').lower())
                ]

            def row_getter(m):
                return [
                    str(m.id),
                    m.codigo or '',
                    f"{m.animal_nombre} ({m.animal_codigo})" if m.animal_nombre else '—',
                    m.especie or '—',
                    m.tipo_muestra or '',
                    m.fecha_recoleccion or '',
                    m.estado or '',
                    '⚠' if m.urgente else '—',
                    m.tecnico or '—'
                ]

            def tag_getter(m):
                tags = [m.estado]
                if m.urgente:
                    tags.append('urgente')
                return tuple(tags)

            self.table.populate(
                data=muestras,
                row_getter=row_getter,
                tag_getter=tag_getter)
            self._actualizar_stats(muestras)

        except Exception as e:
            show_error(self, "No se pudieron cargar las muestras.", e)

    def _actualizar_stats(self, muestras):
        total = len(muestras)
        pendientes = len([m for m in muestras if m.estado == 'Pendiente'])
        proceso = len([m for m in muestras if m.estado == 'En Proceso'])
        completadas = len([m for m in muestras if m.estado == 'Completado'])
        urgentes = len([m for m in muestras if m.urgente])

        self.stats_labels['total'].setText(str(total))
        self.stats_labels['pendientes'].setText(str(pendientes))
        self.stats_labels['proceso'].setText(str(proceso))
        self.stats_labels['completadas'].setText(str(completadas))
        self.stats_labels['urgentes'].setText(str(urgentes))

    def _buscar(self, texto: str):
        self._search_text = texto.strip()
        self._cargar_datos()

    def _filtrar_rapido(self):
        seleccion = self.filtro_grupo.checkedButton()
        if not seleccion:
            return

        texto = seleccion.text()
        self.current_filtros = {}

        if texto == "Pendientes":
            self.current_filtros['estado'] = 'Pendiente'
        elif texto == "En Proceso":
            self.current_filtros['estado'] = 'En Proceso'
        elif texto == "Completadas":
            self.current_filtros['estado'] = 'Completado'
        elif texto == "Urgentes":
            self.current_filtros['urgente'] = True

        self.estado_filter.setCurrentText('Todos')
        self.tipo_filter.setCurrentText('Todos')
        self._cargar_datos()

    def _filtrar_estado(self, estado: str):
        if estado != 'Todos':
            self.current_filtros['estado'] = estado
        elif 'estado' in self.current_filtros:
            del self.current_filtros['estado']

        if self.filtro_grupo.buttons():
            for btn in self.filtro_grupo.buttons():
                if btn.text() == "Todas":
                    btn.setChecked(True)
                    break
        self._cargar_datos()

    def _filtrar_tipo(self, tipo: str):
        if tipo != 'Todos':
            self.current_filtros['tipo'] = tipo
        elif 'tipo' in self.current_filtros:
            del self.current_filtros['tipo']
        self._cargar_datos()

    def _get_selected_id(self):
        muestra_id = self.table.get_selected_id()
        if not muestra_id:
            show_warning(self, "Selección", "Por favor seleccione una muestra")
        return muestra_id

    def _nueva_muestra(self):
        dialog = NuevaMuestraDialog(self, self._cargar_datos)
        dialog.exec()

    def _ingresar_resultados(self):
        muestra_id = self._get_selected_id()
        if not muestra_id:
            return

        try:
            muestra = self.service.obtener_muestra(muestra_id)

            if muestra.estado == 'Completado':
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Warning)
                msg.setWindowTitle("Muestra ya Completada")
                msg.setText(
                    "Esta muestra ya tiene resultados registrados y un PDF generado.\n\n"
                    "¿Estás seguro de que deseas editar los resultados para corregir un error?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.No)

                from config import QT_STYLES
                msg.setStyleSheet(f"""
                    QMessageBox {{ background-color: white; }}
                    QLabel {{ color: #1E293B; font-size: 13px; font-weight: normal; }}
                    QPushButton {{
                        background-color: {QT_STYLES['primary']};
                        color: white; padding: 6px 20px; border: none;
                        border-radius: 4px; font-weight: bold; min-width: 60px;
                    }}
                    QPushButton:hover {{ background-color: {QT_STYLES['secondary']}; }}
                """)

                if msg.exec() == QMessageBox.No:
                    return

            dialog = ResultadoMuestraDialog(
                self, muestra_id, self._cargar_datos)
            dialog.exec()

        except Exception as e:
            show_error(self, "No se pudo abrir el registro.", e)

    def _ver_detalle(self):
        muestra_id = self._get_selected_id()
        if muestra_id:
            dialog = DetalleMuestraDialog(self, muestra_id)
            dialog.exec()

    def refresh(self):
        self._cargar_datos()
