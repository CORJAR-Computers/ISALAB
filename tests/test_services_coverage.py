"""
Tests unitarios comprehensivos para services restantes de IsaLab.

Cubre:
- ConsultaService: registro, obtención, actualización de consultas
- VacunaService: registro, obtención de vacunaciones
- HistoriaService: creación, obtención, actualización de historias clínicas
- RecepcionService: registro, obtención de recepciones
- ConfiguracionService: carga y guardado de configuración

Estos tests usan una DB temporal aislada (ver conftest.py).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Any

import pytest

# Asegurar que la raíz del repo esté en sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _setup_test_db() -> None:
    """Crea las tablas mínimas para tests de services."""
    from config import DB_PATH
    from database.connection import DatabaseManager

    db = DatabaseManager()

    # Crear tablas necesarias
    db.execute("DROP TABLE IF EXISTS usuarios")
    db.execute("DROP TABLE IF EXISTS animales")
    db.execute("DROP TABLE IF EXISTS movimientos")
    db.execute("DROP TABLE IF EXISTS muestras")
    db.execute("DROP TABLE IF EXISTS recepciones")
    db.execute("DROP TABLE IF EXISTS consultas")
    db.execute("DROP TABLE IF EXISTS vacunaciones")
    db.execute("DROP TABLE IF EXISTS cirugias")
    db.execute("DROP TABLE IF EXISTS historias_clinicas")
    db.execute("DROP TABLE IF EXISTS codigo_contadores")

    db.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre TEXT,
            rol TEXT DEFAULT 'usuario',
            activo INTEGER DEFAULT 1,
            ultimo_acceso TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS animales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT,
            especie TEXT,
            raza TEXT,
            sexo TEXT,
            color TEXT,
            tipo_pelo TEXT,
            senas_particulares TEXT,
            microchip TEXT,
            edad INTEGER,
            unidad_edad TEXT DEFAULT 'Años',
            fecha_nacimiento TEXT,
            peso REAL,
            propietario TEXT,
            propietario_tipo_doc TEXT,
            propietario_documento TEXT,
            propietario_direccion TEXT,
            propietario_oficio TEXT,
            telefono TEXT,
            email TEXT,
            fecha_ingreso TEXT,
            estado TEXT DEFAULT 'Activo',
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            motivo TEXT,
            responsable TEXT,
            destino TEXT,
            FOREIGN KEY (animal_id) REFERENCES animales(id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS recepciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            animal_id INTEGER NOT NULL,
            fecha_hora TEXT NOT NULL,
            motivo TEXT,
            veterinario TEXT,
            estado TEXT DEFAULT 'En espera',
            proxima_cita TEXT,
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (animal_id) REFERENCES animales(id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            animal_id INTEGER NOT NULL,
            historia_id INTEGER,
            fecha TEXT NOT NULL,
            motivo TEXT NOT NULL,
            evolucion TEXT,
            examen_fisico TEXT,
            tratamiento TEXT,
            medicamentos TEXT,
            proxima_consulta TEXT,
            veterinario TEXT,
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (animal_id) REFERENCES animales(id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS vacunaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            animal_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            producto TEXT NOT NULL,
            lote TEXT,
            dosis TEXT,
            via TEXT,
            fecha_aplicacion TEXT NOT NULL,
            fecha_proxima TEXT,
            veterinario TEXT,
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (animal_id) REFERENCES animales(id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS historias_clinicas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recepcion_id INTEGER NOT NULL,
            animal_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            anamnesis TEXT,
            examen_fisico TEXT,
            temperatura REAL,
            frecuencia_cardiaca INTEGER,
            frecuencia_respiratoria INTEGER,
            peso_consulta REAL,
            dieta TEXT,
            enfermedades_previas TEXT,
            cirugias_previas TEXT,
            esterilizado TEXT,
            numero_partos INTEGER,
            esquema_vacunal TEXT,
            ultima_desparasitacion TEXT,
            tratamientos_recientes TEXT,
            viajes_recientes TEXT,
            convive_con_animales TEXT,
            comportamiento TEXT,
            condicion_corporal TEXT,
            tllc TEXT,
            trpc TEXT,
            mucosas TEXT,
            pulso TEXT,
            deshidratacion TEXT,
            diagnostico TEXT,
            diagnostico_diferencial TEXT,
            tratamiento TEXT,
            pronostico TEXT,
            veterinario TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recepcion_id) REFERENCES recepciones(id),
            FOREIGN KEY (animal_id) REFERENCES animales(id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS cirugias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            animal_id INTEGER NOT NULL,
            historia_id INTEGER,
            fecha TEXT NOT NULL,
            tipo_cirugia TEXT NOT NULL,
            descripcion TEXT,
            anestesia TEXT,
            protocolo_anestesico TEXT,
            duracion_min INTEGER,
            cirujano TEXT,
            anestesiologo TEXT,
            asistente TEXT,
            complicaciones TEXT,
            cuidados_post TEXT,
            estado TEXT DEFAULT 'Programada',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (animal_id) REFERENCES animales(id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS codigo_contadores (
            prefijo TEXT PRIMARY KEY,
            contador INTEGER DEFAULT 0
        )
    """)

    # Reset singleton
    DatabaseManager._instance = None
    DatabaseManager()


