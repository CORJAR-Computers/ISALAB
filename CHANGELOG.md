# Changelog

All notable changes to IsaLab will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-21

### 🎉 First Stable Release

IsaLab v1.0.0 is the first stable release after a comprehensive 6-phase refactoring effort that addressed **77 issues** across the entire codebase. The project evolved from a 39 KLOC monolith with multiple critical deficiencies to a clean, well-tested, production-ready application.

---

### 📊 Refactoring Summary

| Phase | Scope | Issues Fixed | Status |
|-------|-------|--------------|--------|
| 1 | Repo Hygiene + Tooling | 5 DevOps | ✅ |
| 2 | DB CRITICAL | 5 DB + 2 HIGH DB | ✅ |
| 3 | Security CRITICAL | 4 Security | ✅ |
| 4 | GUI CRITICAL | 4 GUI | ✅ |
| 5 | HIGH Issues | 8 GUI + 6 Services + 3 DB + 1 Bonus | ✅ |
| 6 | MEDIUM/LOW Issues | 8 DB + 14 Services + 14 GUI + 6 DevOps | ✅ |
| **Total** | | **77 issues** | ✅ |

---

### Added

- **LazyService descriptor** (`gui_pyside/utils/services.py`) for dialog service lazy-init
- **100+ tests** across all phases (database, security, GUI, services)
- **PIIRedactionFilter** for logging (redacts bcrypt hashes, emails, passwords)
- **LoadingOverlay** for PDF generation feedback
- **`--version` flag** for `main.py`
- **`--debug` flag** for `build_app.py`
- **`updated_at` audit column** on 9 tables with `before_flush` listener
- **`CheckConstraint`** on sexo/estado/via fields
- **Empty-state support** in `DataTable.populate`
- **Password toggle** in `LoginDialog` (show/hide)
- **Caps Lock warning** in `LoginDialog`
- **`DEFAULT_WINDOW_SIZE`** constant in `app.py`
- **Lazy code generation** for samples and animals (preview on open, consume on save)

---

### Changed

- **Password policy**: New passwords now require at least 1 symbol (in addition to 8+ chars, uppercase, lowercase, digit)
- **`actualizar_usuario`**: Now raises `ValidationError` if no valid fields provided
- **`cambiar_password`**: Now rejects same password as "new"
- **`ErrorHandler`**: Sanitizes exceptions and finds parent widget automatically
- **`_show_view(name, factory)`**: Consolidated 9 `_show_X` methods in `app.py`
- **`recepciones_hoy`**: Now uses SQL WHERE clause instead of filtering in Python
- **`icon_manager` logger**: Uses `%-format` instead of f-strings
- **`PermissionDeniedError`**: Now inherits from `IsaLabException`
- **`MuestraService.generar_codigo`**: Split into `preview_siguiente_codigo` + `consumir_codigo`
- **`AnimalService`**: Split into `preview_siguiente_codigo` + `consumir_codigo`

---

### Fixed

