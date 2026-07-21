# gui_pyside/dialogs/animal_dialog.py
"""Diálogos de pacientes para PySide6 - VERSIÓN AMPLIADA"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QFrame,
    QMessageBox,
    QFormLayout,
    QGroupBox,
    QDoubleSpinBox,
    QSpinBox)
from PySide6.QtCore import Qt, QDate

from gui_pyside.dialogs.base_dialog import BaseDialog
from gui_pyside.components.components import ErrorHandler, StatusBadge
from gui_pyside.utils.messages import show_error, show_warning
from gui_pyside.styles import IsaStyles, style_button, style_group, style_input
from services.animal_service import AnimalService
from gui_pyside.components.forms import FormField, FormRow


# =======================================================================
# 1. DIÁLOGO DE NUEVO PACIENTE
# =======================================================================
class NuevoAnimalDialog(BaseDialog):
    def __init__(self, parent=None, on_save=None):
        # Aumentamos un poco la altura de la ventana para que quepa todo
        super().__init__(parent, "➕ Nuevo Paciente", 950, 700)
        self.on_save = on_save
        self.service = AnimalService()
        self._build()

    def _build(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        self.content_layout.addLayout(main_layout)

        # --- CARD IZQUIERDA: Datos Médicos y Fenotípicos ---
        left_card = QGroupBox("🐾 Perfil Clínico y Fenotipo")
        style_group(left_card, IsaStyles.ACCENT)
        left_layout = QFormLayout(left_card)
        left_layout.setSpacing(12)
        left_layout.setLabelAlignment(Qt.AlignLeft)

        # Fila 1: Código + Microchip
        self.codigo_field = FormField("Código", 'lineedit', required=True)
        self.microchip_field = FormField(
            "Microchip",
            'lineedit',
            required=False,
            placeholder="N° Microchip")

        codigo_generado = self.service.obtener_siguiente_codigo()
        input_codigo = self.codigo_field.findChild(QLineEdit)
        if input_codigo:
            input_codigo.setText(codigo_generado)
            input_codigo.setReadOnly(True)
            input_codigo.setStyleSheet(
                f"background-color: #F1F5F9; color: {IsaStyles.GRAY}; font-weight: bold;")

        left_layout.addRow(FormRow([self.codigo_field, self.microchip_field]))

        # Fila 2: Nombre + Sexo
        self.nombre_field = FormField(
            "Nombre",
            'lineedit',
            required=True,
            placeholder="Nombre del paciente")
        self.sexo_field = FormField(
            "Sexo", 'combo', required=False, items=[
                "Macho", "Hembra", "Desconocido"])
        left_layout.addRow(FormRow([self.nombre_field, self.sexo_field]))

        # Fila 3: Especie + Raza
        self.especie_field = FormField(
            "Especie", 'combo', required=False, items=[
                "Canino", "Felino", "Ave", "Bovino", "Equino", "Otro"])
        self.raza_field = FormField(
            "Raza",
            'lineedit',
            required=False,
            placeholder="Raza")
        left_layout.addRow(FormRow([self.especie_field, self.raza_field]))

        # Fila 4: Fecha Nac. + Edad + Unidad (Agrupado)
        self.fecha_nac_field = FormField(
            "F. Nacimiento",
            'lineedit',
            required=False,
            placeholder="DD/MM/AAAA")
        self.edad_field = FormField(
            "Edad",
            'spin',
            required=False,
            range=(
                0,
                100))
        self.unidad_edad_field = FormField(
            "Unidad", 'combo', required=False, items=[
                "Años", "Meses", "Semanas"])
        left_layout.addRow(
            FormRow([self.fecha_nac_field, self.edad_field, self.unidad_edad_field]))

        # Fila 5: Peso + Color + Pelo
        self.peso_field = FormField(
            "Peso", 'doublespin', required=False, range=(
                0, 500), suffix=" kg", decimals=2)
        self.color_field = FormField(
            "Color",
            'lineedit',
            required=False,
            placeholder="Ej: Atigrado")
        self.pelo_field = FormField(
            "Tipo Pelo",
            'lineedit',
            required=False,
            placeholder="Ej: Corto")
        left_layout.addRow(
            FormRow([self.peso_field, self.color_field, self.pelo_field]))

        # Fila 6: Señas + Estado
        self.senas_field = FormField(
            "Señas Particulares",
            'lineedit',
            required=False,
            placeholder="Ej: Mancha blanca en pata")
        self.estado_field = FormField(
            "Estado", 'combo', required=False, items=[
                "Activo", "En Tratamiento", "Cuarentena"])
        left_layout.addRow(FormRow([self.senas_field, self.estado_field]))

        main_layout.addWidget(left_card, 1)

        # --- CARD DERECHA: Datos del Propietario ---
        right_card = QGroupBox("👤 Datos del Propietario")
        style_group(right_card, IsaStyles.PRIMARY)
        right_layout = QFormLayout(right_card)
        right_layout.setSpacing(12)

        # Propietario completo
        self.propietario_field = FormField(
            "Nombre del Dueño",
            'lineedit',
            required=False,
            placeholder="Nombre completo")
        right_layout.addRow(self.propietario_field)

        # Documento
        self.tipo_doc_field = FormField(
            "Tipo Doc.", 'combo', required=False, items=[
                "CC", "CE", "NIT", "Pasaporte", "Otro"])
        self.documento_field = FormField(
            "Número Doc.",
            'lineedit',
            required=False,
            placeholder="N° Documento")
        right_layout.addRow(
            FormRow([self.tipo_doc_field, self.documento_field]))

        # Residencia y Oficio
        self.direccion_field = FormField(
            "Dirección",
            'lineedit',
            required=False,
            placeholder="Dirección de residencia")
        self.oficio_field = FormField(
            "Oficio",
            'lineedit',
            required=False,
            placeholder="Profesión u ocupación")
        right_layout.addRow(FormRow([self.direccion_field, self.oficio_field]))

        # Contacto
        self.telefono_field = FormField(
            "Teléfono",
            'lineedit',
            required=False,
            placeholder="Celular o fijo")
        self.email_field = FormField(
            "Email",
            'lineedit',
            required=False,
            placeholder="correo@ejemplo.com")
        right_layout.addRow(FormRow([self.telefono_field, self.email_field]))

        # Observaciones
        self.observaciones_field = FormField(
            "Notas",
            'textarea',
            required=False,
            max_height=80,
            placeholder="Alergias, condiciones previas...")
        right_layout.addRow(self.observaciones_field)

        main_layout.addWidget(right_card, 1)

        # Botones
        self.btn_guardar.setText("💾 Guardar Paciente")
        style_button(self.btn_guardar, 'primary')
        self.btn_cancelar.setText("❌ Cancelar")
        style_button(self.btn_cancelar, 'ghost')

        self.set_save_callback(self._guardar)

    def _validate(self) -> bool:
        valid = True
        if not self.codigo_field.validate():
            valid = False
        if not self.nombre_field.validate():
            valid = False
        return valid

    @ErrorHandler.handle_exception
    def _guardar(self):
        if not self._validate():
            return

        # Mapeamos TODO al diccionario que espera Pydantic y SQLAlchemy
        data = {
            'codigo': self.codigo_field.get_value(),
            'microchip': self.microchip_field.get_value() or None,
            'nombre': self.nombre_field.get_value(),
            'sexo': self.sexo_field.get_value(),
            'especie': self.especie_field.get_value(),
            'raza': self.raza_field.get_value() or None,
            'fecha_nacimiento': self.fecha_nac_field.get_value() or None,
            'edad': self.edad_field.get_value() if self.edad_field.get_value() > 0 else None,
            'unidad_edad': self.unidad_edad_field.get_value(),
            'peso': self.peso_field.get_value() if self.peso_field.get_value() > 0 else None,
            'color': self.color_field.get_value() or None,
            'tipo_pelo': self.pelo_field.get_value() or None,
            'senas_particulares': self.senas_field.get_value() or None,
            'estado': self.estado_field.get_value(),
            'propietario': self.propietario_field.get_value() or None,
            'propietario_tipo_doc': self.tipo_doc_field.get_value() or None,
            'propietario_documento': self.documento_field.get_value() or None,
            'propietario_direccion': self.direccion_field.get_value() or None,
            'propietario_oficio': self.oficio_field.get_value() or None,
            'telefono': self.telefono_field.get_value() or None,
            'email': self.email_field.get_value() or None,
            'observaciones': self.observaciones_field.get_value() or None,
            'fecha_ingreso': QDate.currentDate().toString("yyyy-MM-dd")}

        self.service.registrar_ingreso(data)
        QMessageBox.information(
            self, "✅ Éxito", f"Paciente <b>{
                data['nombre']}</b> registrado.")
        if self.on_save:
            self.on_save()
        self.accept()


# =======================================================================
# 2. DIÁLOGO DE EDICIÓN
# =======================================================================
class EditarAnimalDialog(NuevoAnimalDialog):
    def __init__(self, parent=None, animal_id=None, on_save=None):
        self.animal_id = animal_id
        super().__init__(parent, on_save)
        self.setWindowTitle("✏️ Editar Paciente")

        input_codigo = self.codigo_field.findChild(QLineEdit)
        if input_codigo:
            input_codigo.setEnabled(False)

        self._cargar_datos()

    def _cargar_datos(self):
        try:
            animal = self.service.obtener_animal(self.animal_id)

            # Usar setters seguros para cargar los datos en los FormFields
            self.codigo_field.findChild(QLineEdit).setText(animal.codigo)
            if hasattr(animal, 'microchip') and animal.microchip:
                self.microchip_field.findChild(QLineEdit).setText(
                    animal.microchip)

            self.nombre_field.findChild(QLineEdit).setText(animal.nombre)
            if hasattr(animal, 'sexo') and animal.sexo:
                self.sexo_field.findChild(
                    QComboBox).setCurrentText(animal.sexo)
            self.especie_field.findChild(
                QComboBox).setCurrentText(animal.especie)
            if animal.raza:
                self.raza_field.findChild(QLineEdit).setText(animal.raza)

            if hasattr(animal, 'fecha_nacimiento') and animal.fecha_nacimiento:
                self.fecha_nac_field.findChild(
                    QLineEdit).setText(animal.fecha_nacimiento)
            if animal.edad:
                self.edad_field.findChild(QSpinBox).setValue(animal.edad)
            if hasattr(animal, 'unidad_edad') and animal.unidad_edad:
                self.unidad_edad_field.findChild(
                    QComboBox).setCurrentText(animal.unidad_edad)

            if animal.peso:
                self.peso_field.findChild(QDoubleSpinBox).setValue(animal.peso)
            if hasattr(animal, 'color') and animal.color:
                self.color_field.findChild(QLineEdit).setText(animal.color)
            if hasattr(animal, 'tipo_pelo') and animal.tipo_pelo:
                self.pelo_field.findChild(QLineEdit).setText(
                    animal.tipo_pelo)
            if hasattr(
                    animal,
                    'senas_particulares') and animal.senas_particulares:
                self.senas_field.findChild(
                    QLineEdit).setText(animal.senas_particulares)
            self.estado_field.findChild(
                QComboBox).setCurrentText(animal.estado)

            if animal.propietario:
                self.propietario_field.findChild(
                    QLineEdit).setText(animal.propietario)
            if hasattr(
                    animal,
                    'propietario_tipo_doc') and animal.propietario_tipo_doc:
                self.tipo_doc_field.findChild(
                    QComboBox).setCurrentText(animal.propietario_tipo_doc)
            if hasattr(
                    animal,
                    'propietario_documento') and animal.propietario_documento:
                self.documento_field.findChild(
                    QLineEdit).setText(animal.propietario_documento)
            if hasattr(
                    animal,
                    'propietario_direccion') and animal.propietario_direccion:
                self.direccion_field.findChild(
                    QLineEdit).setText(animal.propietario_direccion)
            if hasattr(
                    animal,
                    'propietario_oficio') and animal.propietario_oficio:
                self.oficio_field.findChild(
                    QLineEdit).setText(animal.propietario_oficio)

            if animal.telefono:
                self.telefono_field.findChild(
                    QLineEdit).setText(animal.telefono)
            if animal.email:
                self.email_field.findChild(QLineEdit).setText(animal.email)
            if animal.observaciones:
                self.observaciones_field.findChild(
                    QTextEdit).setPlainText(animal.observaciones)

        except Exception as e:
            show_error(self, "No se pudo cargar el paciente.", e)
            self.reject()

    @ErrorHandler.handle_exception
    def _guardar(self):
        if not self.nombre_field.get_value():
            show_warning(self, "Error", "El nombre es obligatorio.")
            return

        data = {
            'microchip': self.microchip_field.get_value() or None,
            'nombre': self.nombre_field.get_value(),
            'sexo': self.sexo_field.get_value(),
            'especie': self.especie_field.get_value(),
            'raza': self.raza_field.get_value() or None,
            'fecha_nacimiento': self.fecha_nac_field.get_value() or None,
            'edad': self.edad_field.get_value() if self.edad_field.get_value() > 0 else None,
            'unidad_edad': self.unidad_edad_field.get_value(),
            'peso': self.peso_field.get_value() if self.peso_field.get_value() > 0 else None,
            'color': self.color_field.get_value() or None,
            'tipo_pelo': self.pelo_field.get_value() or None,
            'senas_particulares': self.senas_field.get_value() or None,
            'estado': self.estado_field.get_value(),
            'propietario': self.propietario_field.get_value() or None,
            'propietario_tipo_doc': self.tipo_doc_field.get_value() or None,
            'propietario_documento': self.documento_field.get_value() or None,
            'propietario_direccion': self.direccion_field.get_value() or None,
            'propietario_oficio': self.oficio_field.get_value() or None,
            'telefono': self.telefono_field.get_value() or None,
            'email': self.email_field.get_value() or None,
            'observaciones': self.observaciones_field.get_value() or None}

        self.service.actualizar_datos(self.animal_id, data)
        QMessageBox.information(self, "✅ Éxito", "Datos actualizados.")
        if self.on_save:
            self.on_save()
        self.accept()


# =======================================================================
# 3. DIÁLOGO DE DETALLES
# =======================================================================
class DetalleAnimalDialog(BaseDialog):
    def __init__(self, parent=None, animal_id=None):
        super().__init__(parent, "📋 Ficha del Paciente", 950, 600)
        self.animal_id = animal_id
        self.service = AnimalService()
        self._build()

    def _build(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        self.content_layout.addLayout(main_layout)

        try:
            animal = self.service.obtener_animal(self.animal_id)

            # --- CARD IZQUIERDA: Perfil General ---
            perfil_card = QGroupBox("🐾 Perfil del Paciente")
            style_group(perfil_card, IsaStyles.ACCENT)
            perfil_layout = QFormLayout(perfil_card)
            perfil_layout.setSpacing(12)

            estado_badge = StatusBadge(animal.estado)
            perfil_layout.addRow("Estado:", estado_badge)

            perfil_layout.addRow("Código:", QLabel(f"<b>{animal.codigo}</b>"))
            if hasattr(animal, 'microchip') and animal.microchip:
                perfil_layout.addRow(
                    "Microchip:", QLabel(
                        f"<b>{
                            animal.microchip}</b>"))

            sexo = getattr(animal, 'sexo', '')
            perfil_layout.addRow("Nombre:", QLabel(
                f"<span style='font-size:16px;'>{animal.nombre} ({sexo})</span>"))
            perfil_layout.addRow(
                "Especie/Raza:", QLabel(f"{animal.especie} - {animal.raza or 'N/A'}"))

            unidad = getattr(animal, 'unidad_edad', 'Años')
            nacimiento = getattr(animal, 'fecha_nacimiento', '')
            nac_str = f" (Nac: {nacimiento})" if nacimiento else ""
            fisico_text = f"Edad: <b>{
                animal.edad or 'N/A'} {unidad}</b>{nac_str}  |  Peso: <b>{
                animal.peso or 'N/A'} kg</b>"
            perfil_layout.addRow("Físico:", QLabel(fisico_text))

            color = getattr(animal, 'color', '')
            pelo = getattr(animal, 'tipo_pelo', '')
            senas = getattr(animal, 'senas_particulares', '')
            if color or pelo or senas:
                fenotipo = f"Color: {color} | Pelo: {pelo}<br>Señas: {senas}"
                perfil_layout.addRow("Fenotipo:", QLabel(fenotipo))

            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet(f"background-color: {IsaStyles.BORDER};")
            perfil_layout.addRow(line)

            perfil_layout.addRow("Propietario:", QLabel(
                f"<b>{animal.propietario or 'N/A'}</b>"))

            doc_tipo = getattr(animal, 'propietario_tipo_doc', '')
            doc_num = getattr(animal, 'propietario_documento', '')
            if doc_num:
                perfil_layout.addRow(
                    "Documento:", QLabel(
                        f"{doc_tipo} {doc_num}"))

            direccion = getattr(animal, 'propietario_direccion', '')
            if direccion:
                perfil_layout.addRow("Dirección:", QLabel(direccion))

            contacto = f"{animal.telefono or ''} | {animal.email or ''}"
            perfil_layout.addRow(
                "Contacto:", QLabel(
                    contacto or "No registrado"))

            main_layout.addWidget(perfil_card, 1)

            # --- CARD DERECHA: Historial ---
            historial_card = QGroupBox("📜 Historial de Movimientos")
            style_group(historial_card, IsaStyles.SECONDARY)
            historial_layout = QVBoxLayout(historial_card)

            movimientos = self.service.obtener_historial(self.animal_id)
            if movimientos:
                for i, m in enumerate(movimientos[:8]):
                    fecha = m.fecha_hora[:10] if m.fecha_hora else ""
                    tipo_icon = "📥" if m.tipo == 'Entrada' else "📤"

                    mov_widget = QWidget()
                    mov_layout = QHBoxLayout(mov_widget)
                    mov_layout.setContentsMargins(0, 0, 0, 0)

                    lbl = QLabel(
                        f"{tipo_icon} <b>{fecha}</b> | {m.tipo} - {m.motivo}")
                    lbl.setStyleSheet(
                        f"color: {
                            IsaStyles.DARK}; padding: 4px;")
                    if i % 2 == 0:
                        lbl.setStyleSheet(
                            f"background-color: {
                                IsaStyles.LIGHT_BG}; color: {
                                IsaStyles.DARK}; padding: 4px; border-radius: 4px;")

                    mov_layout.addWidget(lbl)
                    historial_layout.addWidget(mov_widget)
            else:
                lbl = QLabel("No hay movimientos registrados.")
                lbl.setStyleSheet(
                    f"color: {
                        IsaStyles.GRAY}; font-style: italic;")
                historial_layout.addWidget(lbl)

            historial_layout.addStretch()
            main_layout.addWidget(historial_card, 1)

        except Exception as e:
            main_layout.addWidget(
                QLabel(
                    f"<span style='color:red;'>Error cargando ficha: {e}</span>"))

        self.btn_guardar.setText("✅ Cerrar")
        style_button(self.btn_guardar, 'secondary')
        self.btn_guardar.clicked.connect(self.accept)
        self.btn_cancelar.hide()


# =======================================================================
# 4. DIÁLOGO DE SALIDA / ALTA (MEJORADO)
# =======================================================================
class SalidaAnimalDialog(BaseDialog):
    def __init__(self, parent=None, animal_id=None, on_save=None):
        super().__init__(parent, "📤 Registrar Salida / Alta", 450, 350)
        self.animal_id = animal_id
        self.on_save = on_save
        self.service = AnimalService()
        self._build()

    def _build(self):
        layout = QFormLayout()
        layout.setSpacing(16)

        # Información del paciente
        try:
            animal = self.service.obtener_animal(self.animal_id)
            info = QLabel(
                f"Paciente: <b>{animal.nombre}</b> ({animal.codigo})")
            info.setStyleSheet(
                f"color: {
                    IsaStyles.SECONDARY}; font-size: 14px; padding: 8px; background-color: {
                    IsaStyles.LIGHT_BG}; border-radius: 6px;")
            layout.addRow(info)
        except Exception:
            pass

        # Motivo
        layout.addRow("Motivo de Salida *:")
        self.motivo = QTextEdit()
        self.motivo.setPlaceholderText(
            "Ej: Alta médica, traslado a otra clínica, fallecimiento...")
        self.motivo.setMaximumHeight(100)
        self.motivo.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid {IsaStyles.BORDER};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
            QTextEdit:focus {{
                border-color: {IsaStyles.WARNING};
            }}
        """)
        layout.addRow(self.motivo)

        # Responsable
        layout.addRow("Responsable *:")
        self.responsable = QLineEdit()
        self.responsable.setPlaceholderText(
            "Nombre de quien autoriza la salida")
        style_input(self.responsable)
        layout.addRow(self.responsable)

        # Destino opcional
        layout.addRow("Destino (opcional):")
        self.destino = QLineEdit()
        self.destino.setPlaceholderText(
            "Ej: Casa del propietario, otra clínica...")
        style_input(self.destino)
        layout.addRow(self.destino)

        # Advertencia
        warning = QLabel(
            "⚠️ <b>Advertencia:</b> Esta acción cambiará el estado del paciente a 'Dado de Alta'.")
        warning.setStyleSheet(
            f"color: {
                IsaStyles.WARNING}; background-color: #FEF3C7; padding: 10px; border-radius: 6px; font-size: 11px;")
        warning.setWordWrap(True)
        layout.addRow(warning)

        self.content_layout.addLayout(layout)

        # Botones
        self.btn_guardar.setText("📤 Confirmar Salida")
        style_button(self.btn_guardar, 'primary')
        self.btn_cancelar.setText("❌ Cancelar")
        style_button(self.btn_cancelar, 'ghost')

        self.set_save_callback(self._guardar)

    @ErrorHandler.handle_exception
    def _guardar(self):
        motivo = self.motivo.toPlainText().strip()
        responsable = self.responsable.text().strip()

        if not motivo or not responsable:
            show_warning(
                self,
                "Error",
                "El motivo y el responsable son obligatorios")
            return

        # Confirmación adicional
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "¿Está seguro de registrar la salida de este paciente?<br>"
            "El estado cambiará a <b>'Dado de Alta'</b>.",
            QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.No:
            return

        self.service.registrar_salida(self.animal_id, {
            'motivo': motivo,
            'responsable': responsable,
            'destino': self.destino.text().strip() or None
        })

        QMessageBox.information(
            self, "✅ Éxito", "Salida registrada correctamente")

        if self.on_save:
            self.on_save()
        self.accept()
