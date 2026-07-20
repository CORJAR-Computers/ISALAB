# gui_pyside/views/reportes.py
"""Vista de reportes para PySide6"""

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QFrame, QMessageBox,
                               QTabWidget, QTextEdit, QDateEdit, QFormLayout)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QTextCursor

from gui_pyside.components.components import ErrorHandler
from services.report_service import ReportService
from config import QT_STYLES

# Importar matplotlib para gráficos
import matplotlib
matplotlib.use('Agg')


class ReportesView(QWidget):
    """Vista principal de reportes"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = ReportService()
        self.setObjectName("reportesView")

        self._build_layout()
        self._cargar_datos()

    def _build_layout(self):
        """Construye el layout de la vista"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Título
        titulo = QLabel("Reportes y Estadísticas")
        titulo.setStyleSheet(f"""
            QLabel {{
                color: {QT_STYLES['secondary']};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        main_layout.addWidget(titulo)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #E2E8F0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #1E3A5F;
                font-weight: bold;
            }
        """)

        # Crear pestañas
        self._crear_tab_dashboard()
        self._crear_tab_muestras()

        main_layout.addWidget(self.tabs)

    def _crear_tab_dashboard(self):
        """Crea la pestaña de dashboard"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Botón actualizar
        btn_actualizar = QPushButton("↻ Actualizar Datos")
        btn_actualizar.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['primary']};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                max-width: 180px;
            }}
            QPushButton:hover {{
                background-color: {QT_STYLES['secondary']};
            }}
        """)
        btn_actualizar.clicked.connect(self._cargar_datos)
        layout.addWidget(btn_actualizar, alignment=Qt.AlignLeft)

        # Área de scroll para estadísticas
        self.stats_widget = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_widget)

        scroll = QFrame()
        scroll.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
            }
        """)
        scroll_layout = QVBoxLayout(scroll)
        scroll_layout.addWidget(self.stats_widget)

        layout.addWidget(scroll)

        self.tabs.addTab(tab, "📊 Dashboard")

    def _crear_tab_muestras(self):
        """Crea la pestaña de reporte de muestras"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Filtros
        filtros_widget = QWidget()
        filtros_layout = QHBoxLayout(filtros_widget)
        filtros_layout.setContentsMargins(0, 0, 0, 10)

        # Fecha inicio
        lbl_inicio = QLabel("Fecha inicio:")
        lbl_inicio.setStyleSheet(f"color: {QT_STYLES['gray']};")
        filtros_layout.addWidget(lbl_inicio)

        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDate(QDate.currentDate().addDays(-30))
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setDisplayFormat("yyyy-MM-dd")
        filtros_layout.addWidget(self.fecha_inicio)

        filtros_layout.addSpacing(20)

        # Fecha fin
        lbl_fin = QLabel("Fecha fin:")
        lbl_fin.setStyleSheet(f"color: {QT_STYLES['gray']};")
        filtros_layout.addWidget(lbl_fin)

        self.fecha_fin = QDateEdit()
        self.fecha_fin.setDate(QDate.currentDate())
        self.fecha_fin.setCalendarPopup(True)
        self.fecha_fin.setDisplayFormat("yyyy-MM-dd")
        filtros_layout.addWidget(self.fecha_fin)

        filtros_layout.addSpacing(20)

        # Botón generar
        btn_generar = QPushButton("Generar Reporte")
        btn_generar.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['accent']};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #256B5E;
            }}
        """)
        btn_generar.clicked.connect(self._generar_reporte_muestras)
        filtros_layout.addWidget(btn_generar)

        filtros_layout.addStretch()

        layout.addWidget(filtros_widget)

        # Área de texto para el reporte
        self.reporte_text = QTextEdit()
        self.reporte_text.setReadOnly(True)
        self.reporte_text.setFont(QFont("Courier New", 10))
        layout.addWidget(self.reporte_text)

        self.tabs.addTab(tab, "🧪 Reporte Muestras")

    @ErrorHandler.handle_exception
    def _cargar_datos(self):
        """Carga los datos del dashboard"""
        try:
            stats = self.service.get_dashboard_stats()
            metrics = self.service.get_efficiency_metrics()

            # Limpiar layout anterior
            self._limpiar_layout(self.stats_layout)

            # Estadísticas generales
            general_group = self._crear_grupo("Estadísticas Generales")
            general_layout = QFormLayout(general_group)

            general_layout.addRow("Animales activos:",
                                  QLabel(str(stats['activos'])))
            general_layout.addRow("Ingresos hoy:", QLabel(str(stats['hoy'])))
            general_layout.addRow("Muestras pendientes:",
                                  QLabel(str(stats['muestras_pendientes'])))
            general_layout.addRow("Muestras urgentes:",
                                  QLabel(str(stats['urgentes'])))
            general_layout.addRow("Completadas (semana):",
                                  QLabel(str(stats['completadas_semana'])))
            general_layout.addRow("Tiempo promedio:",
                                  QLabel(f"{stats['tiempo_promedio']} días"))

            self.stats_layout.addWidget(general_group)

            # Eficiencia
            eficiencia_group = self._crear_grupo("Eficiencia")
            eficiencia_layout = QFormLayout(eficiencia_group)

            eficiencia_layout.addRow("Tasa de cumplimiento:", QLabel(
                f"{metrics['tasa_cumplimiento']}%"))

            self.stats_layout.addWidget(eficiencia_group)

            # Gráfico de técnicos
            if metrics['por_tecnico']:
                self._crear_grafico_tecnicos(metrics['por_tecnico'])

            self.stats_layout.addStretch()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando datos: {e}")

    def _crear_grupo(self, titulo):
        """Crea un grupo con estilo"""
        group = QFrame()
        group.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
        """)
        layout = QVBoxLayout(group)

        label = QLabel(titulo)
        label.setStyleSheet(f"""
            QLabel {{
                color: {QT_STYLES['secondary']};
                font-weight: bold;
                font-size: 14px;
            }}
        """)
        layout.addWidget(label)

        return group

    def _crear_grafico_tecnicos(self, data):
        """Crea un gráfico de barras para técnicos"""
        group = QFrame()
        group.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
        """)
        layout = QVBoxLayout(group)

        label = QLabel("Muestras por Técnico (Top 5)")
        label.setStyleSheet(f"""
            QLabel {{
                color: {QT_STYLES['secondary']};
                font-weight: bold;
                font-size: 14px;
            }}
        """)
        layout.addWidget(label)

        # Crear figura
        fig = Figure(figsize=(8, 3.5))
        ax = fig.add_subplot(111)

        tecnicos, cantidades = zip(*data[:5])
        ax.bar(tecnicos, cantidades, color=QT_STYLES['primary'])
        ax.set_ylabel('Cantidad')
        ax.tick_params(axis='x', rotation=30)

        fig.tight_layout()

        # Embed en Qt
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)

        self.stats_layout.addWidget(group)

    @ErrorHandler.handle_exception
    def _generar_reporte_muestras(self):
        """Genera el reporte de muestras"""
        try:
            inicio = self.fecha_inicio.date().toString("yyyy-MM-dd")
            fin = self.fecha_fin.date().toString("yyyy-MM-dd")

            muestras = self.service.get_reporte_muestras(inicio, fin)

            self.reporte_text.clear()

            if not muestras:
                self.reporte_text.setPlainText(
                    "No hay muestras en el período seleccionado.")
                return

            # Generar reporte
            lines = []
            lines.append("=" * 80)
            lines.append("REPORTE DE MUESTRAS")
            lines.append(f"Período: {inicio} — {fin}")
            lines.append(f"Total muestras: {len(muestras)}")
            lines.append("=" * 80)
            lines.append("")

            for m in muestras:
                lines.append(f"Muestra:  {m['codigo']}")
                lines.append(
                    f"Animal:   {
                        m['animal_nombre']} ({
                        m['animal_codigo']})")
                lines.append(f"Tipo:     {m['tipo_muestra']}")
                lines.append(f"Fecha:    {m['fecha_recoleccion']}")
                lines.append(f"Estado:   {m['estado']}")
                if m.get('resultado'):
                    lines.append(f"Resultado: {m['resultado'][:100]}...")
                lines.append("-" * 40)
                lines.append("")

            self.reporte_text.setPlainText("\n".join(lines))

            # Mover al inicio
            cursor = self.reporte_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.reporte_text.setTextCursor(cursor)

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Error generando reporte: {e}")

    def _limpiar_layout(self, layout):
        """Limpia un layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def refresh(self):
        """Refresca los datos"""
        self._cargar_datos()
