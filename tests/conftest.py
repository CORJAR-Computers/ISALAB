"""
IsaLab — Configuración compartida de pytest.

Provee fixtures para:
- Base de datos temporal (aislada del `data/isalab.db` de desarrollo).
- QApplication de PySide6 (para tests de GUI con pytest-qt).

Ver issue H7 del análisis: antes de este archivo, los tests corrían contra
la DB real y la mutaban.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Iterator

# --- HACK: AISLAR DB ---
_temp_dir = tempfile.mkdtemp(prefix="isalab_test_")
_temp_db_path = os.path.join(_temp_dir, "test_isalab.db")
os.environ["ISALAB_DB_PATH"] = _temp_db_path
os.environ["ISALAB_PRODUCTION_MODE"] = "0"
os.environ["ISALAB_LOG_LEVEL"] = "WARNING"
# -----------------------

import pytest


# ── Aislar la base de datos ANTES de cualquier import de config ──────────────
# ``config.py`` lee ``DB_PATH`` al importarse, así que el monkeypatch
# tiene que ocurrir antes de cualquier ``from config import ...`` en los
# módulos del proyecto. Usamos una fixture de sesión que parchea
# ``os.environ`` y luego recarga ``config`` si ya estaba importado.


@pytest.fixture(scope="session")
def tmp_db_path() -> Path:
    """Ruta absoluta a una DB SQLite temporal para toda la sesión de tests."""
    return Path(_temp_db_path)


@pytest.fixture(scope="session", autouse=True)
def _isolate_db_env(tmp_db_path: Path) -> Iterator[None]:
    """Fuerza a que ``config.DB_PATH`` apunte a una DB temporal."""
    os.environ["ISALAB_DB_PATH"] = str(tmp_db_path)
    os.environ["ISALAB_PRODUCTION_MODE"] = "0"
    os.environ["ISALAB_LOG_LEVEL"] = "WARNING"
    yield
    # Limpieza: nada que hacer, pytest borra tmp_path automáticamente.


# ── QApplication para tests de PySide6 (pytest-qt) ───────────────────────────
@pytest.fixture(scope="session")
def qapp_cls():
    """Permite que pytest-qt use la QApplication correcta."""
    from PySide6.QtWidgets import QApplication
    return QApplication


@pytest.fixture(scope="session")
def qapp(qapp_cls):
    """Devuelve la QApplication singleton para tests de GUI."""
    import sys
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


# ── Marcadores de tests ──────────────────────────────────────────────────────
def pytest_configure(config: pytest.Config) -> None:
    """Registra marcadores adicionales."""
    config.addinivalue_line("markers", "slow: tests lentos (saltar con -m 'not slow')")
    config.addinivalue_line("markers", "integration: tests que tocan la DB real")
    config.addinivalue_line("markers", "gui: tests que requieren QApplication")
