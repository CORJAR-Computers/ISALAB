# gui_pyside/components.py
"""Componentes reutilizables para PySide6"""

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QMessageBox)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor

from config import QT_STYLES
from utils.logger import setup_logger

logger = setup_logger()


class ErrorHandler:
    """Manejador de errores decorador.

    Fase 5 (issue HIGH H-G1): antes este decorador llamaba al método
    ``critical`` de ``QMessageBox`` con ``parent=None``, mostraba el
    mensaje crudo de la excepción al usuario y retornaba ``None``
    implícitamente. Eso causaba tres problemas: el messagebox podía
    quedar detrás de la ventana activa sin foco, se filtraban detalles
    internos (nombres de tablas, rutas, identificadores) al usuario
    final, y los callers que esperaban un valor de retorno recibían
    ``None`` y rompían con ``TypeError`` downstream.

    Ahora:
      - Localiza un parent razonable (el primer arg si es ``QWidget``,
        sino la ventana activa de ``QApplication``, sino ``None``).
      - Construye un mensaje sanitizado: si la excepción hereda de
        ``IsaLabException`` usa su ``str()`` (ya user-friendly); para
        cualquier otra, muestra "Ocurrió un error inesperado" + el tipo
        de excepción (sin el detalle crudo).
      - Retorna el sentinel ``_ERROR_SENTINEL`` para que los callers
        puedan detectar el fallo sin TypeError.
    """
    _ERROR_SENTINEL = object()

    @staticmethod
    def handle_exception(func):
        from utils.exceptions import IsaLabException

        def _find_parent(args):
            """Busca un QWidget válido entre los args del método."""
            try:
                from PySide6.QtWidgets import QWidget, QApplication
            except ImportError:
                return None
            for a in args:
                if isinstance(a, QWidget):
                    return a
            # Sin widget explícito: usar la ventana activa de la app.
            app = QApplication.instance()
            if app is not None:
                active = app.activeWindow()
                if active is not None:
                    return active
            return None

        def _sanitize_message(e: Exception) -> str:
            """Mensaje seguro para el usuario final."""
            if isinstance(e, IsaLabException):
                # La jerarquía IsaLabException ya user-friendly.
                return str(e) or "Error de lógica de negocio."
            # No exponer detalles internos (SQL, paths, etc.).
            return (
                "Ocurrió un error inesperado. "
                "Consulte el log para más detalles."
            )

        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error en UI: {e}", exc_info=True)
                parent = _find_parent(args)
                msg = _sanitize_message(e)
                QMessageBox.critical(parent, "Error", msg)
                return ErrorHandler._ERROR_SENTINEL
        return wrapper


class LogoWidget(QLabel):
    """Widget para mostrar el logo"""

    def __init__(self, size=(200, 70), parent=None):
        super().__init__(parent)
        self.setText("IsaLab")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                color: {QT_STYLES['primary']};
                font-size: 24px;
                font-weight: bold;
            }}
        """)


class SearchBar(QWidget):
    """Barra de búsqueda con debounce"""
    search_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Fase 6 (G-L5): antes ``QTimer()`` sin parent — el timer
        # quedaba huérfano en la jerarquía Qt. Si la SearchBar se
        # destruía (por ejemplo, al cambiar de vista), el timer
        # seguía vivo hasta que Python GC lo recolectara, pero podía
        # emitir ``timeout`` a un slot ya destruido → crash "C++
        # object deleted" en PySide6. Pasar ``self`` como parent
        # asegura la limpieza automática con la jerarquía.
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_search)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar...")
        self.search_input.setFixedWidth(260)
        self.search_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.search_input)

        self.clear_btn = QPushButton("Limpiar")
        self.clear_btn.setFixedWidth(80)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {QT_STYLES['gray']};
                color: white;
            }}
            QPushButton:hover {{
                background-color: {QT_STYLES['secondary']};
            }}
        """)
        self.clear_btn.clicked.connect(self.clear)
        layout.addWidget(self.clear_btn)

    def _on_text_changed(self):
        self._debounce_timer.start(300)

    def _emit_search(self):
        self.search_changed.emit(self.search_input.text())

    def clear(self):
        self.search_input.clear()
        self.search_changed.emit("")


