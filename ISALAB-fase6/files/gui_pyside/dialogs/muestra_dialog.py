# gui_pyside/dialogs/muestra_dialog.py
"""Diálogos de muestras para PySide6 - VERSIÓN PRO"""

from config import TIPOS_MUESTRA, TIPOS_ANALISIS, ESTADOS_MUESTRA
from services.animal_service import AnimalService
from services.muestra_service import MuestraService
from gui_pyside.styles import IsaStyles, style_button, style_group, style_input
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QTextEdit,
    QPushButton,
    QFrame,
    QMessageBox,
    QFormLayout,
    QDateEdit,
    QGroupBox,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QApplication,
    QAbstractItemView)
from PySide6.QtCore import Qt, QDate, QThread, Signal, QObject, QEvent
import os
import json

from gui_pyside.dialogs.base_dialog import BaseDialog
from gui_pyside.dialogs.animal_dialog import NuevoAnimalDialog
from gui_pyside.components.components import ErrorHandler
from gui_pyside.components.forms import LoadingOverlay
from gui_pyside.utils.messages import show_error, show_warning
from utils.logger import setup_logger

logger = setup_logger()


# ─────────────────────────────────────────────────────────────────────────────
# Fase 5 (H-G7): Event filter para "pegado mágico" en tabla de resultados.
# ─────────────────────────────────────────────────────────────────────────────
# Antes, ``ResultadoMuestraDialog`` monkey-patcheaba
# ``self.tabla_resultados.keyPressEvent = self._pegar_magico_en_tabla`` para
# interceptar Ctrl+V y pegar filas parseadas desde el portapapeles. Eso
# rompía encapsulación y era frágil. Este event filter hace lo mismo
# pero por el mecanismo oficial de Qt (``installEventFilter``), sin
# tocar la clase original de ``QTableWidget``.


class _PegadoMagicoFilter(QObject):
    """Intercepta ``Ctrl+V`` sobre una ``QTableWidget`` y delega al handler.

    El ``handler`` es un callable ``(event) -> bool`` que recibe el
    ``QEvent`` original (cast a ``QKeyEvent`` por el caller). Si retorna
    ``True``, el evento se considera manejado y NO se propaga al widget;
    si retorna ``False``, el evento sigue su curso normal (comportamiento
    por defecto de ``QTableWidget``).
    """

    def __init__(self, target_table, handler):
        super().__init__(target_table)  # parent = target → se limpia solo
        self._handler = handler

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_V and (
                    event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                # Delegar al handler del diálogo. Si consume el evento
                # (retorna True o None), marcamos como manejado.
                result = self._handler(event)
                if result is not False:
                    return True
        # Propagar al widget original.
        return super().eventFilter(obj, event)


# ─────────────────────────────────────────────────────────────────────────────
# Fase 5 (H-G8): PDFProWorker hoisted de método anidado → clase de módulo.
# ─────────────────────────────────────────────────────────────────────────────
# Antes, ``PDFProWorker`` se definía DENTRO de ``_imprimir_pdf`` como
# clase anidada, lo que significa que Python RE-CREABA la clase en cada
# click del botón "Imprimir Resultados Pro" (definición nueva, dirs
# nuevos en ``sys.modules``, etc.). Peor aún, el ``QThread`` arrancado
# no tenía ``finished`` conectado ni ``deleteLater()``, así que cada
# click acumulaba un QThread zombie hasta que el GC de Python lo
# recolectara (eventualmente, si es que lo hacía — Qt mantiene refs
# internas que pueden impedirlo).
#
# Ahora ``PDFProWorker`` es una clase de módulo (se define una sola vez
# al importar) y el diálogo conecta su señal ``finished`` a
# ``deleteLater()`` para que Qt limpie el QThread al terminar.


class PDFProWorker(QThread):
    """Worker thread para generar PDF de resultados de laboratorio.

    Emite ``terminado(bytes)`` con el contenido del PDF al terminar
    exitosamente, o ``error(str)`` con el mensaje de error si falla.
    La señal ``finished`` (de ``QThread``) se conecta externamente a
    ``deleteLater()`` para limpiar el thread.
    """

    terminado = Signal(bytes)
    error = Signal(str)

    def __init__(self, muestra_id, es_empresa, datos_empresa, parent=None):
        super().__init__(parent)
        self.muestra_id = muestra_id
        self.es_empresa = es_empresa
        self.datos_empresa = datos_empresa

    def run(self):
        try:
            # Import diferido para evitar import circular en tests sin
            # WeasyPrint instalado.
            from services.report_laboratorio import ReporteLaboratorioService
            svc = ReporteLaboratorioService()
            pdf_bytes = svc.generar_pdf(
                self.muestra_id,
                es_empresa=self.es_empresa,
                datos_empresa=self.datos_empresa
            )
            self.terminado.emit(pdf_bytes)
        except Exception as e:
            logger.error(f"PDFProWorker falló: {e}", exc_info=True)
            self.error.emit(str(e))


class PacienteSelector(QWidget):
    def __init__(self, parent=None, on_nuevo_callback=None):
        super().__init__(parent)
        self.on_nuevo_callback = on_nuevo_callback
        self.animal_service = AnimalService()
        self._setup_ui()
        self._cargar_animales()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.combo = QComboBox()
        self.combo.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        style_input(self.combo)
        layout.addWidget(self.combo, 1)

        self.btn_nuevo = QPushButton("➕")
        self.btn_nuevo.setFixedSize(36, IsaStyles.INPUT_HEIGHT)
        self.btn_nuevo.setCursor(Qt.PointingHandCursor)
        self.btn_nuevo.setToolTip("Registrar nuevo paciente")
        self.btn_nuevo.setStyleSheet(f"""
            QPushButton {{
                background-color: {IsaStyles.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {IsaStyles.SECONDARY};
            }}
        """)
        self.btn_nuevo.clicked.connect(self._abrir_nuevo_paciente)
        layout.addWidget(self.btn_nuevo)

    def _cargar_animales(self):
        self.combo.clear()
        try:
            animales = self.animal_service.listar_animales(
                {'estado': 'Activo'})
            for a in animales:
                self.combo.addItem(f"{a.nombre} ({a.codigo})", a.id)
        except Exception as e:
            logger.warning(
                f"No se pudieron cargar pacientes para muestras: {e}")

    def _abrir_nuevo_paciente(self):
        # Pasar el padre correcto para mantener la jerarquía
        dialog = NuevoAnimalDialog(
            parent=self.parent(),
            on_save=self._cargar_animales)
        if dialog.exec() == dialog.Accepted and self.on_nuevo_callback:
            self.on_nuevo_callback()

    def current_data(self):
        return self.combo.currentData()

    def set_current_by_id(self, animal_id):
        idx = self.combo.findData(animal_id)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)