- **AnimalRepository.update** losing 12 fields on save (Phase 2)
- **Thread-local connection leak** in `database/connection.py` (Phase 2)
- **Alembic dual-access issues** (Phase 2)
- **RBAC implementation** with `Authorizer.require_role` (Phase 3)
- **Jinja2 autoescape** for all PDF generation (Phase 3)
- **Dashboard display issues** (Phase 4)
- **`os.startfile()`** replaced with `QDesktopServices.openUrl()` (Phase 4)
- **ErrorHandler** sanitizes exceptions properly (H-G1)
- **WindowManager** dead code removed (H-G2)
- **boton_generar_reportes.py** dead code removed (H-G3)
- **RecepcionView._get_selected_animal_id** removed (H-G4)
- **theme_changed signal** connected in `app.py` (H-G5)
- **QDialog.Accepted** used in `usuarios.py` (H-G6)
- **Monkey-patch** replaced with event filter in `muestra_dialog` (H-G7)
- **PDFProWorker** hoisted to module level + `deleteLater` (H-G8)
- **Login timing-attack** mitigation with `dummy_verify_password` (H-S1)
- **Password strength** unified across dialogs (H-S2)
- **Path-traversal** check in `MuestraValidator` (H-S3)
- **Estado whitelist** validation in services (H-S4)
- **`_float`/`_int`** allow 0 and clearing (H-S5)
- **`password_reset_required`** flag (H-S6)
- **FK indexes** migration (H-D4)
- **`created_at`** columns added to all ORM models (H-D3)
- **Dead `empresa`** field removed from `RecepcionSchema` (H-D6)
- **`urgente`** mapped as Boolean (DB-M1)
- **`movimientos.fecha_hora`** made NOT NULL (DB-M6)
- **`valor_ref` ↔ `valor_referencia`** synonym (DB-M7)
- **Package `__init__.py`** files with docstrings (DB-M8)
- **Dead `_validar`** methods removed (S-M2)
- **`recepciones_hoy`** uses SQL WHERE (S-M6)
- **`report_laboratorio`** calls `muestra.es_urgente()` correctly (S-M7)
- **`tiempo_promedio`** excludes invalid date ranges (S-M8)
- **`tasa_cumplimiento`** counts Completado-with-NULL correctly (S-M9)
- **`configuracion_service`** deep merge + `chmod 0o600` (S-M10)
- **`usuarios.py`** `stateChanged` argument handling (G-M10)
- **`LoginDialog._do_login`** sanitizes error messages (G-L1)
- **`splash.py`** re-entrancy guard for `processEvents` (G-L4)
- **`SearchBar._debounce_timer`** parented to `self` (G-L5)
- **`LoadingOverlay.showEvent`** None guard (G-L6)
- **`IsaLab.spec`** hiddenimports audited (D-L6)

---

### Security

- **RBAC** implemented with `Authorizer.require_role` decorator
- **bcrypt** password hashing via `utils/security.py`
- **PIIRedactionFilter** for logging (redacts bcrypt hashes, emails, passwords)
- **Log file** created with `chmod 0o600`
- **Configuration file** saved with `chmod 0o600`

---

### Removed

- **WindowManager** dead code (`gui_pyside/utils/window_manager.py`)
- **boton_generar_reportes.py** dead code
- **`_get_selected_animal_id`** from `RecepcionView`
- **Dead `_validar` methods** from 4 services
- **`ISALAB-fase*` directories** (Phase documentation packages)
- **Dead temp scripts** (`_run_tests.py`, `_cleanup_isalab_fase.py`)
- **CustomTkinter** remnants (CTK_CONFIG)
- **Unused QtSvg/QtSvgWidgets** hiddenimports from `IsaLab.spec`

---

### Deprecated

- **`PermissionError`** alias in `utils/security.py` — Kept for backward compatibility but deprecated in favor of `PermissionDeniedError`. Will be removed in v2.0.0.

---

### 🧪 Testing

- **Phase 5:** Added 11 unit tests for `LazyService` descriptor
- **Phase 6:** Added 47 new tests in `tests/test_fase6_medium_low.py`
- **Total:** ~100+ tests covering database, security, GUI, and services
- All tests run on Python 3.10/3.11/3.12 in CI

---

### ⚠️ Breaking Changes

1. **Password Policy (S-L5):** New passwords now require at least 1 symbol (in addition to 8+ chars, uppercase, lowercase, digit). Existing users are unaffected.

2. **`actualizar_usuario` (S-L2):** Now raises `ValidationError` if no valid fields are provided. Callers must handle this exception.

3. **`cambiar_password` (S-L6):** Now rejects the same password as "new". Users must choose a different password.

---

### 📦 Database Migrations

| Migration | Description |
|-----------|-------------|
| `c1a2b3c4d5e6` | FK indexes + `password_reset_required` column |
| `b3c4d5e6f7a8` | `updated_at` audit column + `CheckConstraint` on 9 tables |

To apply migrations:
```bash
python -m alembic upgrade head
```

---

### 🙏 Acknowledgments

This refactoring effort was completed over 6 phases, addressing issues from the initial worklog analysis. Special thanks to the team for their dedication to code quality and best practices.

---

## [0.x.x] - Pre-refactoring

> Prior to v1.0.0, IsaLab was delivered as a single 39 KLOC commit with multiple
> critical deficiencies. The 6-phase refactoring plan was created to address these
> issues systematically.
