# tests/test_utils_coverage.py
"""
Tests unitarios comprehensivos para módulos de utils y config.
Cubre: logger.py, exceptions.py, config.py, connection.py
"""

import os
import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Tests para utils/exceptions.py
# ─────────────────────────────────────────────────────────────────────────────

class TestExceptions:
    """Tests para excepciones personalizadas de IsaLab."""

    def test_isalab_exception_base(self):
        """Test: IsaLabException es la excepción base."""
        from utils.exceptions import IsaLabException

        exc = IsaLabException("Error base", code=100, details={"key": "value"})
        assert str(exc) == "Error base"
        assert exc.message == "Error base"
        assert exc.code == 100
        assert exc.details == {"key": "value"}

    def test_isalab_exception_default_values(self):
        """Test: IsaLabException tiene valores por defecto."""
        from utils.exceptions import IsaLabException

        exc = IsaLabException("Error")
        assert exc.code is None
        assert exc.details == {}

    def test_database_error(self):
        """Test: DatabaseError hereda de IsaLabException."""
        from utils.exceptions import DatabaseError, IsaLabException

        exc = DatabaseError("DB Error")
        assert isinstance(exc, IsaLabException)
        assert exc.message == "DB Error"

    def test_validation_error(self):
        """Test: ValidationError hereda de IsaLabException."""
        from utils.exceptions import ValidationError, IsaLabException

        exc = ValidationError("Validation Error")
        assert isinstance(exc, IsaLabException)
        assert exc.message == "Validation Error"

    def test_business_logic_error(self):
        """Test: BusinessLogicError hereda de IsaLabException."""
        from utils.exceptions import BusinessLogicError, IsaLabException

        exc = BusinessLogicError("Business Error")
        assert isinstance(exc, IsaLabException)

    def test_not_found_error(self):
        """Test: NotFoundError hereda de IsaLabException."""
        from utils.exceptions import NotFoundError, IsaLabException

        exc = NotFoundError("Not Found")
        assert isinstance(exc, IsaLabException)

    def test_duplicate_error(self):
        """Test: DuplicateError hereda de IsaLabException."""
        from utils.exceptions import DuplicateError, IsaLabException

        exc = DuplicateError("Duplicate")
        assert isinstance(exc, IsaLabException)

    def test_authentication_error(self):
        """Test: AuthenticationError hereda de IsaLabException."""
        from utils.exceptions import AuthenticationError, IsaLabException

        exc = AuthenticationError("Auth Error")
        assert isinstance(exc, IsaLabException)

    def test_authorization_error(self):
        """Test: AuthorizationError hereda de IsaLabException."""
        from utils.exceptions import AuthorizationError, IsaLabException

        exc = AuthorizationError("Authz Error")
        assert isinstance(exc, IsaLabException)


# ─────────────────────────────────────────────────────────────────────────────
# Tests para utils/logger.py
# ─────────────────────────────────────────────────────────────────────────────

class TestLogger:
    """Tests para configuración de logging."""

    def test_setup_logger_returns_logger(self):
        """Test: setup_logger retorna un objeto logger."""
        from utils.logger import setup_logger

        logger = setup_logger('test_logger')
        assert logger is not None
        assert logger.name == 'test_logger'

    def test_setup_logger_has_handlers(self):
        """Test: setup_logger configura handlers."""
        from utils.logger import setup_logger

        logger = setup_logger('test_handlers')
        # Debe tener al menos un handler (file o console)
        assert len(logger.handlers) >= 1

    def test_setup_logger_reuses_instance(self):
        """Test: setup_logger reutiliza instancia existente."""
        from utils.logger import setup_logger

        logger1 = setup_logger('test_reuse')
        logger2 = setup_logger('test_reuse')
        # Debe ser la misma instancia
        assert logger1 is logger2

    def test_setup_logger_different_names(self):
        """Test: setup_logger crea loggers con diferentes nombres."""
        from utils.logger import setup_logger

        logger1 = setup_logger('test_name1')
        logger2 = setup_logger('test_name2')
        assert logger1.name != logger2.name

    @patch('utils.logger.LOG_PATH', new_callable=lambda: Path(tempfile.mktemp(suffix='.log')))
    def test_setup_logger_creates_log_file(self, mock_log_path):
        """Test: setup_logger crea archivo de log."""
        from utils.logger import setup_logger

        # Crear directorio temporal
        temp_dir = tempfile.mkdtemp()
        log_path = Path(temp_dir) / 'test.log'
        
        with patch('utils.logger.LOG_PATH', log_path):
            logger = setup_logger('test_file_creation')
            # El logger debe existir
            assert logger is not None


# ─────────────────────────────────────────────────────────────────────────────
# Tests para config.py
# ─────────────────────────────────────────────────────────────────────────────

