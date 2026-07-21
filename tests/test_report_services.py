# tests/test_report_services.py
"""
Tests unitarios comprehensivos para todos los services de reportes.
Cubre: ReporteCirugiaService, ReporteConsultaService, ReporteFormulaMedicaService,
       ReporteConsentimientoService, ReporteHistoriaClinicaService,
       ReporteLaboratorioService, ReporteReciboService, ReporteVacunacionService,
       ReportService, PDFService
"""

import json
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import pytest

from services.report_cirugia import ReporteCirugiaService
from services.report_consulta import ReporteConsultaService
from services.report_formula_medica import ReporteFormulaMedicaService
from services.report_consentimiento import ReporteConsentimientoService
from services.report_historia_clinica import ReporteHistoriaClinicaService
from services.report_laboratorio import ReporteLaboratorioService
from services.report_recibo import ReporteReciboService
from services.report_vacunacion import ReporteVacunacionService
from services.report_service import ReportService
from services.pdf_service import PDFService


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_cirugia():
    """Mock de un objeto Cirugia."""
    cirugia = Mock()
    cirugia.id = 1
    cirugia.animal_id = 10
    cirugia.historia_id = 5
    cirugia.fecha = "2024-01-15"
    cirugia.protocolo_anestesico = "Acepromazina 0.02 mg/kg IM"
    cirugia.diagnostico = "Ovariohisterectomía"
    cirugia.estado = "Completada"
    return cirugia


@pytest.fixture
def mock_animal():
    """Mock de un objeto Animal."""
    animal = Mock()
    animal.id = 10
    animal.nombre = "Luna"
    animal.especie = "Canino"
    animal.raza = "Labrador"
    animal.sexo = "Hembra"
    animal.fecha_ingreso = datetime(2024, 1, 10)
    animal.fecha_nacimiento = datetime(2023, 1, 15)
    animal.peso = 25.5
    animal.propietario_nombre = "María García"
    animal.propietario_telefono = "555-1234"
    animal.propietario_direccion = "Calle Principal 123"
    return animal


@pytest.fixture
def mock_historia():
    """Mock de un objeto HistoriaClinica."""
    historia = Mock()
    historia.id = 5
    historia.animal_id = 10
    historia.fecha = "2024-01-15"
    historia.diagnostico = "Ovariohisterectomía programada"
    historia.pronostico = "Bueno"
    historia.tratamiento = "Cirugía electiva"
    historia.anamnesis = "Paciente femenina, 1 año, sin antecedentes"
    historia.examen_fisico = "Buen estado general, mucosas rosadas"
    historia.diagnostico_diferencial = ""
    historia.veterinario = "Dr. Carlos López"
    historia.temperatura = 38.5
    historia.frecuencia_cardiaca = 120
    historia.frecuencia_respiratoria = 20
    historia.peso_consulta = 25.5
    historia.recepcion_codigo = "REC-2024-001"
    return historia


@pytest.fixture
def mock_consulta():
    """Mock de un objeto Consulta."""
    consulta = Mock()
    consulta.id = 1
    consulta.animal_id = 10
    consulta.fecha = "2024-01-20"
    consulta.codigo = "CON-2024-001"
    consulta.motivo = "Control postquirúrgico"
    consulta.diagnostico = "Evolución favorable"
    consulta.evolucion = "Paciente evoluciona favorablemente"
    consulta.examen_fisico = "Herida quirúrgica limpia"
    consulta.tratamiento = "Antibiótico por 5 días"
    consulta.medicamentos = "Amoxicilina 250mg"
    consulta.veterinario = "Dr. Carlos López"
    consulta.proxima_consulta = datetime(2024, 1, 27)
    return consulta


@pytest.fixture
def mock_vacunacion():
    """Mock de un objeto Vacunacion."""
    vacunacion = Mock()
    vacunacion.id = 1
    vacunacion.animal_id = 10
    vacunacion.fecha_aplicacion = datetime(2024, 1, 15)
    vacunacion.fecha_proxima = datetime(2024, 7, 15)
    vacunacion.producto = "Vacuna Triple Canina"
    vacunacion.tipo = "Vacuna"
    vacunacion.via = "SC"
    vacunacion.lote = "LOT-2024-001"
    vacunacion.veterinario = "Dr. Carlos López"
    vacunacion.dosis = "1 ml"
    return vacunacion


@pytest.fixture
def mock_muestra():
    """Mock de un objeto Muestra."""
    muestra = Mock()
    muestra.id = 1
    muestra.animal_id = 10
    muestra.codigo = "MUE-2024-001"
    muestra.tipo_analisis = "Biometría Hemática"
    muestra.fecha_recoleccion = datetime(2024, 1, 15)
    muestra.fecha_entrega = datetime(2024, 1, 16)
    muestra.estado = "Completado"
    muestra.es_urgente = False
    muestra.tecnico = "Tech. Ana Martínez"
    muestra.veterinario_ref = "Dr. Carlos López"
    muestra.resultado = json.dumps([
        {"item": "Hematies", "resultado": "6.5", "unidades": "mill/µL", "ref_texto": "5.5 - 8.5", "seccion": "HEMATOLOGÍA"},
        {"item": "Hemoglobina", "resultado": "14.2", "unidades": "g/dL", "ref_texto": "12.0 - 18.0", "seccion": "HEMATOLOGÍA"}
    ])
    muestra.valor_ref = "5.5 - 8.5"
    muestra.observaciones = "Muestra en buenas condiciones"
    return muestra


@pytest.fixture
def mock_formula_data():
    """Mock de datos de fórmula médica."""
    return {
        "fecha": "2024-01-20",
        "veterinario": "Dr. Carlos López",
        "paciente_nombre": "Luna",
        "paciente_especie": "Canino",
        "diagnostico": "Infección bacteriana",
        "medicamentos": [
            {"nombre": "Amoxicilina", "dosis": "250mg", "frecuencia": "Cada 8 horas", "duracion": "7 días"}
        ]
    }


@pytest.fixture
def mock_consentimiento_data():
    """Mock de datos de consentimiento informado."""
    return {
        "fecha": "2024-01-20",
        "paciente_nombre": "Luna",
        "propietario_nombre": "María García",
        "propietario_id": "12345678-9",
        "procedimiento": "Ovariohisterectomía",
        "riesgos": "Sangrado, infección, reacción anestésica",
        "firma_paciente": True,
        "firma_veterinario": True
    }


