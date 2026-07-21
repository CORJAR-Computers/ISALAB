# gui_pyside/views/boton_generar_reportes.py
"""
Ejemplo completo de cómo integrar los reportes en la GUI.
Esto va dentro de tu vista de PySide6, en el callback de un botón.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QMessageBox
)
from PySide6.QtCore import QThread, Signal

# Importar los servicios de reportes
from services.report_laboratorio import ReporteLaboratorioService
from services.report_vacunacion import ReporteVacunacionService
from services.report_historia_clinica import ReporteHistoriaClinicaService
from services.report_cirugia import ReporteCirugiaService


class WorkerGenerarPDF(QThread):
    """Hilo en background para no congelar la GUI mientras genera el PDF."""

    terminado = Signal(bytes, str)     # (pdf_bytes, ruta_str)
    error = Signal(str)

    def __init__(
            self,
            tipo_reporte,
            datos_orm=None,
            datos_manual=None,
            cliente_data=None,
            es_empresa=False):
        super().__init__()
        self.tipo_reporte = tipo_reporte
        self.datos_orm = datos_orm
        self.datos_manual = datos_manual
        self.cliente_data = cliente_data
        self.es_empresa = es_empresa

    def run(self):
        try:
            if self.tipo_reporte == "laboratorio":
                svc = ReporteLaboratorioService()
                resultado = svc.generar_y_guardar(
                    resultado_orm=self.datos_orm,
                    datos_manual=self.datos_manual,
                    cliente_data=self.cliente_data,
                    es_empresa=self.es_empresa,
                    guardar=True,
                    usuario="Dr. Pérez",  # Del usuario logueado
                )
            elif self.tipo_reporte == "vacunacion":
                resultado = generar_reporte_vacunacion(
                    vacunacion_orm=self.datos_orm,
                    datos_manual=self.datos_manual,
                    cliente_data=self.cliente_data,
                    guardar=True,
                )
            elif self.tipo_reporte == "historia_clinica":
                resultado = generar_reporte_historia_clinica(
                    hc_orm=self.datos_orm,
                    datos_manual=self.datos_manual,
                    cliente_data=self.cliente_data,
                    guardar=True,
                )
            elif self.tipo_reporte == "cirugia":
                resultado = generar_reporte_cirugia(
                    cirugia_orm=self.datos_orm,
                    datos_manual=self.datos_manual,
                    cliente_data=self.cliente_data,
                    guardar=True,
                )
            else:
                self.error.emit(
                    f"Tipo de reporte desconocido: {
                        self.tipo_reporte}")
                return

            pdf_bytes, ruta = resultado
            self.terminado.emit(pdf_bytes, str(ruta))

        except Exception as e:
            self.error.emit(f"Error generando reporte: {str(e)}")


class PanelReportes(QWidget):
    """Panel de la GUI para generar reportes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.worker = None

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Selector de tipo
        row_tipo = QHBoxLayout()
        row_tipo.addWidget(QLabel("Tipo de reporte:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems([
            "laboratorio",
            "vacunacion",
            "historia_clinica",
            "cirugia",
        ])
        row_tipo.addWidget(self.combo_tipo)
        layout.addLayout(row_tipo)

        # Check empresa
        row_empresa = QHBoxLayout()
        self.check_empresa = QComboBox()
        self.check_empresa.addItems(["Persona Natural", "Empresa"])
        row_empresa.addWidget(QLabel("Cliente:"))
        row_empresa.addWidget(self.check_empresa)
        layout.addLayout(row_empresa)

        # Botón generar
        self.btn_generar = QPushButton("📄 Generar PDF")
        self.btn_generar.setMinimumHeight(40)
        self.btn_generar.clicked.connect(self.on_generar)
        layout.addWidget(self.btn_generar)

        # Botón generar con datos de prueba
        self.btn_prueba = QPushButton("🧪 Generar PDF de Prueba")
        self.btn_prueba.clicked.connect(self.on_generar_prueba)
        layout.addWidget(self.btn_prueba)

        # Label estado
        self.lbl_estado = QLabel("Listo")
        layout.addWidget(self.lbl_estado)

        layout.addStretch()

    def on_generar(self):
        """Generar reporte desde ORM (cuando tengas los modelos listos)."""
        tipo = self.combo_tipo.currentText()
        es_empresa = self.check_empresa.currentIndex() == 1

        self.lbl_estado.setText("Generando...")
        self.btn_generar.setEnabled(False)

        # Aquí obtendrías el objeto ORM de tu base de datos
        # resultado_orm = session.query(ResultadoLaboratorio).get(id_seleccionado)
        # cliente_data = self._obtener_datos_cliente_desde_gui()

        # Por ahora, usamos datos de prueba
        self._lanzar_worker(tipo, datos_manual=None, es_empresa=es_empresa)

    def on_generar_prueba(self):
        """Generar reporte con datos de prueba para verificar que todo funciona."""
        tipo = self.combo_tipo.currentText()
        es_empresa = self.check_empresa.currentIndex() == 1
        datos = self._obtener_datos_prueba(tipo)
        cliente = self._obtener_cliente_prueba(es_empresa)

        self.lbl_estado.setText("Generando prueba...")
        self.btn_prueba.setEnabled(False)

        self._lanzar_worker(
            tipo,
            datos_manual=datos,
            cliente_data=cliente,
            es_empresa=es_empresa)

    def _lanzar_worker(
            self,
            tipo,
            datos_orm=None,
            datos_manual=None,
            cliente_data=None,
            es_empresa=False):
        self.worker = WorkerGenerarPDF(
            tipo_reporte=tipo,
            datos_orm=datos_orm,
            datos_manual=datos_manual,
            cliente_data=cliente_data,
            es_empresa=es_empresa,
        )
        self.worker.terminado.connect(self._on_pdf_listo)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_pdf_listo(self, pdf_bytes: bytes, ruta: str):
        self.btn_generar.setEnabled(True)
        self.btn_prueba.setEnabled(True)
        self.lbl_estado.setText(f"✅ Generado: {ruta}")
        QMessageBox.information(
            self, "Reporte Generado",
            f"PDF generado exitosamente:\n{ruta}\n\n¿Desea abrirlo?",
            QMessageBox.Open | QMessageBox.Close
        )

    def _on_error(self, mensaje: str):
        self.btn_generar.setEnabled(True)
        self.btn_prueba.setEnabled(True)
        self.lbl_estado.setText("❌ Error")
        QMessageBox.critical(self, "Error", mensaje)

    def _obtener_cliente_prueba(self, es_empresa: bool) -> dict:
        if es_empresa:
            return {
                "razon_social": "GRANJA EL PORVENIR S.A.S.",
                "nit": "900.123.456-8",
                "contacto": "Carlos Méndez",
                "cargo": "Gerente de Producción",
                "telefono": "601-456-7890",
                "email": "produccion@granjaelporvenir.com",
                "direccion": "Km 15 Vía Bogotá - Medellín, Chocontá",
                "nombre_completo": "GRANJA EL PORVENIR S.A.S.",
                "numero_documento": "900.123.456-8",
            }
        return {
            "nombre_completo": "María Fernanda López García",
            "tipo_documento": "CC",
            "numero_documento": "1.023.456.789",
            "telefono": "601-234-5678",
            "celular": "311-234-5678",
            "email": "maria.lopez@email.com",
            "direccion": "Calle 78 No. 15-23, Apt 401",
        }

    def _obtener_datos_prueba(self, tipo: str) -> dict:
        """Datos de prueba completos para cada tipo de reporte."""

        if tipo == "laboratorio":
            return {
                "veterinario_nombre": "Dra. Isabel Ramírez Torres",
                "paciente": {
                    "nombre": "Max",
                    "especie": "Canino",
                    "raza": "Golden Retriever",
                    "sexo": "Macho",
                    "edad_texto": "5 años",
                    "peso": 32.5,
                    "peso_unidad": "kg",
                    "color": "Dorado",
                    "identificacion": "Microchip 985121004512345",
                    "fecha_nacimiento": "15/03/2020",
                },
                "muestra": {
                    "codigo": "M-2024-0456",
                    "tipo": "Sangre venosa",
                    "fecha_toma": "20/01/2025",
                    "hora_toma": "08:30 AM",
                    "fecha_recibo": "20/01/2025",
                    "hora_recibo": "09:15 AM",
                    "estado": "Procesada",
                    "condiciones": "Refrigerada, sin hemólisis",
                },
                "perfil": {
                    "nombre": "Hemograma Completo + Química Sanguínea",
                    "medico_solicita": "Dr. Pedro Martínez",
                    "diagnostico_presuntivo": "Hepatopatía crónica",
                },
                "resultados": [
                    {
                        "nombre": "HEMOGRAMA",
                        "items": [
                            {"nombre": "Hematocrito", "resultado": 45.2, "unidad": "%", "ref_min": 37, "ref_max": 55, "metodo": "Microcentrifugación"},
                            {"nombre": "Hemoglobina", "resultado": 15.1, "unidad": "g/dL", "ref_min": 12, "ref_max": 18, "metodo": "Cianometahemoglobina"},
                            {"nombre": "Glóbulos Rojos", "resultado": 6.8, "unidad": "x10⁶/μL", "ref_min": 5.5, "ref_max": 8.5, "metodo": "Impedancia"},
                            {"nombre": "VGM", "resultado": 66.5, "unidad": "fL", "ref_min": 60, "ref_max": 77, "metodo": "Calculado"},
                            {"nombre": "Leucocitos", "resultado": 18500, "unidad": "/μL", "ref_min": 6000, "ref_max": 17000, "metodo": "Impedancia"},
                            {"nombre": "Plaquetas", "resultado": 85000, "unidad": "/μL", "ref_min": 175000, "ref_max": 500000, "metodo": "Impedancia"},
                        ]
                    },
                    {
                        "nombre": "QUÍMICA SANGUÍNEA",
                        "items": [
                            {"nombre": "Glucosa", "resultado": 95, "unidad": "mg/dL", "ref_min": 74, "ref_max": 143, "metodo": "Enzimático GOD-PAP"},
                            {"nombre": "BUN", "resultado": 18, "unidad": "mg/dL", "ref_min": 7, "ref_max": 27, "metodo": "Ureasa"},
                            {"nombre": "Creatinina", "resultado": 1.2, "unidad": "mg/dL", "ref_min": 0.5, "ref_max": 1.8, "metodo": "Jaffé"},
                            {"nombre": "ALT (GPT)", "resultado": 185, "unidad": "U/L", "ref_min": 10, "ref_max": 125, "metodo": "UV Cinético"},
                            {"nombre": "AST (GOT)", "resultado": 210, "unidad": "U/L", "ref_min": 10, "ref_max": 80, "metodo": "UV Cinético"},
                            {"nombre": "ALP", "resultado": 450, "unidad": "U/L", "ref_min": 23, "ref_max": 212, "metodo": "PNPP"},
                            {"nombre": "GGT", "resultado": 28, "unidad": "U/L", "ref_min": 0, "ref_max": 11, "metodo": "Szász"},
                            {"nombre": "Bilirrubina Total", "resultado": 2.8, "unidad": "mg/dL", "ref_min": 0.1, "ref_max": 0.5, "metodo": "Diazo"},
                            {"nombre": "Proteínas Totales", "resultado": 7.2, "unidad": "g/dL", "ref_min": 5.5, "ref_max": 7.5, "metodo": "Biuret"},
                            {"nombre": "Albúmina", "resultado": 2.8, "unidad": "g/dL", "ref_min": 2.3, "ref_max": 4.0, "metodo": "BCG"},
                            {"nombre": "Colesterol", "resultado": 285, "unidad": "mg/dL", "ref_min": 110, "ref_max": 320, "metodo": "Enzimático"},
                        ]
                    }
                ],
                "observaciones": "Muestra procesada dentro de las 2 horas posteriores a la toma. "
                "Se sugiere complementar con ecografía abdominal y perfil hepático extendido "
                "(amonio, ácidos biliares). Los valores elevados de ALT, AST, ALP y GGT "
                "son compatibles con hepatopatía de origen mixto (hepatocelular y colestásico).",
            }

        elif tipo == "vacunacion":
            return {
                "numero_historia": "HC-2024-0123",
                "veterinario_nombre": "Dra. Isabel Ramírez Torres",
                "paciente": {
                    "nombre": "Luna",
                    "especie": "Felina",
                    "raza": "Persa",
                    "sexo": "Hembra",
                    "edad_texto": "3 meses",
                    "peso": 1.2,
                    "peso_unidad": "kg",
                    "fecha_nacimiento": "20/10/2024",
                    "identificacion": "—",
                },
                "vacunas": [
                    {
                        "nombre": "Vacuna Polivalente Felina (VPRC)",
                        "laboratorio": "Zoetis",
                        "lote": "VPR-2024-A089",
                        "fecha_vencimiento": "15/06/2026",
                        "tipo": "Viva atenuada",
                        "dosis": [
                            {"nombre": "Primovacunación 1ra", "fecha_aplicacion": "20/01/2025", "fecha_proxima": "", "veterinario": "Dra. Isabel Ramírez"},
                            {"nombre": "Refuerzo 2da", "fecha_aplicacion": "", "fecha_proxima": "20/02/2025", "veterinario": ""},
                            {"nombre": "Refuerzo Anual", "fecha_aplicacion": "", "fecha_proxima": "20/01/2026", "veterinario": ""},
                        ]
                    },
                    {
                        "nombre": "Vacuna Antirrábica",
                        "laboratorio": "Boehringer Ingelheim",
                        "lote": "RA-2024-B234",
                        "fecha_vencimiento": "30/09/2027",
                        "tipo": "Inactivada",
                        "dosis": [
                            {"nombre": "Primovacunación", "fecha_aplicacion": "20/01/2025", "fecha_proxima": "", "veterinario": "Dra. Isabel Ramírez"},
                            {"nombre": "Refuerzo Anual", "fecha_aplicacion": "", "fecha_proxima": "20/01/2026", "veterinario": ""},
                        ]
                    }
                ],
                "proxima_vacuna": {
                    "fecha": "20/02/2025",
                    "vacuna": "Vacuna Polivalente Felina (VPRC)",
                    "dosis": "Refuerzo 2da",
                },
                "observaciones": "Paciente presentó leve reacción local post-vacunal (dureza en zona de aplicación) "
                "que se resolvió espontáneamente en 48 horas. Se recomienda observar comportamiento "
                "en la próxima vacunación.",
            }

        elif tipo == "historia_clinica":
            return {
                "numero_historia": "HC-2024-0123",
                "fecha_apertura": "15/11/2024",
                "numero_consulta": "004",
                "total_consultas": 4,
                "veterinario_nombre": "Dra. Isabel Ramírez Torres",
                "veterinario_registro": "MVZ-14582",
                "paciente": {
                    "nombre": "Max",
                    "especie": "Canino",
                    "raza": "Golden Retriever",
                    "sexo": "Macho",
                    "edad_texto": "5 años",
                    "peso": 32.5,
                    "peso_unidad": "kg",
                    "foto_b64": "",
                },
                "motivo_consulta": "Propietario refiere anorexia de 5 días de evolución, vómito bilioso esporádico (2-3 veces/día), letargo progresivo y mucosas ictéricas desde hace 2 días. Paciente con acceso a jardín. No se conoce ingesta de tóxicos.",
                "anamnesis": "Diet: Alimento comercial premium (Royal Canin Golden Retriever Adult). Cambio de dieta hace 3 semanas a marca blanca por problemas de abastecimiento. Vacunación completa (último refuerzo hace 8 meses). Desparasitación interna hace 2 meses (Milbemax). No antecedentes de enfermedades previas. No medicación actual.",
                "signos_vitales": {
                    "temperatura": 39.2,
                    "fc": 110,
                    "fr": 28,
                    "pulso": 110,
                    "peso": 32.5,
                    "tllc": 2.5,
                    "mucosas": "Ictéricas, húmedas",
                    "hidratacion": 8,
                    "glicemia": 88,
                    "spo2": 97,
                },
                "examen_fisico": "Estado general: Depresivo, ambulatorio. Condición corporal: 5/9. Pelaje: Opaco, con descamación leve en dorso.\n\nCabeza: Mucosas orales, conjuntivales y esclerales ictéricas (coloración amarillo intensa). Linfonodos submandibulares: no reactivos.\n\nTórax: Auscultación cardíaca: rítmica, sin soplos. FC 110 lpm. Auscultación pulmonar: campos pulmonares limpios, FR 28 rpm.\n\nAbdomen: Palpación superficial: dolor leve en epigastrio. Palpación profunda: hepatomegalia moderada (borde hepático 3-4 cm por debajo del arco costal). Vesícula biliar no palpable. Intestino: sin alteraciones.\n\nSistema nervioso: Alerta, responisivo. Sin signos neurológicos focales.\n\nPiel y anexos: Ictericia generalizada. No se observan lesiones cutáneas.",
                "diagnosticos": [
                    {"nombre": "Hepatopatía tóxica por ingesta de micotoxinas", "tipo": "Presuntivo", "cie10": "K71.9", "observaciones": "Asociada a cambio reciente de alimento"},
                    {"nombre": "Hepatomegalia", "tipo": "Definitivo", "cie10": "R16.0", "observaciones": "Confirmada por palpación abdominal"},
                    {"nombre": "Ictericia", "tipo": "Definitivo", "cie10": "R17", "observaciones": "Mucosas ictéricas con patrón obstructivo-mixto"},
                ],
                "tratamiento": {
                    "medicamentos": [
                        {"nombre": "S-Adenosilmetionina (SAMe)", "dosis": "20 mg/kg", "via": "PO", "frecuencia": "Cada 24 horas", "duracion": "30 días", "indicacion": "Hepatoprotección y regeneración hepatocelular"},
                        {"nombre": "Silibinina (Marinyl)", "dosis": "5 mg/kg", "via": "PO", "frecuencia": "Cada 12 horas", "duracion": "21 días", "indicacion": "Antioxidante hepático"},
                        {"nombre": "Omeprazol", "dosis": "1 mg/kg", "via": "PO", "frecuencia": "Cada 24 horas", "duracion": "7 días", "indicacion": "Antiulceroso gástrico"},
                        {"nombre": "Metoclopramida", "dosis": "0.3 mg/kg", "via": "SC", "frecuencia": "Cada 8 horas", "duracion": "3 días", "indicacion": "Antiemético"},
                        {"nombre": "Suero Ringer Lactato", "dosis": "30 mL/kg", "via": "IV", "frecuencia": "Cada 24 horas", "duracion": "3 días", "indicacion": "Terapia de fluidos"},
                        {"nombre": "Vitamina K1", "dosis": "0.5 mg/kg", "via": "SC", "frecuencia": "Cada 12 horas", "duracion": "3 dosis", "indicacion": "Profilaxis coagulopatía por hepatopatía"},
                    ],
                    "procedimientos": [
                        {"nombre": "Toma de muestras sanguíneas", "detalle": "Hemograma completo, química sanguínea, coagulograma, ácidos biliares, amonio"},
                    ],
                    "indicaciones": "Dieta hepática comercial (Hepatic de Royal Canin o similar) por mínimo 6 semanas. Restringir proteínas si se observa encefalopatía hepática. No administrar medicamentos hepatotóxicos (acetaminofén, AINEs). Evitar ejercicio intenso por 2 semanas.",
                },
                "pronostico": {
                    "tipo": "Reservado",
                    "observaciones": "Depende de la respuesta al tratamiento en las primeras 72 horas y de los resultados de laboratorio. Favorable si se retira el agente causal.",
                },
                "controles": [
                    {"fecha": "23/01/2025", "motivo": "Reevaluación y revisión de resultados de laboratorio", "observaciones": "Ver respuesta a SAMe y silibinina"},
                    {"fecha": "30/01/2025", "motivo": "Control de hepática y signos vitales", "observaciones": "Repetir perfil hepático si hay mejoría clínica"},
                    {"fecha": "20/02/2025", "motivo": "Control final del tratamiento agudo", "observaciones": "Decidir continuidad de hepatoprotectores"},
                ],
            }

        elif tipo == "cirugia":
            return {
                "tipo_cirugia": "Ovariohisterectomía Electiva",
                "nivel": "Menor",
                "fecha_cirugia": "22/01/2025",
                "hora_inicio": "09:00:00",
                "hora_fin": "10:25:00",
                "duracion": "1h 25m",
                "paciente": {
                    "nombre": "Luna",
                    "especie": "Felina",
                    "raza": "Persa",
                    "sexo": "Hembra",
                    "peso": 3.2,
                    "peso_unidad": "kg",
                },
                "equipo": {
                    "cirujano": "Dra. Isabel Ramírez Torres",
                    "ayudante": "Dr. Carlos Vega",
                    "anestesiologo": "Dr. Juan Pablo Ruiz",
                    "instrumentista": "Tec. Laura Martínez",
                },
                "diagnostico": "Esterilización electiva — Paciente sana para procedimiento",
                "cie10": "Z30.2",
                "procedimiento": "Ovariohisterectomía por abordaje medio ventral. Se realiza incisión de 2 cm a nivel de umbiligo. Se identifica y exterioriza cada cuerno uterino con sus respectivos ovarios. Se ligan arterias y venas ováricas con sutura absorbible 3-0. Se continua con ligadura del cuerpo uterino a nivel del cérvix con sutura absorbible 2-0. Se verifica hemostasia. Se cierra línea alba con sutura absorbible 2-0 en patrón simple continuo. Se afronta subcutis con sutura absorbible 3-0. Se cierra piel con sutura nylon 4-0 en patrón intradérmico.",
                "fases": [
                    {"nombre": "Preparación Preoperatoria", "descripcion": "Ayuno 12h, examen físico preanestésico, colocación de vía venosa cephalica derecha, administración de premedicación (Acepromazina 0.02 mg/kg + Tramadol 2 mg/kg IM). Monitoreo base de signos vitales.", "hora": "08:30"},
                    {"nombre": "Inducción Anestésica", "descripcion": "Inducción con Ketamina 5 mg/kg + Diazepam 0.5 mg/kg IV. Intubación endotraqueal con tubo #3.5. Conexión a circuito de Mapleson D con oxígeno a 1L/min. Mantenimiento con Isoflurano al 1.5-2%.", "hora": "09:00"},
                    {"nombre": "Preparación del Campo Quirúrgico", "descripcion": "Tricotomía amplia de región ventral (desde xifoides hasta pubis). Desinfección con clorhexidina al 2% tres veces. Colocación de campos quirúrgicos estériles.", "hora": "09:08"},
                    {"nombre": "Procedimiento Quirúrgico", "descripcion": "Abordaje medio ventral. Ovariohisterectomía bilateral completa. Ligadura triple de arterias ováricas y cuerpo uterino. Hemostasia verificada.", "hora": "09:15"},
                    {"nombre": "Cierre de Cavidad", "descripcion": "Cierre por planos: línea alba (Vicryl 2-0), subcutis (Vicryl 3-0), piel intradérmico (Nylon 4-0). Aplicación de spray antibiótico local.", "hora": "10:10"},
                    {"nombre": "Recuperación Anestésica", "descripcion": "Suspensión de isoflurano. Extubación espontánea a los 8 minutos. Colocación en jaula de recuperación con fuente de calor. Monitoreo continuo.", "hora": "10:20"},
                    {"nombre": "Finalización", "descripcion": "Paciente despierta, en decúbito esternal. Signos vitales estables. Se coloca collar isabelino.", "hora": "10:25"},
                ],
                "anestesia": {
                    "tipo": "General inhalatoria (Isoflurano)",
                    "induccion": "Ketamina 5 mg/kg + Diazepam 0.5 mg/kg IV",
                    "mantenimiento": "Isoflurano 1.5-2% en O₂ a 1L/min",
                    "medicamentos": [
                        {"nombre": "Acepromazina", "dosis": "0.02 mg/kg", "via": "IM"},
                        {"nombre": "Tramadol", "dosis": "2 mg/kg", "via": "IM"},
                        {"nombre": "Ketamina", "dosis": "5 mg/kg", "via": "IV"},
                        {"nombre": "Diazepam", "dosis": "0.5 mg/kg", "via": "IV"},
                        {"nombre": "Meloxicam", "dosis": "0.1 mg/kg", "via": "SC"},
                        {"nombre": "Cefazolina", "dosis": "25 mg/kg", "via": "IV"},
                    ],
                    "signos_monitoreo": [
                        {"hora": "08:30", "fc": 180, "fr": 32, "spo2": 98, "temperatura": 38.5, "pulso": 180, "reflejos": "Presentes", "estado_anestesico": "Consciente"},
                        {"hora": "09:00", "fc": 140, "fr": 20, "spo2": 99, "temperatura": 38.3, "pulso": 140, "reflejos": "Ausentes", "estado_anestesico": "Plano III-2"},
                        {"hora": "09:15", "fc": 135, "fr": 18, "spo2": 99, "temperatura": 38.1, "pulso": 135, "reflejos": "Ausentes", "estado_anestesico": "Plano III-3"},
                        {"hora": "09:45", "fc": 130, "fr": 18, "spo2": 99, "temperatura": 37.9, "pulso": 130, "reflejos": "Ausentes", "estado_anestesico": "Plano III-2"},
                        {"hora": "10:10", "fc": 140, "fr": 20, "spo2": 98, "temperatura": 37.8, "pulso": 140, "reflejos": "Palpebral presente", "estado_anestesico": "Plano II"},
                        {"hora": "10:20", "fc": 160, "fr": 24, "spo2": 98, "temperatura": 37.6, "pulso": 160, "reflejos": "Presentes", "estado_anestesico": "Despertando"},
                        {"hora": "10:25", "fc": 170, "fr": 28, "spo2": 99, "temperatura": 37.5, "pulso": 170, "reflejos": "Presentes", "estado_anestesico": "Consciente"},
                    ]
                },
                "hallazgos": "Utero y ovarios sin alteraciones macroscópicas. Ovarios de tamaño y consistencia normales. No se evidencian quistes, neoplasias ni alteraciones en estructuras reproductivas. Línea alba íntegra. No se observan adherencias ni líquido libre en cavidad abdominal.",
                "complicaciones": "",
                "muestras": None,
                "material": [
                    {"nombre": "Bisturí", "detalle": "Hoja #15 y #10"},
                    {"nombre": "Pinzas hemostáticas", "detalle": "4 Kelly, 2 Kocher, 2 Crile"},
                    {"nombre": "Portaagujas", "detalle": "1 Mayo-Hegar"},
                    {"nombre": "Tijeras", "detalle": "1 Mayo, 1 Metzenbaum, 1 iris"},
                    {"nombre": "Separadores", "detalle": "1 Farabeuf pequeño"},
                    {"nombre": "Suturas", "detalle": "Vicryl 2-0, Vicryl 3-0, Nylon 4-0"},
                ],
                "conteo_instrumental": [
                    {"nombre": "Bisturí #15", "antes": 1, "despues": 1, "diferencia": 0, "correcto": True},
                    {"nombre": "Bisturí #10", "antes": 1, "despues": 1, "diferencia": 0, "correcto": True},
                    {"nombre": "Pinzas Kelly", "antes": 4, "despues": 4, "diferencia": 0, "correcto": True},
                    {"nombre": "Pinzas Kocher", "antes": 2, "despues": 2, "diferencia": 0, "correcto": True},
                    {"nombre": "Agujas", "antes": 6, "despues": 6, "diferencia": 0, "correcto": True},
                    {"nombre": "Gasas (paquetes)", "antes": 5, "despues": 5, "diferencia": 0, "correcto": True},
                ],
                "postoperatorio": {
                    "estado_despertar": "Decúbito esternal, alerta, responde a estímulos",
                    "temperatura": 37.5,
                    "fc": 170,
                    "escala_dolor": "1 ( leve)",
                    "observaciones": "Herida quirúrgica limpia, sin sangrado. Se administra Meloxicam 0.1 mg/kg SC y Tramadol 2 mg/kg SC como analgesia postoperatoria.",
                },
                "indicaciones": {
                    "medicamentos": [
                        {"nombre": "Meloxicam", "dosis": "0.1 mg/kg", "via": "PO", "frecuencia": "Cada 24 horas", "duracion": "5 días"},
                        {"nombre": "Tramadol", "dosis": "2 mg/kg", "via": "PO", "frecuencia": "Cada 8 horas", "duracion": "3 días"},
                        {"nombre": "Cefazolina", "dosis": "25 mg/kg", "via": "PO", "frecuencia": "Cada 12 horas", "duracion": "7 días"},
                    ],
                    "cuidados": "Usar collar isabelino por 10 días. No bañar hasta retiro de puntos. Dieta blanda las primeras 48 horas. Restringir actividad física por 10 días. Observar la herida quirúrgica diariamente (enrojecimiento, secreción, dehiscencia). No permitir que la paciente lama la herida.",
                    "fecha_revision": "29/01/2025",
                    "fecha_retiro_puntos": "01/02/2025",
                },
                "observaciones": "Procedimiento realizado sin complicaciones. Se aplicó técnica aséptica en todo momento. Tiempo quirúrgico dentro de los parámetros normales para la especie y procedimiento. Paciente toleró satisfactoriamente el protocolo anestésico.",
            }

        return {}