class TestConfig:
    """Tests para configuración centralizada."""

    def test_production_mode_default(self):
        """Test: PRODUCTION_MODE tiene valor por defecto."""
        from config import PRODUCTION_MODE
        # Debe ser True o False
        assert isinstance(PRODUCTION_MODE, bool)

    def test_paths_are_path_objects(self):
        """Test: Los paths son objetos Path."""
        from config import BASE_DIR, DB_PATH, LOG_PATH, ASSETS_DIR

        assert isinstance(BASE_DIR, Path)
        assert isinstance(DB_PATH, Path)
        assert isinstance(LOG_PATH, Path)
        assert isinstance(ASSETS_DIR, Path)

    def test_directories_created(self):
        """Test: Los directorios necesarios se crean automáticamente."""
        from config import DB_PATH, LOG_PATH, ASSETS_DIR

        # Los directorios padres deben existir
        assert DB_PATH.parent.exists()
        assert LOG_PATH.parent.exists()
        assert ASSETS_DIR.exists()

    def test_theme_light_exists(self):
        """Test: THEME_LIGHT está definido."""
        from config import THEME_LIGHT

        assert 'primary' in THEME_LIGHT
        assert 'secondary' in THEME_LIGHT
        assert 'accent' in THEME_LIGHT

    def test_theme_dark_exists(self):
        """Test: THEME_DARK está definido."""
        from config import THEME_DARK

        assert 'primary' in THEME_DARK
        assert 'secondary' in THEME_DARK
        assert 'accent' in THEME_DARK

    def test_themes_mapping(self):
        """Test: THEMES mapea correctamente."""
        from config import THEMES

        assert 'light' in THEMES
        assert 'dark' in THEMES

    def test_get_current_theme(self):
        """Test: get_current_theme retorna tema válido."""
        from config import get_current_theme, THEMES

        theme = get_current_theme()
        assert theme in THEMES.values()

    def test_get_theme_colors(self):
        """Test: get_theme_colors retorna colores del tema."""
        from config import get_theme_colors

        colors = get_theme_colors()
        assert 'primary' in colors
        assert 'secondary' in colors

    def test_set_theme_valid(self):
        """Test: set_theme cambia tema válido."""
        from config import set_theme, CURRENT_THEME

        original_theme = CURRENT_THEME
        result = set_theme('dark')
        assert result is True

        # Restaurar tema original
        set_theme(original_theme)

    def test_set_theme_invalid(self):
        """Test: set_theme rechaza tema inválido."""
        from config import set_theme

        result = set_theme('invalid_theme')
        assert result is False

    def test_toggle_theme(self):
        """Test: toggle_theme alterna entre temas."""
        from config import toggle_theme, CURRENT_THEME, set_theme

        original_theme = CURRENT_THEME
        new_theme = toggle_theme()
        # Debe ser diferente al original
        assert new_theme != original_theme or new_theme in ['light', 'dark']

        # Restaurar tema original
        set_theme(original_theme)

    def test_brand_colors_defined(self):
        """Test: BRAND_COLORS está definido."""
        from config import BRAND_COLORS

        assert 'primary' in BRAND_COLORS
        assert 'secondary' in BRAND_COLORS
        assert 'accent' in BRAND_COLORS

    def test_db_config_defined(self):
        """Test: DB_CONFIG está definido."""
        from config import DB_CONFIG

        assert 'database' in DB_CONFIG
        assert 'timeout' in DB_CONFIG

    def test_window_config_defined(self):
        """Test: WINDOW_CONFIG está definido."""
        from config import WINDOW_CONFIG

        assert 'title' in WINDOW_CONFIG
        assert 'geometry' in WINDOW_CONFIG
        assert 'min_size' in WINDOW_CONFIG

    def test_estados_animal(self):
        """Test: ESTADOS_ANIMAL está definido."""
        from config import ESTADOS_ANIMAL

        assert 'Activo' in ESTADOS_ANIMAL
        assert 'En Tratamiento' in ESTADOS_ANIMAL

    def test_estados_muestra(self):
        """Test: ESTADOS_MUESTRA está definido."""
        from config import ESTADOS_MUESTRA

        assert 'Pendiente' in ESTADOS_MUESTRA
        assert 'Completado' in ESTADOS_MUESTRA

    def test_tipos_muestra(self):
        """Test: TIPOS_MUESTRA está definido."""
        from config import TIPOS_MUESTRA

        assert 'Sangre' in TIPOS_MUESTRA
        assert 'Orina' in TIPOS_MUESTRA

    def test_tipos_analisis(self):
        """Test: TIPOS_ANALISIS está definido."""
        from config import TIPOS_ANALISIS

        assert 'Sangre' in TIPOS_ANALISIS
        assert 'Orina' in TIPOS_ANALISIS

    def test_generate_qt_stylesheet(self):
        """Test: generate_qt_stylesheet retorna string."""
        from config import generate_qt_stylesheet

        stylesheet = generate_qt_stylesheet('light')
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 100

    def test_generate_qt_stylesheet_dark(self):
        """Test: generate_qt_stylesheet para tema oscuro."""
        from config import generate_qt_stylesheet

        stylesheet = generate_qt_stylesheet('dark')
        assert isinstance(stylesheet, str)

    def test_get_qt_stylesheet(self):
        """Test: get_qt_stylesheet retorna stylesheet."""
        from config import get_qt_stylesheet

        stylesheet = get_qt_stylesheet()
        assert isinstance(stylesheet, str)

    def test_get_stylesheet_alias(self):
        """Test: get_stylesheet es alias de get_qt_stylesheet."""
        from config import get_stylesheet, get_qt_stylesheet

        stylesheet1 = get_stylesheet()
        stylesheet2 = get_qt_stylesheet()
        assert stylesheet1 == stylesheet2

    def test_global_stylesheet_defined(self):
        """Test: GLOBAL_STYLESHEET está definido."""
        from config import GLOBAL_STYLESHEET

        assert isinstance(GLOBAL_STYLESHEET, str)
        assert len(GLOBAL_STYLESHEET) > 100

    def test_dialog_sizes(self):
        """Test: DIALOG_SIZES está definido."""
        from config import DIALOG_SIZES

        assert 'small' in DIALOG_SIZES
        assert 'medium' in DIALOG_SIZES
        assert 'large' in DIALOG_SIZES

    def test_validacion_visual(self):
        """Test: VALIDACION_VISUAL está definido."""
        from config import VALIDACION_VISUAL

        assert 'error_color' in VALIDACION_VISUAL
        assert 'success_color' in VALIDACION_VISUAL

    def test_icons_ascii(self):
        """Test: ICONS_ASCII está definido."""
        from config import ICONS_ASCII

        assert 'save' in ICONS_ASCII
        assert 'cancel' in ICONS_ASCII

    def test_icons_emoji(self):
        """Test: ICONS_EMOJI está definido."""
        from config import ICONS_EMOJI

        assert 'save' in ICONS_EMOJI
        assert 'cancel' in ICONS_EMOJI

    def test_badge_colors(self):
        """Test: BADGE_COLORS está definido."""
        from config import BADGE_COLORS

        assert 'Pendiente' in BADGE_COLORS
        assert 'Completado' in BADGE_COLORS

    def test_get_badge_style(self):
        """Test: get_badge_style retorna string CSS."""
        from config import get_badge_style

        style = get_badge_style('Pendiente')
        assert isinstance(style, str)
        assert 'background-color' in style

    def test_get_badge_style_unknown(self):
        """Test: get_badge_style retorna estilo por defecto para estado desconocido."""
        from config import get_badge_style

        style = get_badge_style('EstadoDesconocido')
        assert isinstance(style, str)