@pytest.fixture
def mock_recibo_data():
    """Mock de datos de recibo de pago."""
    return {
        "fecha": "2024-01-20",
        "recibo_numero": "REC-2024-001",
        "cliente_nombre": "María García",
        "paciente_nombre": "Luna",
        "concepto": "Consulta + Cirugía",
        "monto": 1500.00,
        "metodo_pago": "Efectivo",
        "veterinario": "Dr. Carlos López"
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tests para ReporteCirugiaService
# ─────────────────────────────────────────────────────────────────────────────

class TestReporteCirugiaService:
    """Tests para el servicio de reportes de cirugía."""

    @patch('services.report_cirugia.imagen_a_base64', return_value='base64data')
    @patch('services.report_cirugia.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_cirugia.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_cirugia.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_cirugia.formatear_fecha', return_value='15/01/2024')
    @patch('services.report_cirugia.generar_reporte', return_value=b'%PDF-1.4')
    @patch('services.report_cirugia.HistoriaClinicaRepository')
    @patch('services.report_cirugia.AnimalRepository')
    @patch('services.report_cirugia.CirugiaRepository')
    def test_generar_pdf_exitoso(
        self, mock_cirugia_repo, mock_animal_repo, mock_historia_repo,
        mock_generar_reporte, mock_formatear_fecha, mock_gen_codigo,
        mock_gen_barras, mock_gen_qr, mock_imagen, mock_cirugia, mock_animal
    ):
        """Test: generar_pdf retorna bytes del PDF correctamente."""
        mock_cirugia_repo.return_value.get_by_id.return_value = mock_cirugia
        mock_animal_repo.return_value.get_by_id.return_value = mock_animal
        mock_historia_repo.return_value.get_by_id.return_value = None

        service = ReporteCirugiaService()
        resultado = service.generar_pdf(1)

        assert resultado == b'%PDF-1.4'
        mock_generar_reporte.assert_called_once()

    @patch('services.report_cirugia.imagen_a_base64', return_value='base64data')
    @patch('services.report_cirugia.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_cirugia.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_cirugia.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_cirugia.formatear_fecha', return_value='15/01/2024')
    @patch('services.report_cirugia.generar_por_tipo', return_value='/path/to/file.pdf')
    @patch('services.report_cirugia.HistoriaClinicaRepository')
    @patch('services.report_cirugia.AnimalRepository')
    @patch('services.report_cirugia.CirugiaRepository')
    def test_generar_y_guardar(
        self, mock_cirugia_repo, mock_animal_repo, mock_historia_repo,
        mock_generar_por_tipo, mock_formatear_fecha, mock_gen_codigo,
        mock_gen_barras, mock_gen_qr, mock_imagen, mock_cirugia, mock_animal
    ):
        """Test: generar_y_guardar guarda el PDF en disco."""
        mock_cirugia_repo.return_value.get_by_id.return_value = mock_cirugia
        mock_animal_repo.return_value.get_by_id.return_value = mock_animal
        mock_historia_repo.return_value.get_by_id.return_value = None

        service = ReporteCirugiaService()
        resultado = service.generar_y_guardar(1, '/path/to/file.pdf')

        assert resultado == '/path/to/file.pdf'

    def test_parsear_protocolo_json_valido(self):
        """Test: _parsear_protocolo parsea JSON válido correctamente."""
        protocolo = json.dumps({
            "preanestesia": "Acepromazina 0.02 mg/kg IM",
            "induccion": "Ketamina 5 mg/kg IV",
            "mantenimiento": "Isofluorano 1.5%",
            "monitoreo": "FC, FR, SpO2"
        })

        service = ReporteCirugiaService()
        resultado = service._parsear_protocolo(protocolo)

        assert resultado is not None
        assert resultado["preanestesia"] == "Acepromazina 0.02 mg/kg IM"
        assert resultado["induccion"] == "Ketamina 5 mg/kg IV"

    def test_parsear_protocolo_texto_plano(self):
        """Test: _parsear_protocolo retorna None para texto plano."""
        protocolo = "Acepromazina 0.02 mg/kg IM - Ketamina 5 mg/kg IV"

        service = ReporteCirugiaService()
        resultado = service._parsear_protocolo(protocolo)

        assert resultado is None

    def test_parsear_protocolo_none(self):
        """Test: _parsear_protocolo retorna None para None."""
        service = ReporteCirugiaService()
        resultado = service._parsear_protocolo(None)

        assert resultado is None

    def test_parsear_protocolo_json_invalido(self):
        """Test: _parsear_protocolo retorna None para JSON inválido."""
        protocolo = "esto no es json"

        service = ReporteCirugiaService()
        resultado = service._parsear_protocolo(protocolo)

        assert resultado is None

    def test_pronostico_css_bueno(self):
        """Test: _pronostico_css retorna 'bueno' para pronóstico favorable."""
        assert ReporteCirugiaService._pronostico_css("Bueno") == "bueno"
        assert ReporteCirugiaService._pronostico_css("Favorable") == "bueno"
        assert ReporteCirugiaService._pronostico_css("BUENO") == "bueno"

    def test_pronostico_css_grave(self):
        """Test: _pronostico_css retorna 'grave' para pronóstico grave."""
        assert ReporteCirugiaService._pronostico_css("Grave") == "grave"
        assert ReporteCirugiaService._pronostico_css("Desfavorable") == "grave"
        assert ReporteCirugiaService._pronostico_css("Fatal") == "grave"

    def test_pronostico_css_reservado(self):
        """Test: _pronostico_css retorna 'reservado' para pronóstico reservado."""
        assert ReporteCirugiaService._pronostico_css("Reservado") == "reservado"
        assert ReporteCirugiaService._pronostico_css("Otro") == "reservado"

    def test_pronostico_css_none(self):
        """Test: _pronostico_css retorna 'reservado' para None."""
        assert ReporteCirugiaService._pronostico_css(None) == "reservado"

    def test_merge_datos_adicionales_con_historia(self):
        """Test: _merge_datos_adicionales usa datos de historia clínica."""
        service = ReporteCirugiaService()
        historia = Mock()
        historia.diagnostico = "Dx de historia"
        historia.pronostico = "Bueno"
        historia.tratamiento = "Tratamiento de historia"

        resultado = service._merge_datos_adicionales(None, historia)

        assert resultado["diagnostico_preoperatorio"] == "Dx de historia"
        assert resultado["pronostico"] == "Bueno"
        assert resultado["observaciones_pronostico"] == "Tratamiento de historia"

    def test_merge_datos_adicionales_con_extras(self):
        """Test: _merge_datos_adicionales sobrescribe con datos extras."""
        service = ReporteCirugiaService()
        extras = {
            "diagnostico_preoperatorio": "Dx de caller",
            "pronostico": "Grave"
        }

        resultado = service._merge_datos_adicionales(extras, None)

        assert resultado["diagnostico_preoperatorio"] == "Dx de caller"
        assert resultado["pronostico"] == "Grave"


# ─────────────────────────────────────────────────────────────────────────────
# Tests para ReporteConsultaService
# ─────────────────────────────────────────────────────────────────────────────

class TestReporteConsultaService:
    """Tests para el servicio de reportes de consulta."""

    @patch('services.report_consulta.imagen_a_base64', return_value='base64data')
    @patch('services.report_consulta.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_consulta.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_consulta.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_consulta.formatear_fecha', return_value='20/01/2024')
    @patch('services.report_consulta.calcular_edad', return_value='1 año')
    @patch('services.report_consulta.generar_reporte', return_value=b'%PDF-1.4')
    @patch('services.report_consulta.AnimalRepository')
    def test_generar_pdf_exitoso(
        self, mock_animal_repo, mock_generar_reporte, mock_calc_edad,
        mock_formatear_fecha, mock_gen_codigo, mock_gen_barras, mock_gen_qr,
        mock_imagen, mock_consulta, mock_animal
    ):
        """Test: generar_pdf retorna bytes del PDF correctamente."""
        mock_animal_repo.return_value.get_by_id.return_value = mock_animal

        service = ReporteConsultaService()
        resultado = service.generar_pdf(mock_consulta)

        assert resultado == b'%PDF-1.4'

    @patch('services.report_consulta.imagen_a_base64', return_value='base64data')
    @patch('services.report_consulta.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_consulta.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_consulta.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_consulta.formatear_fecha', return_value='20/01/2024')
    @patch('services.report_consulta.calcular_edad', return_value='1 año')
    @patch('services.report_consulta.generar_por_tipo', return_value='/path/to/file.pdf')
    @patch('services.report_consulta.ConsultaRepository')
    @patch('services.report_consulta.AnimalRepository')
    def test_generar_y_guardar(
        self, mock_animal_repo, mock_consulta_repo, mock_generar_por_tipo,
        mock_calc_edad, mock_formatear_fecha, mock_gen_codigo,
        mock_gen_barras, mock_gen_qr, mock_imagen, mock_animal
    ):
        """Test: generar_y_guardar guarda el PDF en disco."""
        mock_consulta_repo.return_value.get_by_id.return_value = Mock()
        mock_animal_repo.return_value.get_by_id.return_value = mock_animal

        service = ReporteConsultaService()
        resultado = service.generar_y_guardar(1, '/path/to/file.pdf')

        assert resultado == '/path/to/file.pdf'

    @patch('services.report_consulta.imagen_a_base64', return_value='base64data')
    @patch('services.report_consulta.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_consulta.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_consulta.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_consulta.formatear_fecha', return_value='20/01/2024')
    @patch('services.report_consulta.calcular_edad', return_value='1 año')
    @patch('services.report_consulta.AnimalRepository')
    def test_construir_contexto(
        self, mock_animal_repo, mock_calc_edad, mock_formatear_fecha,
        mock_gen_codigo, mock_gen_barras, mock_gen_qr, mock_imagen,
        mock_consulta, mock_animal
    ):
        """Test: _construir_contexto retorna contexto completo."""
        mock_animal_repo.return_value.get_by_id.return_value = mock_animal

        service = ReporteConsultaService()
        contexto = service._construir_contexto(mock_consulta)

        assert "lab" in contexto
        assert "consulta" in contexto
        assert "animal" in contexto
        assert "codigo_verificacion" in contexto
        assert "firma_base64" in contexto


# ─────────────────────────────────────────────────────────────────────────────
# Tests para ReporteFormulaMedicaService
# ─────────────────────────────────────────────────────────────────────────────

class TestReporteFormulaMedicaService:
    """Tests para el servicio de reportes de fórmula médica."""

    @patch('services.report_formula_medica.imagen_a_base64', return_value='base64data')
    @patch('services.report_formula_medica.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_formula_medica.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_formula_medica.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_formula_medica.formatear_fecha', return_value='20/01/2024')
    @patch('services.report_formula_medica.generar_reporte', return_value=b'%PDF-1.4')
    def test_generar_pdf_exitoso(
        self, mock_generar_reporte, mock_formatear_fecha, mock_gen_codigo,
        mock_gen_barras, mock_gen_qr, mock_imagen, mock_formula_data
    ):
        """Test: generar_pdf retorna bytes del PDF correctamente."""
        service = ReporteFormulaMedicaService()
        resultado = service.generar_pdf(mock_formula_data)

        assert resultado == b'%PDF-1.4'

    @patch('services.report_formula_medica.imagen_a_base64', return_value='base64data')
    @patch('services.report_formula_medica.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_formula_medica.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_formula_medica.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_formula_medica.formatear_fecha', return_value='20/01/2024')
    @patch('services.report_formula_medica.generar_por_tipo', return_value='/path/to/file.pdf')
    def test_generar_y_guardar(
        self, mock_generar_por_tipo, mock_formatear_fecha, mock_gen_codigo,
        mock_gen_barras, mock_gen_qr, mock_imagen, mock_formula_data
    ):
        """Test: generar_y_guardar guarda el PDF en disco."""
        service = ReporteFormulaMedicaService()
        resultado = service.generar_y_guardar(mock_formula_data, '/path/to/file.pdf')

        assert resultado == '/path/to/file.pdf'

    @patch('services.report_formula_medica.imagen_a_base64', return_value='base64data')
    @patch('services.report_formula_medica.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_formula_medica.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_formula_medica.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_formula_medica.formatear_fecha', return_value='20/01/2024')
    def test_construir_contexto(
        self, mock_formatear_fecha, mock_gen_codigo,
        mock_gen_barras, mock_gen_qr, mock_imagen, mock_formula_data
    ):
        """Test: _construir_contexto retorna contexto completo."""
        service = ReporteFormulaMedicaService()
        contexto = service._construir_contexto(mock_formula_data)

        assert "lab" in contexto
        assert "formula" in contexto
        assert "codigo_verificacion" in contexto
        assert contexto["veterinario_nombre"] == "Dr. Carlos López"


# ─────────────────────────────────────────────────────────────────────────────
# Tests para ReporteConsentimientoService
# ─────────────────────────────────────────────────────────────────────────────

class TestReporteConsentimientoService:
    """Tests para el servicio de reportes de consentimiento informado."""

    @patch('services.report_consentimiento.imagen_a_base64', return_value='base64data')
    @patch('services.report_consentimiento.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_consentimiento.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_consentimiento.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_consentimiento.formatear_fecha', return_value='20/01/2024')
    @patch('services.report_consentimiento.generar_reporte', return_value=b'%PDF-1.4')
    def test_generar_pdf_exitoso(
        self, mock_generar_reporte, mock_formatear_fecha, mock_gen_codigo,
        mock_gen_barras, mock_gen_qr, mock_imagen, mock_consentimiento_data
    ):
        """Test: generar_pdf retorna bytes del PDF correctamente."""
        service = ReporteConsentimientoService()
        resultado = service.generar_pdf(mock_consentimiento_data)

        assert resultado == b'%PDF-1.4'

    @patch('services.report_consentimiento.imagen_a_base64', return_value='base64data')
    @patch('services.report_consentimiento.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_consentimiento.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_consentimiento.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_consentimiento.formatear_fecha', return_value='20/01/2024')
    @patch('services.report_consentimiento.generar_por_tipo', return_value='/path/to/file.pdf')
    def test_generar_y_guardar(
        self, mock_generar_por_tipo, mock_formatear_fecha, mock_gen_codigo,
        mock_gen_barras, mock_gen_qr, mock_imagen, mock_consentimiento_data
    ):
        """Test: generar_y_guardar guarda el PDF en disco."""
        service = ReporteConsentimientoService()
        resultado = service.generar_y_guardar(
            mock_consentimiento_data, '/path/to/file.pdf')

        assert resultado == '/path/to/file.pdf'

    @patch('services.report_consentimiento.imagen_a_base64', return_value='base64data')
    @patch('services.report_consentimiento.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_consentimiento.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_consentimiento.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_consentimiento.formatear_fecha', return_value='20/01/2024')
    def test_construir_contexto_incluye_colores(
        self, mock_formatear_fecha, mock_gen_codigo,
        mock_gen_barras, mock_gen_qr, mock_imagen, mock_consentimiento_data
    ):
        """Test: _construir_contexto incluye colores y tipografía."""
        service = ReporteConsentimientoService()
        contexto = service._construir_contexto(mock_consentimiento_data)

        assert "colores" in contexto
        assert "tipografia" in contexto
        assert "config" in contexto
        assert "margenes" in contexto
        assert "metadatos" in contexto

    @patch('services.report_consentimiento.imagen_a_base64', return_value='base64data')
    @patch('services.report_consentimiento.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_consentimiento.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_consentimiento.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_consentimiento.formatear_fecha', return_value='20/01/2024')
    def test_construir_contexto_logo_isalab(
        self, mock_formatear_fecha, mock_gen_codigo,
        mock_gen_barras, mock_gen_qr, mock_imagen, mock_consentimiento_data
    ):
        """Test: _construir_contexto incluye logo de ISALAB."""
        service = ReporteConsentimientoService()
        contexto = service._construir_contexto(mock_consentimiento_data)

        assert "logo_isalab" in contexto


# ─────────────────────────────────────────────────────────────────────────────
# Tests para ReporteHistoriaClinicaService
# ─────────────────────────────────────────────────────────────────────────────

class TestReporteHistoriaClinicaService:
    """Tests para el servicio de reportes de historia clínica."""

    @patch('services.report_historia_clinica.imagen_a_base64', return_value='base64data')
    @patch('services.report_historia_clinica.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_historia_clinica.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_historia_clinica.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_historia_clinica.formatear_fecha', return_value='15/01/2024')
    @patch('services.report_historia_clinica.calcular_edad', return_value='1 año')
    @patch('services.report_historia_clinica.generar_reporte', return_value=b'%PDF-1.4')
    @patch('services.report_historia_clinica.VacunacionRepository')
    @patch('services.report_historia_clinica.ConsultaRepository')
    @patch('services.report_historia_clinica.AnimalRepository')
    @patch('services.report_historia_clinica.HistoriaClinicaRepository')
    def test_generar_pdf_exitoso(
        self, mock_historia_repo, mock_animal_repo, mock_consulta_repo,
        mock_vacuna_repo, mock_generar_reporte, mock_calc_edad,
        mock_formatear_fecha, mock_gen_codigo, mock_gen_barras, mock_gen_qr,
        mock_imagen, mock_historia, mock_animal
    ):
        """Test: generar_pdf retorna bytes del PDF correctamente."""
        mock_historia_repo.return_value.get_by_id.return_value = mock_historia
        mock_animal_repo.return_value.get_by_id.return_value = mock_animal
        mock_consulta_repo.return_value.get_by_animal.return_value = []
        mock_vacuna_repo.return_value.get_by_animal.return_value = []

        service = ReporteHistoriaClinicaService()
        resultado = service.generar_pdf(5)

        assert resultado == b'%PDF-1.4'

    @patch('services.report_historia_clinica.imagen_a_base64', return_value='base64data')
    @patch('services.report_historia_clinica.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_historia_clinica.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_historia_clinica.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_historia_clinica.formatear_fecha', return_value='15/01/2024')
    @patch('services.report_historia_clinica.calcular_edad', return_value='1 año')
    @patch('services.report_historia_clinica.generar_reporte', return_value=b'%PDF-1.4')
    @patch('services.report_historia_clinica.VacunacionRepository')
    @patch('services.report_historia_clinica.ConsultaRepository')
    @patch('services.report_historia_clinica.AnimalRepository')
    @patch('services.report_historia_clinica.HistoriaClinicaRepository')
    def test_generar_pdf_con_consultas_y_vacunas(
        self, mock_historia_repo, mock_animal_repo, mock_consulta_repo,
        mock_vacuna_repo, mock_generar_reporte, mock_calc_edad,
        mock_formatear_fecha, mock_gen_codigo, mock_gen_barras, mock_gen_qr,
        mock_imagen, mock_historia, mock_animal, mock_consulta, mock_vacunacion
    ):
        """Test: generar_pdf incluye consultas y vacunas."""
        mock_historia_repo.return_value.get_by_id.return_value = mock_historia
        mock_animal_repo.return_value.get_by_id.return_value = mock_animal
        mock_consulta_repo.return_value.get_by_animal.return_value = [mock_consulta]
        mock_vacuna_repo.return_value.get_by_animal.return_value = [mock_vacunacion]

        service = ReporteHistoriaClinicaService()
        resultado = service.generar_pdf(5, incluir_consultas=True, incluir_vacunas=True)

        assert resultado == b'%PDF-1.4'

    def test_formatear_signos(self):
        """Test: _formatear_signos formatea signos vitales correctamente."""
        historia = Mock()
        historia.temperatura = 38.5
        historia.frecuencia_cardiaca = 120
        historia.frecuencia_respiratoria = 20
        historia.peso_consulta = 25.5

        resultado = ReporteHistoriaClinicaService._formatear_signos(historia)

        assert resultado["temperatura"] == "38.5 °C"
        assert resultado["fc"] == "120 lpm"
        assert resultado["fr"] == "20 rpm"
        assert resultado["peso"] == "25.5 kg"

    def test_formatear_signos_none(self):
        """Test: _formatear_signos muestra '—' para valores None."""
        historia = Mock()
        historia.temperatura = None
        historia.frecuencia_cardiaca = None
        historia.frecuencia_respiratoria = None
        historia.peso_consulta = None

        resultado = ReporteHistoriaClinicaService._formatear_signos(historia)

        assert resultado["temperatura"] == "—"
        assert resultado["fc"] == "—"
        assert resultado["fr"] == "—"
        assert resultado["peso"] == "—"

    def test_badge_pronostico_bueno(self):
        """Test: _badge_pronostico retorna badge para pronóstico bueno."""
        resultado = ReporteHistoriaClinicaService._badge_pronostico("Bueno")
        assert resultado["texto"] == "Bueno"
        assert resultado["css"] == "pronostico-bueno"

    def test_badge_pronostico_grave(self):
        """Test: _badge_pronostico retorna badge para pronóstico grave."""
        resultado = ReporteHistoriaClinicaService._badge_pronostico("Grave")
        assert resultado["texto"] == "Grave"
        assert resultado["css"] == "pronostico-grave"

    def test_badge_pronostico_none(self):
        """Test: _badge_pronostico retorna badge para None."""
        resultado = ReporteHistoriaClinicaService._badge_pronostico(None)
        assert resultado["texto"] == "No definido"
        assert resultado["css"] == "pronostico-sin"

    def test_formatear_consulta(self):
        """Test: _formatear_consulta retorna dict formateado."""
        consulta = Mock()
        consulta.codigo = "CON-001"
        consulta.fecha = datetime(2024, 1, 20)
        consulta.motivo = "Control"
        consulta.evolucion = "Favorable"
        consulta.examen_fisico = "Normal"
        consulta.tratamiento = "Antibiótico"
        consulta.medicamentos = "Amoxicilina"
        consulta.veterinario = "Dr. López"
        consulta.proxima_consulta = datetime(2024, 1, 27)

        resultado = ReporteHistoriaClinicaService._formatear_consulta(consulta)

        assert resultado["codigo"] == "CON-001"
        assert resultado["motivo"] == "Control"
        assert resultado["veterinario"] == "Dr. López"
        assert resultado["proxima_consulta"] is not None


# ─────────────────────────────────────────────────────────────────────────────
# Tests para ReporteLaboratorioService
# ─────────────────────────────────────────────────────────────────────────────

class TestReporteLaboratorioService:
    """Tests para el servicio de reportes de laboratorio."""

    @patch('services.report_laboratorio.imagen_a_base64', return_value='base64data')
    @patch('services.report_laboratorio.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_laboratorio.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_laboratorio.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_laboratorio.formatear_fecha', return_value='15/01/2024')
    @patch('services.report_laboratorio.calcular_edad_anios', return_value='1 año')
    @patch('services.report_laboratorio.clasificar_valor', return_value='normal')
    @patch('services.report_laboratorio.formatear_valor_numerico', return_value='6.50')
    @patch('services.report_laboratorio.generar_reporte', return_value=b'%PDF-1.4')
    @patch('services.report_laboratorio.AnimalService')
    @patch('services.report_laboratorio.MuestraService')
    def test_generar_pdf_persona_natural(
        self, mock_muestra_svc, mock_animal_svc, mock_generar_reporte,
        mock_formatear_valor, mock_clasificar, mock_calc_edad,
        mock_formatear_fecha, mock_gen_codigo, mock_gen_barras, mock_gen_qr,
        mock_imagen, mock_muestra, mock_animal
    ):
        """Test: generar_pdf para persona natural."""
        mock_muestra_svc.return_value.obtener_muestra.return_value = mock_muestra
        mock_animal_svc.return_value.obtener_animal.return_value = mock_animal

        service = ReporteLaboratorioService()
        resultado = service.generar_pdf(1, es_empresa=False)

        assert resultado == b'%PDF-1.4'

    @patch('services.report_laboratorio.imagen_a_base64', return_value='base64data')
    @patch('services.report_laboratorio.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_laboratorio.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_laboratorio.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_laboratorio.formatear_fecha', return_value='15/01/2024')
    @patch('services.report_laboratorio.calcular_edad_anios', return_value='1 año')
    @patch('services.report_laboratorio.clasificar_valor', return_value='normal')
    @patch('services.report_laboratorio.formatear_valor_numerico', return_value='6.50')
    @patch('services.report_laboratorio.generar_reporte', return_value=b'%PDF-1.4')
    @patch('services.report_laboratorio.AnimalService')
    @patch('services.report_laboratorio.MuestraService')
    def test_generar_pdf_empresa(
        self, mock_muestra_svc, mock_animal_svc, mock_generar_reporte,
        mock_formatear_valor, mock_clasificar, mock_calc_edad,
        mock_formatear_fecha, mock_gen_codigo, mock_gen_barras, mock_gen_qr,
        mock_imagen, mock_muestra, mock_animal
    ):
        """Test: generar_pdf para empresa."""
        mock_muestra_svc.return_value.obtener_muestra.return_value = mock_muestra
        mock_animal_svc.return_value.obtener_animal.return_value = mock_animal

        service = ReporteLaboratorioService()
        resultado = service.generar_pdf(
            1, es_empresa=True, datos_empresa={"nombre": "Empresa ABC"})

        assert resultado == b'%PDF-1.4'

    def test_parsear_referencia_rango(self):
        """Test: _parsear_referencia parsea rango correctamente."""
        service = ReporteLaboratorioService()
        ref_min, ref_max = service._parsear_referencia("5.0 - 10.0")

        assert ref_min == 5.0
        assert ref_max == 10.0

    def test_parsear_referencia_vacio(self):
        """Test: _parsear_referencia retorna None para string vacío."""
        service = ReporteLaboratorioService()
        ref_min, ref_max = service._parsear_referencia("")

        assert ref_min is None
        assert ref_max is None

    def test_parsear_referencia_none(self):
        """Test: _parsear_referencia retorna None para None."""
        service = ReporteLaboratorioService()
        ref_min, ref_max = service._parsear_referencia(None)

        assert ref_min is None
        assert ref_max is None

    def test_agrupar_por_seccion(self):
        """Test: _agrupar_por_seccion agrupa items correctamente."""
        items = [
            {"item": "Hematies", "seccion": "HEMATOLOGÍA"},
            {"item": "Leucocitos", "seccion": "HEMATOLOGÍA"},
            {"item": "Glucosa", "seccion": "QUÍMICA SANGUÍNEA"}
        ]

        service = ReporteLaboratorioService()
        resultado = service._agrupar_por_seccion(items)

        assert len(resultado) == 2
        assert resultado[0]["nombre"] == "HEMATOLOGÍA"
        assert len(resultado[0]["items"]) == 2

    def test_clasificar_item_normal(self):
        """Test: _clasificar_item retorna 'normal' para valor dentro de rango."""
        item = {"resultado": "7.0", "ref_min": 5.0, "ref_max": 10.0}

        service = ReporteLaboratorioService()
        resultado = service._clasificar_item(item)

        assert resultado == "normal"

    def test_a_float_valido(self):
        """Test: _a_float convierte string a float."""
        resultado = ReporteLaboratorioService._a_float("3.14")
        assert resultado == 3.14

    def test_a_float_none(self):
        """Test: _a_float retorna None para None."""
        resultado = ReporteLaboratorioService._a_float(None)
        assert resultado is None

    def test_a_float_invalido(self):
        """Test: _a_float retorna None para string no numérico."""
        resultado = ReporteLaboratorioService._a_float("abc")
        assert resultado is None

    def test_normalizar_items(self):
        """Test: _normalizar_items asegura keys requeridas."""
        items = [
            {"item": "Hematies", "resultado": "6.5", "unidades": "mill/µL",
             "ref_texto": "5.5 - 8.5", "seccion": "HEMATOLOGÍA"}
        ]

        service = ReporteLaboratorioService()
        resultado = service._normalizar_items(items)

        assert len(resultado) == 1
        assert "item" in resultado[0]
        assert "resultado" in resultado[0]
        assert "ref_min" in resultado[0]
        assert "ref_max" in resultado[0]


# ─────────────────────────────────────────────────────────────────────────────
# Tests para ReporteReciboService
# ─────────────────────────────────────────────────────────────────────────────

class TestReporteReciboService:
    """Tests para el servicio de reportes de recibo."""

    @patch('services.report_recibo.generar_reporte', return_value=b'%PDF-1.4')
    def test_generar_pdf_exitoso(self, mock_generar_reporte, mock_recibo_data):
        """Test: generar_pdf retorna bytes del PDF correctamente."""
        service = ReporteReciboService()
        resultado = service.generar_pdf(mock_recibo_data)

        assert resultado == b'%PDF-1.4'

    @patch('services.report_recibo.generar_reporte', return_value=b'%PDF-1.4')
    def test_generar_y_guardar(self, mock_generar_reporte, mock_recibo_data):
        """Test: generar_y_guardar guarda el PDF en disco."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            service = ReporteReciboService()
            resultado = service.generar_y_guardar(mock_recibo_data, tmp_path)

            assert resultado == tmp_path
            assert os.path.exists(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @patch('services.report_recibo.generar_reporte', return_value=b'%PDF-1.4')
    def test_construir_contexto(self, mock_generar_reporte, mock_recibo_data):
        """Test: _construir_contexto retorna contexto completo."""
        service = ReporteReciboService()
        contexto = service._construir_contexto(mock_recibo_data)

        assert "lab" in contexto
        assert "datos" in contexto
        assert "fecha_str" in contexto
        assert contexto["datos"] == mock_recibo_data

    @patch('services.report_recibo.generar_reporte', return_value=b'%PDF-1.4')
    def test_construir_contexto_fecha_default(self, mock_generar_reporte):
        """Test: _construir_contexto usa fecha actual por defecto."""
        service = ReporteReciboService()
        contexto = service._construir_contexto({})

        assert "fecha_str" in contexto
        # La fecha debe tener formato dd/mm/yyyy
        assert len(contexto["fecha_str"].split("/")) == 3


# ─────────────────────────────────────────────────────────────────────────────
# Tests para ReporteVacunacionService
# ─────────────────────────────────────────────────────────────────────────────

class TestReporteVacunacionService:
    """Tests para el servicio de reportes de vacunación."""

    @patch('services.report_vacunacion.imagen_a_base64', return_value='base64data')
    @patch('services.report_vacunacion.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_vacunacion.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_vacunacion.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_vacunacion.formatear_fecha', return_value='15/01/2024')
    @patch('services.report_vacunacion.calcular_edad', return_value='1 año')
    @patch('services.report_vacunacion.generar_reporte', return_value=b'%PDF-1.4')
    @patch('services.report_vacunacion.AnimalRepository')
    @patch('services.report_vacunacion.VacunacionRepository')
    def test_generar_pdf_vacuna(
        self, mock_vacuna_repo, mock_animal_repo, mock_generar_reporte,
        mock_calc_edad, mock_formatear_fecha, mock_gen_codigo,
        mock_gen_barras, mock_gen_qr, mock_imagen, mock_vacunacion, mock_animal
    ):
        """Test: generar_pdf para vacuna."""
        mock_vacuna_repo.return_value.get_by_id.return_value = mock_vacunacion
        mock_animal_repo.return_value.get_by_id.return_value = mock_animal
        mock_vacuna_repo.return_value.get_by_animal.return_value = []

        service = ReporteVacunacionService()
        resultado = service.generar_pdf(1)

        assert resultado == b'%PDF-1.4'

    @patch('services.report_vacunacion.imagen_a_base64', return_value='base64data')
    @patch('services.report_vacunacion.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_vacunacion.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_vacunacion.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_vacunacion.formatear_fecha', return_value='15/01/2024')
    @patch('services.report_vacunacion.calcular_edad', return_value='1 año')
    @patch('services.report_vacunacion.generar_reporte', return_value=b'%PDF-1.4')
    @patch('services.report_vacunacion.AnimalRepository')
    @patch('services.report_vacunacion.VacunacionRepository')
    def test_generar_pdf_desparasitacion(
        self, mock_vacuna_repo, mock_animal_repo, mock_generar_reporte,
        mock_calc_edad, mock_formatear_fecha, mock_gen_codigo,
        mock_gen_barras, mock_gen_qr, mock_imagen, mock_animal
    ):
        """Test: generar_pdf para desparasitación."""
        vacunacion = Mock()
        vacunacion.id = 1
        vacunacion.animal_id = 10
        vacunacion.fecha_aplicacion = datetime(2024, 1, 15)
        vacunacion.fecha_proxima = datetime(2024, 7, 15)
        vacunacion.producto = "Desparasitante Interno"
        vacunacion.tipo = "Desparasitación"
        vacunacion.via = "PO"
        vacunacion.lote = "LOT-001"
        vacunacion.veterinario = "Dr. López"

        mock_vacuna_repo.return_value.get_by_id.return_value = vacunacion
        mock_animal_repo.return_value.get_by_id.return_value = mock_animal
        mock_vacuna_repo.return_value.get_by_animal.return_value = []

        service = ReporteVacunacionService()
        resultado = service.generar_pdf(1)

        assert resultado == b'%PDF-1.4'

    @patch('services.report_vacunacion.imagen_a_base64', return_value='base64data')
    @patch('services.report_vacunacion.generar_qr_base64', return_value='qrbase64')
    @patch('services.report_vacunacion.generar_codigo_barras_base64', return_value='barbase64')
    @patch('services.report_vacunacion.generar_codigo_verificacion', return_value='VER-123')
    @patch('services.report_vacunacion.formatear_fecha', return_value='15/01/2024')
    @patch('services.report_vacunacion.calcular_edad', return_value='1 año')
    @patch('services.report_vacunacion.generar_por_tipo', return_value='/path/to/file.pdf')
    @patch('services.report_vacunacion.AnimalRepository')
    @patch('services.report_vacunacion.VacunacionRepository')
    def test_generar_y_guardar(
        self, mock_vacuna_repo, mock_animal_repo, mock_generar_por_tipo,
        mock_calc_edad, mock_formatear_fecha, mock_gen_codigo,
        mock_gen_barras, mock_gen_qr, mock_imagen, mock_vacunacion, mock_animal
    ):
        """Test: generar_y_guardar guarda el PDF en disco."""
        mock_vacuna_repo.return_value.get_by_id.return_value = mock_vacunacion
        mock_animal_repo.return_value.get_by_id.return_value = mock_animal
        mock_vacuna_repo.return_value.get_by_animal.return_value = []

        service = ReporteVacunacionService()
        resultado = service.generar_y_guardar(1, '/path/to/file.pdf')

        assert resultado == '/path/to/file.pdf'

    def test_badge_via_sc(self):
        """Test: _badge_via retorna badge para SC."""
        resultado = ReporteVacunacionService._badge_via("SC")
        assert resultado["css"] == "via-sc"
        assert resultado["label"] == "Subcutánea"

    def test_badge_via_im(self):
        """Test: _badge_via retorna badge para IM."""
        resultado = ReporteVacunacionService._badge_via("IM")
        assert resultado["css"] == "via-im"
        assert resultado["label"] == "Intramuscular"

    def test_badge_via_iv(self):
        """Test: _badge_via retorna badge para IV."""
        resultado = ReporteVacunacionService._badge_via("IV")
        assert resultado["css"] == "via-iv"
        assert resultado["label"] == "Intravenosa"

    def test_badge_via_po(self):
        """Test: _badge_via retorna badge para PO."""
        resultado = ReporteVacunacionService._badge_via("PO")
        assert resultado["css"] == "via-po"
        assert resultado["label"] == "Oral"

    def test_badge_via_top(self):
        """Test: _badge_via retorna badge para TOP."""
        resultado = ReporteVacunacionService._badge_via("TOP")
        assert resultado["css"] == "via-top"
        assert resultado["label"] == "Tópica"

    def test_badge_via_none(self):
        """Test: _badge_via retorna badge por defecto para None."""
        resultado = ReporteVacunacionService._badge_via(None)
        assert resultado["css"] == "via-default"
        assert resultado["label"] == "—"


# ─────────────────────────────────────────────────────────────────────────────
# Tests para ReportService
# ─────────────────────────────────────────────────────────────────────────────

class TestReportService:
    """Tests para el servicio de reportes del dashboard."""

    @patch('services.report_service.DatabaseManager')
    def test_get_dashboard_stats(self, mock_db):
        """Test: get_dashboard_stats retorna estadísticas del dashboard."""
        mock_instance = mock_db.return_value
        mock_instance.fetch_one.side_effect = [
            {'total': 15},  # activos
            {'total': 3},   # hoy
            {'total': 5},   # muestras_pendientes
            {'total': 2},   # urgentes
            {'total': 10},  # completadas_semana
            {'promedio': 2.5}  # tiempo_promedio
        ]

        service = ReportService()
        stats = service.get_dashboard_stats()

        assert stats['activos'] == 15
        assert stats['hoy'] == 3
        assert stats['muestras_pendientes'] == 5
        assert stats['urgentes'] == 2
        assert stats['completadas_semana'] == 10
        assert stats['tiempo_promedio'] == 2.5

    @patch('services.report_service.DatabaseManager')
    def test_get_efficiency_metrics(self, mock_db):
        """Test: get_efficiency_metrics retorna métricas de eficiencia."""
        mock_instance = mock_db.return_value
        mock_instance.fetch_one.return_value = {'tasa': 85.5}
        mock_instance.fetch_all.return_value = [
            {'tecnico': 'Tech. Ana', 'total': 20},
            {'tecnico': 'Tech. Carlos', 'total': 15}
        ]

        service = ReportService()
        metrics = service.get_efficiency_metrics()

        assert metrics['tasa_cumplimiento'] == 85.5
        assert len(metrics['por_tecnico']) == 2

    @patch('services.report_service.DatabaseManager')
    def test_get_reporte_muestras(self, mock_db):
        """Test: get_reporte_muestras retorna reporte de muestras."""
        mock_instance = mock_db.return_value
        mock_instance.fetch_all.return_value = [
            {'id': 1, 'codigo': 'MUE-001', 'animal_nombre': 'Luna'},
            {'id': 2, 'codigo': 'MUE-002', 'animal_nombre': 'Max'}
        ]

        service = ReportService()
        resultado = service.get_reporte_muestras('2024-01-01', '2024-01-31')

        assert len(resultado) == 2
        assert resultado[0]['codigo'] == 'MUE-001'


# ─────────────────────────────────────────────────────────────────────────────
# Tests para PDFService
# ─────────────────────────────────────────────────────────────────────────────

class TestPDFService:
    """Tests para el servicio facade de PDFs."""

    @patch('services.pdf_service.ReporteLaboratorioService')
    def test_generar_laboratorio(self, mock_laboratorio_svc):
        """Test: generar_laboratorio delega al servicio correcto."""
        mock_laboratorio_svc.return_value.generar_pdf.return_value = b'%PDF-1.4'

        service = PDFService()
        resultado = service.generar_laboratorio(1)

        assert resultado == b'%PDF-1.4'
        mock_laboratorio_svc.return_value.generar_pdf.assert_called_once()

    @patch('services.pdf_service.ReporteLaboratorioService')
    def test_guardar_laboratorio(self, mock_laboratorio_svc):
        """Test: guardar_laboratorio delega al servicio correcto."""
        mock_laboratorio_svc.return_value.generar_y_guardar.return_value = '/path/file.pdf'

        service = PDFService()
        resultado = service.guardar_laboratorio(1, '/path/file.pdf')

        assert resultado == '/path/file.pdf'

    @patch('services.pdf_service.ReporteVacunacionService')
    def test_generar_vacunacion(self, mock_vacuna_svc):
        """Test: generar_vacunacion delega al servicio correcto."""
        mock_vacuna_svc.return_value.generar_pdf.return_value = b'%PDF-1.4'

        service = PDFService()
        resultado = service.generar_vacunacion(1)

        assert resultado == b'%PDF-1.4'

    @patch('services.pdf_service.ReporteVacunacionService')
    def test_guardar_vacunacion(self, mock_vacuna_svc):
        """Test: guardar_vacunacion delega al servicio correcto."""
        mock_vacuna_svc.return_value.generar_y_guardar.return_value = '/path/file.pdf'

        service = PDFService()
        resultado = service.guardar_vacunacion(1, '/path/file.pdf')

        assert resultado == '/path/file.pdf'

    @patch('services.pdf_service.ReporteHistoriaClinicaService')
    def test_generar_historia_clinica(self, mock_historia_svc):
        """Test: generar_historia_clinica delega al servicio correcto."""
        mock_historia_svc.return_value.generar_pdf.return_value = b'%PDF-1.4'

        service = PDFService()
        resultado = service.generar_historia_clinica(1)

        assert resultado == b'%PDF-1.4'

    @patch('services.pdf_service.ReporteHistoriaClinicaService')
    def test_guardar_historia_clinica(self, mock_historia_svc):
        """Test: guardar_historia_clinica delega al servicio correcto."""
        mock_historia_svc.return_value.generar_y_guardar.return_value = '/path/file.pdf'

        service = PDFService()
        resultado = service.guardar_historia_clinica(1, '/path/file.pdf')

        assert resultado == '/path/file.pdf'

    @patch('services.pdf_service.ReporteCirugiaService')
    def test_generar_cirugia(self, mock_cirugia_svc):
        """Test: generar_cirugia delega al servicio correcto."""
        mock_cirugia_svc.return_value.generar_pdf.return_value = b'%PDF-1.4'

        service = PDFService()
        resultado = service.generar_cirugia(1)

        assert resultado == b'%PDF-1.4'

    @patch('services.pdf_service.ReporteCirugiaService')
    def test_guardar_cirugia(self, mock_cirugia_svc):
        """Test: guardar_cirugia delega al servicio correcto."""
        mock_cirugia_svc.return_value.generar_y_guardar.return_value = '/path/file.pdf'

        service = PDFService()
        resultado = service.guardar_cirugia(1, '/path/file.pdf')

        assert resultado == '/path/file.pdf'

    @patch('services.pdf_service.ReporteConsultaService')
    def test_generar_consulta(self, mock_consulta_svc):
        """Test: generar_consulta delega al servicio correcto."""
        mock_consulta_svc.return_value.generar_pdf.return_value = b'%PDF-1.4'

        service = PDFService()
        resultado = service.generar_consulta(Mock())

        assert resultado == b'%PDF-1.4'

    @patch('services.pdf_service.ReporteConsultaService')
    def test_guardar_consulta(self, mock_consulta_svc):
        """Test: guardar_consulta delega al servicio correcto."""
        mock_consulta_svc.return_value.generar_y_guardar.return_value = '/path/file.pdf'

        service = PDFService()
        resultado = service.guardar_consulta(1, '/path/file.pdf')

        assert resultado == '/path/file.pdf'

    @patch('services.pdf_service.ReporteReciboService')
    def test_generar_recibo(self, mock_recibo_svc):
        """Test: generar_recibo delega al servicio correcto."""
        mock_recibo_svc.return_value.generar_pdf.return_value = b'%PDF-1.4'

        service = PDFService()
        resultado = service.generar_recibo({"monto": 100})

        assert resultado == b'%PDF-1.4'

    @patch('services.pdf_service.ReporteReciboService')
    def test_guardar_recibo(self, mock_recibo_svc):
        """Test: guardar_recibo delega al servicio correcto."""
        mock_recibo_svc.return_value.generar_y_guardar.return_value = '/path/file.pdf'

        service = PDFService()
        resultado = service.guardar_recibo({"monto": 100}, '/path/file.pdf')

        assert resultado == '/path/file.pdf'

    def test_ruta_default(self):
        """Test: ruta_default retorna ruta válida."""
        resultado = PDFService.ruta_default("test.pdf")

        assert "test.pdf" in resultado
        assert os.path.isabs(resultado)

    def test_extraer_resultados_json_lista(self):
        """Test: _extraer_resultados parsea JSON con lista."""
        muestra = Mock()
        muestra.resultado = json.dumps([
            {"item": "Hematies", "resultado": "6.5"}
        ])

        resultado = PDFService._extraer_resultados(muestra)

        assert resultado is not None
        assert len(resultado) == 1

    def test_extraer_resultados_json_secciones(self):
        """Test: _extraer_resultados parsea JSON con secciones."""
        muestra = Mock()
        muestra.resultado = json.dumps({
            "secciones": [
                {"nombre": "HEMATOLOGÍA", "items": [{"item": "Hematies"}]}
            ]
        })

        resultado = PDFService._extraer_resultados(muestra)

        assert resultado is not None
        assert len(resultado) == 1
        assert resultado[0]["seccion"] == "HEMATOLOGÍA"

    def test_extraer_resultados_json_items(self):
        """Test: _extraer_resultados parsea JSON con items."""
        muestra = Mock()
        muestra.resultado = json.dumps({
            "items": [{"item": "Hematies"}]
        })

        resultado = PDFService._extraer_resultados(muestra)

        assert resultado is not None
        assert len(resultado) == 1

    def test_extraer_resultados_none(self):
        """Test: _extraer_resultados retorna None para None."""
        muestra = Mock()
        muestra.resultado = None

        resultado = PDFService._extraer_resultados(muestra)

        assert resultado is None

    def test_extraer_resultados_texto_plano(self):
        """Test: _extraer_resultados retorna None para texto plano."""
        muestra = Mock()
        muestra.resultado = "Esto es texto plano"

        resultado = PDFService._extraer_resultados(muestra)

        assert resultado is None
