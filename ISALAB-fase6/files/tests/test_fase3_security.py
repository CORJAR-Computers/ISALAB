"""
Tests de regresión para Fase 3 — Fix CRITICAL de seguridad.

Cubre los 4 issues CRITICAL del análisis (Task 4 — services & security):

- C1: RBAC burlado — Authorizer solo cableado en UsuarioService.
  Tras Fase 3, todos los servicios cablean Authorizer y las operaciones
  de escritura requieren rol mínimo.

- C2: RecepcionService.generar_codigo no incrementaba el contador →
  colisión ISAL-0001 con UNIQUE constraint. Tras Fase 3, usa
  ``DatabaseManager.generar_codigo('ISAL')`` atómico.

- C3: reports/generators.py construía Jinja2 ``Environment`` SIN
  ``autoescape``, permitiendo HTML injection / WeasyPrint SSRF. Tras
  Fase 3, ``autoescape=select_autoescape(...)`` + ``url_fetcher``
  sandboxed que bloquea http(s)://, ftp://, data: y file:// fuera
  del sandbox.

- C4: ``PermissionError(Exception)`` en ``utils/security.py`` shadow
  del builtin de Python. Tras Fase 3, se renombra a
  ``PermissionDeniedError(IsaLabException)`` y se mantiene alias
  deprecated.

Estos tests NO requieren DB real ni QApplication — usan mocks y
fixtures temporales.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _setup_test_db(tmp_path: Path) -> None:
    """Crea las tablas mínimas en la DB de test de sesión.

    Usa ``config.DB_PATH`` (que el conftest ya aisló a una ruta
    temporal a nivel sesión). Crea las tablas clínicas mínimas
    que el singleton ``DatabaseManager`` no crea por sí solo
    (las delega a Alembic en producción).
    """
    from config import DB_PATH

    # Asegurar que el singleton esté inicializado (crea codigo_contadores
    # y usuarios, que el test de RBAC de usuarios puede necesitar).
    from database.connection import DatabaseManager
    DatabaseManager()

    # Añadir las tablas clínicas mínimas para los tests.
    # Fase 6: DROP IF EXISTS + CREATE garantiza que el esquema refleja
    # exactamente lo que el test espera (con ``updated_at`` y
    # ``created_at``). Sin esto, si una corrida anterior creó las
    # tablas con un esquema viejo, ``CREATE IF NOT EXISTS`` lo deja
    # pasar y los INSERT fallan con ``no such column``.
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS recepciones")
    cur.execute("DROP TABLE IF EXISTS animales")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS recepciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            animal_id INTEGER NOT NULL,
            fecha_hora TEXT NOT NULL,
            motivo TEXT,
            veterinario TEXT,
            estado TEXT DEFAULT 'Pendiente',
            proxima_cita TEXT,
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS animales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT,
            especie TEXT,
            raza TEXT,
            edad TEXT,
            propietario TEXT,
            telefono TEXT,
            email TEXT,
            fecha_ingreso TEXT,
            estado TEXT DEFAULT 'Activo',
            observaciones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)

    # Fase 6: resetear contadores para garantizar aislamiento entre
    # tests (la DB es de sesión, así que sin esto el contador ISAL-XXXX
    # acumula entre tests y rompe las aserciones).
    cur.execute("DELETE FROM codigo_contadores")

    conn.commit()
    conn.close()

    # Resetear el singleton para que la siguiente operación pique la
    # nueva conexión con las tablas nuevas (sqlite3 cachea la conexión
    # en thread-local).
    DatabaseManager._instance = None
    DatabaseManager()


@pytest.fixture
def clean_current_user():
    """Limpia el usuario thread-local antes y después de cada test."""
    from utils.security import clear_current_user, get_current_user
    clear_current_user()
    assert get_current_user() is None
    yield
    clear_current_user()


# ─────────────────────────────────────────────────────────────────────────────
# C4 — PermissionError rename
# ─────────────────────────────────────────────────────────────────────────────

def test_C4_permission_denied_error_does_not_shadow_builtin():
    """
    Issue C4: ``utils.security.PermissionError`` no debe shadow el
    builtin de Python.

    Antes: ``from utils.security import PermissionError`` reemplazaba
    el acceso al builtin en cualquier módulo que importara el archivo.

    Ahora: ``PermissionDeniedError`` es la clase canónica, y
    ``PermissionError`` es un alias deprecated que apunta a la misma
    clase (mantenido por compat). El builtin
    ``PermissionError`` (que es ``OSError`` subclass) sigue accesible
    vía ``builtins.PermissionError``.
    """
    import builtins
    from utils.security import PermissionDeniedError, PermissionError as SecPermError
    from utils.exceptions import IsaLabException

    # La clase canónica existe y hereda de IsaLabException
    assert issubclass(PermissionDeniedError, IsaLabException)
    assert issubclass(PermissionDeniedError, Exception)

    # El alias deprecated apunta a la misma clase
    assert SecPermError is PermissionDeniedError

    # El builtin sigue siendo el de Python (subclass de OSError)
    assert builtins.PermissionError is not PermissionDeniedError
    assert issubclass(builtins.PermissionError, OSError)
    assert not issubclass(builtins.PermissionError, IsaLabException)

    # Podemos levantar y atrapar ambos independientemente
    try:
        raise PermissionDeniedError("denied")
    except PermissionDeniedError as e:
        assert "denied" in str(e)
    except builtins.PermissionError:  # pragma: no cover
        pytest.fail("PermissionDeniedError fue atrapado como builtin — shadow no resuelto")

    # Y el builtin sigue funcionando para errores OS-level
    try:
        # Simular un error OS-level (archivo sin permiso)
        raise builtins.PermissionError(13, "Permission denied")
    except builtins.PermissionError as e:
        assert e.errno == 13


# ─────────────────────────────────────────────────────────────────────────────
# C1 — RBAC bypass
# ─────────────────────────────────────────────────────────────────────────────

def test_C1_anonymous_user_cannot_register_animal(clean_current_user, tmp_path):
    """
    Issue C1: sin usuario autenticado, ``AnimalService.registrar_ingreso``
    debe levantar ``PermissionDeniedError``.

    Antes: cualquier proceso podía instanciar ``AnimalService()`` y
    registrar animales sin autenticación.
    """
    _setup_test_db(tmp_path)
    from services.animal_service import AnimalService
    from utils.security import PermissionDeniedError

    svc = AnimalService()  # sin usuario_actual → anónimo

    with pytest.raises(PermissionDeniedError):
        svc.registrar_ingreso({
            'codigo': 'PAC-TEST',
            'nombre': 'Test',
            'especie': 'Test',
            'fecha_ingreso': '2026-01-01',
        })


def test_C1_asistente_can_register_animal_but_not_consulta(clean_current_user, tmp_path):
    """
    Issue C1: rol ``asistente`` puede registrar animales (rol mínimo
    ``asistente``) pero NO puede registrar consultas (rol mínimo
    ``veterinario``).
    """
    _setup_test_db(tmp_path)
    from services.animal_service import AnimalService
    from services.consulta_service import ConsultaService
    from utils.security import (
        PermissionDeniedError,
        set_current_user,
    )

    asistente = {
        'id': 1,
        'username': 'asistente1',
        'rol': 'asistente',
    }
    set_current_user(asistente)

    # Asistente SÍ puede llamar registrar_ingreso (mínimo: asistente)
    # — el registro real puede fallar por validación Pydantic, pero
    # NO debe fallar con PermissionDeniedError.
    svc_animal = AnimalService()
    try:
        svc_animal.registrar_ingreso({
            'codigo': 'PAC-X1',
            'nombre': 'X',
            'especie': 'Test',
            'fecha_ingreso': '2026-01-01',
        })
    except PermissionDeniedError:
        pytest.fail(
            "asistente deberia poder registrar_ingreso — fallo de RBAC"
        )
    except Exception:
        # Cualquier otro error (validación, DB, etc.) es OK para este
        # test — lo que importa es que NO sea PermissionDeniedError.
        pass

    # Asistente NO puede registrar consultas (mínimo: veterinario)
    svc_consulta = ConsultaService()
    with pytest.raises(PermissionDeniedError):
        svc_consulta.registrar_consulta({
            'animal_id': 1,
            'fecha': '2026-01-01',
            'motivo': 'test',
        })


def test_C1_veterinario_can_register_consulta(clean_current_user, tmp_path):
    """veterinario puede registrar consultas (rol mínimo: veterinario)."""
    _setup_test_db(tmp_path)
    from services.consulta_service import ConsultaService
    from utils.security import (
        PermissionDeniedError,
        set_current_user,
    )

    vet = {'id': 2, 'username': 'vet1', 'rol': 'veterinario'}
    set_current_user(vet)

    svc = ConsultaService()
    # No debe levantar PermissionDeniedError (puede fallar por
    # validación o DB, pero no por permisos).
    try:
        svc.registrar_consulta({
            'animal_id': 1,
            'fecha': '2026-01-01',
            'motivo': 'Consulta test',
        })
    except PermissionDeniedError:
        pytest.fail("veterinario debería poder registrar_consulta")
    except Exception:
        pass


def test_C1_admin_can_guardar_configuracion(clean_current_user, tmp_path):
    """admin puede guardar_configuracion (rol mínimo: admin)."""
    _setup_test_db(tmp_path)
    from services.configuracion_service import ConfiguracionService
    from utils.security import (
        PermissionDeniedError,
        set_current_user,
    )

    admin = {'id': 1, 'username': 'admin1', 'rol': 'admin'}
    set_current_user(admin)

    svc = ConfiguracionService()
    # Debe poder guardar sin PermissionDeniedError
    try:
        svc.guardar_configuracion({'test': 'value'})
    except PermissionDeniedError:
        pytest.fail("admin debería poder guardar_configuracion")
    except Exception:
        pass

    # Limpieza del archivo temporal
    cfg_path = svc.config_path
    if cfg_path.exists():
        cfg_path.unlink()


def test_C1_asistente_cannot_guardar_configuracion(clean_current_user, tmp_path):
    """asistente NO puede guardar_configuracion (rol mínimo: admin)."""
    _setup_test_db(tmp_path)
    from services.configuracion_service import ConfiguracionService
    from utils.security import (
        PermissionDeniedError,
        set_current_user,
    )

    asistente = {'id': 2, 'username': 'asistente1', 'rol': 'asistente'}
    set_current_user(asistente)

    svc = ConfiguracionService()
    with pytest.raises(PermissionDeniedError):
        svc.guardar_configuracion({'test': 'value'})


# ─────────────────────────────────────────────────────────────────────────────
# C2 — RecepcionService.generar_codigo atómico
# ─────────────────────────────────────────────────────────────────────────────

def test_C2_generar_codigo_increments_counter(clean_current_user, tmp_path):
    """
    Issue C2: ``RecepcionService.generar_codigo`` debe INCREMENTAR el
    contador cada vez que se llama (atómico).

    Antes: era preview-only (solo SELECT sin UPDATE), por lo que cada
    ``registrar_recepcion`` producía ``ISAL-0001`` y chocaba con la
    UNIQUE constraint.
    """
    _setup_test_db(tmp_path)
    from services.recepcion_service import RecepcionService
    from utils.security import set_current_user

    set_current_user({'id': 1, 'username': 'admin', 'rol': 'admin'})

    svc = RecepcionService()

    codigo1 = svc.generar_codigo()
    codigo2 = svc.generar_codigo()
    codigo3 = svc.generar_codigo()

    assert codigo1 == "ISAL-0001", f"Esperado ISAL-0001, got {codigo1}"
    assert codigo2 == "ISAL-0002", f"Esperado ISAL-0002, got {codigo2}"
    assert codigo3 == "ISAL-0003", f"Esperado ISAL-0003, got {codigo3}"


def test_C2_two_recepciones_do_not_collide(clean_current_user, tmp_path):
    """
    Issue C2 (regresión end-to-end): dos ``registrar_recepcion``
    consecutivos deben producir códigos distintos y NO chocar con la
    UNIQUE constraint de ``recepciones.codigo``.

    Antes: ambos producían ``ISAL-0001`` y el segundo INSERT fallaba
    con ``IntegrityError: UNIQUE constraint failed: recepciones.codigo``.
    """
    _setup_test_db(tmp_path)
    from services.recepcion_service import RecepcionService
    from utils.security import set_current_user

    set_current_user({'id': 1, 'username': 'admin', 'rol': 'admin'})

    svc = RecepcionService()

    # Insertar un animal mínimo para que la FK de recepciones valide
    import sqlite3
    from config import DB_PATH
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO animales (codigo, nombre, especie, fecha_ingreso, estado) "
        "VALUES (?, ?, ?, ?, ?)",
        ('PAC-T1', 'Test Animal', 'Test', '2026-01-01', 'Activo')
    )
    conn.commit()
    conn.close()

    # Reset singleton para que el service pique la conexión con la
    # tabla animales ya creada.
    from database.connection import DatabaseManager
    DatabaseManager._instance = None

    # Primera recepción
    rec1_id = svc.registrar_recepcion({
        'animal_id': 1,
        'fecha_hora': '2026-01-01 10:00',
        'motivo': 'Consulta 1',
        'veterinario': 'Dr. Test',
        'estado': 'Pendiente',
    })

    # Segunda recepción — antes chocaba con UNIQUE constraint
    rec2_id = svc.registrar_recepcion({
        'animal_id': 1,
        'fecha_hora': '2026-01-01 11:00',
        'motivo': 'Consulta 2',
        'veterinario': 'Dr. Test',
        'estado': 'Pendiente',
    })

    # Recuperar los códigos para verificar que son distintos
    rec1 = svc.obtener_recepcion(rec1_id)
    rec2 = svc.obtener_recepcion(rec2_id)
    codigo1 = rec1.codigo
    codigo2 = rec2.codigo

    assert codigo1 != codigo2, (
        f"Códigos deben ser distintos (colisión UNIQUE). "
        f"recibido: {codigo1!r} == {codigo2!r}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# C3 — Jinja2 autoescape + WeasyPrint sandbox
# ─────────────────────────────────────────────────────────────────────────────

def test_C3_generators_jinja_env_has_autoescape():
    """
    Issue C3: ``reports.generators._build_jinja_env`` debe construir un
    ``Environment`` con ``autoescape`` activado para HTML/XML.

    Antes: ``Environment(loader=...)`` sin autoescape → HTML injection
    vía cualquier campo user-controlled (animal.nombre, diagnóstico,
    observaciones, etc.).
    """
    from reports.generators import _build_jinja_env
    from jinja2 import Environment
    from jinja2.utils import select_autoescape

    env = _build_jinja_env()
    assert isinstance(env, Environment)

    # autoescape debe estar activo (callable o bool True)
    ae = env.autoescape
    assert ae is not None and ae is not False, (
        "autoescape debe estar activo en reports.generators._build_jinja_env"
    )

    # Verificar comportamiento: un string con HTML debe ser escapado
    template = env.from_string("{{ nombre }}")
    rendered = template.render(nombre="<script>alert('xss')</script>")
    assert "<script>" not in rendered, (
        f"HTML no escapado detectado: {rendered!r}"
    )
    assert "&lt;script&gt;" in rendered, (
        f"Se esperaba HTML escapado, recibido: {rendered!r}"
    )


def test_C3_safe_url_fetcher_blocks_external_http():
    """
    Issue C3: el ``url_fetcher`` sandboxed debe RECHAZAR URLs
    ``http(s)://`` externos. WeasyPrint los usaría para fetchear
    CSS, imágenes, fuentes, etc. — riesgo de SSRF.
    """
    from reports.generators import _safe_url_fetcher

    external_urls = [
        "http://example.com/evil.css",
        "https://attacker.com/exfil?data=x",
        "ftp://ftp.example.com/file.txt",
        "data:text/html,<script>alert(1)</script>",
    ]

    for url in external_urls:
        with pytest.raises(ValueError, match="no permitid"):
            _safe_url_fetcher(url)


def test_C3_safe_url_fetcher_blocks_file_outside_sandbox(tmp_path):
    """
    Issue C3: ``file://`` fuera de ``TEMPLATES_DIR`` o ``BASE_DIR``
    también debe ser rechazado (previene leer ``/etc/passwd`` o
    archivos arbitrarios del filesystem).
    """
    from reports.generators import _safe_url_fetcher

    # /etc/passwd es un archivo fuera del sandbox del proyecto
    with pytest.raises(ValueError, match="fuera del sandbox|no permitid"):
        _safe_url_fetcher("file:///etc/passwd")


def test_C3_generar_reporte_with_malicious_context_escapes_html(tmp_path):
    """
    Issue C3 (regresión end-to-end): ``generar_reporte(template,
    contexto)`` debe renderizar con autoescape, de modo que un campo
    malicioso como ``<script>`` no aparezca literalmente en el HTML
    antes de pasarse a WeasyPrint.

    Hacemos mock de ``HTML.write_pdf`` para capturar el HTML
    renderizado sin generar un PDF real.
    """
    from reports import generators

    # Crear un template temporal con un placeholder
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    template_file = templates_dir / "test_c3.html"
    template_file.write_text(
        "<html><body>{{ nombre }}</body></html>",
        encoding="utf-8",
    )

    # Parchear TEMPLATES_DIR para que apunte al temporal
    original_templates = generators.TEMPLATES_DIR
    generators.TEMPLATES_DIR = templates_dir

    captured_html = []

    class FakeHTML:
        def __init__(self, string=None, base_url=None, url_fetcher=None):
            self.string = string
            self.base_url = base_url
            self.url_fetcher = url_fetcher
            captured_html.append(string)

        def write_pdf(self):
            return b"%PDF-fake"

    try:
        with patch("reports.generators.HTML", FakeHTML):
            from reports.generators import generar_reporte
            generar_reporte(
                "test_c3",
                {"nombre": "<script>alert('xss')</script>"},
            )

        assert len(captured_html) == 1
        html = captured_html[0]
        assert "<script>alert('xss')</script>" not in html, (
            f"HTML inyectado sin escapar en: {html!r}"
        )
        assert "&lt;script&gt;" in html, (
            f"Se esperaba HTML escapado, recibido: {html!r}"
        )
    finally:
        generators.TEMPLATES_DIR = original_templates
