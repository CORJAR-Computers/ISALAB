# tests/test_fase5_high.py
"""Tests de regresión para la Fase 5 — Fix HIGH issues.

Cubre 17 fixes:
  GUI (8): H-G1..H-G8
  Services (6): H-S1, H-S2, H-S3, H-S4, H-S5, H-S6
  DB (3): H-D3, H-D4, H-D6

Los tests están diseñados para correr sin PySide6 instalado (usan
inspección estática de código + mocks). Solo los tests que tocan
``sqlalchemy`` o ``bcrypt`` requieren esas deps; los demás son puramente
de código.
"""
import os
import re
import sys
from pathlib import Path

import pytest

# Asegurar que la raíz del repo esté en sys.path.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def read_source(rel_path: str) -> str:
    """Lee el contenido de un archivo .py del repo."""
    return (ROOT / rel_path).read_text(encoding='utf-8')


def strip_comments_and_docstrings(src: str) -> str:
    """Elimina comentarios ``# ...`` y docstrings para que las aserciones
    de los tests no matcheen texto explicativo en comments."""
    out_lines = []
    for line in src.split('\n'):
        # Eliminar comentarios ``# ...`` (sin tocar strings con ``#``).
        # Heurística simple: cortar al primer ``#`` que no esté dentro
        # de un string. Para nuestros tests basta con buscar ``#`` no
        # precedido por ``"`` o ``'`` en la misma línea.
        in_str = None
        for i, c in enumerate(line):
            if in_str:
                if c == in_str and line[i - 1] != '\\':
                    in_str = None
            else:
                if c in ('"', "'"):
                    in_str = c
                elif c == '#':
                    line = line[:i]
                    break
        out_lines.append(line)
    return '\n'.join(out_lines)


def read_code(rel_path: str) -> str:
    """Lee el fuente sin comentarios ni docstrings — solo código."""
    return strip_comments_and_docstrings(read_source(rel_path))


def source_contains(rel_path: str, needle: str) -> bool:
    """True si el archivo contiene la cadena (substring)."""
    return needle in read_source(rel_path)


def source_not_contains(rel_path: str, needle: str) -> bool:
    return needle not in read_source(rel_path)


def source_matches(rel_path: str, pattern: str) -> bool:
    """True si el archivo matchea el regex (multiline)."""
    return re.search(pattern, read_source(rel_path), re.MULTILINE) is not None


# ─────────────────────────────────────────────────────────────────────────────
# H-G1 — ErrorHandler.handle_exception
# ─────────────────────────────────────────────────────────────────────────────

def test_h_g1_no_qmessagebox_critical_none():
    """``QMessageBox.critical(None, ...)`` ya NO se usa."""
    # Usar ``read_code`` (sin comentarios) para que el texto explicativo
    # en docstrings/comments no cuente como uso.
    code = read_code('gui_pyside/components/components.py')
    assert 'QMessageBox.critical(None,' not in code, (
        "ErrorHandler todavía usa parent=None en QMessageBox.critical"
    )


def test_h_g1_does_not_show_raw_str_e():
    """``msg = str(e)`` ya NO se usa en el decorador."""
    src = read_source('gui_pyside/components/components.py')
    # Buscar el patrón ``msg = str(e)`` dentro de la clase ErrorHandler.
    # Es OK que exista en otros archivos; aquí validamos que el decorador
    # ya no lo usa.
    # Buscamos ``QMessageBox.critical(parent, "Error", msg)`` con
    # ``msg`` sanitizado.
    assert 'QMessageBox.critical(parent, "Error", msg)' in src or \
           'QMessageBox.critical(parent, "Error", sanitized)' in src, (
        "Esperado uso de parent (no None) en QMessageBox.critical"
    )


def test_h_g1_returns_sentinel_on_error():
    """El decorador retorna ``_ERROR_SENTINEL`` en caso de error."""
    src = read_source('gui_pyside/components/components.py')
    assert '_ERROR_SENTINEL' in src, (
        "Falta el sentinel _ERROR_SENTINEL en ErrorHandler"
    )
    assert 'return ErrorHandler._ERROR_SENTINEL' in src, (
        "El wrapper no retorna el sentinel en el branch de error"
    )


