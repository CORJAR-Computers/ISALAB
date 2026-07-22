"""
Tests de integración para repositories de IsaLab.

Estos tests verifican operaciones CRUD contra la base de datos real
usando una DB SQLite temporal aislada.

Cubre:
- AnimalRepository: create, get_by_id, get_by_codigo, get_all, update, update_estado
- MuestraRepository: create, get_by_id, get_all, update_estado
- RecepcionRepository: create, get_by_id, get_all, update_estado, get_by_animal

Estos tests requieren que las tablas existan en la DB temporal.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from utils.exceptions import NotFoundError

# Asegurar que la raíz del repo esté en sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _setup_test_db() -> None:
    """Crea las tablas mínimas para tests de integración."""
    from config import DB_PATH
    from database.connection import DatabaseManager

    db = DatabaseManager()

    # Crear tablas necesarias
    db.execute("DROP TABLE IF EXISTS usuarios")
    db.execute("DROP TABLE IF EXISTS animales")
    db.execute("DROP TABLE IF EXISTS movimientos")
    db.execute("DROP TABLE IF EXISTS muestras")
    db.execute("DROP TABLE IF EXISTS recepciones")
    db.execute("DROP TABLE IF EXISTS cirugias")
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
        CREATE TABLE IF NOT EXISTS muestras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            animal_id INTEGER NOT NULL,
            empresa TEXT,
            tipo_muestra TEXT NOT NULL,
            tipo_analisis TEXT,
            fecha_recoleccion TEXT NOT NULL,
            fecha_entrega TEXT,
            estado TEXT DEFAULT 'Pendiente',
            resultado TEXT,
            valor_referencia TEXT,
            observaciones TEXT,
            tecnico TEXT,
            veterinario_ref TEXT,
            urgente INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
        CREATE TABLE IF NOT EXISTS codigo_contadores (
            prefijo TEXT PRIMARY KEY,
            ultimo INTEGER DEFAULT 0
        )
    """)

    # Inicializar contadores
    for p in ('ISAL', 'CONS', 'CIRU', 'VAC', 'PAC', 'LAB'):
        db.execute(
            "INSERT OR IGNORE INTO codigo_contadores (prefijo, ultimo) VALUES (?, 0)",
            (p,)
        )

    # Reset singleton
    DatabaseManager._instance = None
    DatabaseManager()


