"""
Tests de regresión para Fase 2 — Fix CRITICAL de base de datos.

Cubre:
- Cadena Alembic: ``alembic upgrade head`` debe funcionar sin error
  ``MultipleHeads`` (issue C1).
- Tabla ``usuarios`` con columna ``password_hash`` (no ``password``)
  después de la migración (issue C3).
- ``create_table('animales')`` no se ejecuta dos veces (issue C2).
- ``AnimalRepository.update`` persiste los 25 campos editables (issue HIGH).
- ``HistoriaClinicaRepository.get_all`` existe y retorna data (issue C4).
- ``DatabaseManager.close_all_connections`` cierra conexiones de otros
  threads (issue HIGH thread-leak).

Estos tests se ejecutan contra una DB SQLite temporal (ver conftest.py).
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_alembic_upgrade(tmp_db_path: Path) -> subprocess.CompletedProcess:
    """Ejecuta ``alembic upgrade head`` contra una DB temporal."""
    env = os.environ.copy()
    env["ISALAB_DB_PATH"] = str(tmp_db_path)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests de la cadena Alembic
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_alembic_upgrade_head_no_multiple_heads(tmp_db_path: Path):
    """
    Issue C1: ``alembic upgrade head`` debe completarse sin error.

    Antes de Fase 2, fallaba con::

        CommandError: Multiple head revisions are present for given
        argument 'head'; agregar_created_at_todas_tablas,
        agregar_created_at_usuarios
    """
    result = _run_alembic_upgrade(tmp_db_path)
    assert result.returncode == 0, (
        f"alembic upgrade head falló:\n"
        f"--- STDOUT ---\n{result.stdout}\n"
        f"--- STDERR ---\n{result.stderr}\n"
    )


@pytest.mark.integration
def test_alembic_upgrade_head_creates_all_tables(tmp_db_path: Path):
    """La DB resultante debe tener las 8 tablas principales + usuarios + contadores."""
    result = _run_alembic_upgrade(tmp_db_path)
    if result.returncode != 0:
        pytest.skip(f"alembic upgrade falló (cubrimos esto en test anterior): {result.stderr}")

    import sqlite3
    conn = sqlite3.connect(str(tmp_db_path))
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        tables = {r[0] for r in rows}

        expected = {
            'alembic_version',
            'animales', 'movimientos', 'muestras', 'recepciones',
            'vacunaciones', 'historias_clinicas', 'cirugias', 'consultas',
        }
        missing = expected - tables
        assert not missing, f"Faltan tablas: {missing}"
    finally:
        conn.close()


@pytest.mark.integration
def test_alembic_no_duplicate_create_table_animales(tmp_db_path: Path):
    """
    Issue C2: la migración ``e03e74d43e0d`` no debe recrear ``animales``.

    Verificamos que la columna ``propietario_documento`` (que solo existe
    si la migración se ejecutó como add_column, no como create_table
    sobre una tabla ya creada) esté presente exactamente una vez.
    """
    result = _run_alembic_upgrade(tmp_db_path)
    if result.returncode != 0:
        pytest.skip(f"alembic upgrade falló: {result.stderr}")

    import sqlite3
    conn = sqlite3.connect(str(tmp_db_path))
    try:
        # PRAGMA table_info retorna una fila por columna
        rows = conn.execute("PRAGMA table_info(animales)").fetchall()
        col_names = [r[1] for r in rows]

        # Las columnas nuevas de la migración e03e74d43e0d deben estar
        assert 'propietario_documento' in col_names, \
            "propietario_documento falta en animales (migración e03e74d43e0d no aplicó)"
        assert 'propietario_tipo_doc' in col_names
        assert 'propietario_direccion' in col_names
        assert 'propietario_oficio' in col_names

        # Y no debe haber duplicados (count == 1)
        assert col_names.count('propietario_documento') == 1
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Tests de la columna password_hash
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_usuarios_table_has_password_hash_not_password(tmp_db_path: Path):
    """
    Issue C3: la tabla ``usuarios`` debe tener ``password_hash`` (no ``password``).

    Antes de Fase 2, la migración ``agregar_created_at_usuarios`` creaba la
    tabla con ``password`` (sin ``_hash``), rompiendo ``UsuarioService.autenticar``
    que hace ``SELECT ... password_hash FROM usuarios``.
    """
    result = _run_alembic_upgrade(tmp_db_path)
    if result.returncode != 0:
        pytest.skip(f"alembic upgrade falló: {result.stderr}")

    import sqlite3
    conn = sqlite3.connect(str(tmp_db_path))
    try:
        rows = conn.execute("PRAGMA table_info(usuarios)").fetchall()
        col_names = {r[1] for r in rows}

        assert 'password_hash' in col_names, \
            f"password_hash falta en usuarios. Columnas: {col_names}"
        assert 'password' not in col_names, \
            f"Encontrada columna 'password' (debería ser 'password_hash'). Columnas: {col_names}"
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Tests de AnimalRepository.update
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_animal_repository_update_persists_all_fields(tmp_db_path: Path):
    """
    Issue HIGH: ``AnimalRepository.update`` debe persistir TODOS los campos
    editables (antes perdía 12 campos incluyendo los 4 de propietario).
    """
    # Solo correr si SQLAlchemy + el resto de deps están instalados
    pytest.importorskip("sqlalchemy")
    pytest.importorskip("bcrypt")

    # Reset singleton state for test isolation
    from database.connection import DatabaseManager
    DatabaseManager._instance = None

    # Run alembic to set up schema
    result = _run_alembic_upgrade(tmp_db_path)
    if result.returncode != 0:
        pytest.skip(f"alembic upgrade falló: {result.stderr}")

    from database.models import Animal
    from database.repositories import AnimalRepository

    repo = AnimalRepository()

    # Crear un animal
    a = Animal(
        codigo="PAC-TEST-001",
        nombre="Test Perro",
        especie="Canino",
        raza="Mestizo",
        propietario="Juan",
        propietario_tipo_doc="CC",
        propietario_documento="1234567890",
        propietario_direccion="Calle 123",
        propietario_oficio="Ingeniero",
        sexo="M",
        color="Café",
        tipo_pelo="Corto",
        senas_particulares="Mancha blanca",
        microchip="CHIP-001",
        unidad_edad="Años",
        fecha_nacimiento="2020-01-01",
        edad=5,
        peso=15.5,
        telefono="555-1234",
        email="test@test.com",
        fecha_ingreso="2026-01-01",
        estado="Activo",
        observaciones="Ninguna",
    )
    animal_id = repo.create(a)

    # Modificar TODOS los campos y actualizar
    a.id = animal_id
    a.codigo = "PAC-TEST-001"  # no cambiar (UNIQUE)
    a.nombre = "Test Perro Modificado"
    a.especie = "Felino"
    a.raza = "Siamés"
    a.propietario = "María"
    a.propietario_tipo_doc = "CE"
    a.propietario_documento = "9876543210"
    a.propietario_direccion = "Carrera 456"
    a.propietario_oficio = "Médica"
    a.sexo = "F"
    a.color = "Blanco"
    a.tipo_pelo = "Largo"
    a.senas_particulares = "Cola cortada"
    a.microchip = "CHIP-002"
    a.unidad_edad = "Meses"
    a.fecha_nacimiento = "2021-06-15"
    a.edad = 3
    a.peso = 4.2
    a.telefono = "555-5678"
    a.email = "maria@test.com"
    a.estado = "Inactivo"
    a.observaciones = "Modificado"

    repo.update(a)

    # Recuperar y verificar
    a_loaded = repo.get_by_id(animal_id)
    assert a_loaded.nombre == "Test Perro Modificado"
    assert a_loaded.especie == "Felino"
    # Los 12 campos que antes se perdían:
    assert a_loaded.sexo == "F", "sexo se perdió en update"
    assert a_loaded.color == "Blanco", "color se perdió en update"
    assert a_loaded.tipo_pelo == "Largo", "tipo_pelo se perdió en update"
    assert a_loaded.senas_particulares == "Cola cortada", \
        "senas_particulares se perdió en update"
    assert a_loaded.microchip == "CHIP-002", "microchip se perdió en update"
    assert a_loaded.unidad_edad == "Meses", "unidad_edad se perdió en update"
    assert a_loaded.fecha_nacimiento == "2021-06-15", \
        "fecha_nacimiento se perdió en update"
    assert a_loaded.propietario_tipo_doc == "CE", \
        "propietario_tipo_doc se perdió en update"
    assert a_loaded.propietario_documento == "9876543210", \
        "propietario_documento se perdió en update"
    assert a_loaded.propietario_direccion == "Carrera 456", \
        "propietario_direccion se perdió en update"
    assert a_loaded.propietario_oficio == "Médica", \
        "propietario_oficio se perdió en update"


# ─────────────────────────────────────────────────────────────────────────────
# Tests de HistoriaClinicaRepository.get_all
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_historia_repository_get_all_exists(tmp_db_path: Path):
    """
    Issue C4: ``HistoriaClinicaRepository`` debe tener método ``get_all``.

    Antes de Fase 2, este método no existía, forzando a ``historia.py``
    a ejecutar SQL crudo vía ``repo.db.fetch_all(...)``.
    """
    pytest.importorskip("sqlalchemy")

    from database.connection import DatabaseManager
    DatabaseManager._instance = None

    result = _run_alembic_upgrade(tmp_db_path)
    if result.returncode != 0:
        pytest.skip(f"alembic upgrade falló: {result.stderr}")

    from database.repositories import HistoriaClinicaRepository
    repo = HistoriaClinicaRepository()

    # El método debe existir y ser callable
    assert hasattr(repo, 'get_all'), \
        "HistoriaClinicaRepository no tiene método get_all (issue C4)"
    data = repo.get_all()
    assert isinstance(data, list)


# ─────────────────────────────────────────────────────────────────────────────
# Tests de close_all_connections
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_close_all_connections_closes_other_thread_connections(tmp_db_path: Path):
    """
    Issue HIGH: ``close_all_connections`` debe cerrar conexiones abiertas
    por otros threads (no solo la del thread actual).
    """
    pytest.importorskip("sqlalchemy")

    from database.connection import DatabaseManager
    DatabaseManager._instance = None

    result = _run_alembic_upgrade(tmp_db_path)
    if result.returncode != 0:
        pytest.skip(f"alembic upgrade falló: {result.stderr}")

    db = DatabaseManager()

    # Abrir una conexión desde un thread secundario
    other_thread_conn_holder: dict = {}
    def _open_in_other_thread():
        with db.get_connection() as conn:
            other_thread_conn_holder['conn'] = conn
            # Mantenerla abierta hasta que el thread principal diga
            other_thread_conn_holder['event'].wait(timeout=5)

    import threading
    other_thread_conn_holder['event'] = threading.Event()
    t = threading.Thread(target=_open_in_other_thread)
    t.start()

    # Esperar a que el thread secundario abra su conexión
    import time
    deadline = time.time() + 2.0
    while 'conn' not in other_thread_conn_holder and time.time() < deadline:
        time.sleep(0.05)

    assert 'conn' in other_thread_conn_holder, \
        "El thread secundario no abrió su conexión a tiempo"

    other_conn = other_thread_conn_holder['conn']

    # Lanzar close_all_connections desde el thread principal
    db.close_all_connections()

    # Liberar el thread secundario
    other_thread_conn_holder['event'].set()
    t.join(timeout=2)

    # Verificar que la conexión del thread secundario se cerró
    # (sqlite3.Connection.closed no existe; intentamos ejecutar algo y debe fallar)
    try:
        other_conn.execute("SELECT 1").fetchone()
        connection_still_open = True
    except Exception:
        connection_still_open = False

    assert not connection_still_open, \
        "La conexión del thread secundario sigue abierta después de close_all_connections"