class NuevaMuestraDialog(BaseDialog):
    def __init__(self, parent=None, on_save=None):
        super().__init__(parent, "🧪 Nueva Muestra de Laboratorio", 900, 520)
        self.on_save = on_save
        self.service = MuestraService()
        self._build()

    def _build(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        self.content_layout.addLayout(main_layout)

        # Fase 6 (G-L7): antes se llamaba a ``self.service.generar_codigo()``
        # aquí, en ``_build()``, ANTES de que el usuario llenara nada.
        # Eso consumía un código LAB-XXXX del contador atómico en CADA
        # apertura del diálogo, incluso si el usuario cancelaba. Con
        # tiempo, la tabla de muestras quedaba con huecos enormes en la
        # secuencia (LAB-0001, LAB-0007, LAB-0015, ...) porque los
        # códigos cancelados no se podían reciclar.
        #
        # Ahora mostramos un placeholder "LAB-????" y solo consumimos
        # un código real al guardar. Si el servicio tiene
        # ``preview_siguiente_codigo`` (API planeada por el batch 9-b),
        # lo usamos para mostrar el código siguiente sin consumirlo.
        # Mientras 9-b no lo añada, el placeholder es la mejor opción.
        #
        # Defensive: si ``preview_siguiente_codigo`` existe pero falla
        # (ej: requiere usuario autenticado y el diálogo no lo pasa
        # aún), caemos al placeholder en lugar de propagar la
        # excepción. Mejor mostrar "LAB-????" que crashear al abrir
        # el diálogo.
        self.codigo_generado = "LAB-????"
        preview_fn = getattr(self.service, 'preview_siguiente_codigo', None)
        if callable(preview_fn):
            try:
                self.codigo_generado = preview_fn()
            except Exception as e:
                logger.warning(
                    f"preview_siguiente_codigo falló, usando "
                    f"placeholder 'LAB-????': {e}")

        left_card = QGroupBox("⚙️ Configuración del Análisis")
        style_group(left_card, IsaStyles.PRIMARY)
        left_layout = QFormLayout(left_card)
        left_layout.setSpacing(14)

        codigo_container = QWidget()
        codigo_layout = QHBoxLayout(codigo_container)
        codigo_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_codigo = QLabel(
            f"<b style='font-size:18px; color:{IsaStyles.PRIMARY};'>{self.codigo_generado}</b>")
        self.lbl_codigo.setStyleSheet(f"""
            background-color: {IsaStyles.LIGHT_BG};
            padding: 10px 16px;
            border-radius: 6px;
            border: 2px dashed {IsaStyles.PRIMARY};
        """)
        codigo_layout.addWidget(self.lbl_codigo)

        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedSize(32, 32)
        # Fase 6 (G-L7): el botón "🔄" antes llamaba a ``generar_codigo()``
        # que CONSUME el código. Si el servicio aún no tiene
        # ``preview_siguiente_codigo``, deshabilitamos el botón refresh
        # (no tiene sentido refrescar un placeholder). Cuando 9-b
        # añada el método preview, el botón se re-habilita solo.
        btn_refresh.setToolTip("Previsualizar siguiente código")
        if not callable(preview_fn):
            btn_refresh.setEnabled(False)
            btn_refresh.setToolTip(
                "Previsualización no disponible aún — el código se "
                "generará al guardar.")
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {IsaStyles.BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {IsaStyles.LIGHT_BG};
            }}
            QPushButton:disabled {{
                color: {IsaStyles.GRAY};
                background-color: {IsaStyles.LIGHT_BG};
            }}
        """)
        btn_refresh.clicked.connect(self._regenerar_codigo)
        codigo_layout.addWidget(btn_refresh)
        codigo_layout.addStretch()

        left_layout.addRow("Código de Muestra:", codigo_container)

        self.selector_paciente = PacienteSelector(self)
        left_layout.addRow("Paciente *:", self.selector_paciente)

        self.empresa = QComboBox()
        self.empresa.setEditable(True)
        self.empresa.addItems(["Persona Natural",
                               "C. V. RUFFOS HOUSE",
                               "C. V. COCKER",
                               "C. V. DRA YUS",
                               "C. V. AMARENA"])
        self.empresa.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        style_input(self.empresa)
        self.empresa.lineEdit().setPlaceholderText("Seleccione o escriba la entidad")
        left_layout.addRow("Entidad/Clínica:", self.empresa)

        self.tipo_muestra = QComboBox()
        self.tipo_muestra.addItems(TIPOS_MUESTRA)
        self.tipo_muestra.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        style_input(self.tipo_muestra)
        self.tipo_muestra.currentTextChanged.connect(self._actualizar_analisis)
        left_layout.addRow("Tipo de Muestra *:", self.tipo_muestra)

        self.tipo_analisis = QComboBox()
        self.tipo_analisis.setEditable(True)
        self.tipo_analisis.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        style_input(self.tipo_analisis)
        self._actualizar_analisis(self.tipo_muestra.currentText())
        left_layout.addRow("Análisis Solicitado *:", self.tipo_analisis)

        self.urgente = QCheckBox("⚠️ MARCAR COMO URGENTE")
        self.urgente.setStyleSheet(f"""
            QCheckBox {{
                color: {IsaStyles.DANGER};
                font-weight: bold;
                font-size: 13px;
                spacing: 10px;
                margin-top: 8px;
            }}
            QCheckBox::indicator {{
                width: 22px;
                height: 22px;
                border: 2px solid {IsaStyles.DANGER};
                border-radius: 4px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {IsaStyles.DANGER};
                image: none;
            }}
        """)
        left_layout.addRow("", self.urgente)

        main_layout.addWidget(left_card, 1)

        right_card = QGroupBox("📅 Logística y Observaciones")
        style_group(right_card, IsaStyles.ACCENT)
        right_layout = QFormLayout(right_card)
        right_layout.setSpacing(14)

        fechas_widget = QWidget()
        fechas_layout = QHBoxLayout(fechas_widget)
        fechas_layout.setContentsMargins(0, 0, 0, 0)
        fechas_layout.setSpacing(12)

        rec_container = QWidget()
        rec_layout = QVBoxLayout(rec_container)
        rec_layout.setContentsMargins(0, 0, 0, 0)
        rec_layout.setSpacing(4)
        rec_layout.addWidget(QLabel("Recolección *:"))
        self.fecha_rec = QDateEdit(QDate.currentDate())
        self.fecha_rec.setCalendarPopup(True)
        self.fecha_rec.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        style_input(self.fecha_rec)
        rec_layout.addWidget(self.fecha_rec)
        fechas_layout.addWidget(rec_container, 1)

        ent_container = QWidget()
        ent_layout = QVBoxLayout(ent_container)
        ent_layout.setContentsMargins(0, 0, 0, 0)
        ent_layout.setSpacing(4)
        ent_layout.addWidget(QLabel("Entrega Estimada:"))
        self.fecha_ent = QDateEdit(QDate.currentDate().addDays(2))
        self.fecha_ent.setCalendarPopup(True)
        self.fecha_ent.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        style_input(self.fecha_ent)
        ent_layout.addWidget(self.fecha_ent)
        fechas_layout.addWidget(ent_container, 1)

        right_layout.addRow(fechas_widget)

        self.observaciones = QTextEdit()
        self.observaciones.setPlaceholderText(
            "Instrucciones especiales: refrigeración, ayuno del paciente, precauciones...")
        self.observaciones.setMaximumHeight(100)
        self.observaciones.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid {IsaStyles.BORDER};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
            QTextEdit:focus {{
                border-color: {IsaStyles.ACCENT};
            }}
        """)
        right_layout.addRow("Instrucciones:", self.observaciones)

        tip = QLabel(
            "💡 <b>Tip:</b> Las muestras urgentes se procesan en máximo 24 horas")
        tip.setStyleSheet(
            "background-color: #FEF3C7; color: #92400E; padding: 10px; border-radius: 6px; font-size: 11px;")
        tip.setWordWrap(True)
        right_layout.addRow(tip)

        main_layout.addWidget(right_card, 1)

        self.btn_guardar.setText("🧪 Registrar Muestra")
        style_button(self.btn_guardar, 'primary')
        self.btn_cancelar.setText("❌ Cancelar")
        style_button(self.btn_cancelar, 'ghost')

        self.set_save_callback(self._guardar)

    def _regenerar_codigo(self):
        # Fase 6 (G-L7): si el servicio tiene ``preview_siguiente_codigo``,
        # lo usamos (NO consume el contador). Si no lo tiene, este botón
        # está deshabilitado en ``_build`` y nunca debería llamarse —
        # pero por defensividad, si llega aquí, no hacemos nada.
        preview_fn = getattr(self.service, 'preview_siguiente_codigo', None)
        if not callable(preview_fn):
            return
        try:
            self.codigo_generado = preview_fn()
        except Exception as e:
            logger.warning(f"preview_siguiente_codigo falló: {e}")
            return
        self.lbl_codigo.setText(
            f"<b style='font-size:18px; color:{IsaStyles.PRIMARY};'>{self.codigo_generado}</b>")

    def _actualizar_analisis(self, tipo_muestra):
        self.tipo_analisis.clear()
        analisis = TIPOS_ANALISIS.get(tipo_muestra, ['Otro'])
        self.tipo_analisis.addItems(analisis)

    def _validar(self) -> bool:
        valid = True
        if not self.selector_paciente.current_data():
            show_warning(
                self,
                "Campo Requerido",
                "Debe seleccionar un paciente")
            self.selector_paciente.combo.setFocus()
            valid = False
        if not self.tipo_muestra.currentText():
            self.tipo_muestra.setStyleSheet(
                f"QComboBox {{ border: 2px solid {
                    IsaStyles.DANGER}; border-radius: 6px; min-height: {
                    IsaStyles.INPUT_HEIGHT}px; }}")
            valid = False
        return valid

    def _parsear_texto_a_json(
            self,
            texto_plano: str,
            ref_global: str = "") -> str:
        """
        Convierte texto pegado de la máquina en un JSON estructurado.
        Ejemplo de entrada: "Leucocitos WBC# 16.4 10^9/L"
        Ejemplo de salida: [{"item": "Leucocitos WBC#", "resultado": "16.4", "unidades": "10^9/L", "ref_texto": ""}]
        """
        lineas = texto_plano.strip().split('\n')
        items_estructurados = []

        for linea in lineas:
            if not linea.strip():
                continue

            # 1. Intentar separar por Tabulaciones (muy común al copiar de
            # Excel o equipos)
            partes = linea.split('\t')

            # 2. Si no hay tabulaciones, separar por espacios (máximo 4 trozos)
            if len(partes) < 3:
                # split(None, 3) divide por cualquier espacio, ignorando
                # espacios múltiples
                partes = linea.strip().split(None, 3)

                # 3. Armamos el diccionario del análisis
            item = {
                "item": partes[0].strip() if len(partes) > 0 else "",
                "resultado": partes[1].strip() if len(partes) > 1 else "",
                "unidades": partes[2].strip() if len(partes) > 2 else "",
                "ref_texto": partes[3].strip() if len(partes) > 3 else ref_global}

            # Si tiene nombre y resultado, lo guardamos
            if item["item"] and item["resultado"]:
                items_estructurados.append(item)

        # Si logró separar al menos un análisis, lo devuelve como JSON. Si no,
        # devuelve el texto original.
        if items_estructurados:
            return json.dumps(items_estructurados, ensure_ascii=False)
        else:
            return texto_plano

    @ErrorHandler.handle_exception
    def _guardar(self):
        if not self._validar():
            return

        animal_id = self.selector_paciente.current_data()

        # Fase 6 (G-L7): aquí sí consumimos un código real del contador
        # atómico. Si el usuario llegó hasta este punto, es porque
        # validó el form y decidió guardar — consumir el código es
        # legítimo. Antes se consumía en ``_build`` (al abrir el
        # diálogo), gastando códigos en aperturas canceladas.
        #
        # Si el servicio tiene ``consumir_codigo()`` (API planeada por
        # 9-b), la usamos (algunas implementaciones separan preview de
        # consumir). Si no, usamos ``generar_codigo()`` que consume
        # atómicamente.
        if self.codigo_generado == "LAB-????" or not self.codigo_generado:
            # Placeholder → consumir uno real ahora.
            consumir_fn = getattr(self.service, 'consumir_codigo', None)
            if callable(consumir_fn):
                self.codigo_generado = consumir_fn()
            else:
                self.codigo_generado = self.service.generar_codigo()

        datos_muestra = {
            'codigo': self.codigo_generado,
            'animal_id': animal_id,
            'empresa': self.empresa.currentText(),
            'tipo_muestra': self.tipo_muestra.currentText(),
            'tipo_analisis': self.tipo_analisis.currentText(),
            'urgente': self.urgente.isChecked(),
            'fecha_recoleccion': self.fecha_rec.date().toString("yyyy-MM-dd"),
            'fecha_entrega': self.fecha_ent.date().toString("yyyy-MM-dd"),
            'observaciones': self.observaciones.toPlainText().strip(),
        }

        try:
            self.service.registrar_muestra(datos_muestra)
            QMessageBox.information(
                self, "✅ Éxito", f"Muestra {
                    self.codigo_generado} registrada correctamente.")

            if self.on_save:
                self.on_save()
            self.accept()
        except Exception as e:
            show_error(self, "No se pudo registrar la muestra.", e)