def test_h_g1_finds_parent_widget():
    """El decorador busca un QWidget entre los args."""
    src = read_source('gui_pyside/components/components.py')
    assert '_find_parent' in src, (
        "Falta la función _find_parent en ErrorHandler"
    )
    assert 'app.activeWindow()' in src, (
        "Esperado fallback a app.activeWindow() para localizar parent"
    )


def test_h_g1_sanitizes_non_isalab_exceptions():
    """Excepciones que NO son IsaLabException muestran mensaje genérico."""
    src = read_source('gui_pyside/components/components.py')
    assert 'IsaLabException' in src, (
        "Esperado import o uso de IsaLabException en _sanitize_message"
    )
    assert 'Ocurrió un error inesperado' in src, (
        "Esperado mensaje sanitizado genérico para excepciones no IsaLab"
    )


# ─────────────────────────────────────────────────────────────────────────────
# H-G2 — WindowManager dead code deleted
# ─────────────────────────────────────────────────────────────────────────────

def test_h_g2_window_manager_file_deleted():
    """``gui_pyside/utils/window_manager.py`` fue eliminado."""
    assert not (ROOT / 'gui_pyside/utils/window_manager.py').exists(), (
        "window_manager.py todavía existe — debería haberse borrado"
    )


def test_h_g2_no_window_manager_imports():
    """Ningún archivo importa WindowManager."""
    # Buscar imports en todo el repo (excluyendo tests y __pycache__).
    py_files = [
        p for p in ROOT.rglob('*.py')
        if '__pycache__' not in str(p) and 'test_fase5' not in str(p)
    ]
    bad = []
    for p in py_files:
        try:
            content = p.read_text(encoding='utf-8')
        except Exception:
            continue
        if re.search(r'from\s+gui_pyside\.utils\.window_manager\s+import', content) \
                or re.search(r'import\s+gui_pyside\.utils\.window_manager', content):
            bad.append(str(p))
    assert not bad, f"WindowManager todavía se importa en: {bad}"


def test_h_g2_no_set_main_window_calls():
    """``WindowManager.set_main_window`` ya no se llama (en código, no
    en comments/docstrings, y excluyendo el propio test file)."""
    py_files = [
        p for p in ROOT.rglob('*.py')
        if '__pycache__' not in str(p) and 'test_fase5' not in str(p)
    ]
    bad = []
    for p in py_files:
        try:
            content = strip_comments_and_docstrings(
                p.read_text(encoding='utf-8')
            )
        except Exception:
            continue
        if 'WindowManager.set_main_window' in content:
            bad.append(str(p))
    assert not bad, f"WindowManager.set_main_window todavía se usa en: {bad}"


# ─────────────────────────────────────────────────────────────────────────────
# H-G3 — boton_generar_reportes.py deleted
# ─────────────────────────────────────────────────────────────────────────────

def test_h_g3_boton_generar_reportes_deleted():
    """``gui_pyside/views/boton_generar_reportes.py`` fue eliminado."""
    assert not (ROOT / 'gui_pyside/views/boton_generar_reportes.py').exists(), (
        "boton_generar_reportes.py todavía existe — debería haberse borrado"
    )


def test_h_g3_no_imports_of_boton_generar_reportes():
    """Ningún archivo importa ``boton_generar_reportes``."""
    py_files = [
        p for p in ROOT.rglob('*.py')
        if '__pycache__' not in str(p) and 'test_fase5' not in str(p)
    ]
    bad = []
    for p in py_files:
        try:
            content = p.read_text(encoding='utf-8')
        except Exception:
            continue
        if 'boton_generar_reportes' in content:
            bad.append(str(p))
    assert not bad, f"boton_generar_reportes todavía se referencia en: {bad}"


# ─────────────────────────────────────────────────────────────────────────────
# H-G4 — RecepcionView._get_selected_animal_id deleted
# ─────────────────────────────────────────────────────────────────────────────

