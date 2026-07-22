"""
Tests unitarios comprehensivos para los services principales de IsaLab.

Cubre:
- UsuarioService: autenticación, CRUD, cambio de contraseña, RBAC
- AnimalService: registro, actualización, validación de datos
- MuestraService: registro, actualización de estado, validación
- CirugiaService: programación, actualización, validación

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


def _create_test_user(
    username: str = "testuser",
    password: str = "Test1234!",
    nombre: str = "Test User",
    rol: str = "usuario"
) -> int:
    """Crea un usuario de prueba y retorna su ID."""
    from database.connection import DatabaseManager
    from utils.security import hash_password

    db = DatabaseManager()
    pwd_hash = hash_password(password)
    cursor = db.execute(
        "INSERT INTO usuarios (username, password_hash, nombre, rol) VALUES (?, ?, ?, ?)",
        (username, pwd_hash, nombre, rol)
    )
    return cursor.lastrowid


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
def admin_user():
    """Usuario administrador para tests de RBAC."""
    user_id = _create_test_user(
        username="admin",
        password="Admin1234!",
        nombre="Admin Test",
        rol="admin"
    )
    return {"id": user_id, "username": "admin", "rol": "admin"}


@pytest.fixture
def vet_user():
    """Usuario veterinario para tests de RBAC."""
    user_id = _create_test_user(
        username="vet1",
        password="Vet1234!",
        nombre="Vet Test",
        rol="veterinario"
    )
    return {"id": user_id, "username": "vet1", "rol": "veterinario"}


@pytest.fixture
def test_animal():
    """Animal de prueba para tests."""
    animal_id = _create_test_animal()
    return animal_id


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: USUARIO SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class TestUsuarioService:
    """Tests para UsuarioService - Autenticación y CRUD."""

    def test_autenticar_usuario_exitoso(self, admin_user):
        """Test: autenticación exitosa con credenciales correctas."""
        from services.usuario_service import UsuarioService

        svc = UsuarioService()
        result = svc.autenticar("admin", "Admin1234!")

        assert result is not None
        assert result['username'] == "admin"
        assert result['rol'] == "admin"
        assert 'id' in result

    def test_autenticar_usuario_fallido_password(self, admin_user):
        """Test: autenticación fallida con contraseña incorrecta."""
        from services.usuario_service import UsuarioService
        from utils.exceptions import AuthenticationError

        svc = UsuarioService()

        with pytest.raises(AuthenticationError):
            svc.autenticar("admin", "WrongPassword123!")

    def test_autenticar_usuario_no_existe(self):
        """Test: autenticación fallida con usuario inexistente."""
        from services.usuario_service import UsuarioService
        from utils.exceptions import AuthenticationError

        svc = UsuarioService()

        with pytest.raises(AuthenticationError):
            svc.autenticar("nonexistent", "AnyPassword123!")

    def test_crear_usuario_exitoso(self, admin_user):
        """Test: creación exitosa de usuario con permisos admin."""
        from services.usuario_service import UsuarioService

        svc = UsuarioService(usuario_actual=admin_user)
        user_id = svc.crear_usuario(
            username="newuser",
            password="NewUser1234!",
            nombre="New User",
            rol="veterinario"
        )

        assert user_id is not None
        assert user_id > 0

    def test_crear_usuario_sin_permisos(self, vet_user):
        """Test: intento de crear usuario sin permisos de admin."""
        from services.usuario_service import UsuarioService
        from utils.security import PermissionDeniedError

        svc = UsuarioService(usuario_actual=vet_user)

        with pytest.raises(PermissionDeniedError):
            svc.crear_usuario(
                username="newuser",
                password="NewUser1234!",
                nombre="New User"
            )

    def test_crear_usuario_username_corto(self, admin_user):
        """Test: creación fallida con username muy corto."""
        from services.usuario_service import UsuarioService

        svc = UsuarioService(usuario_actual=admin_user)

        with pytest.raises(ValueError, match="al menos 3 caracteres"):
            svc.crear_usuario(
                username="ab",
                password="ValidPass123!",
                nombre="Short Username"
            )

    def test_crear_usuario_password_debil(self, admin_user):
        """Test: creación fallida con contraseña débil."""
        from services.usuario_service import UsuarioService

        svc = UsuarioService(usuario_actual=admin_user)

        with pytest.raises(ValueError):
            svc.crear_usuario(
                username="newuser",
                password="weak",
                nombre="Weak Password"
            )

    def test_crear_usuario_rol_invalido(self, admin_user):
        """Test: creación fallida con rol inválido."""
        from services.usuario_service import UsuarioService

        svc = UsuarioService(usuario_actual=admin_user)

        with pytest.raises(ValueError, match="no válido"):
            svc.crear_usuario(
                username="newuser",
                password="ValidPass123!",
                nombre="Invalid Role",
                rol="rol_inexistente"
            )

    def test_crear_usuario_duplicado(self, admin_user):
        """Test: creación fallida con username duplicado."""
        from services.usuario_service import UsuarioService
        from utils.exceptions import DuplicateError

        svc = UsuarioService(usuario_actual=admin_user)

        # Crear primer usuario
        svc.crear_usuario(
            username="duplicate",
            password="ValidPass123!",
            nombre="First User"
        )

        # Intentar crear segundo con mismo username
        with pytest.raises(DuplicateError):
            svc.crear_usuario(
                username="duplicate",
                password="AnotherPass123!",
                nombre="Second User"
            )

    def test_obtener_usuario(self, admin_user):
        """Test: obtener usuario por ID."""
        from services.usuario_service import UsuarioService

        svc = UsuarioService(usuario_actual=admin_user)
        user_data = svc.obtener_usuario(admin_user['id'])

        assert user_data is not None
        assert user_data['username'] == "admin"
        assert user_data['rol'] == "admin"

    def test_obtener_usuario_no_existe(self, admin_user):
        """Test: obtener usuario inexistente lanza error."""
        from services.usuario_service import UsuarioService
        from utils.exceptions import NotFoundError

        svc = UsuarioService(usuario_actual=admin_user)

        with pytest.raises(NotFoundError):
            svc.obtener_usuario(99999)

    def test_actualizar_usuario(self, admin_user):
        """Test: actualizar datos de usuario."""
        from services.usuario_service import UsuarioService

        svc = UsuarioService(usuario_actual=admin_user)
        svc.actualizar_usuario(admin_user['id'], {'nombre': 'Nuevo Nombre'})

        user_data = svc.obtener_usuario(admin_user['id'])
        assert user_data['nombre'] == 'Nuevo Nombre'

    def test_cambiar_password_exitoso(self, admin_user):
        """Test: cambio de contraseña exitoso."""
        from services.usuario_service import UsuarioService

        svc = UsuarioService(usuario_actual=admin_user)
        result = svc.cambiar_password(
            admin_user['id'],
            "Admin1234!",
            "NewAdmin1234!"
        )

        assert result is True

    def test_cambiar_password_incorrecta(self, admin_user):
        """Test: cambio de contraseña fallido con contraseña actual incorrecta."""
        from services.usuario_service import UsuarioService
        from utils.exceptions import AuthenticationError

        svc = UsuarioService(usuario_actual=admin_user)

        with pytest.raises(AuthenticationError):
            svc.cambiar_password(
                admin_user['id'],
                "WrongCurrentPassword!",
                "NewAdmin1234!"
            )

    def test_desactivar_usuario(self, admin_user):
        """Test: desactivar usuario (eliminación lógica)."""
        from services.usuario_service import UsuarioService

        # Crear usuario para desactivar
        user_id = _create_test_user(
            username="todelete",
            password="Delete1234!",
            nombre="To Delete",
            rol="usuario"
        )

        svc = UsuarioService(usuario_actual=admin_user)
        svc.desactivar_usuario(user_id)

        # Verificar que fue desactivado
        from database.connection import DatabaseManager
        db = DatabaseManager()
        row = db.fetch_one("SELECT activo FROM usuarios WHERE id = ?", (user_id,))
        assert row['activo'] == 0

    def test_listar_usuarios(self, admin_user):
        """Test: listar todos los usuarios."""
        from services.usuario_service import UsuarioService

        # Crear algunos usuarios
        _create_test_user("user1", "User11234!", "User 1", "usuario")
        _create_test_user("user2", "User21234!", "User 2", "veterinario")

        svc = UsuarioService(usuario_actual=admin_user)
        users = svc.listar_usuarios()

        assert len(users) >= 3  # admin + user1 + user2


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: ANIMAL SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class TestAnimalService:
    """Tests para AnimalService - CRUD de animales."""

    def test_registrar_ingreso_exitoso(self):
        """Test: registro de ingreso exitoso."""
        from services.animal_service import AnimalService

        svc = AnimalService()
        animal = svc.registrar_ingreso({
            'codigo': 'PAC-TEST-001',
            'nombre': 'Max',
            'especie': 'Canino',
            'raza': 'Labrador',
            'propietario': 'Juan Pérez',
            'fecha_ingreso': '2026-01-01',
            'estado': 'Activo'
        })

        assert animal is not None
        assert animal.codigo == 'PAC-TEST-001'
        assert animal.nombre == 'Max'

    def test_registrar_ingreso_codigo_duplicado(self):
        """Test: registro fallido con código duplicado."""
        from services.animal_service import AnimalService
        from utils.exceptions import DuplicateError

        svc = AnimalService()

        # Primer registro
        svc.registrar_ingreso({
            'codigo': 'PAC-TEST-001',
            'nombre': 'Max',
            'especie': 'Canino',
            'fecha_ingreso': '2026-01-01'
        })

        # Segundo registro con mismo código
        with pytest.raises(DuplicateError):
            svc.registrar_ingreso({
                'codigo': 'PAC-TEST-001',
                'nombre': 'Otro',
                'especie': 'Felino',
                'fecha_ingreso': '2026-01-01'
            })

    def test_obtener_animal(self, test_animal):
        """Test: obtener animal por ID."""
        from services.animal_service import AnimalService

        svc = AnimalService()
        animal = svc.obtener_animal(test_animal)

        assert animal is not None
        assert animal.codigo == 'PAC-TEST-001'

    def test_actualizar_datos(self, test_animal):
        """Test: actualizar datos de animal."""
        from services.animal_service import AnimalService

        svc = AnimalService()
        animal = svc.actualizar_datos(test_animal, {
            'codigo': 'PAC-TEST-001',  # Mantener código
            'nombre': 'Max Actualizado',
            'especie': 'Canino',
            'raza': 'Labrador',
            'fecha_ingreso': '2026-01-01',
            'estado': 'Activo',
            'peso': 25.5,
            'telefono': '555-1234'
        })

        assert animal.nombre == 'Max Actualizado'
        assert animal.peso == 25.5

    def test_listar_animales(self, test_animal):
        """Test: listar animales con filtros."""
        from services.animal_service import AnimalService

        # Crear más animales
        _create_test_animal("PAC-TEST-002", "Luna", "Felino")
        _create_test_animal("PAC-TEST-003", "Rex", "Canino")

        svc = AnimalService()
        animales = svc.listar_animales()

        assert len(animales) >= 3

    def test_listar_animales_con_filtro(self, test_animal):
        """Test: listar animales con filtro de búsqueda."""
        from services.animal_service import AnimalService

        svc = AnimalService()
        animales = svc.listar_animales(filtros={'especie': 'Canino'})

        assert len(animales) >= 1
        for a in animales:
            assert a.especie == 'Canino'

    def test_obtener_siguiente_codigo(self):
        """Test: generación de código correlativo."""
        from services.animal_service import AnimalService

        svc = AnimalService()
        codigo1 = svc.obtener_siguiente_codigo()
        codigo2 = svc.obtener_siguiente_codigo()

        assert codigo1.startswith('PAC-')
        assert codigo2.startswith('PAC-')
        assert codigo1 != codigo2

    def test_registrar_salida(self, test_animal):
        """Test: registrar salida de animal."""
        from services.animal_service import AnimalService
        from database.connection import DatabaseManager

        svc = AnimalService()
        svc.registrar_salida(test_animal, {
            'motivo': 'Alta médica',
            'responsable': 'Dr. Test',
            'destino': 'Hogar'
        })

        # Verificar que el estado cambió
        animal = svc.obtener_animal(test_animal)
        assert animal.estado == 'Dado de Alta'

        # Verificar que se creó el movimiento de salida
        db = DatabaseManager()
        movimientos = db.fetch_all(
            "SELECT * FROM movimientos WHERE animal_id = ? AND tipo = 'Salida'",
            (test_animal,)
        )
        assert len(movimientos) >= 1
        assert movimientos[0]['motivo'] == 'Alta médica'

    def test_registrar_salida_sin_motivo(self, test_animal):
        """Test: registrar salida sin motivo lanza error."""
        from services.animal_service import AnimalService
        from utils.exceptions import BusinessLogicError

        svc = AnimalService()

        with pytest.raises(BusinessLogicError):
            svc.registrar_salida(test_animal, {
                'responsable': 'Dr. Test'
            })


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: MUESTRA SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class TestMuestraService:
    """Tests para MuestraService - CRUD de muestras de laboratorio."""

    def test_registrar_muestra_exitoso(self, test_animal):
        """Test: registro de muestra exitoso."""
        from services.muestra_service import MuestraService

        svc = MuestraService()
        muestra = svc.registrar_muestra({
            'codigo': 'LAB-TEST-001',
            'animal_id': test_animal,
            'tipo_muestra': 'Sangre',
            'fecha_recoleccion': '2026-01-01',
            'tecnico': 'Tech Test'
        })

        assert muestra is not None
        assert muestra.codigo == 'LAB-TEST-001'

    def test_registrar_muestra_generar_codigo(self, test_animal):
        """Test: generación automática de código de muestra."""
        from services.muestra_service import MuestraService

        svc = MuestraService()
        muestra = svc.registrar_muestra({
            'animal_id': test_animal,
            'tipo_muestra': 'Orina',
            'fecha_recoleccion': '2026-01-01'
        })

        assert muestra.codigo.startswith('LAB-')

    def test_obtener_muestra(self, test_animal):
        """Test: obtener muestra por ID."""
        from services.muestra_service import MuestraService

        svc = MuestraService()
        muestra_creada = svc.registrar_muestra({
            'codigo': 'LAB-TEST-002',
            'animal_id': test_animal,
            'tipo_muestra': 'Heces',
            'fecha_recoleccion': '2026-01-01'
        })

        muestra = svc.obtener_muestra(muestra_creada.id)
        assert muestra is not None
        assert muestra.codigo == 'LAB-TEST-002'

    def test_obtener_muestra_no_existe(self):
        """Test: obtener muestra inexistente lanza error."""
        from services.muestra_service import MuestraService
        from utils.exceptions import NotFoundError

        svc = MuestraService()

        with pytest.raises(NotFoundError):
            svc.obtener_muestra(99999)

    def test_actualizar_estado(self, test_animal):
        """Test: actualizar estado de muestra."""
        from services.muestra_service import MuestraService

        svc = MuestraService()
        muestra = svc.registrar_muestra({
            'codigo': 'LAB-TEST-003',
            'animal_id': test_animal,
            'tipo_muestra': 'Sangre',
            'fecha_recoleccion': '2026-01-01'
        })

        svc.actualizar_estado(muestra.id, 'En Proceso')
        muestra_actualizada = svc.obtener_muestra(muestra.id)
        assert muestra_actualizada.estado == 'En Proceso'

    def test_actualizar_estado_con_resultado(self, test_animal):
        """Test: actualizar estado con resultado."""
        from services.muestra_service import MuestraService

        svc = MuestraService()
        muestra = svc.registrar_muestra({
            'codigo': 'LAB-TEST-004',
            'animal_id': test_animal,
            'tipo_muestra': 'Sangre',
            'fecha_recoleccion': '2026-01-01'
        })

        svc.actualizar_estado(
            muestra.id,
            'Completado',
            resultado='Hemograma normal',
            valor_ref='37-55%'
        )

        muestra_resultado = svc.obtener_muestra(muestra.id)
        assert muestra_resultado.estado == 'Completado'
        assert muestra_resultado.resultado == 'Hemograma normal'

    def test_actualizar_estado_invalido(self, test_animal):
        """Test: actualizar con estado inválido lanza error."""
        from services.muestra_service import MuestraService
        from utils.exceptions import BusinessLogicError

        svc = MuestraService()
        muestra = svc.registrar_muestra({
            'codigo': 'LAB-TEST-005',
            'animal_id': test_animal,
            'tipo_muestra': 'Sangre',
            'fecha_recoleccion': '2026-01-01'
        })

        with pytest.raises(BusinessLogicError):
            svc.actualizar_estado(muestra.id, 'EstadoInvalido')

    def test_obtener_pendientes(self, test_animal):
        """Test: obtener muestras pendientes."""
        from services.muestra_service import MuestraService

        svc = MuestraService()
        svc.registrar_muestra({
            'codigo': 'LAB-TEST-006',
            'animal_id': test_animal,
            'tipo_muestra': 'Sangre',
            'fecha_recoleccion': '2026-01-01'
        })

        pendientes = svc.obtener_pendientes()
        assert len(pendientes) >= 1

    def test_generar_codigo(self):
        """Test: generación de código de laboratorio."""
        from services.muestra_service import MuestraService

        svc = MuestraService()
        codigo1 = svc.generar_codigo()
        codigo2 = svc.generar_codigo()

        assert codigo1.startswith('LAB-')
        assert codigo1 != codigo2


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: CIRUGIA SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class TestCirugiaService:
    """Tests para CirugiaService - CRUD de cirugías."""

    def test_programar_cirugia_exitoso(self, test_animal):
        """Test: programación de cirugía exitosa."""
        from services.cirugia_service import CirugiaService

        svc = CirugiaService()
        cirugia = svc.programar_cirugia({
            'animal_id': test_animal,
            'tipo_cirugia': 'Castración',
            'fecha': '2026-01-15',
            'cirujano': 'Dr. Test'
        })

        assert cirugia is not None
        assert cirugia.codigo.startswith('CIRU-')
        assert cirugia.tipo_cirugia == 'Castración'

    def test_programar_cirugia_generar_codigo(self, test_animal):
        """Test: generación automática de código de cirugía."""
        from services.cirugia_service import CirugiaService

        svc = CirugiaService()
        cirugia = svc.programar_cirugia({
            'animal_id': test_animal,
            'tipo_cirugia': 'Laparotomía',
            'fecha': '2026-01-20'
        })

        assert cirugia.codigo.startswith('CIRU-')

    def test_obtener_cirugia(self, test_animal):
        """Test: obtener cirugía por ID."""
        from services.cirugia_service import CirugiaService

        svc = CirugiaService()
        cirugia_creada = svc.programar_cirugia({
            'animal_id': test_animal,
            'tipo_cirugia': 'Osteosíntesis',
            'fecha': '2026-01-25'
        })

        cirugia = svc.obtener_cirugia(cirugia_creada.id)
        assert cirugia is not None
        assert cirugia.tipo_cirugia == 'Osteosíntesis'

    def test_actualizar_estado_cirugia(self, test_animal):
        """Test: actualizar estado de cirugía."""
        from services.cirugia_service import CirugiaService

        svc = CirugiaService()
        cirugia = svc.programar_cirugia({
            'animal_id': test_animal,
            'tipo_cirugia': 'Amputación',
            'fecha': '2026-02-01'
        })

        svc.actualizar_estado(cirugia.id, 'En Proceso')
        cirugia_actualizada = svc.obtener_cirugia(cirugia.id)
        assert cirugia_actualizada.estado == 'En Proceso'

    def test_actualizar_estado_con_complicaciones(self, test_animal):
        """Test: actualizar estado con complicaciones."""
        from services.cirugia_service import CirugiaService

        svc = CirugiaService()
        cirugia = svc.programar_cirugia({
            'animal_id': test_animal,
            'tipo_cirugia': 'Cirugía Mayor',
            'fecha': '2026-02-05'
        })

        svc.actualizar_estado(
            cirugia.id,
            'Completada',
            complicaciones='Sangrado menor controlado'
        )

        cirugia_final = svc.obtener_cirugia(cirugia.id)
        assert cirugia_final.estado == 'Completada'
        assert cirugia_final.complicaciones == 'Sangrado menor controlado'

    def test_listar_cirugias(self, test_animal):
        """Test: listar cirugías."""
        from services.cirugia_service import CirugiaService

        svc = CirugiaService()
        svc.programar_cirugia({
            'animal_id': test_animal,
            'tipo_cirugia': 'Cirugía 1',
            'fecha': '2026-01-10'
        })
        svc.programar_cirugia({
            'animal_id': test_animal,
            'tipo_cirugia': 'Cirugía 2',
            'fecha': '2026-01-20'
        })

        cirugias = svc.listar_cirugias()
        assert len(cirugias) >= 2

    def test_cirugias_por_paciente(self, test_animal):
        """Test: obtener cirugías de un paciente."""
        from services.cirugia_service import CirugiaService

        svc = CirugiaService()
        svc.programar_cirugia({
            'animal_id': test_animal,
            'tipo_cirugia': 'Cirugía Paciente',
            'fecha': '2026-01-25'
        })

        cirugias = svc.cirugias_por_paciente(test_animal)
        assert len(cirugias) >= 1

    def test_generar_codigo_cirugia(self):
        """Test: generación de código de cirugía."""
        from services.cirugia_service import CirugiaService

        svc = CirugiaService()
        codigo1 = svc.generar_codigo()
        codigo2 = svc.generar_codigo()

        assert codigo1.startswith('CIRU-')
        assert codigo1 != codigo2


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: VALIDACIONES
# ══════════════════════════════════════════════════════════════════════════════

class TestValidators:
    """Tests para validadores de datos."""

    def test_validar_fortaleza_password_fuerte(self):
        """Test: contraseña fuerte pasa validación."""
        from utils.security import validar_fortaleza_password

        es_valida, msg = validar_fortaleza_password("StrongPass123!")
        assert es_valida is True

    def test_validar_fortaleza_password_corta(self):
        """Test: contraseña corta falla validación."""
        from utils.security import validar_fortaleza_password

        es_valida, msg = validar_fortaleza_password("Ab1!")
        assert es_valida is False
        assert "8 caracteres" in msg

    def test_validar_fortaleza_password_sin_mayuscula(self):
        """Test: contraseña sin mayúscula falla."""
        from utils.security import validar_fortaleza_password

        es_valida, msg = validar_fortaleza_password("nouppercase123!")
        assert es_valida is False
        assert "mayúscula" in msg

    def test_validar_fortaleza_password_sin_numero(self):
        """Test: contraseña sin número falla."""
        from utils.security import validar_fortaleza_password

        es_valida, msg = validar_fortaleza_password("NoNumberHere!")
        assert es_valida is False
        assert "número" in msg


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: SEGURIDAD
# ══════════════════════════════════════════════════════════════════════════════

class TestSecurity:
    """Tests para funciones de seguridad."""

    def test_hash_password(self):
        """Test: hashing de contraseña."""
        from utils.security import hash_password, verify_password

        password = "TestPassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrecta(self):
        """Test: verificación con contraseña incorrecta."""
        from utils.security import hash_password, verify_password

        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password("WrongPassword!", hashed) is False

    def test_generar_password_temporal(self):
        """Test: generación de contraseña temporal."""
        from utils.security import generar_password_temporal

        pwd = generar_password_temporal(12)
        assert len(pwd) == 12
        assert any(c.isupper() for c in pwd)
        assert any(c.islower() for c in pwd)
        assert any(c.isdigit() for c in pwd)

    def test_authorizer_rol_jerarquia(self):
        """Test: jeraría de roles en Authorizer."""
        from utils.security import Authorizer

        # Admin tiene nivel 4
        admin_auth = Authorizer({'rol': 'admin'})
        assert admin_auth.tiene_rol('admin') is True
        assert admin_auth.tiene_rol('veterinario') is True

        # Veterinario tiene nivel 3
        vet_auth = Authorizer({'rol': 'veterinario'})
        assert vet_auth.tiene_rol('admin') is False
        assert vet_auth.tiene_rol('veterinario') is True
        assert vet_auth.tiene_rol('asistente') is True

    def test_authorizer_require_role_falla(self):
        """Test: require_role lanza excepción si no tiene permisos."""
        from utils.security import Authorizer, PermissionDeniedError

        vet_auth = Authorizer({'rol': 'veterinario'})

        with pytest.raises(PermissionDeniedError):
            vet_auth.require_role('admin')


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: REPOSITORY
# ══════════════════════════════════════════════════════════════════════════════

class TestRepositories:
    """Tests para repositories - operaciones CRUD contra BD."""

    def test_animal_repository_create(self):
        """Test: crear animal en repository."""
        from database.repositories import AnimalRepository
        from database.models import Animal

        repo = AnimalRepository()
        animal = Animal(
            codigo="PAC-REPO-001",
            nombre="Repo Test",
            especie="Canino",
            fecha_ingreso="2026-01-01"
        )

        animal_id = repo.create(animal)
        assert animal_id is not None

    def test_animal_repository_get_by_id(self):
        """Test: obtener animal por ID en repository."""
        from database.repositories import AnimalRepository
        from database.models import Animal

        repo = AnimalRepository()
        animal = Animal(
            codigo="PAC-REPO-002",
            nombre="Get Test",
            especie="Felino",
            fecha_ingreso="2026-01-01"
        )

        animal_id = repo.create(animal)
        retrieved = repo.get_by_id(animal_id)

        assert retrieved is not None
        assert retrieved.codigo == "PAC-REPO-002"

    def test_animal_repository_get_by_codigo(self):
        """Test: obtener animal por código en repository."""
        from database.repositories import AnimalRepository
        from database.models import Animal

        repo = AnimalRepository()
        animal = Animal(
            codigo="PAC-REPO-003",
            nombre="Codigo Test",
            especie="Canino",
            fecha_ingreso="2026-01-01"
        )

        repo.create(animal)
        retrieved = repo.get_by_codigo("PAC-REPO-003")

        assert retrieved is not None
        assert retrieved.nombre == "Codigo Test"

    def test_animal_repository_update(self):
        """Test: actualizar animal en repository."""
        from database.repositories import AnimalRepository
        from database.models import Animal

        repo = AnimalRepository()
        animal = Animal(
            codigo="PAC-REPO-004",
            nombre="Update Test",
            especie="Canino",
            fecha_ingreso="2026-01-01"
        )

        animal_id = repo.create(animal)
        animal.id = animal_id
        animal.nombre = "Updated Name"
        repo.update(animal)

        retrieved = repo.get_by_id(animal_id)
        assert retrieved.nombre == "Updated Name"


# ══════════════════════════════════════════════════════════════════════════════
# TESTS: SCHEMAS (PYDANTIC)
# ══════════════════════════════════════════════════════════════════════════════

class TestSchemas:
    """Tests para validación de schemas Pydantic."""

    def test_animal_schema_valido(self):
        """Test: schema de animal con datos válidos."""
        from schemas.animal import AnimalSchema

        schema = AnimalSchema(
            codigo="PAC-SCHEMA-001",
            nombre="Schema Test",
            especie="Canino",
            fecha_ingreso="2026-01-01"
        )

        assert schema.codigo == "PAC-SCHEMA-001"
        assert schema.nombre == "Schema Test"

    def test_animal_schema_codigo_corto(self):
        """Test: schema falla con código muy corto."""
        from schemas.animal import AnimalSchema
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AnimalSchema(
                codigo="AB",  # Menos de 3 caracteres
                nombre="Test",
                especie="Canino"
            )

    def test_animal_schema_nombre_vacio(self):
        """Test: schema falla con nombre vacío."""
        from schemas.animal import AnimalSchema
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AnimalSchema(
                codigo="PAC-SCHEMA-002",
                nombre="",  # Nombre vacío
                especie="Canino"
            )

    def test_animal_schema_edad_invalida(self):
        """Test: schema falla con edad inválida."""
        from schemas.animal import AnimalSchema
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AnimalSchema(
                codigo="PAC-SCHEMA-003",
                nombre="Test",
                especie="Canino",
                edad=150  # Edad mayor a 100
            )

    def test_cirugia_schema_valido(self):
        """Test: schema de cirugía con datos válidos."""
        from schemas.clinica import CirugiaSchema

        schema = CirugiaSchema(
            codigo="CIRU-SCHEMA-001",
            animal_id=1,
            fecha="2026-01-15",
            tipo_cirugia="Castración"
        )

        assert schema.tipo_cirugia == "Castración"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