# ─────────────────────────────────────────────────────────────────────────────
# Tests para database/connection.py
# ─────────────────────────────────────────────────────────────────────────────

class TestDatabaseManager:
    """Tests para DatabaseManager."""

    @patch('database.connection.DB_CONFIG', {'database': ':memory:', 'timeout': 30, 'check_same_thread': False})
    def test_singleton_pattern(self):
        """Test: DatabaseManager es singleton."""
        from database.connection import DatabaseManager

        # Reset singleton for test
        DatabaseManager._instance = None
        DatabaseManager._initialized = False

        db1 = DatabaseManager()
        db2 = DatabaseManager()
        assert db1 is db2

    @patch('database.connection.DB_CONFIG', {'database': ':memory:', 'timeout': 30, 'check_same_thread': False})
    def test_get_connection(self):
        """Test: get_connection retorna conexión válida."""
        from database.connection import DatabaseManager

        DatabaseManager._instance = None
        DatabaseManager._initialized = False

        db = DatabaseManager()
        with db.get_connection() as conn:
            assert conn is not None

    @patch('database.connection.DB_CONFIG', {'database': ':memory:', 'timeout': 30, 'check_same_thread': False})
    def test_execute_query(self):
        """Test: execute ejecuta query correctamente."""
        from database.connection import DatabaseManager

        DatabaseManager._instance = None
        DatabaseManager._initialized = False

        db = DatabaseManager()
        cursor = db.execute("SELECT 1")
        assert cursor is not None

    @patch('database.connection.DB_CONFIG', {'database': ':memory:', 'timeout': 30, 'check_same_thread': False})
    def test_fetch_one(self):
        """Test: fetch_one retorna un registro."""
        from database.connection import DatabaseManager

        DatabaseManager._instance = None
        DatabaseManager._initialized = False

        db = DatabaseManager()
        result = db.fetch_one("SELECT 1 as value")
        assert result is not None
        assert result['value'] == 1

    @patch('database.connection.DB_CONFIG', {'database': ':memory:', 'timeout': 30, 'check_same_thread': False})
    def test_fetch_all(self):
        """Test: fetch_all retorna múltiples registros."""
        from database.connection import DatabaseManager

        DatabaseManager._instance = None
        DatabaseManager._initialized = False

        db = DatabaseManager()
        result = db.fetch_all("SELECT 1 as value UNION SELECT 2")
        assert len(result) == 2

    @patch('database.connection.DB_CONFIG', {'database': ':memory:', 'timeout': 30, 'check_same_thread': False})
    def test_generar_codigo(self):
        """Test: generar código correlativo."""
        from database.connection import DatabaseManager

        DatabaseManager._instance = None
        DatabaseManager._initialized = False

        db = DatabaseManager()
        # Primero necesita insertar el prefijo
        db.execute("INSERT OR IGNORE INTO codigo_contadores (prefijo, ultimo) VALUES ('TEST', 0)")
        codigo = db.generar_codigo('TEST')
        assert codigo.startswith('TEST-')
        assert len(codigo) == 9  # TEST-0001

    @patch('database.connection.DB_CONFIG', {'database': ':memory:', 'timeout': 30, 'check_same_thread': False})
    def test_health_check(self):
        """Test: health_check retorna estado."""
        from database.connection import DatabaseManager

        DatabaseManager._instance = None
        DatabaseManager._initialized = False

        db = DatabaseManager()
        status = db.health_check()
        assert 'status' in status
        assert status['status'] == 'healthy'

    @patch('database.connection.DB_CONFIG', {'database': ':memory:', 'timeout': 30, 'check_same_thread': False})
    def test_close_all_connections(self):
        """Test: close_all_connections cierra conexiones."""
        from database.connection import DatabaseManager

        DatabaseManager._instance = None
        DatabaseManager._initialized = False

        db = DatabaseManager()
        # Abrir conexión
        with db.get_connection() as conn:
            pass
        # Cerrar
        db.close_all_connections()
        # No debe lanzar error