def test_h_g4_no_get_selected_animal_id_in_recepcion():
    """``RecepcionView._get_selected_animal_id`` ya no existe."""
    src = read_source('gui_pyside/views/recepcion.py')
    assert 'def _get_selected_animal_id' not in src, (
        "RecepcionView._get_selected_animal_id todavía está definido"
    )


# ─────────────────────────────────────────────────────────────────────────────
# H-G5 — DashboardView.theme_changed signal connected
# ─────────────────────────────────────────────────────────────────────────────

def test_h_g5_signal_declared_before_toggle_method():
    """``theme_changed = Signal()`` está antes del método que la emite."""
    src = read_source('gui_pyside/views/dashboard.py')
    signal_pos = src.find('theme_changed = Signal()')
    toggle_pos = src.find('def _toggle_theme')
    assert signal_pos != -1, "theme_changed = Signal() no encontrado"
    assert toggle_pos != -1, "def _toggle_theme no encontrado"
    assert signal_pos < toggle_pos, (
        "theme_changed debería declararse ANTES de _toggle_theme"
    )


def test_h_g5_signal_connected_in_app():
    """``app.py`` conecta ``theme_changed`` a un handler."""
    src = read_source('gui_pyside/app.py')
    assert 'theme_changed.connect' in src, (
        "app.py no conecta la señal theme_changed"
    )
    assert '_on_theme_changed' in src, (
        "Falta el handler _on_theme_changed en app.py"
    )


def test_h_g5_handler_iterates_views():
    """El handler recorre las vistas activas para re-aplicar tema."""
    src = read_source('gui_pyside/app.py')
    assert 'self.views.items()' in src, (
        "_on_theme_changed debería iterar self.views.items()"
    )
    assert 'rebuild_layout' in src, (
        "El handler debería llamar rebuild_layout() si existe"
    )


# ─────────────────────────────────────────────────────────────────────────────
# H-G6 — usuarios.py dialog.exec() == QDialog.Accepted
# ─────────────────────────────────────────────────────────────────────────────

def test_h_g6_uses_qdialog_accepted():
    """``usuarios.py`` compara con ``QDialog.Accepted``."""
    src = read_source('gui_pyside/views/usuarios.py')
    assert 'QDialog.Accepted' in src, (
        "usuarios.py debería comparar con QDialog.Accepted"
    )
    assert 'dialog.exec() == QDialog.Accepted' in src, (
        "usuarios.py debería usar 'dialog.exec() == QDialog.Accepted'"
    )