class ResultadoMuestraDialog(BaseDialog):
    def __init__(self, parent=None, muestra_id=None, on_save=None):
        super().__init__(parent, "🧪 Ingresar Resultados de Laboratorio", 1000, 720)
        self.muestra_id = muestra_id
        self.on_save = on_save
        self.service = MuestraService()
        self._build()
        self._cargar_datos()

    def _build(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        self.content_layout.addLayout(main_layout)

        # ── CARD IZQUIERDA ────────────────────────────────────────────────
        left_card = QGroupBox("📋 Información de la Muestra")
        style_group(left_card, IsaStyles.SECONDARY)
        left_layout = QFormLayout(left_card)
        left_layout.setSpacing(12)

        self.lbl_codigo = QLabel("-")
        self.lbl_codigo.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addRow("Código:", self.lbl_codigo)

        self.lbl_paciente = QLabel("-")
        left_layout.addRow("Paciente:", self.lbl_paciente)

        self.lbl_empresa = QLabel("-")
        left_layout.addRow("Entidad:", self.lbl_empresa)

        self.lbl_tipo = QLabel("-")
        left_layout.addRow("Tipo:", self.lbl_tipo)

        self.lbl_analisis = QLabel("-")
        left_layout.addRow("Análisis:", self.lbl_analisis)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"background-color: {IsaStyles.BORDER};")
        left_layout.addRow(line)

        self.estado = QComboBox()
        self.estado.addItems(ESTADOS_MUESTRA)
        self.estado.setMinimumHeight(IsaStyles.INPUT_HEIGHT)
        style_input(self.estado)
        left_layout.addRow("Estado:", self.estado)

        estados_widget = QWidget()
        estados_layout = QHBoxLayout(estados_widget)
        estados_layout.setContentsMargins(0, 0, 0, 0)
        estados_layout.setSpacing(6)

        for estado_btn in ['Pendiente', 'En Proceso', 'Completado']:
            btn = QPushButton(estado_btn)
            btn.setFixedHeight(28)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {IsaStyles.LIGHT_BG};
                    border: 1px solid {IsaStyles.BORDER};
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 4px 12px;
                }}
                QPushButton:hover {{
                    background-color: {IsaStyles.PRIMARY};
                    color: white;
                }}
            """)
            btn.clicked.connect(lambda checked,
                                e=estado_btn: self.estado.setCurrentText(e))
            estados_layout.addWidget(btn)
        left_layout.addRow("Cambiar a:", estados_widget)

        self.lbl_recoleccion = QLabel("-")
        self.lbl_recoleccion.setStyleSheet(
            f"color: {IsaStyles.GRAY}; font-size: 11px;")
        left_layout.addRow("Recolección:", self.lbl_recoleccion)
        left_layout.addRow("", QLabel(""))

        self.btn_imprimir = QPushButton("🖨️ Guardar e Imprimir PDF")
        style_button(self.btn_imprimir, 'secondary')
        self.btn_imprimir.clicked.connect(self._imprimir_pdf)
        left_layout.addRow(self.btn_imprimir)

        main_layout.addWidget(left_card, 0)

        # ── CARD DERECHA ──────────────────────────────────────────────────
        right_card = QGroupBox("📝 Resultados del Análisis")
        style_group(right_card, IsaStyles.ACCENT)
        right_layout = QVBoxLayout(right_card)
        right_layout.setSpacing(12)

        resultados_header = QWidget()
        resultados_header_layout = QHBoxLayout(resultados_header)
        resultados_header_layout.setContentsMargins(0, 0, 0, 0)
        resultados_title = QLabel("<b>Resultados (Ctrl+V para pegar):</b>")
        resultados_title.setStyleSheet(
            f"color: {IsaStyles.DARK}; font-size: 13px;")
        resultados_header_layout.addWidget(resultados_title)
        resultados_header_layout.addStretch()
        right_layout.addWidget(resultados_header)

        # ✅ LA TABLA
        self.tabla_resultados = QTableWidget()
        self.tabla_resultados.setColumnCount(4)
        self.tabla_resultados.setHorizontalHeaderLabels(
            ["Ítem", "Resultado", "Unidades", "Referencia"])
        self.tabla_resultados.horizontalHeader().setStretchLastSection(True)
        self.tabla_resultados.setColumnWidth(0, 200)
        self.tabla_resultados.setColumnWidth(1, 100)
        self.tabla_resultados.setColumnWidth(2, 100)
        self.tabla_resultados.setMinimumHeight(200)
        self.tabla_resultados.setStyleSheet(f"""
            QTableWidget {{
                border: 2px solid {IsaStyles.BORDER};
                border-radius: 6px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                gridline-color: {IsaStyles.BORDER};
            }}
            QTableWidget::item {{ padding: 4px; }}
            QHeaderView::section {{
                background-color: {IsaStyles.PRIMARY};
                color: white;
                padding: 4px;
                border: 1px solid {IsaStyles.SECONDARY};
                font-weight: bold;
            }}
        """)
        # Fase 5 (H-G7): antes se monkey-patcheaba ``keyPressEvent``
        # directamente sobre la instancia:
        #     self.tabla_resultados.keyPressEvent = self._pegar_magico_en_tabla
        # Eso rompía encapsulación (sobrescribía un método de instancia
        # sin subclass) y era frágil: cualquier código externo que
        # guardara referencia a ``tabla_resultados.keyPressEvent`` perdía
        # la sobreescritura, y PySide6 puede no respetar la asignación
        # directa de métodos Python sobre objetos C++.
        #
        # Ahora se usa un ``QObject`` event filter instalado vía
        # ``installEventFilter``, que es el mecanismo oficial de Qt para
        # interceptar eventos sin subclassing. El filter sólo intercepta
        # ``Ctrl+V``; todo lo demás pasa al handler original.
        self._pegado_magico_filter = _PegadoMagicoFilter(
            self.tabla_resultados, self._pegar_magico_en_tabla)
        self.tabla_resultados.installEventFilter(self._pegado_magico_filter)
        right_layout.addWidget(self.tabla_resultados, 1)

        # ✅ CAMPO DE OBSERVACIONES
        obs_header = QLabel("<b>📝 Observaciones (Se guardarán en el PDF):</b>")
        obs_header.setStyleSheet(f"color: {IsaStyles.DARK}; font-size: 12px;")
        right_layout.addWidget(obs_header)

        self.observaciones_text = QTextEdit()
        self.observaciones_text.setPlaceholderText(
            "Escriba aquí observaciones clínicas relevantes...\n\nEjemplo:\nLínea Roja: EN RANGO (HIPOCROMIA)\nPlaquetas: TROMBOCITOSIS LEVE")
        self.observaciones_text.setMaximumHeight(80)
        self.observaciones_text.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid {IsaStyles.BORDER};
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                background-color: #FFFBEB; /* Amarillo muy suave para dar importancia */
            }}
        """)
        right_layout.addWidget(self.observaciones_text)

        main_layout.addWidget(right_card, 1)

        self.btn_guardar.setText("💾 Guardar Resultados")
        style_button(self.btn_guardar, 'primary')
        self.btn_cancelar.setText("❌ Cancelar")
        style_button(self.btn_cancelar, 'ghost')
        self.set_save_callback(self._guardar)

    def _cargar_datos(self):
        try:
            muestra = self.service.obtener_muestra(self.muestra_id)
            self.lbl_codigo.setText(muestra.codigo)
            self.lbl_paciente.setText(
                f"{muestra.animal_nombre} ({muestra.animal_codigo})")
            self.lbl_empresa.setText(muestra.empresa or 'Persona Natural')
            self.lbl_tipo.setText(muestra.tipo_muestra)
            self.lbl_analisis.setText(
                muestra.tipo_analisis or "No especificado")
            self.lbl_recoleccion.setText(muestra.fecha_recoleccion)

            self.estado.setCurrentText(muestra.estado)
            if muestra.estado in ['Pendiente', 'En Proceso']:
                self.estado.setCurrentText('Completado')

            # Si hay resultados, los dibujamos en la tabla
            if muestra.resultado:
                try:
                    datos = json.loads(muestra.resultado)
                    items = []

                    # Compatibilidad: si es lista directa o si es el nuevo
                    # formato con "items"
                    if isinstance(datos, list):
                        items = datos
                    elif isinstance(datos, dict) and "items" in datos:
                        items = datos["items"]

                    self.tabla_resultados.setRowCount(len(items))
                    for fila, item in enumerate(items):
                        self.tabla_resultados.setItem(
                            fila, 0, QTableWidgetItem(str(item.get("item", ""))))
                        self.tabla_resultados.setItem(
                            fila, 1, QTableWidgetItem(str(item.get("resultado", ""))))
                        self.tabla_resultados.setItem(
                            fila, 2, QTableWidgetItem(str(item.get("unidades", ""))))
                        self.tabla_resultados.setItem(
                            fila, 3, QTableWidgetItem(str(item.get("ref_texto", ""))))
                except json.JSONDecodeError:
                    pass  # Si es texto viejo, la tabla queda vacía

            # Cargar observaciones guardadas
            obs_texto = ""
            if muestra.resultado:
                try:
                    datos = json.loads(muestra.resultado)
                    if isinstance(datos, dict) and "observaciones" in datos:
                        obs_lista = datos["observaciones"]
                        if isinstance(obs_lista, list):
                            obs_texto = "\n".join(obs_lista)
                        else:
                            obs_texto = str(obs_lista)
                except Exception:
                    pass

            self.observaciones_text.setPlainText(obs_texto)

        except Exception as e:
            show_error(self, "No se pudo cargar la muestra.", e)
            self.reject()

    def _validar(self) -> bool:
        estado = self.estado.currentText()
        hay_datos = self.tabla_resultados.rowCount(
        ) > 0 or self.observaciones_text.toPlainText().strip()
        if estado == 'Completado' and not hay_datos:
            resp = QMessageBox.question(
                self,
                "Confirmar",
                "No ha ingresado resultados pero el estado es 'Completado'.<br>¿Desea continuar?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
            return resp == QMessageBox.Yes
        return True

    # ══════════════════════════════════════════════════════════════
    # PEGADO MÁGICO
    # ══════════════════════════════════════════════════════════════

    def _pegar_magico_en_tabla(self, event):
        """Pega filas parseadas desde el portapapeles a la tabla de resultados.

        Fase 5 (H-G7): antes este método se asignaba directamente como
        ``self.tabla_resultados.keyPressEvent`` (monkey-patch sobre la
        instancia), por lo que tenía que manejar también el caso "no es
        Ctrl+V" llamando a ``QTableWidget.keyPressEvent(self.tabla_resultados,
        event)``. Ahora el método solo se invoca cuando el event filter
        ``_PegadoMagicoFilter`` ya confirmó que es Ctrl+V; el resto de
        las teclas pasa directo al widget original.
        """
        clipboard = QApplication.clipboard().text()
        if not clipboard:
            return False
        import re
        patron_numero = re.compile(r'(\d+[.,]?\d*)')
        lineas = clipboard.strip().split('\n')
        fila_inicial = self.tabla_resultados.rowCount()
        nuevas_filas = 0
        datos_temporales = []
        for linea in lineas:
            if not linea.strip():
                continue
            match = patron_numero.search(linea.strip())
            if not match:
                continue
            pos = match.start()
            nombre = linea[:pos].strip()
            resto = linea[pos:].strip()
            partes = resto.split(None, 2)
            datos_temporales.append([nombre, partes[0].strip().replace(',', '.'), partes[1].strip(
            ) if len(partes) > 1 else "", partes[2].strip() if len(partes) > 2 else ""])
            nuevas_filas += 1
        if nuevas_filas == 0:
            return False
        self.tabla_resultados.setRowCount(fila_inicial + nuevas_filas)
        for i, datos in enumerate(datos_temporales):
            fila = fila_inicial + i
            for col, texto in enumerate(datos):
                self.tabla_resultados.setItem(
                    fila, col, QTableWidgetItem(texto))
        event.accept()
        return True

    # ══════════════════════════════════════════════════════════════
    # INTELIGENCIA: COLOREAR Y ANALIZAR RANGOS
    # ══════════════════════════════════════════════════════════════

    def _evaluar_rango(self, valor_str: str, ref_str: str) -> tuple:
        """Retorna (estado, texto_obs). Estado puede ser 'normal', 'bajo', 'alto'"""
        if not valor_str or not ref_str:
            return "normal", ""
        try:
            valor = float(valor_str.replace(',', '.'))
            # Limpiar guiones raros y separar por espacios
            partes = ref_str.replace('–', '-').replace(',', '.').split()
            min_val, max_val = 0, 0
            if len(partes) >= 3:
                min_val, max_val = float(partes[0]), float(partes[2])
            elif len(partes) == 2:
                min_val, max_val = float(partes[0]), float(partes[1])
            else:
                return "normal", ""

            if valor < min_val:
                return "bajo", f"{ref_str} (BAJO)"
            if valor > max_val:
                return "alto", f"{ref_str} (ALTO)"
            return "normal", ""
        except Exception:
            return "normal", ""

    def _colorear_tabla_y_generar_observaciones(self) -> list:
        """Pinta la tabla y devuelve una lista de alertas automáticas."""
        from PySide6.QtGui import QColor
        alertas_auto = []

        color_alto_bg = QColor("#FFEBEE")  # Rojo suave
        color_bajo_bg = QColor("#E3F2FD")  # Azul suave
        texto_peligro = QColor("#C62828")
        texto_advertencia = QColor("#1565C0")

        for fila in range(self.tabla_resultados.rowCount()):
            item_nombre = self.tabla_resultados.item(fila, 0)
            if not item_nombre:
                continue

            nombre = item_nombre.text().strip()
            valor_str = self.tabla_resultados.item(
                fila, 1).text().strip() if self.tabla_resultados.item(
                fila, 1) else ""
            ref_str = self.tabla_resultados.item(
                fila, 3).text().strip() if self.tabla_resultados.item(
                fila, 3) else ""

            estado, texto_alerta = self._evaluar_rango(valor_str, ref_str)

            if estado == "alto":
                alertas_auto.append(f"• {nombre}: {texto_alerta}")
                for c in range(4):
                    it = self.tabla_resultados.item(fila, c)
                    if it:
                        it.setBackground(color_alto_bg)
                        it.setForeground(texto_peligro)
            elif estado == "bajo":
                alertas_auto.append(f"• {nombre}: {texto_alerta}")
                for c in range(4):
                    it = self.tabla_resultados.item(fila, c)
                    if it:
                        it.setBackground(color_bajo_bg)
                        it.setForeground(texto_advertencia)

        return alertas_auto

    def _extraer_json_desde_tabla(self) -> str:
        """Convierte la tabla al JSON final que lee el PDF (AHORA CON COLORES)."""
        items = []
        for fila in range(self.tabla_resultados.rowCount()):
            item_nombre = self.tabla_resultados.item(fila, 0)
            if not item_nombre or not item_nombre.text().strip():
                continue

            # Leemos los valores para evaluar
            valor_str = self.tabla_resultados.item(
                fila, 1).text().strip() if self.tabla_resultados.item(
                fila, 1) else ""
            ref_str = self.tabla_resultados.item(
                fila, 3).text().strip() if self.tabla_resultados.item(
                fila, 3) else ""

            # ✅ Evaluamos el rango (igual que hace la tabla para colorearse)
            estado, _ = self._evaluar_rango(valor_str, ref_str)

            items.append({
                "item": item_nombre.text().strip(),
                "resultado": valor_str,
                "unidades": self.tabla_resultados.item(fila, 2).text().strip() if self.tabla_resultados.item(fila,
                                                                                                             2) else "",
                "ref_texto": ref_str,
                "clasificacion": estado  # ✅ LE DECIMOS AL PDF SI ES "alto", "bajo" o "normal"
            })

        # Analizar y generar observaciones
        alertas_auto = self._colorear_tabla_y_generar_observaciones()
        obs_manuales = [
            o.strip() for o in self.observaciones_text.toPlainText().split('\n') if o.strip()]
        todas_obs = alertas_auto + obs_manuales

        json_final = {
            "items": items,
            "observaciones": todas_obs
        }
        return json.dumps(json_final, ensure_ascii=False) if items else ""

    # ══════════════════════════════════════════════════════════════
    # GUARDAR E IMPRIMIR
    # ══════════════════════════════════════════════════════════════

    @ErrorHandler.handle_exception
    def _guardar(self):
        if not self._validar():
            return

        estado = self.estado.currentText()
        resultado_final = self._extraer_json_desde_tabla()
        # Fase 4 (C1): antes se referenciaba `self.ref_text.toPlainText()`
        # pero ese widget NUNCA se crea en el diálogo, así que el botón
        # "💾 Guardar Resultados" siempre levantaba AttributeError y los
        # resultados no se persistían. Las referencias por ítem ya viajan
        # dentro del JSON de `resultado_final` (columna "Referencia" de
        # `tabla_resultados`); el campo global `valor_referencia` de la
        # muestra queda como None cuando no hay texto global adicional.
        valor_ref = None

        self.service.actualizar_estado(
            self.muestra_id, estado, resultado_final, valor_ref)
        QMessageBox.information(
            self, "✅ Éxito", "Resultados guardados correctamente.")
        if self.on_save:
            self.on_save()
        self.accept()

    @ErrorHandler.handle_exception
    def _imprimir_pdf(self):
        estado = self.estado.currentText()
        resultado_final = self._extraer_json_desde_tabla()

        self.service.actualizar_estado(
            self.muestra_id, estado, resultado_final)
        if self.on_save:
            self.on_save()

        from services.report_laboratorio import ReporteLaboratorioService
        import os

        muestra = self.service.obtener_muestra(self.muestra_id)
        entidad = getattr(muestra, 'empresa', None) or 'Persona Natural'
        es_empresa = entidad.strip().upper() != "PERSONA NATURAL"
        datos_empresa = {"nombre": entidad} if es_empresa else None

        nuevo_motor = ReporteLaboratorioService()
        pdf_bytes = nuevo_motor.generar_pdf(
            self.muestra_id,
            es_empresa=es_empresa,
            datos_empresa=datos_empresa
        )

        dir_path = "data/pdfs"
        os.makedirs(dir_path, exist_ok=True)
        codigo_limpio = self.lbl_codigo.text().replace("/", "-")
        filepath = os.path.join(dir_path, f"LAB_{codigo_limpio}.pdf")

        with open(filepath, "wb") as f:
            f.write(pdf_bytes)

        # Fase 4 (C4): reemplazo de `os.startfile(filepath)` que solo
        # existe en Windows y rompía "🖨️ Guardar e Imprimir PDF" en
        # macOS/Linux. El helper usa `open` / `xdg-open` según el SO.
        from gui_pyside.utils.platform_utils import open_file_externally
        open_file_externally(filepath)


class DetalleMuestraDialog(BaseDialog):
    def __init__(self, parent=None, muestra_id=None):
        super().__init__(parent, "📄 Reporte de Muestra", 1000, 600)
        self.muestra_id = muestra_id
        self.service = MuestraService()
        # Fase 6 (G-M8): overlay de carga para el botón "Imprimir
        # Resultados Pro" (spawn de ``PDFProWorker``). Lazy-init: se
        # crea solo si el usuario dispara la impresión. ``parent=self``
        # para que el overlay se redimensione con el diálogo y se
        # destruya automáticamente al cerrarlo.
        self._loading_overlay = None
        self._build()
        self._cargar_datos()

    def _ensure_loading_overlay(self):
        """Crea el ``LoadingOverlay`` perezosamente."""
        if self._loading_overlay is None:
            self._loading_overlay = LoadingOverlay(self, "Generando PDF...")
        return self._loading_overlay

    def _build(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        self.content_layout.addLayout(main_layout)

        # ── CARD IZQUIERDA ────────────────────────────────────────────────
        left_card = QGroupBox("📋 Información General")
        style_group(left_card, IsaStyles.SECONDARY)
        left_layout = QFormLayout(left_card)
        left_layout.setSpacing(12)

        self.lbl_codigo = QLabel("-")
        self.lbl_codigo.setStyleSheet(
            "font-weight: bold; font-size: 16px; color: #1E3A5F;")
        left_layout.addRow("Código:", self.lbl_codigo)

        self.lbl_paciente = QLabel("-")
        left_layout.addRow("Paciente:", self.lbl_paciente)
        self.lbl_empresa = QLabel("-")
        left_layout.addRow("Entidad:", self.lbl_empresa)
        self.lbl_especie = QLabel("-")
        left_layout.addRow("Especie:", self.lbl_especie)
        self.lbl_tipo = QLabel("-")
        left_layout.addRow("Tipo:", self.lbl_tipo)
        self.lbl_analisis = QLabel("-")
        left_layout.addRow("Análisis:", self.lbl_analisis)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(
            f"background-color: {IsaStyles.BORDER}; margin: 8px 0;")
        left_layout.addRow(line)

        self.lbl_estado = QLabel("-")
        left_layout.addRow("Estado:", self.lbl_estado)
        self.lbl_recoleccion = QLabel("-")
        left_layout.addRow("Recolección:", self.lbl_recoleccion)
        self.lbl_urgente = QLabel("")
        left_layout.addRow("Prioridad:", self.lbl_urgente)
        main_layout.addWidget(left_card, 0)

        # ── CARD DERECHA: TABLA DE SOLO LECTURA ──────────────────────
        right_card = QGroupBox("📝 Resultados del Laboratorio")
        style_group(right_card, IsaStyles.ACCENT)
        right_layout = QVBoxLayout(right_card)
        right_layout.setSpacing(16)

        # La Tabla
        self.tabla_resultados = QTableWidget()
        self.tabla_resultados.setColumnCount(4)
        self.tabla_resultados.setHorizontalHeaderLabels(
            ["Ítem", "Resultado", "Unidades", "Referencia"])
        self.tabla_resultados.horizontalHeader().setStretchLastSection(True)
        self.tabla_resultados.setColumnWidth(0, 200)
        self.tabla_resultados.setColumnWidth(1, 100)
        self.tabla_resultados.setColumnWidth(2, 100)
        self.tabla_resultados.setMinimumHeight(200)
        self.tabla_resultados.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)  # SOLO LECTURA
        self.tabla_resultados.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectItems)
        self.tabla_resultados.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection)
        self.tabla_resultados.setStyleSheet(f"""
            QTableWidget {{
                border: 2px solid {IsaStyles.BORDER};
                border-radius: 6px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                gridline-color: {IsaStyles.BORDER};
            }}
            QTableWidget::item {{ padding: 4px; }}
            QHeaderView::section {{
                background-color: {IsaStyles.PRIMARY};
                color: white;
                padding: 4px;
                border: 1px solid {IsaStyles.SECONDARY};
                font-weight: bold;
            }}
        """)
        right_layout.addWidget(self.tabla_resultados, 1)

        # Observaciones (Solo lectura)
        self.observaciones_text = QLabel("-")
        self.observaciones_text.setWordWrap(True)
        self.observaciones_text.setStyleSheet(
            f"color: {
                IsaStyles.DARK}; font-size: 12px; padding: 10px; background-color: {
                IsaStyles.LIGHT_BG}; border-radius: 4px; border: 1px solid {
                IsaStyles.BORDER};")
        right_layout.addWidget(self.observaciones_text, 1)

        # Botón Imprimir
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch()

        self.btn_imprimir = QPushButton("🖨️ Imprimir Resultados Pro")
        style_button(self.btn_imprimir, 'primary')
        self.btn_imprimir.setMinimumWidth(200)
        self.btn_imprimir.clicked.connect(self._imprimir_pdf)
        btn_layout.addWidget(self.btn_imprimir)
        right_layout.addWidget(btn_container)

        main_layout.addWidget(right_card, 1)

        self.btn_guardar.setText("✅ Cerrar")
        style_button(self.btn_guardar, 'secondary')
        self.set_save_callback(self.accept)
        self.btn_cancelar.hide()

    def _cargar_datos(self):
        from PySide6.QtGui import QColor

        try:
            muestra = self.service.obtener_muestra(self.muestra_id)
            self.lbl_codigo.setText(muestra.codigo)
            self.lbl_paciente.setText(
                f"{muestra.animal_nombre} ({muestra.animal_codigo})")
            self.lbl_empresa.setText(muestra.empresa or 'Persona Natural')
            self.lbl_especie.setText(muestra.especie or 'No especificada')
            self.lbl_tipo.setText(muestra.tipo_muestra)
            self.lbl_analisis.setText(
                muestra.tipo_analisis or "No especificado")
            self.lbl_estado.setText(muestra.estado)
            self.lbl_recoleccion.setText(muestra.fecha_recoleccion)

            if muestra.urgente:
                self.lbl_urgente.setText(
                    "⚠️ <b style='color:#EF4444;'>URGENTE</b>")
            else:
                self.lbl_urgente.setText(
                    "<span style='color:#22C55E;'>Normal</span>")

            # Observaciones
            obs_texto = "Sin observaciones registradas."
            try:
                if muestra.resultado:
                    datos = json.loads(muestra.resultado)
                    if isinstance(datos, dict) and "observaciones" in datos:
                        obs_lista = datos["observaciones"]
                        if isinstance(obs_lista, list):
                            obs_texto = "\n".join(
                                [f"• {o}" for o in obs_lista if o])
            except Exception:
                pass  # Si el JSON falla, no pasa nada, mantiene el texto por defecto

            self.observaciones_text.setText(obs_texto)

            # Tabla de Resultados
            items = []
            if muestra.resultado:
                try:
                    datos = json.loads(muestra.resultado)
                    if isinstance(datos, list):
                        items = datos
                    elif isinstance(datos, dict) and "items" in datos:
                        items = datos["items"]
                except Exception:
                    pass

            self.tabla_resultados.setRowCount(len(items))

            color_alto_bg = QColor("#FFEBEE")
            color_bajo_bg = QColor("#E3F2FD")
            texto_peligro = QColor("#C62828")
            texto_advertencia = QColor("#1565C0")

            for fila, item in enumerate(items):
                self.tabla_resultados.setItem(
                    fila, 0, QTableWidgetItem(str(item.get("item", ""))))
                self.tabla_resultados.setItem(
                    fila, 1, QTableWidgetItem(str(item.get("resultado", ""))))
                self.tabla_resultados.setItem(
                    fila, 2, QTableWidgetItem(str(item.get("unidades", ""))))
                self.tabla_resultados.setItem(
                    fila, 3, QTableWidgetItem(str(item.get("ref_texto", ""))))

                # ✅ Colorear filas alteradas (igual que en la pantalla de ingreso)
                clasificacion = item.get("clasificacion", "normal")
                if clasificacion == "alto":
                    for c in range(4):
                        it = self.tabla_resultados.item(fila, c)
                        if it:
                            it.setBackground(color_alto_bg)
                            it.setForeground(texto_peligro)
                elif clasificacion == "bajo":
                    for c in range(4):
                        it = self.tabla_resultados.item(fila, c)
                        if it:
                            it.setBackground(color_bajo_bg)
                            it.setForeground(texto_advertencia)

            if not items:
                self.tabla_resultados.setRowCount(1)
                self.tabla_resultados.setItem(
                    0, 0, QTableWidgetItem("Sin resultados estructurados"))

        except Exception as e:
            show_error(self, "No se pudo cargar la muestra.", e)

    @ErrorHandler.handle_exception
    def _imprimir_pdf(self):
        self.btn_imprimir.setText("Generando Reporte Pro... ⏳")
        self.btn_imprimir.setEnabled(False)

        # Fase 6 (G-M8): mostramos el overlay de carga ANTES de
        # arrancar el worker. ``LoadingOverlay.start()`` no bloquea —
        # es solo un widget semitransparente sobre el diálogo. El
        # worker corre en otro thread, así que la UI sigue responsiva
        # (el overlay gira) mientras el PDF se genera.
        self._ensure_loading_overlay().start("Generando PDF...")

        muestra = self.service.obtener_muestra(self.muestra_id)
        entidad = getattr(muestra, 'empresa', None) or 'Persona Natural'
        es_empresa = entidad.strip().upper() != "PERSONA NATURAL"
        datos_empresa = {"nombre": entidad} if es_empresa else None

        # Fase 5 (H-G8): ``PDFProWorker`` ahora es clase de módulo (no
        # anidada en este método). Conectamos ``finished`` a
        # ``deleteLater()`` para que Qt limpie el QThread al terminar,
        # evitando la fuga de threads que ocurría antes (cada click
        # acumulaba un QThread zombie).
        # Si ya había un worker corriendo (doble-click rápido), lo
        # cancelamos y dejamos que Qt lo limpie.
        if getattr(self, 'worker', None) is not None and \
                self.worker.isRunning():
            try:
                self.worker.quit()
                self.worker.wait(2000)  # 2s de gracia
            except Exception:
                pass
        self.worker = PDFProWorker(
            self.muestra_id, es_empresa, datos_empresa, parent=self)
        self.worker.terminado.connect(self._pdf_exito)
        self.worker.error.connect(self._pdf_error)
        # Limpieza automática al terminar (éxito o error).
        self.worker.finished.connect(self.worker.deleteLater)
        # Fase 6 (G-M8): ocultar overlay cuando el worker termine
        # (éxito o error). ``finished`` se emite DESPUÉS de
        # ``terminado``/``error``, así que las callbacks ya
        # actualizaron la UI — el overlay ya no es necesario.
        self.worker.finished.connect(self._hide_loading_overlay)
        self.worker.start()

    def _hide_loading_overlay(self):
        """Oculta el overlay de carga si está visible."""
        if self._loading_overlay is not None:
            self._loading_overlay.stop()

    def _pdf_exito(self, pdf_bytes):
        dir_path = "data/pdfs"
        os.makedirs(dir_path, exist_ok=True)
        codigo_limpio = self.lbl_codigo.text().replace("/", "-")
        filename = f"LAB_{codigo_limpio}.pdf"
        filepath = os.path.join(dir_path, filename)
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)
        # Fase 4 (C4): helper multiplataforma en lugar de `os.startfile`
        # (que solo existe en Windows y rompía el botón
        # "🖨️ Imprimir Resultados Pro" en macOS/Linux).
        from gui_pyside.utils.platform_utils import open_file_externally
        open_file_externally(filepath)
        self.btn_imprimir.setText("🖨️ Imprimir Resultados Pro")
        self.btn_imprimir.setEnabled(True)

    def _pdf_error(self, error_msg):
        self.btn_imprimir.setText("🖨️ Imprimir Resultados Pro")
        self.btn_imprimir.setEnabled(True)
        # Fase 6 (G-M8): en error, ocultamos el overlay acá también
        # (aunque ``finished`` ya lo hará, lo hacemos acá para que el
        # overlay desaparezca antes de que aparezca el QMessageBox de
        # error — sinó el overlay tapa el dialog).
        self._hide_loading_overlay()
        show_error(
            self,
            "Fallo en el motor de impresión.",
            Exception(error_msg))