def _create_test_animal(
    codigo: str = "PAC-TEST-001",
    nombre: str = "Test Perro",
    especie: str = "Canino",
    estado: str = "Activo"
) -> int:
    """Crea un animal de prueba y retorna su ID."""
    from database.connection import DatabaseManager

    db = DatabaseManager()
    cursor = db.execute(
        "INSERT INTO animales (codigo, nombre, especie, fecha_ingreso, estado) VALUES (?, ?, ?, ?, ?)",
        (codigo, nombre, especie, "2026-01-01", estado)
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


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: ANIMAL REPOSITORY
# ══════════════════════════════════════════════════════════════════════════════

class TestAnimalRepository:
    """Tests de integración para AnimalRepository."""

    def test_create_animal(self):
        """Test: crear un animal en la base de datos."""
        from database.repositories import AnimalRepository
        from database.models import Animal

        repo = AnimalRepository()
        animal = Animal(
            codigo="PAC-INT-001",
            nombre="Buddy",
            especie="Canino",
            raza="Labrador",
            sexo="Macho",
            color="Dorado",
            peso=30.5,
            propietario="Juan Pérez",
            telefono="555-1234",
            fecha_ingreso="2026-01-15",
            estado="Activo"
        )

        animal_id = repo.create(animal)
        assert animal_id is not None
        assert animal_id > 0

    def test_get_by_id(self, test_animal_id):
        """Test: obtener animal por ID."""
        from database.repositories import AnimalRepository

        repo = AnimalRepository()
        animal = repo.get_by_id(test_animal_id)

        assert animal is not None
        assert animal.id == test_animal_id
        assert animal.codigo == "PAC-TEST-001"
        assert animal.nombre == "Test Perro"

    def test_get_by_id_not_found(self):
        """Test: obtener animal inexistente lanza error."""
        from database.repositories import AnimalRepository
        from utils.exceptions import NotFoundError

        repo = AnimalRepository()

        with pytest.raises(NotFoundError):
            repo.get_by_id(99999)

    def test_get_by_codigo(self, test_animal_id):
        """Test: obtener animal por código."""
        from database.repositories import AnimalRepository

        repo = AnimalRepository()
        animal = repo.get_by_codigo("PAC-TEST-001")

        assert animal is not None
        assert animal.codigo == "PAC-TEST-001"
        assert animal.nombre == "Test Perro"

    def test_get_by_codigo_not_found(self):
        """Test: obtener animal por código inexistente retorna None."""
        from database.repositories import AnimalRepository

        repo = AnimalRepository()
        animal = repo.get_by_codigo("PAC-NO-EXISTE")

        assert animal is None

    def test_get_all(self, test_animal_id):
        """Test: obtener todos los animales."""
        from database.repositories import AnimalRepository

        # Crear más animales
        _create_test_animal("PAC-TEST-002", "Luna", "Felino")
        _create_test_animal("PAC-TEST-003", "Rex", "Canino")

        repo = AnimalRepository()
        animales = repo.get_all()

        assert len(animales) >= 3

    def test_get_all_with_filter_estado(self, test_animal_id):
        """Test: obtener animales con filtro de estado."""
        from database.repositories import AnimalRepository

        # Crear animal inactivo
        _create_test_animal("PAC-TEST-004", "Max", "Canino", estado="Inactivo")

        repo = AnimalRepository()
        activos = repo.get_all(filtros={'estado': 'Activo'})

        assert len(activos) >= 1
        for a in activos:
            assert a.estado == 'Activo'

    def test_get_all_with_filter_especie(self, test_animal_id):
        """Test: obtener animales con filtro de especie."""
        from database.repositories import AnimalRepository

        _create_test_animal("PAC-TEST-005", "Michi", "Felino")

        repo = AnimalRepository()
        felinos = repo.get_all(filtros={'especie': 'Felino'})

        assert len(felinos) >= 1
        for a in felinos:
            assert a.especie == 'Felino'

    def test_get_all_with_filter_busqueda(self, test_animal_id):
        """Test: obtener animales con filtro de búsqueda."""
        from database.repositories import AnimalRepository

        _create_test_animal("PAC-TEST-006", "Buddy Jr", "Canino")
        _create_test_animal("PAC-TEST-006B", "Buddy Senior", "Canino")

        repo = AnimalRepository()
        resultados = repo.get_all(filtros={'busqueda': 'Buddy'})

        assert len(resultados) >= 2

    def test_get_all_with_limit(self, test_animal_id):
        """Test: obtener animales con límite."""
        from database.repositories import AnimalRepository

        _create_test_animal("PAC-TEST-007", "Perro 1", "Canino")
        _create_test_animal("PAC-TEST-008", "Perro 2", "Canino")
        _create_test_animal("PAC-TEST-009", "Perro 3", "Canino")

        repo = AnimalRepository()
        animales = repo.get_all(limit=2)

        assert len(animales) <= 2

    def test_update_animal(self, test_animal_id):
        """Test: actualizar datos de animal."""
        from database.repositories import AnimalRepository
        from database.models import Animal

        repo = AnimalRepository()
        animal = repo.get_by_id(test_animal_id)

        # Modificar datos
        animal.nombre = "Test Perro Actualizado"
        animal.peso = 25.0
        animal.telefono = "555-9999"
        animal.observaciones = "Actualizado en test"

        repo.update(animal)

        # Verificar cambios
        animal_actualizado = repo.get_by_id(test_animal_id)
        assert animal_actualizado.nombre == "Test Perro Actualizado"
        assert animal_actualizado.peso == 25.0
        assert animal_actualizado.telefono == "555-9999"

    def test_update_estado(self, test_animal_id):
        """Test: actualizar solo el estado del animal."""
        from database.repositories import AnimalRepository

        repo = AnimalRepository()
        repo.update_estado(test_animal_id, "Dado de Alta")

        animal = repo.get_by_id(test_animal_id)
        assert animal.estado == "Dado de Alta"

    def test_get_max_id(self, test_animal_id):
        """Test: obtener el máximo ID de animales."""
        from database.repositories import AnimalRepository

        _create_test_animal("PAC-TEST-010", "Último", "Canino")

        repo = AnimalRepository()
        max_id = repo.get_max_id()

        assert max_id >= test_animal_id


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: MUESTRA REPOSITORY
# ══════════════════════════════════════════════════════════════════════════════

class TestMuestraRepository:
    """Tests de integración para MuestraRepository."""

    def test_create_muestra(self, test_animal_id):
        """Test: crear una muestra en la base de datos."""
        from database.repositories import MuestraRepository
        from database.models import Muestra

        repo = MuestraRepository()
        muestra = Muestra(
            codigo="LAB-INT-001",
            animal_id=test_animal_id,
            tipo_muestra="Sangre",
            fecha_recoleccion="2026-01-20",
            tecnico="Tech Test",
            urgente=0,
            estado="Pendiente"
        )

        muestra_id = repo.create(muestra)
        assert muestra_id is not None
        assert muestra_id > 0

    def test_get_by_id(self, test_animal_id):
        """Test: obtener muestra por ID."""
        from database.repositories import MuestraRepository
        from database.models import Muestra

        repo = MuestraRepository()
        muestra = Muestra(
            codigo="LAB-INT-002",
            animal_id=test_animal_id,
            tipo_muestra="Orina",
            fecha_recoleccion="2026-01-21"
        )

        muestra_id = repo.create(muestra)
        muestra_obtenida = repo.get_by_id(muestra_id)

        assert muestra_obtenida is not None
        assert muestra_obtenida.codigo == "LAB-INT-002"
        assert muestra_obtenida.tipo_muestra == "Orina"

    def test_get_by_id_not_found(self):
        """Test: obtener muestra inexistente lanza error."""
        from database.repositories import MuestraRepository
        from utils.exceptions import NotFoundError

        repo = MuestraRepository()

        with pytest.raises(NotFoundError):
            repo.get_by_id(99999)

    def test_get_all(self, test_animal_id):
        """Test: obtener todas las muestras."""
        from database.repositories import MuestraRepository
        from database.models import Muestra

        repo = MuestraRepository()

        # Crear varias muestras
        for i in range(3):
            muestra = Muestra(
                codigo=f"LAB-INT-{100+i}",
                animal_id=test_animal_id,
                tipo_muestra="Sangre",
                fecha_recoleccion=f"2026-01-{20+i}"
            )
            repo.create(muestra)

        muestras = repo.get_all()
        assert len(muestras) >= 3

    def test_get_all_with_filter_estado(self, test_animal_id):
        """Test: obtener muestras con filtro de estado."""
        from database.repositories import MuestraRepository
        from database.models import Muestra

        repo = MuestraRepository()

        # Crear muestra en proceso
        muestra = Muestra(
            codigo="LAB-INT-010",
            animal_id=test_animal_id,
            tipo_muestra="Heces",
            fecha_recoleccion="2026-01-25",
            estado="En Proceso"
        )
        repo.create(muestra)

        # Crear muestra pendiente
        muestra2 = Muestra(
            codigo="LAB-INT-011",
            animal_id=test_animal_id,
            tipo_muestra="Orina",
            fecha_recoleccion="2026-01-26",
            estado="Pendiente"
        )
        repo.create(muestra2)

        en_proceso = repo.get_all(filtros={'estado': 'En Proceso'})
        assert len(en_proceso) >= 1
        for m in en_proceso:
            assert m.estado == 'En Proceso'

    def test_get_all_with_filter_urgente(self, test_animal_id):
        """Test: obtener muestras urgentes."""
        from database.repositories import MuestraRepository
        from database.models import Muestra

        repo = MuestraRepository()

        # Crear muestra urgente
        muestra = Muestra(
            codigo="LAB-INT-012",
            animal_id=test_animal_id,
            tipo_muestra="Sangre",
            fecha_recoleccion="2026-01-27",
            urgente=1
        )
        repo.create(muestra)

        urgentes = repo.get_all(filtros={'urgente': True})
        assert len(urgentes) >= 1
        for m in urgentes:
            assert m.urgente == 1

    def test_update_estado(self, test_animal_id):
        """Test: actualizar estado de muestra."""
        from database.repositories import MuestraRepository
        from database.models import Muestra

        repo = MuestraRepository()
        muestra = Muestra(
            codigo="LAB-INT-013",
            animal_id=test_animal_id,
            tipo_muestra="Sangre",
            fecha_recoleccion="2026-01-28"
        )

        muestra_id = repo.create(muestra)
        repo.update_estado(muestra_id, "Completado", resultado="Normal", valor_ref="37-55%")

        muestra_actualizada = repo.get_by_id(muestra_id)
        assert muestra_actualizada.estado == "Completado"
        assert muestra_actualizada.resultado == "Normal"


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: RECEPCION REPOSITORY
# ══════════════════════════════════════════════════════════════════════════════

class TestRecepcionRepository:
    """Tests de integración para RecepcionRepository."""

    def test_create_recepcion(self, test_animal_id):
        """Test: crear una recepción en la base de datos."""
        from database.repositories import RecepcionRepository
        from database.models import Recepcion

        repo = RecepcionRepository()
        recepcion = Recepcion(
            codigo="ISAL-INT-001",
            animal_id=test_animal_id,
            fecha_hora="2026-01-15 10:00:00",
            motivo="Consulta general",
            veterinario="Dr. Test",
            estado="En espera"
        )

        recepcion_id = repo.create(recepcion)
        assert recepcion_id is not None
        assert recepcion_id > 0

    def test_get_by_id(self, test_animal_id):
        """Test: obtener recepción por ID."""
        from database.repositories import RecepcionRepository
        from database.models import Recepcion

        repo = RecepcionRepository()
        recepcion = Recepcion(
            codigo="ISAL-INT-002",
            animal_id=test_animal_id,
            fecha_hora="2026-01-16 11:00:00",
            motivo="Vacunación",
            veterinario="Dr. Test"
        )

        recepcion_id = repo.create(recepcion)
        recepcion_obtenida = repo.get_by_id(recepcion_id)

        assert recepcion_obtenida is not None
        assert recepcion_obtenida.codigo == "ISAL-INT-002"
        assert recepcion_obtenida.motivo == "Vacunación"

    def test_get_by_id_not_found(self):
        """Test: obtener recepción inexistente lanza error."""
        from database.repositories import RecepcionRepository
        from utils.exceptions import NotFoundError

        repo = RecepcionRepository()

        with pytest.raises(NotFoundError):
            repo.get_by_id(99999)

    def test_get_all(self, test_animal_id):
        """Test: obtener todas las recepciones."""
        from database.repositories import RecepcionRepository
        from database.models import Recepcion

        repo = RecepcionRepository()

        # Crear varias recepciones
        for i in range(3):
            recepcion = Recepcion(
                codigo=f"ISAL-INT-{100+i}",
                animal_id=test_animal_id,
                fecha_hora=f"2026-01-{15+i} 10:00:00",
                motivo=f"Motivo {i+1}",
                veterinario="Dr. Test"
            )
            repo.create(recepcion)

        recepciones = repo.get_all()
        assert len(recepciones) >= 3

    def test_get_all_with_filter_estado(self, test_animal_id):
        """Test: obtener recepciones con filtro de estado."""
        from database.repositories import RecepcionRepository
        from database.models import Recepcion

        repo = RecepcionRepository()

        # Crear recepción en espera
        recepcion = Recepcion(
            codigo="ISAL-INT-020",
            animal_id=test_animal_id,
            fecha_hora="2026-01-20 09:00:00",
            motivo="Urgencia",
            estado="En espera"
        )
        repo.create(recepcion)

        # Crear recepción atendida
        recepcion2 = Recepcion(
            codigo="ISAL-INT-021",
            animal_id=test_animal_id,
            fecha_hora="2026-01-21 10:00:00",
            motivo="Control",
            estado="Atendido"
        )
        repo.create(recepcion2)

        en_espera = repo.get_all(filtros={'estado': 'En espera'})
        assert len(en_espera) >= 1
        for r in en_espera:
            assert r.estado == 'En espera'

    def test_get_all_with_filter_animal(self, test_animal_id):
        """Test: obtener recepciones de un animal específico."""
        from database.repositories import RecepcionRepository
        from database.models import Recepcion

        # Crear segundo animal
        animal2_id = _create_test_animal("PAC-TEST-020", "Luna", "Felino")

        repo = RecepcionRepository()

        # Crear recepciones para ambos animales
        repo.create(Recepcion(
            codigo="ISAL-INT-030",
            animal_id=test_animal_id,
            fecha_hora="2026-01-22 10:00:00",
            motivo="Animal 1"
        ))
        repo.create(Recepcion(
            codigo="ISAL-INT-031",
            animal_id=animal2_id,
            fecha_hora="2026-01-22 11:00:00",
            motivo="Animal 2"
        ))

        recepciones_animal1 = repo.get_all(filtros={'animal_id': test_animal_id})
        assert len(recepciones_animal1) >= 1
        for r in recepciones_animal1:
            assert r.animal_id == test_animal_id

    def test_get_all_with_filter_busqueda(self, test_animal_id):
        """Test: obtener recepciones con filtro de búsqueda."""
        from database.repositories import RecepcionRepository
        from database.models import Recepcion

        repo = RecepcionRepository()

        repo.create(Recepcion(
            codigo="ISAL-INT-040",
            animal_id=test_animal_id,
            fecha_hora="2026-01-23 10:00:00",
            motivo="Cirugía programada"
        ))

        resultados = repo.get_all(filtros={'busqueda': 'Cirugía'})
        assert len(resultados) >= 1
        # Verificar que el término de búsqueda está en los resultados
        for r in resultados:
            assert 'Cirugía' in r.motivo or 'Cirugía' in r.codigo

    def test_update_estado(self, test_animal_id):
        """Test: actualizar estado de recepción."""
        from database.repositories import RecepcionRepository
        from database.models import Recepcion

        repo = RecepcionRepository()
        recepcion = Recepcion(
            codigo="ISAL-INT-050",
            animal_id=test_animal_id,
            fecha_hora="2026-01-24 10:00:00",
            motivo="Pendiente de revisión"
        )

        recepcion_id = repo.create(recepcion)
        repo.update_estado(recepcion_id, "Atendido", proxima_cita="2026-02-01")

        recepcion_actualizada = repo.get_by_id(recepcion_id)
        assert recepcion_actualizada.estado == "Atendido"
        assert recepcion_actualizada.proxima_cita == "2026-02-01"

    def test_get_by_animal(self, test_animal_id):
        """Test: obtener recepciones por animal."""
        from database.repositories import RecepcionRepository
        from database.models import Recepcion

        repo = RecepcionRepository()

        # Crear recepciones para el mismo animal
        for i in range(2):
            repo.create(Recepcion(
                codigo=f"ISAL-INT-{60+i}",
                animal_id=test_animal_id,
                fecha_hora=f"2026-01-{25+i} 10:00:00",
                motivo=f"Visita {i+1}"
            ))

        recepciones = repo.get_by_animal(test_animal_id)
        assert len(recepciones) >= 2
        for r in recepciones:
            assert r.animal_id == test_animal_id

    def test_generar_codigo(self):
        """Test: generación de código de recepción."""
        from database.repositories import RecepcionRepository

        repo = RecepcionRepository()
        codigo1 = repo.generar_codigo()
        codigo2 = repo.generar_codigo()

        assert codigo1.startswith('ISAL-')
        assert codigo1 != codigo2


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: CIRUGIA REPOSITORY
# ══════════════════════════════════════════════════════════════════════════════

class TestCirugiaRepository:
    """Tests de integración para CirugiaRepository."""

    def test_create_cirugia(self, test_animal_id):
        """Test: crear una cirugía en la base de datos."""
        from database.repositories import CirugiaRepository
        from database.models import Cirugia

        repo = CirugiaRepository()
        cirugia = Cirugia(
            codigo="CIRU-INT-001",
            animal_id=test_animal_id,
            fecha="2026-02-01",
            tipo_cirugia="Castración",
            cirujano="Dr. Test",
            estado="Programada"
        )

        cirugia_id = repo.create(cirugia)
        assert cirugia_id is not None
        assert cirugia_id > 0

    def test_get_by_id(self, test_animal_id):
        """Test: obtener cirugía por ID."""
        from database.repositories import CirugiaRepository
        from database.models import Cirugia

        repo = CirugiaRepository()
        cirugia = Cirugia(
            codigo="CIRU-INT-002",
            animal_id=test_animal_id,
            fecha="2026-02-02",
            tipo_cirugia="Laparotomía"
        )

        cirugia_id = repo.create(cirugia)
        cirugia_obtenida = repo.get_by_id(cirugia_id)

        assert cirugia_obtenida is not None
        assert cirugia_obtenida.codigo == "CIRU-INT-002"
        assert cirugia_obtenida.tipo_cirugia == "Laparotomía"

    def test_get_by_id_not_found(self):
        """Test: obtener cirugía inexistente lanza error."""
        from database.repositories import CirugiaRepository
        from utils.exceptions import NotFoundError

        repo = CirugiaRepository()

        with pytest.raises(NotFoundError):
            repo.get_by_id(99999)

    def test_get_all(self, test_animal_id):
        """Test: obtener todas las cirugías."""
        from database.repositories import CirugiaRepository
        from database.models import Cirugia

        repo = CirugiaRepository()

        for i in range(3):
            repo.create(Cirugia(
                codigo=f"CIRU-INT-{100+i}",
                animal_id=test_animal_id,
                fecha=f"2026-02-{1+i:02d}",
                tipo_cirugia=f"Cirugía {i+1}"
            ))

        cirugias = repo.get_all()
        assert len(cirugias) >= 3

    def test_get_all_with_filter_estado(self, test_animal_id):
        """Test: obtener cirugías con filtro de estado."""
        from database.repositories import CirugiaRepository
        from database.models import Cirugia

        repo = CirugiaRepository()

        repo.create(Cirugia(
            codigo="CIRU-INT-010",
            animal_id=test_animal_id,
            fecha="2026-02-10",
            tipo_cirugia="Cirugía Programada",
            estado="Programada"
        ))
        repo.create(Cirugia(
            codigo="CIRU-INT-011",
            animal_id=test_animal_id,
            fecha="2026-02-11",
            tipo_cirugia="Cirugía Completada",
            estado="Completada"
        ))

        programadas = repo.get_all(filtros={'estado': 'Programada'})
        assert len(programadas) >= 1
        for c in programadas:
            assert c.estado == 'Programada'

    def test_get_by_animal(self, test_animal_id):
        """Test: obtener cirugías por animal."""
        from database.repositories import CirugiaRepository
        from database.models import Cirugia

        repo = CirugiaRepository()

        for i in range(2):
            repo.create(Cirugia(
                codigo=f"CIRU-INT-{20+i}",
                animal_id=test_animal_id,
                fecha=f"2026-02-{15+i:02d}",
                tipo_cirugia=f"Cirugía Animal {i+1}"
            ))

        cirugias = repo.get_by_animal(test_animal_id)
        assert len(cirugias) >= 2
        for c in cirugias:
            assert c.animal_id == test_animal_id

    def test_update_estado(self, test_animal_id):
        """Test: actualizar estado de cirugía."""
        from database.repositories import CirugiaRepository
        from database.models import Cirugia

        repo = CirugiaRepository()
        cirugia = Cirugia(
            codigo="CIRU-INT-030",
            animal_id=test_animal_id,
            fecha="2026-02-20",
            tipo_cirugia="Cirugía Estado"
        )

        cirugia_id = repo.create(cirugia)
        repo.update_estado(cirugia_id, "En Proceso")

        cirugia_actualizada = repo.get_by_id(cirugia_id)
        assert cirugia_actualizada.estado == "En Proceso"

    def test_update_cirugia(self, test_animal_id):
        """Test: actualizar datos de cirugía."""
        from database.repositories import CirugiaRepository
        from database.models import Cirugia

        repo = CirugiaRepository()
        cirugia = Cirugia(
            codigo="CIRU-INT-040",
            animal_id=test_animal_id,
            fecha="2026-02-25",
            tipo_cirugia="Cirugía Original",
            cirujano="Dr. Original"
        )

        cirugia_id = repo.create(cirugia)
        cirugia.id = cirugia_id
        cirugia.tipo_cirugia = "Cirugía Actualizada"
        cirugia.cirujano = "Dr. Actualizado"
        cirugia.duracion_min = 120

        repo.update(cirugia)

        cirugia_obtenida = repo.get_by_id(cirugia_id)
        assert cirugia_obtenida.tipo_cirugia == "Cirugía Actualizada"
        assert cirugia_obtenida.cirujano == "Dr. Actualizado"
        assert cirugia_obtenida.duracion_min == 120

    def test_generar_codigo(self):
        """Test: generación de código de cirugía."""
        from database.repositories import CirugiaRepository

        repo = CirugiaRepository()
        codigo1 = repo.generar_codigo()
        codigo2 = repo.generar_codigo()

        assert codigo1.startswith('CIRU-')
        assert codigo1 != codigo2


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: MOVIMIENTO REPOSITORY
# ══════════════════════════════════════════════════════════════════════════════

class TestMovimientoRepository:
    """Tests de integración para MovimientoRepository."""

    def test_create_movimiento(self, test_animal_id):
        """Test: crear un movimiento en la base de datos."""
        from database.repositories import MovimientoRepository
        from database.models import Movimiento

        repo = MovimientoRepository()
        movimiento = Movimiento(
            animal_id=test_animal_id,
            tipo="Entrada",
            motivo="Ingreso inicial",
            responsable="Sistema"
        )

        movimiento_id = repo.create(movimiento)
        assert movimiento_id is not None
        assert movimiento_id > 0

    def test_get_by_animal(self, test_animal_id):
        """Test: obtener movimientos por animal."""
        from database.repositories import MovimientoRepository
        from database.models import Movimiento

        repo = MovimientoRepository()

        # Crear varios movimientos
        for i in range(3):
            repo.create(Movimiento(
                animal_id=test_animal_id,
                tipo="Entrada" if i % 2 == 0 else "Salida",
                motivo=f"Movimiento {i+1}",
                responsable="Test"
            ))

        movimientos = repo.get_by_animal(test_animal_id)
        assert len(movimientos) >= 3
        for m in movimientos:
            assert m.animal_id == test_animal_id


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: BASE REPOSITORY
# ══════════════════════════════════════════════════════════════════════════════

class TestBaseRepository:
    """Tests de integración para BaseRepository - sesión y transacciones."""

    def test_session_commit_on_success(self, test_animal_id):
        """Test: la sesión hace commit cuando todo sale bien."""
        from database.repositories import AnimalRepository
        from database.models import Animal

        repo = AnimalRepository()
        animal = Animal(
            codigo="PAC-BASE-001",
            nombre="Commit Test",
            especie="Canino",
            fecha_ingreso="2026-01-01"
        )

        animal_id = repo.create(animal)
        
        # Verificar que el animal fue guardado
        animal_guardado = repo.get_by_id(animal_id)
        assert animal_guardado.codigo == "PAC-BASE-001"

    def test_session_rollback_on_error(self, test_animal_id):
        """Test: la sesión hace rollback cuando hay error."""
        from database.repositories import AnimalRepository
        from database.models import Animal

        repo = AnimalRepository()

        # Intentar crear animal con código duplicado
        animal1 = Animal(
            codigo="PAC-BASE-002",
            nombre="Original",
            especie="Canino",
            fecha_ingreso="2026-01-01"
        )
        repo.create(animal1)

        animal2 = Animal(
            codigo="PAC-BASE-002",  # Duplicado
            nombre="Duplicado",
            especie="Felino",
            fecha_ingreso="2026-01-02"
        )

        # Debe fallar por UNIQUE constraint
        with pytest.raises(Exception):
            repo.create(animal2)

        # Verificar que el primer animal sigue existiendo
        animal_original = repo.get_by_codigo("PAC-BASE-002")
        assert animal_original.nombre == "Original"


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: CONSULTA REPOSITORY
# ══════════════════════════════════════════════════════════════════════════════

class TestConsultaRepository:
    """Tests de integración para ConsultaRepository."""

    def test_create_consulta(self, test_animal_id):
        """Test: crear una consulta en la base de datos."""
        from database.repositories import ConsultaRepository
        from database.models import Consulta

        repo = ConsultaRepository()
        consulta = Consulta(
            codigo="CONS-INT-001",
            animal_id=test_animal_id,
            fecha="2026-03-01",
            motivo="Dolor estomacal",
            veterinario="Dr. Test"
        )

        consulta_id = repo.create(consulta)
        assert consulta_id is not None
        assert consulta_id > 0

    def test_get_by_id(self, test_animal_id):
        """Test: obtener consulta por ID."""
        from database.repositories import ConsultaRepository
        from database.models import Consulta

        repo = ConsultaRepository()
        consulta = Consulta(
            codigo="CONS-INT-002",
            animal_id=test_animal_id,
            fecha="2026-03-02",
            motivo="Control de rutina"
        )

        consulta_id = repo.create(consulta)
        consulta_obtenida = repo.get_by_id(consulta_id)

        assert consulta_obtenida is not None
        assert consulta_obtenida.codigo == "CONS-INT-002"
        assert consulta_obtenida.motivo == "Control de rutina"

    def test_get_by_id_not_found(self):
        """Test: obtener consulta inexistente lanza error."""
        from database.repositories import ConsultaRepository

        repo = ConsultaRepository()

        with pytest.raises(NotFoundError):
            repo.get_by_id(99999)

    def test_get_all(self, test_animal_id):
        """Test: obtener todas las consultas."""
        from database.repositories import ConsultaRepository
        from database.models import Consulta

        repo = ConsultaRepository()

        for i in range(3):
            repo.create(Consulta(
                codigo=f"CONS-INT-{100+i}",
                animal_id=test_animal_id,
                fecha=f"2026-03-{1+i:02d}",
                motivo=f"Consulta {i+1}"
            ))

        consultas = repo.get_all()
        assert len(consultas) >= 3

    def test_get_all_with_filter_animal(self, test_animal_id):
        """Test: obtener consultas con filtro de animal."""
        from database.repositories import ConsultaRepository
        from database.models import Consulta

        animal2_id = _create_test_animal("PAC-TEST-030", "Luna", "Felino")

        repo = ConsultaRepository()

        repo.create(Consulta(
            codigo="CONS-INT-020",
            animal_id=test_animal_id,
            fecha="2026-03-10",
            motivo="Animal 1"
        ))
        repo.create(Consulta(
            codigo="CONS-INT-021",
            animal_id=animal2_id,
            fecha="2026-03-11",
            motivo="Animal 2"
        ))

        consultas = repo.get_all(filtros={'animal_id': test_animal_id})
        assert len(consultas) >= 1
        for c in consultas:
            assert c.animal_id == test_animal_id

    def test_get_by_animal(self, test_animal_id):
        """Test: obtener consultas por animal."""
        from database.repositories import ConsultaRepository
        from database.models import Consulta

        repo = ConsultaRepository()

        for i in range(2):
            repo.create(Consulta(
                codigo=f"CONS-INT-{30+i}",
                animal_id=test_animal_id,
                fecha=f"2026-03-{15+i:02d}",
                motivo=f"Visita {i+1}"
            ))

        consultas = repo.get_by_animal(test_animal_id)
        assert len(consultas) >= 2
        for c in consultas:
            assert c.animal_id == test_animal_id

    def test_update_consulta(self, test_animal_id):
        """Test: actualizar datos de consulta."""
        from database.repositories import ConsultaRepository
        from database.models import Consulta

        repo = ConsultaRepository()
        consulta = Consulta(
            codigo="CONS-INT-040",
            animal_id=test_animal_id,
            fecha="2026-03-20",
            motivo="Consulta Original"
        )

        consulta_id = repo.create(consulta)
        consulta.id = consulta_id
        consulta.motivo = "Consulta Actualizada"
        consulta.tratamiento = "Medicación oral"

        repo.update(consulta)

        consulta_obtenida = repo.get_by_id(consulta_id)
        assert consulta_obtenida.motivo == "Consulta Actualizada"
        assert consulta_obtenida.tratamiento == "Medicación oral"

    def test_generar_codigo(self):
        """Test: generación de código de consulta."""
        from database.repositories import ConsultaRepository

        repo = ConsultaRepository()
        codigo1 = repo.generar_codigo()
        codigo2 = repo.generar_codigo()

        assert codigo1.startswith('CONS-')
        assert codigo1 != codigo2


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: VACUNACION REPOSITORY
# ══════════════════════════════════════════════════════════════════════════════

class TestVacunacionRepository:
    """Tests de integración para VacunacionRepository."""

    def test_create_vacunacion(self, test_animal_id):
        """Test: crear una vacunación en la base de datos."""
        from database.repositories import VacunacionRepository
        from database.models import Vacunacion

        repo = VacunacionRepository()
        vacunacion = Vacunacion(
            codigo="VAC-INT-001",
            animal_id=test_animal_id,
            tipo="Vacuna",
            producto="Rabia",
            fecha_aplicacion="2026-03-01",
            veterinario="Dr. Test"
        )

        vacunacion_id = repo.create(vacunacion)
        assert vacunacion_id is not None
        assert vacunacion_id > 0

    def test_get_by_id(self, test_animal_id):
        """Test: obtener vacunación por ID."""
        from database.repositories import VacunacionRepository
        from database.models import Vacunacion

        repo = VacunacionRepository()
        vacunacion = Vacunacion(
            codigo="VAC-INT-002",
            animal_id=test_animal_id,
            tipo="Desparasitación",
            producto="Pyrantel",
            fecha_aplicacion="2026-03-02"
        )

        vacunacion_id = repo.create(vacunacion)
        vacunacion_obtenida = repo.get_by_id(vacunacion_id)

        assert vacunacion_obtenida is not None
        assert vacunacion_obtenida.codigo == "VAC-INT-002"
        assert vacunacion_obtenida.producto == "Pyrantel"

    def test_get_by_id_not_found(self):
        """Test: obtener vacunación inexistente lanza error."""
        from database.repositories import VacunacionRepository

        repo = VacunacionRepository()

        with pytest.raises(NotFoundError):
            repo.get_by_id(99999)

    def test_get_all(self, test_animal_id):
        """Test: obtener todas las vacunaciones."""
        from database.repositories import VacunacionRepository
        from database.models import Vacunacion

        repo = VacunacionRepository()

        for i in range(3):
            repo.create(Vacunacion(
                codigo=f"VAC-INT-{100+i}",
                animal_id=test_animal_id,
                tipo="Vacuna",
                producto=f"Vacuna {i+1}",
                fecha_aplicacion=f"2026-03-{1+i:02d}"
            ))

        vacunaciones = repo.get_all()
        assert len(vacunaciones) >= 3

    def test_get_all_with_filter_tipo(self, test_animal_id):
        """Test: obtener vacunaciones con filtro de tipo."""
        from database.repositories import VacunacionRepository
        from database.models import Vacunacion

        repo = VacunacionRepository()

        repo.create(Vacunacion(
            codigo="VAC-INT-010",
            animal_id=test_animal_id,
            tipo="Vacuna",
            producto="Rabia",
            fecha_aplicacion="2026-03-10"
        ))
        repo.create(Vacunacion(
            codigo="VAC-INT-011",
            animal_id=test_animal_id,
            tipo="Desparasitación",
            producto="Pyrantel",
            fecha_aplicacion="2026-03-11"
        ))

        vacunas = repo.get_all(filtros={'tipo': 'Vacuna'})
        assert len(vacunas) >= 1
        for v in vacunas:
            assert v.tipo == 'Vacuna'

    def test_get_by_animal(self, test_animal_id):
        """Test: obtener vacunaciones por animal."""
        from database.repositories import VacunacionRepository
        from database.models import Vacunacion

        repo = VacunacionRepository()

        for i in range(2):
            repo.create(Vacunacion(
                codigo=f"VAC-INT-{20+i}",
                animal_id=test_animal_id,
                tipo="Vacuna",
                producto=f"Vacuna Animal {i+1}",
                fecha_aplicacion=f"2026-03-{15+i:02d}"
            ))

        vacunaciones = repo.get_by_animal(test_animal_id)
        assert len(vacunaciones) >= 2
        for v in vacunaciones:
            assert v.animal_id == test_animal_id

    def test_generar_codigo(self):
        """Test: generación de código de vacunación."""
        from database.repositories import VacunacionRepository

        repo = VacunacionRepository()
        codigo1 = repo.generar_codigo()
        codigo2 = repo.generar_codigo()

        assert codigo1.startswith('VAC-')
        assert codigo1 != codigo2


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: HISTORIA CLINICA REPOSITORY
# ══════════════════════════════════════════════════════════════════════════════

class TestHistoriaClinicaRepository:
    """Tests de integración para HistoriaClinicaRepository."""

    def test_create_historia(self, test_animal_id):
        """Test: crear una historia clínica en la base de datos."""
        from database.repositories import HistoriaClinicaRepository, RecepcionRepository
        from database.models import HistoriaClinica, Recepcion

        # Primero crear una recepción
        recepcion_repo = RecepcionRepository()
        recepcion = Recepcion(
            codigo="ISAL-HIST-001",
            animal_id=test_animal_id,
            fecha_hora="2026-03-01 10:00:00",
            motivo="Primera visita"
        )
        recepcion_id = recepcion_repo.create(recepcion)

        repo = HistoriaClinicaRepository()
        historia = HistoriaClinica(
            recepcion_id=recepcion_id,
            animal_id=test_animal_id,
            fecha="2026-03-01",
            anamnesis="Mascota trae por dolor",
            diagnostico="Gastritis",
            tratamiento="Dieta blanda"
        )

        historia_id = repo.create(historia)
        assert historia_id is not None
        assert historia_id > 0

    def test_get_by_id(self, test_animal_id):
        """Test: obtener historia clínica por ID."""
        from database.repositories import HistoriaClinicaRepository, RecepcionRepository
        from database.models import HistoriaClinica, Recepcion

        recepcion_repo = RecepcionRepository()
        recepcion = Recepcion(
            codigo="ISAL-HIST-002",
            animal_id=test_animal_id,
            fecha_hora="2026-03-02 11:00:00",
            motivo="Control"
        )
        recepcion_id = recepcion_repo.create(recepcion)

        repo = HistoriaClinicaRepository()
        historia = HistoriaClinica(
            recepcion_id=recepcion_id,
            animal_id=test_animal_id,
            fecha="2026-03-02",
            diagnostico="Sano"
        )

        historia_id = repo.create(historia)
        historia_obtenida = repo.get_by_id(historia_id)

        assert historia_obtenida is not None
        assert historia_obtenida.diagnostico == "Sano"

    def test_get_by_id_not_found(self):
        """Test: obtener historia clínica inexistente lanza error."""
        from database.repositories import HistoriaClinicaRepository

        repo = HistoriaClinicaRepository()

        with pytest.raises(NotFoundError):
            repo.get_by_id(99999)

    def test_get_by_animal(self, test_animal_id):
        """Test: obtener historias clínicas por animal."""
        from database.repositories import HistoriaClinicaRepository, RecepcionRepository
        from database.models import HistoriaClinica, Recepcion

        recepcion_repo = RecepcionRepository()
        repo = HistoriaClinicaRepository()

        for i in range(2):
            recepcion = Recepcion(
                codigo=f"ISAL-HIST-{10+i}",
                animal_id=test_animal_id,
                fecha_hora=f"2026-03-{10+i} 10:00:00",
                motivo=f"Visita {i+1}"
            )
            recepcion_id = recepcion_repo.create(recepcion)

            repo.create(HistoriaClinica(
                recepcion_id=recepcion_id,
                animal_id=test_animal_id,
                fecha=f"2026-03-{10+i}",
                diagnostico=f"Diagnóstico {i+1}"
            ))

        historias = repo.get_by_animal(test_animal_id)
        assert len(historias) >= 2
        for h in historias:
            assert h.animal_id == test_animal_id

    def test_get_by_recepcion(self, test_animal_id):
        """Test: obtener historia clínica por recepción."""
        from database.repositories import HistoriaClinicaRepository, RecepcionRepository
        from database.models import HistoriaClinica, Recepcion

        recepcion_repo = RecepcionRepository()
        recepcion = Recepcion(
            codigo="ISAL-HIST-020",
            animal_id=test_animal_id,
            fecha_hora="2026-03-20 10:00:00",
            motivo="Consulta específica"
        )
        recepcion_id = recepcion_repo.create(recepcion)

        repo = HistoriaClinicaRepository()
        repo.create(HistoriaClinica(
            recepcion_id=recepcion_id,
            animal_id=test_animal_id,
            fecha="2026-03-20",
            diagnostico="Historia de recepción"
        ))

        historia = repo.get_by_recepcion(recepcion_id)
        assert historia is not None
        assert historia.recepcion_id == recepcion_id

    def test_update_historia(self, test_animal_id):
        """Test: actualizar datos de historia clínica."""
        from database.repositories import HistoriaClinicaRepository, RecepcionRepository
        from database.models import HistoriaClinica, Recepcion

        recepcion_repo = RecepcionRepository()
        recepcion = Recepcion(
            codigo="ISAL-HIST-030",
            animal_id=test_animal_id,
            fecha_hora="2026-03-25 10:00:00",
            motivo="Seguimiento"
        )
        recepcion_id = recepcion_repo.create(recepcion)

        repo = HistoriaClinicaRepository()
        historia = HistoriaClinica(
            recepcion_id=recepcion_id,
            animal_id=test_animal_id,
            fecha="2026-03-25",
            diagnostico="Original"
        )

        historia_id = repo.create(historia)
        historia.id = historia_id
        historia.diagnostico = "Actualizado"
        historia.tratamiento = "Nuevo tratamiento"

        repo.update(historia)

        historia_obtenida = repo.get_by_id(historia_id)
        assert historia_obtenida.diagnostico == "Actualizado"
        assert historia_obtenida.tratamiento == "Nuevo tratamiento"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