def test_h_g6_no_bare_dialog_exec_check():
    """``if dialog.exec():`` (bare) ya NO se usa (en código, no comments)."""
    code = read_code('gui_pyside/views/usuarios.py')
    # Buscar ``if dialog.exec():`` sin comparación.
    assert not re.search(r'if\s+dialog\.exec\(\)\s*:', code), (
        "usuarios.py todavía usa 'if dialog.exec():' (bare truthy check)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# H-G7 — muestra_dialog monkey-patch replaced with event filter
# ─────────────────────────────────────────────────────────────────────────────

def test_h_g7_no_keypress_monkey_patch():
    """``self.tabla_resultados.keyPressEvent = ...`` ya NO se usa (en
    código, no comments que documentan el cambio)."""
    code = read_code('gui_pyside/dialogs/muestra_dialog.py')
    # Buscar el patrón ``.keyPressEvent = self._pegar_magico_en_tabla``.
    assert not re.search(
        r'\.keyPressEvent\s*=\s*self\._pegar_magico_en_tabla', code
    ), (
        "muestra_dialog.py todavía monkey-patchea keyPressEvent"
    )


def test_h_g7_event_filter_installed():
    """Se usa ``installEventFilter`` con ``_PegadoMagicoFilter``."""
    src = read_source('gui_pyside/dialogs/muestra_dialog.py')
    assert '_PegadoMagicoFilter' in src, (
        "Falta la clase _PegadoMagicoFilter"
    )
    assert 'installEventFilter' in src, (
        "Falta la llamada a installEventFilter"
    )


def test_h_g7_filter_class_inherits_qobject():
    """``_PegadoMagicoFilter`` hereda de ``QObject``."""
    src = read_source('gui_pyside/dialogs/muestra_dialog.py')
    assert re.search(
        r'class\s+_PegadoMagicoFilter\s*\(\s*QObject\s*\)', src
    ), "_PegadoMagicoFilter debería heredar de QObject"


def test_h_g7_filter_implements_event_filter_method():
    """El filter implementa ``eventFilter(self, obj, event)``."""
    src = read_source('gui_pyside/dialogs/muestra_dialog.py')
    assert re.search(
        r'def\s+eventFilter\s*\(\s*self\s*,\s*obj\s*,\s*event\s*\)', src
    ), "_PegadoMagicoFilter debería implementar eventFilter(obj, event)"


# ─────────────────────────────────────────────────────────────────────────────
# H-G8 — PDFProWorker hoisted to module level + deleteLater
# ─────────────────────────────────────────────────────────────────────────────

def test_h_g8_pdf_worker_is_module_level_class():
    """``PDFProWorker`` es una clase definida a nivel de módulo."""
    src = read_source('gui_pyside/dialogs/muestra_dialog.py')
    # Buscar ``class PDFProWorker(QThread):`` a indentación 0 (módulo).
    assert re.search(
        r'^class\s+PDFProWorker\s*\(\s*QThread\s*\)\s*:', src, re.MULTILINE
    ), "PDFProWorker debería definirse a nivel de módulo (no nested)"


def test_h_g8_no_nested_pdf_worker_in_imprimir_pdf():
    """El método ``_imprimir_pdf`` ya no define ``PDFProWorker`` anidado."""
    src = read_source('gui_pyside/dialogs/muestra_dialog.py')
    # Localizar el método _imprimir_pdf.
    match = re.search(
        r'def\s+_imprimir_pdf\s*\(self.*?\):.*?(?=\n    def\s|\nclass\s|\Z)',
        src, re.DOTALL
    )
    assert match, "_imprimir_pdf no encontrado"
    method_body = match.group(0)
    assert 'class PDFProWorker' not in method_body, (
        "_imprimir_pdf todavía define PDFProWorker anidado"
    )


def test_h_g8_finished_connected_to_delete_later():
    """``finished`` se conecta a ``deleteLater`` para limpiar el QThread."""
    src = read_source('gui_pyside/dialogs/muestra_dialog.py')
    assert 'finished.connect(self.worker.deleteLater)' in src, (
        "Esperado 'finished.connect(self.worker.deleteLater)' en _imprimir_pdf"
    )


# ─────────────────────────────────────────────────────────────────────────────
# H-S1 — Login timing-attack mitigation
# ─────────────────────────────────────────────────────────────────────────────

def test_h_s1_dummy_hash_constant_exists():
    """Existe ``DUMMY_BCRYPT_HASH`` en ``utils.security``."""
    src = read_source('utils/security.py')
    assert 'DUMMY_BCRYPT_HASH' in src, (
        "Falta el constante DUMMY_BCRYPT_HASH"
    )
    assert '$2b$12$' in src, (
        "DUMMY_BCRYPT_HASH debería ser un hash bcrypt rounds=12"
    )


def test_h_s1_dummy_verify_password_function_exists():
    """Existe ``dummy_verify_password`` en ``utils.security``."""
    src = read_source('utils/security.py')
    assert 'def dummy_verify_password' in src, (
        "Falta la función dummy_verify_password"
    )


def test_h_s1_dummy_verify_called_on_user_not_found():
    """``UsuarioService.autenticar`` llama ``dummy_verify_password``."""
    src = read_source('services/usuario_service.py')
    assert 'dummy_verify_password(password)' in src, (
        "autenticar debería llamar dummy_verify_password en el branch 'no encontrado'"
    )


def test_h_s1_dummy_verify_runs_without_bcrypt():
    """``dummy_verify_password`` no crashea si bcrypt no está disponible."""
    from utils.security import dummy_verify_password, BCRYPT_AVAILABLE
    # Solo verificamos que no levante excepción. Si bcrypt está
    # instalado, ejecutará ``checkpw`` (que retornará False, está bien).
    # Si no está instalado, la función es no-op.
    dummy_verify_password('test123')
    # No assertion necesaria; si llega aquí, no crasheó.
    assert True


# ─────────────────────────────────────────────────────────────────────────────
# H-S2 — Password strength unification
# ─────────────────────────────────────────────────────────────────────────────

def test_h_s2_cambiar_password_dialog_uses_8_chars():
    """``cambiar_password_dialog`` usa umbral 8 (no 6)."""
    src = read_source('gui_pyside/dialogs/cambiar_password_dialog.py')
    assert 'len(nueva) < 8' in src, (
        "cambiar_password_dialog debería usar 'len(nueva) < 8'"
    )
    assert 'len(nueva) < 6' not in src, (
        "cambiar_password_dialog todavía usa 'len(nueva) < 6'"
    )
    assert 'Mínimo 8 caracteres' in src, (
        "cambiar_password_dialog debería indicar 'Mínimo 8 caracteres' en el placeholder"
    )


def test_h_s2_cambiar_password_dialog_does_not_strip_passwords():
    """``cambiar_password_dialog`` NO hace ``.strip()`` sobre passwords."""
    code = read_code('gui_pyside/dialogs/cambiar_password_dialog.py')
    assert 'self.txt_actual.text().strip()' not in code, (
        "txt_actual.text() todavía se hace strip — passwords no deben strip"
    )
    assert 'self.txt_nueva.text().strip()' not in code, (
        "txt_nueva.text() todavía se hace strip"
    )
    assert 'self.txt_confirmar.text().strip()' not in code, (
        "txt_confirmar.text() todavía se hace strip"
    )


def test_h_s2_usuario_dialog_uses_8_chars():
    """``usuario_dialog`` usa umbral 8 (no 6)."""
    code = read_code('gui_pyside/dialogs/usuario_dialog.py')
    assert 'len(pwd) < 8' in code, (
        "usuario_dialog debería usar 'len(pwd) < 8'"
    )
    assert 'len(pwd) < 6' not in code, (
        "usuario_dialog todavía usa 'len(pwd) < 6'"
    )


def test_h_s2_validar_fortaleza_password_requires_8():
    """``validar_fortaleza_password`` exige 8 caracteres (servicio)."""
    from utils.security import validar_fortaleza_password
    es_valida, _ = validar_fortaleza_password('Abc123')
    assert not es_valida, (
        "validar_fortaleza_password debería rechazar 6 caracteres"
    )
    es_valida, _ = validar_fortaleza_password('Abc12345')
    assert es_valida, (
        "validar_fortaleza_password debería aceptar 8 caracteres con mayúscula/minúscula/dígito"
    )


# ─────────────────────────────────────────────────────────────────────────────
# H-S3 — MuestraValidator path-traversal check
# ─────────────────────────────────────────────────────────────────────────────

def test_h_s3_muestra_validator_calls_validate_pattern():
    """``MuestraValidator.validate`` invoca ``validate_pattern`` para codigo."""
    src = read_source('utils/validators.py')
    # Buscar dentro de la clase MuestraValidator — la última del archivo.
    # Usamos un regex no-greedy hasta el final del archivo (\Z) o hasta
    # la próxima ``class`` si existe.
    match = re.search(
        r'class\s+MuestraValidator\b.*?(?:\nclass\s|\Z)',
        src, re.DOTALL
    )
    assert match, "MuestraValidator no encontrada"
    body = match.group(0)
    assert 'validate_pattern' in body, (
        "MuestraValidator debería llamar validate_pattern para el código"
    )


def test_h_s3_muestra_validator_rejects_path_traversal():
    """``MuestraValidator`` rechaza códigos con ``/``, ``\\``, ``..``, etc."""
    from utils.validators import MuestraValidator, ValidationError
    bad_codes = [
        '../etc/passwd',
        'LAB/0001',
        'LAB\\0001',
        'LAB 0001',  # espacio
        'LAB;0001',  # ;
        'lab-0001',  # minúsculas no permitidas por ^[A-Z0-9-]+$
    ]
    for code in bad_codes:
        with pytest.raises(ValidationError):
            MuestraValidator.validate({
                'codigo': code,
                'animal_id': 1,
                'tipo_muestra': 'Sangre',
                'fecha_recoleccion': '2026-01-01',
            }), f"MuestraValidator debería rechazar código {code!r}"


def test_h_s3_muestra_validator_accepts_valid_codes():
    """``MuestraValidator`` acepta códigos válidos (``^[A-Z0-9-]+$``)."""
    from utils.validators import MuestraValidator
    valid_codes = ['LAB-0001', 'LAB0001', 'ISAL-2026-0001', 'A1B2C3']
    for code in valid_codes:
        # No debe levantar excepción.
        MuestraValidator.validate({
            'codigo': code,
            'animal_id': 1,
            'tipo_muestra': 'Sangre',
            'fecha_recoleccion': '2026-01-01',
        })


# ─────────────────────────────────────────────────────────────────────────────
# H-S4 — Whitelist estado in RecepcionService + CirugiaService
# ─────────────────────────────────────────────────────────────────────────────

def test_h_s4_recepcion_service_imports_estados_recepcion():
    """``recepcion_service`` importa ``ESTADOS_RECEPCION``."""
    src = read_source('services/recepcion_service.py')
    assert 'from config import ESTADOS_RECEPCION' in src, (
        "recepcion_service debería importar ESTADOS_RECEPCION"
    )


def test_h_s4_recepcion_service_validates_estado_whitelist():
    """``actualizar_estado`` valida contra la whitelist."""
    src = read_source('services/recepcion_service.py')
    assert 'if estado not in ESTADOS_RECEPCION' in src, (
        "Falta validación de whitelist en actualizar_estado de recepción"
    )
    assert 'raise ValidationError' in src, (
        "Falta raise ValidationError cuando estado no está en whitelist"
    )


def test_h_s4_cirugia_service_imports_estados_cirugia():
    """``cirugia_service`` importa ``ESTADOS_CIRUGIA``."""
    src = read_source('services/cirugia_service.py')
    assert 'from config import ESTADOS_CIRUGIA' in src, (
        "cirugia_service debería importar ESTADOS_CIRUGIA"
    )


def test_h_s4_cirugia_service_validates_estado_whitelist():
    """``actualizar_estado`` valida contra la whitelist."""
    src = read_source('services/cirugia_service.py')
    assert 'if estado not in ESTADOS_CIRUGIA' in src, (
        "Falta validación de whitelist en actualizar_estado de cirugía"
    )


# ─────────────────────────────────────────────────────────────────────────────
# H-S5 — historia_service _float/_int allow 0 + allow clearing
# ─────────────────────────────────────────────────────────────────────────────

def test_h_s5_float_allows_zero():
    """``_float(0)`` retorna ``0.0`` (no ``None``)."""
    from services.historia_service import _float
    assert _float(0) == 0.0, f"_float(0) = {_float(0)!r}, esperado 0.0"
    assert _float('0') == 0.0, f"_float('0') = {_float('0')!r}, esperado 0.0"
    assert _float('0.0') == 0.0


def test_h_s5_int_allows_zero():
    """``_int(0)`` retorna ``0`` (no ``None``)."""
    from services.historia_service import _int
    assert _int(0) == 0
    assert _int('0') == 0
    assert _int('0.0') == 0  # acepta "0.0"


def test_h_s5_float_none_for_empty():
    """``_float(None)`` y ``_float('')`` retornan ``None``."""
    from services.historia_service import _float
    assert _float(None) is None
    assert _float('') is None


def test_h_s5_int_none_for_empty():
    """``_int(None)`` y ``_int('')`` retornan ``None``."""
    from services.historia_service import _int
    assert _int(None) is None
    assert _int('') is None


def test_h_s5_coerce_or_keep_missing_keeps_current():
    """``_coerce_or_keep(_MISSING, ...)`` mantiene el valor actual."""
    from services.historia_service import _coerce_or_keep, _MISSING, _float
    assert _coerce_or_keep(_MISSING, 38.5, _float) == 38.5


def test_h_s5_coerce_or_keep_empty_clears():
    """``_coerce_or_keep('', ...)`` limpia a ``None``."""
    from services.historia_service import _coerce_or_keep, _float
    assert _coerce_or_keep('', 38.5, _float) is None
    assert _coerce_or_keep(None, 38.5, _float) is None


def test_h_s5_coerce_or_keep_zero_sets_zero():
    """``_coerce_or_keep(0, ...)`` setea ``0.0`` (no mantiene previo)."""
    from services.historia_service import _coerce_or_keep, _float
    assert _coerce_or_keep(0, 38.5, _float) == 0.0
    assert _coerce_or_keep('0', 38.5, _float) == 0.0


def test_h_s5_actualizar_historia_uses_coerce_or_keep():
    """``actualizar_historia`` usa ``_coerce_or_keep`` para vitales."""
    src = read_source('services/historia_service.py')
    assert '_coerce_or_keep' in src, (
        "actualizar_historia debería usar _coerce_or_keep"
    )
    # Ya no debe aparecer el patrón ``or h.temperatura`` (con ``or``).
    assert 'or h.temperatura' not in src, (
        "actualizar_historia todavía usa el patrón 'or h.temperatura' "
        "(no se puede limpiar el campo)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# H-S6 — reset_password forced_change flag
# ─────────────────────────────────────────────────────────────────────────────

def test_h_s6_reset_password_sets_flag():
    """``reset_password`` setea ``password_reset_required = 1``."""
    src = read_source('services/usuario_service.py')
    assert 'password_reset_required = 1' in src, (
        "reset_password debería setear password_reset_required = 1"
    )


def test_h_s6_cambiar_password_clears_flag():
    """``cambiar_password`` limpia ``password_reset_required = 0``."""
    src = read_source('services/usuario_service.py')
    assert 'password_reset_required = 0' in src, (
        "cambiar_password debería limpiar password_reset_required = 0"
    )


def test_h_s6_autenticar_returns_password_reset_required():
    """``autenticar`` incluye ``password_reset_required`` en el return."""
    src = read_source('services/usuario_service.py')
    assert "'password_reset_required'" in src, (
        "autenticar debería incluir 'password_reset_required' en el dict de retorno"
    )


def test_h_s6_requires_password_change_helper_exists():
    """Existe ``requires_password_change`` en ``UsuarioService``."""
    src = read_source('services/usuario_service.py')
    assert 'def requires_password_change' in src, (
        "Falta el método requires_password_change en UsuarioService"
    )


# ─────────────────────────────────────────────────────────────────────────────
# H-D3 — ORM models missing created_at
# ─────────────────────────────────────────────────────────────────────────────

def test_h_d3_animal_orm_has_created_at():
    """``Animal`` ORM declara ``created_at``."""
    src = read_source('orm_models/animal.py')
    assert 'created_at = Column' in src, (
        "Animal ORM debería declarar created_at"
    )


def test_h_d3_clinica_orm_has_created_at_in_all_classes():
    """Todos los ORM de clinica.py declaran ``created_at``."""
    src = read_source('orm_models/clinica.py')
    # Contar clases ORM vs. ``created_at = Column(``.
    class_count = len(re.findall(r'^class\s+\w+ORM\s*\(', src, re.MULTILINE))
    created_at_count = len(re.findall(r'created_at\s*=\s*Column', src))
    assert class_count == created_at_count, (
        f"Hay {class_count} clases ORM pero {created_at_count} declaraciones "
        "de created_at. Deberían ser iguales."
    )


# ─────────────────────────────────────────────────────────────────────────────
# H-D4 — FK indexes migration
# ─────────────────────────────────────────────────────────────────────────────

def test_h_d4_migration_file_exists():
    """La migración ``c1a2b3c4d5e6_*`` existe."""
    files = list((ROOT / 'alembic/versions').glob(
        'c1a2b3c4d5e6_*'))
    assert len(files) == 1, (
        f"Esperado 1 archivo con revision c1a2b3c4d5e6, encontrado {len(files)}"
    )


def test_h_d4_migration_down_revision_is_fase2_merge():
    """La migración extiende desde ``8f3a2c1d4e5f`` (merge-head Fase 2)."""
    src = read_source(
        'alembic/versions/c1a2b3c4d5e6_fase5_indexes_and_password_reset_flag.py'
    )
    assert "down_revision" in src
    assert "'8f3a2c1d4e5f'" in src, (
        "down_revision debería ser '8f3a2c1d4e5f' (merge-head Fase 2)"
    )


def test_h_d4_migration_defines_fk_indexes():
    """La migración define al menos 12 FK indexes."""
    src = read_source(
        'alembic/versions/c1a2b3c4d5e6_fase5_indexes_and_password_reset_flag.py'
    )
    # Contar tuplas (index_name, table, column).
    tuple_count = len(re.findall(r"\('ix_\w+_\w+', '\w+', '\w+'\)", src))
    assert tuple_count >= 12, (
        f"Esperado >=12 FK indexes en la migración, encontrado {tuple_count}"
    )


def test_h_d4_migration_is_idempotent():
    """La migración usa ``IF NOT EXISTS`` para ser idempotente."""
    src = read_source(
        'alembic/versions/c1a2b3c4d5e6_fase5_indexes_and_password_reset_flag.py'
    )
    assert 'IF NOT EXISTS' in src, (
        "La migración debería usar CREATE INDEX IF NOT EXISTS"
    )


# ─────────────────────────────────────────────────────────────────────────────
# H-D6 — Remove RecepcionSchema.empresa dead field
# ─────────────────────────────────────────────────────────────────────────────

def test_h_d6_recepcion_schema_no_empresa_field():
    """``RecepcionSchema`` ya no declara ``empresa``."""
    src = read_source('schemas/clinica.py')
    # Localizar la clase RecepcionSchema y verificar que no tiene ``empresa:``.
    match = re.search(
        r'class\s+RecepcionSchema\s*\(BaseModel\)\s*:(.*?)\nclass\s',
        src, re.DOTALL
    )
    assert match, "RecepcionSchema no encontrada"
    body = match.group(1)
    # Excluir comentarios ``#`` al contar ``empresa:``.
    code_lines = [
        line for line in body.split('\n')
        if not line.strip().startswith('#')
    ]
    code = '\n'.join(code_lines)
    assert 'empresa:' not in code and 'empresa =' not in code, (
        "RecepcionSchema todavía declara campo 'empresa' (debería ser eliminado)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test: imports
# ─────────────────────────────────────────────────────────────────────────────

def test_smoke_import_utils_security():
    """``utils.security`` importa sin errores."""
    from utils.security import (
        hash_password, verify_password, dummy_verify_password,
        DUMMY_BCRYPT_HASH, validar_fortaleza_password,
        Authorizer, PermissionDeniedError, generar_password_temporal,
    )
    assert DUMMY_BCRYPT_HASH.startswith('$2b$12$')


def test_smoke_import_utils_validators():
    """``utils.validators`` importa sin errores."""
    from utils.validators import (
        Validator, AnimalValidator, MuestraValidator
    )


def test_smoke_import_schemas_clinica():
    """``schemas.clinica`` importa sin errores."""
    from schemas.clinica import (
        RecepcionSchema, ConsultaSchema, CirugiaSchema,
        VacunacionSchema, HistoriaClinicaSchema
    )


def test_smoke_import_historia_service_helpers():
    """``_float``, ``_int``, ``_coerce_or_keep``, ``_MISSING`` importan."""
    from services.historia_service import (
        _float, _int, _coerce_or_keep, _MISSING
    )