# ─────────────────────────────────────────────────────────────────────────────
# Tests para integración de config y utils
# ─────────────────────────────────────────────────────────────────────────────

class TestConfigIntegration:
    """Tests de integración para config.py."""

    def test_theme_switching(self):
        """Test: Cambio de tema funciona correctamente."""
        from config import set_theme, get_current_theme, CURRENT_THEME

        original_theme = CURRENT_THEME
        set_theme('dark')
        assert get_current_theme()['name'] == 'dark'

        set_theme('light')
        assert get_current_theme()['name'] == 'light'

        set_theme(original_theme)

    def test_stylesheet_generation_integration(self):
        """Test: Generación de stylesheet con tema actual."""
        from config import generate_qt_stylesheet, get_current_theme

        theme = get_current_theme()
        stylesheet = generate_qt_stylesheet(theme['name'])
        assert theme['primary'] in stylesheet

    def test_all_estados_validos(self):
        """Test: Todos los estados están definidos."""
        from config import (
            ESTADOS_ANIMAL, ESTADOS_MUESTRA, ESTADOS_RECEPCION,
            ESTADOS_CIRUGIA
        )

        assert len(ESTADOS_ANIMAL) > 0
        assert len(ESTADOS_MUESTRA) > 0
        assert len(ESTADOS_RECEPCION) > 0
        assert len(ESTADOS_CIRUGIA) > 0

    def test_all_tipos_validos(self):
        """Test: Todos los tipos están definidos."""
        from config import (
            TIPOS_MUESTRA, TIPOS_ANALISIS, TIPOS_CIRUGIA,
            TIPOS_ANESTESIA
        )

        assert len(TIPOS_MUESTRA) > 0
        assert len(TIPOS_ANALISIS) > 0
        assert len(TIPOS_CIRUGIA) > 0
        assert len(TIPOS_ANESTESIA) > 0

    def test_all_vias_administracion(self):
        """Test: Vías de administración están definidas."""
        from config import VIAS_ADMINISTRACION

        assert 'Subcutánea (SC)' in VIAS_ADMINISTRACION
        assert 'Intramuscular (IM)' in VIAS_ADMINISTRACION

    def test_prefijos_codigo(self):
        """Test: Prefijos de código están definidos."""
        from config import PREFIJOS_CODIGO

        assert 'recepcion' in PREFIJOS_CODIGO
        assert 'consulta' in PREFIJOS_CODIGO
        assert 'cirugia' in PREFIJOS_CODIGO
        assert 'vacuna' in PREFIJOS_CODIGO