def _create_test_animal(
    codigo: str = "PAC-TEST-001",
    nombre: str = "Test Perro",
    especie: str = "Canino"
) -> int:
    """Crea un animal de prueba y retorna su ID."""
    from database.connection import DatabaseManager

    db = DatabaseManager()
    cursor = db.execute(
        "INSERT INTO animales (codigo, nombre, especie, fecha_ingreso, estado) VALUES (?, ?, ?, ?, ?)",
        (codigo, nombre, especie, "2026-01-01", "Activo")
    )
    return cursor.lastrowid


def _create_test_recepcion(animal_id: int) -> int:
    """Crea una recepción de prueba y retorna su ID."""
    from database.connection import DatabaseManager

    db = DatabaseManager()
    cursor = db.execute(
        "INSERT INTO recepciones (codigo, animal_id, fecha_hora, motivo, estado) VALUES (?, ?, ?, ?, ?)",
        (f"ISAL-TEST-{animal_id}", animal_id, "2026-01-15 10:00:00", "Consulta inicial", "En espera")
    )
    return cursor.lastrowid


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def setup_db():
    """Setup de DB para cada test."""
    _setup_test_db()
    yield
    # Cleanup
    from database.connection import DatabaseManager
    DatabaseManager._instance = None


@pytest.fixture
def test_animal_id():
    """Animal de prueba para tests."""
    return _create_test_animal()