class DataTable(QTableWidget):
    """Tabla de datos mejorada para PySide6"""

    # Colores para filas por estado
    ROW_COLORS = {
        'Activo': QColor('#DFF0D8'),
        'En Tratamiento': QColor('#FCF8E3'),
        'Cuarentena': QColor('#F2DEDE'),
        'Dado de Alta': QColor('#E8F4F8'),
        'Pendiente': QColor('#FFF8E1'),
        'En Proceso': QColor('#E3F2FD'),
        'Completado': QColor('#E8F5E9'),
        'urgente': QColor('#FFE4E1'),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)

    def setup_columns(self, columns, col_widths=None):
        """Configura las columnas de la tabla.

        Fase 6 (G-L9): ``col_widths`` ahora acepta ``None`` en
        entradas individuales para indicar "esta columna no tiene
        ancho fijo; hereda el modo de resize del header". Antes,
        pasar ``None`` en la lista hacía que ``setColumnWidth(i, None)``
        crasheara con ``TypeError``. Ahora se salta esa entrada y
        deja la columna con el modo por defecto (que el caller puede
        sobreescribir después con ``setSectionResizeMode(col, mode)``).
        """
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)

        if col_widths:
            for i, width in enumerate(col_widths):
                if width is None:
                    # El caller puede setear el modo de resize
                    # después (ej. ``setSectionResizeMode(i, Stretch)``).
                    continue
                self.setColumnWidth(i, width)
            # Si al menos una columna tuvo ``None``, no seteamos el
            # modo Stretch global (entraría en conflicto con los
            # anchos fijos ya seteados). El caller decide.
            if not any(w is None for w in col_widths):
                # Todas las columnas tienen ancho fijo → las que no
                # se hayan tocado quedan con el modo por defecto.
                pass
        else:
            self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def populate(self, data, row_getter, tag_getter=None,
                 empty_message="No hay registros"):
        """
        Rellena la tabla con datos

        Args:
            data: lista de objetos
            row_getter: función que recibe objeto y retorna lista de valores
            tag_getter: función que recibe objeto y retorna tupla de tags
            empty_message: mensaje a mostrar cuando ``data`` está vacío.
                Fase 6 (G-M6): antes, si ``data`` era ``[]``, la tabla
                quedaba en blanco total (sin filas, sin mensaje), lo
                que parecía un bug de carga. Ahora se inserta una fila
                única que ocupa todas las columnas (``setSpan``) con
                el mensaje en cursiva gris, indicando visualmente que
                no hay registros (no que la app se colgó).
        """
        self.setRowCount(0)  # Limpiar

        if not data:
            logger.debug("DataTable: No hay datos para mostrar")
            # Fase 6 (G-M6): empty-state visible. Una sola fila, el
            # mensaje ocupa todas las columnas. Estilo cursiva gris
            # para diferenciarlo de una fila de datos real.
            self.setRowCount(1)
            n_cols = max(self.columnCount(), 1)
            msg_item = QTableWidgetItem(empty_message)
            msg_item.setFlags(Qt.NoItemFlags)  # no seleccionable/editable
            msg_item.setForeground(QColor(150, 150, 150))
            # Italic + tamaño consistente con el resto de la tabla.
            from PySide6.QtGui import QFont
            font = QFont()
            font.setItalic(True)
            msg_item.setFont(font)
            # Centrado horizontal y vertical.
            msg_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(0, 0, msg_item)
            self.setSpan(0, 0, 1, n_cols)
            return

        logger.debug(f"DataTable: Cargando {len(data)} filas")
        self.setRowCount(len(data))

        for row, item in enumerate(data):
            values = row_getter(item)
            tags = tag_getter(item) if tag_getter else ()

            for col, value in enumerate(values):
                cell_item = QTableWidgetItem(
                    str(value) if value is not None else "")
                cell_item.setForeground(QColor(0, 0, 0))  # Forzar texto negro
                self.setItem(row, col, cell_item)

            # Aplicar color según tags
            if tags:
                color = None
                for tag in tags:
                    if tag in self.ROW_COLORS:
                        color = self.ROW_COLORS[tag]
                        break
                if color:
                    for col in range(self.columnCount()):
                        item = self.item(row, col)
                        if item:
                            item.setBackground(color)

        logger.debug(f"DataTable: {self.rowCount()} filas mostradas")

    def get_selected_id(self):
        """Retorna el ID de la fila seleccionada (primera columna)"""
        current_row = self.currentRow()
        if current_row >= 0:
            item = self.item(current_row, 0)
            if item:
                try:
                    return int(item.text())
                except ValueError:
                    return None
        return None


class StatusBadge(QLabel):
    """Etiqueta con estilo de badge para estados"""

    def __init__(self, status, parent=None):
        super().__init__(parent)
        self.setText(f"  {status}  ")
        self.setAlignment(Qt.AlignCenter)

        # Colores por estado
        colors = {
            'Activo': ('#166534', '#DCFCE7'),
            'En Tratamiento': ('#854D0E', '#FEF9C3'),
            'Cuarentena': ('#991B1B', '#FEE2E2'),
            'Pendiente': ('#92400E', '#FEF3C7'),
            'En Proceso': ('#1E40AF', '#DBEAFE'),
            'Completado': ('#166534', '#DCFCE7'),
        }

        fg, bg = colors.get(status, ('#374151', '#F3F4F6'))

        self.setStyleSheet(f"""
            QLabel {{
                color: {fg};
                background-color: {bg};
                border-radius: 6px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 11px;
            }}
        """)


class UrgentBadge(QLabel):
    """Badge para muestras urgentes"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("  ⚠ URGENTE  ")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                color: #7F1D1D;
                background-color: #FEE2E2;
                border-radius: 6px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: 11px;
            }
        """)