@pytest.fixture
def test_recepcion_id(test_animal_id):
    """Recepción de prueba para tests."""
    return _create_test_recepcion(test_animal_id)


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: CONSULTA SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class TestConsultaService:
    """Tests para ConsultaService - CRUD de consultas ambulatorias."""

    def test_registrar_consulta_exitoso(self, test_animal_id):
        """Test: registro de consulta exitoso."""
        from services.consulta_service import ConsultaService

        svc = ConsultaService()
        consulta = svc.registrar_consulta({
            'animal_id': test_animal_id,
            'fecha': '2026-03-01',
            'motivo': 'Dolor estomacal',
            'veterinario': 'Dr. Test'
        })

        assert consulta is not None
        assert consulta.codigo.startswith('CONS-')
        assert consulta.motivo == 'Dolor estomacal'

    def test_registrar_consulta_generar_codigo(self, test_animal_id):
        """Test: generación automática de código de consulta."""
        from services.consulta_service import ConsultaService

        svc = ConsultaService()
        consulta = svc.registrar_consulta({
            'animal_id': test_animal_id,
            'fecha': '2026-03-02',
            'motivo': 'Control de rutina'
        })

        assert consulta.codigo.startswith('CONS-')

    def test_obtener_consulta(self, test_animal_id):
        """Test: obtener consulta por ID."""
        from services.consulta_service import ConsultaService

        svc = ConsultaService()
        consulta_creada = svc.registrar_consulta({
            'animal_id': test_animal_id,
            'fecha': '2026-03-03',
            'motivo': 'Vacunación'
        })

        consulta = svc.obtener_consulta(consulta_creada.id)
        assert consulta is not None
        assert consulta.motivo == 'Vacunación'

    def test_listar_consultas(self, test_animal_id):
        """Test: listar consultas."""
        from services.consulta_service import ConsultaService

        svc = ConsultaService()
        svc.registrar_consulta({
            'animal_id': test_animal_id,
            'fecha': '2026-03-04',
            'motivo': 'Consulta 1'
        })
        svc.registrar_consulta({
            'animal_id': test_animal_id,
            'fecha': '2026-03-05',
            'motivo': 'Consulta 2'
        })

        consultas = svc.listar_consultas()
        assert len(consultas) >= 2

    def test_consultas_por_paciente(self, test_animal_id):
        """Test: obtener consultas por paciente."""
        from services.consulta_service import ConsultaService

        svc = ConsultaService()
        svc.registrar_consulta({
            'animal_id': test_animal_id,
            'fecha': '2026-03-06',
            'motivo': 'Visita paciente'
        })

        consultas = svc.consultas_por_paciente(test_animal_id)
        assert len(consultas) >= 1
        for c in consultas:
            assert c.animal_id == test_animal_id

    def test_actualizar_consulta(self, test_animal_id):
        """Test: actualizar datos de consulta."""
        from services.consulta_service import ConsultaService

        svc = ConsultaService()
        consulta = svc.registrar_consulta({
            'animal_id': test_animal_id,
            'fecha': '2026-03-07',
            'motivo': 'Consulta Original'
        })

        svc.actualizar_consulta(consulta.id, {
            'motivo': 'Consulta Actualizada',
            'tratamiento': 'Medicación oral'
        })

        consulta_actualizada = svc.obtener_consulta(consulta.id)
        assert consulta_actualizada.motivo == 'Consulta Actualizada'
        assert consulta_actualizada.tratamiento == 'Medicación oral'

    def test_generar_codigo(self):
        """Test: generación de código de consulta."""
        from services.consulta_service import ConsultaService

        svc = ConsultaService()
        codigo1 = svc.generar_codigo()
        codigo2 = svc.generar_codigo()

        assert codigo1.startswith('CONS-')
        assert codigo1 != codigo2


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: VACUNA SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class TestVacunaService:
    """Tests para VacunaService - CRUD de vacunaciones."""

    def test_registrar_vacuna_exitoso(self, test_animal_id):
        """Test: registro de vacunación exitoso."""
        from services.vacuna_service import VacunaService

        svc = VacunaService()
        vacunacion = svc.registrar({
            'animal_id': test_animal_id,
            'tipo': 'Vacuna',
            'producto': 'Rabia',
            'fecha_aplicacion': '2026-03-01',
            'veterinario': 'Dr. Test'
        })

        assert vacunacion is not None
        assert vacunacion.codigo.startswith('VAC-')
        assert vacunacion.producto == 'Rabia'

    def test_registrar_desparasitacion(self, test_animal_id):
        """Test: registro de desparasitación exitoso."""
        from services.vacuna_service import VacunaService

        svc = VacunaService()
        vacunacion = svc.registrar({
            'animal_id': test_animal_id,
            'tipo': 'Desparasitación',
            'producto': 'Pyrantel',
            'fecha_aplicacion': '2026-03-02'
        })

        assert vacunacion is not None
        assert vacunacion.tipo == 'Desparasitación'

    def test_registrar_vacuna_generar_codigo(self, test_animal_id):
        """Test: generación automática de código de vacunación."""
        from services.vacuna_service import VacunaService

        svc = VacunaService()
        vacunacion = svc.registrar({
            'animal_id': test_animal_id,
            'tipo': 'Vacuna',
            'producto': 'Moquillo',
            'fecha_aplicacion': '2026-03-03'
        })

        assert vacunacion.codigo.startswith('VAC-')

    def test_obtener_vacuna(self, test_animal_id):
        """Test: obtener vacunación por ID."""
        from services.vacuna_service import VacunaService

        svc = VacunaService()
        vacunacion_creada = svc.registrar({
            'animal_id': test_animal_id,
            'tipo': 'Vacuna',
            'producto': 'Parvovirus',
            'fecha_aplicacion': '2026-03-04'
        })

        vacunacion = svc.obtener(vacunacion_creada.id)
        assert vacunacion is not None
        assert vacunacion.producto == 'Parvovirus'

    def test_listar_vacunas(self, test_animal_id):
        """Test: listar vacunaciones."""
        from services.vacuna_service import VacunaService

        svc = VacunaService()
        svc.registrar({
            'animal_id': test_animal_id,
            'tipo': 'Vacuna',
            'producto': 'Vacuna 1',
            'fecha_aplicacion': '2026-03-05'
        })
        svc.registrar({
            'animal_id': test_animal_id,
            'tipo': 'Vacuna',
            'producto': 'Vacuna 2',
            'fecha_aplicacion': '2026-03-06'
        })

        vacunas = svc.listar()
        assert len(vacunas) >= 2

    def test_por_paciente(self, test_animal_id):
        """Test: obtener vacunaciones por paciente."""
        from services.vacuna_service import VacunaService

        svc = VacunaService()
        svc.registrar({
            'animal_id': test_animal_id,
            'tipo': 'Vacuna',
            'producto': 'Vacuna Paciente',
            'fecha_aplicacion': '2026-03-07'
        })

        vacunas = svc.por_paciente(test_animal_id)
        assert len(vacunas) >= 1
        for v in vacunas:
            assert v.animal_id == test_animal_id

    def test_generar_codigo(self):
        """Test: generación de código de vacunación."""
        from services.vacuna_service import VacunaService

        svc = VacunaService()
        codigo1 = svc.generar_codigo()
        codigo2 = svc.generar_codigo()

        assert codigo1.startswith('VAC-')
        assert codigo1 != codigo2


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: HISTORIA SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class TestHistoriaService:
    """Tests para HistoriaService - CRUD de historias clínicas."""

    def test_crear_historia_exitoso(self, test_animal_id, test_recepcion_id):
        """Test: creación de historia clínica exitosa."""
        from services.historia_service import HistoriaService

        svc = HistoriaService()
        historia = svc.crear_historia({
            'recepcion_id': test_recepcion_id,
            'animal_id': test_animal_id,
            'fecha': '2026-03-01',
            'anamnesis': 'Mascota trae por dolor',
            'diagnostico': 'Gastritis',
            'tratamiento': 'Dieta blanda'
        })

        assert historia is not None
        assert historia.anamnesis == 'Mascota trae por dolor'
        assert historia.diagnostico == 'Gastritis'

    def test_crear_historia_con_signos_vitales(self, test_animal_id, test_recepcion_id):
        """Test: creación de historia con signos vitales."""
        from services.historia_service import HistoriaService

        svc = HistoriaService()
        historia = svc.crear_historia({
            'recepcion_id': test_recepcion_id,
            'animal_id': test_animal_id,
            'temperatura': 38.5,
            'frecuencia_cardiaca': 120,
            'frecuencia_respiratoria': 30,
            'peso_consulta': 15.5
        })

        assert historia.temperatura == 38.5
        assert historia.frecuencia_cardiaca == 120
        assert historia.peso_consulta == 15.5

    def test_obtener_historia(self, test_animal_id, test_recepcion_id):
        """Test: obtener historia clínica por ID."""
        from services.historia_service import HistoriaService

        svc = HistoriaService()
        historia_creada = svc.crear_historia({
            'recepcion_id': test_recepcion_id,
            'animal_id': test_animal_id,
            'diagnostico': 'Test diagnóstico'
        })

        historia = svc.obtener_historia(historia_creada.id)
        assert historia is not None
        assert historia.diagnostico == 'Test diagnóstico'

    def test_historias_por_paciente(self, test_animal_id, test_recepcion_id):
        """Test: obtener historias por paciente."""
        from services.historia_service import HistoriaService

        svc = HistoriaService()
        svc.crear_historia({
            'recepcion_id': test_recepcion_id,
            'animal_id': test_animal_id,
            'diagnostico': 'Historia 1'
        })

        historias = svc.historias_por_paciente(test_animal_id)
        assert len(historias) >= 1
        for h in historias:
            assert h.animal_id == test_animal_id

    def test_historia_de_recepcion(self, test_animal_id, test_recepcion_id):
        """Test: obtener historia por recepción."""
        from services.historia_service import HistoriaService

        svc = HistoriaService()
        svc.crear_historia({
            'recepcion_id': test_recepcion_id,
            'animal_id': test_animal_id,
            'diagnostico': 'Historia de recepción'
        })

        historia = svc.historia_de_recepcion(test_recepcion_id)
        assert historia is not None
        assert historia.recepcion_id == test_recepcion_id

    def test_actualizar_historia(self, test_animal_id, test_recepcion_id):
        """Test: actualizar datos de historia clínica."""
        from services.historia_service import HistoriaService

        svc = HistoriaService()
        historia = svc.crear_historia({
            'recepcion_id': test_recepcion_id,
            'animal_id': test_animal_id,
            'diagnostico': 'Original'
        })

        svc.actualizar_historia(historia.id, {
            'diagnostico': 'Actualizado',
            'tratamiento': 'Nuevo tratamiento'
        })

        historia_actualizada = svc.obtener_historia(historia.id)
        assert historia_actualizada.diagnostico == 'Actualizado'
        assert historia_actualizada.tratamiento == 'Nuevo tratamiento'


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: RECEPCION SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class TestRecepcionService:
    """Tests para RecepcionService - CRUD de recepciones."""

    def test_registrar_recepcion_exitoso(self, test_animal_id):
        """Test: registro de recepción exitoso."""
        from services.recepcion_service import RecepcionService

        svc = RecepcionService()
        recepcion_id = svc.registrar_recepcion({
            'animal_id': test_animal_id,
            'fecha_hora': '2026-03-01 10:00:00',
            'motivo': 'Consulta general',
            'veterinario': 'Dr. Test'
        })

        assert recepcion_id is not None
        assert recepcion_id > 0

    def test_registrar_recepcion_generar_codigo(self, test_animal_id):
        """Test: generación automática de código de recepción."""
        from services.recepcion_service import RecepcionService

        svc = RecepcionService()
        recepcion_id = svc.registrar_recepcion({
            'animal_id': test_animal_id,
            'fecha_hora': '2026-03-02 11:00:00',
            'motivo': 'Urgencia'
        })

        recepcion = svc.obtener_recepcion(recepcion_id)
        assert recepcion.codigo.startswith('ISAL-')

    def test_obtener_recepcion(self, test_animal_id):
        """Test: obtener recepción por ID."""
        from services.recepcion_service import RecepcionService

        svc = RecepcionService()
        recepcion_id = svc.registrar_recepcion({
            'animal_id': test_animal_id,
            'fecha_hora': '2026-03-03 12:00:00',
            'motivo': 'Control'
        })

        recepcion = svc.obtener_recepcion(recepcion_id)
        assert recepcion is not None
        assert recepcion.motivo == 'Control'

    def test_listar_recepciones(self, test_animal_id):
        """Test: listar recepciones."""
        from services.recepcion_service import RecepcionService

        svc = RecepcionService()
        svc.registrar_recepcion({
            'animal_id': test_animal_id,
            'fecha_hora': '2026-03-04 10:00:00',
            'motivo': 'Recepción 1'
        })
        svc.registrar_recepcion({
            'animal_id': test_animal_id,
            'fecha_hora': '2026-03-05 11:00:00',
            'motivo': 'Recepción 2'
        })

        recepciones = svc.listar_recepciones()
        assert len(recepciones) >= 2

    def test_historial_paciente(self, test_animal_id):
        """Test: obtener historial de recepciones por paciente."""
        from services.recepcion_service import RecepcionService

        svc = RecepcionService()
        svc.registrar_recepcion({
            'animal_id': test_animal_id,
            'fecha_hora': '2026-03-06 10:00:00',
            'motivo': 'Visita paciente'
        })

        recepciones = svc.historial_paciente(test_animal_id)
        assert len(recepciones) >= 1
        for r in recepciones:
            assert r.animal_id == test_animal_id

    def test_actualizar_estado(self, test_animal_id):
        """Test: actualizar estado de recepción."""
        from services.recepcion_service import RecepcionService

        svc = RecepcionService()
        recepcion_id = svc.registrar_recepcion({
            'animal_id': test_animal_id,
            'fecha_hora': '2026-03-07 10:00:00',
            'motivo': 'Pendiente'
        })

        svc.actualizar_estado(recepcion_id, "Atendido", proxima_cita="2026-04-01")

        recepcion = svc.obtener_recepcion(recepcion_id)
        assert recepcion.estado == "Atendido"
        assert recepcion.proxima_cita == "2026-04-01"

    def test_generar_codigo(self):
        """Test: generación de código de recepción."""
        from services.recepcion_service import RecepcionService

        svc = RecepcionService()
        codigo1 = svc.generar_codigo()
        codigo2 = svc.generar_codigo()

        assert codigo1.startswith('ISAL-')


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: CONFIGURACION SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class TestConfiguracionService:
    """Tests para ConfiguracionService - Gestión de configuración."""

    def test_cargar_configuracion_vacia(self):
        """Test: cargar configuración cuando no existe archivo."""
        from services.configuracion_service import ConfiguracionService

        svc = ConfiguracionService()
        # Eliminar archivo si existe
        if svc.config_path.exists():
            svc.config_path.unlink()

        config = svc.cargar_configuracion()
        assert config == {}

    def test_guardar_configuracion(self):
        """Test: guardar configuración."""
        from services.configuracion_service import ConfiguracionService

        svc = ConfiguracionService()
        # Eliminar archivo si existe
        if svc.config_path.exists():
            svc.config_path.unlink()

        result = svc.guardar_configuracion({'laboratorio': 'Test Lab', 'telefono': '555-1234'})
        assert result is True

        # Verificar que se guardó
        config = svc.cargar_configuracion()
        assert config['laboratorio'] == 'Test Lab'
        assert config['telefono'] == '555-1234'

    def test_guardar_configuracion_mantiene_anterior(self):
        """Test: guardar configuración mantiene datos anteriores."""
        from services.configuracion_service import ConfiguracionService

        svc = ConfiguracionService()
        # Eliminar archivo si existe
        if svc.config_path.exists():
            svc.config_path.unlink()

        # Guardar primera configuración
        svc.guardar_configuracion({'laboratorio': 'Lab 1'})

        # Guardar segunda configuración
        svc.guardar_configuracion({'telefono': '555-9999'})

        # Verificar que ambas existen
        config = svc.cargar_configuracion()
        assert config['laboratorio'] == 'Lab 1'
        assert config['telefono'] == '555-9999'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
