# ISALAB — Fase 6 — Fix MEDIUM/LOW issues

Esta entrega contiene **~42 fixes MEDIUM/LOW** distribuidos en 4 batches paralelos (DB, Services/Security, GUI, DevOps). Es la última fase del roadmap de refactorización basado en el worklog de análisis (Tasks 3-6).

## 📦 Contenido del paquete

```
ISALAB-fase6/
├── README.md                                   # Este documento
├── patches/
│   ├── 0001-fix-ISALAB-Fase-6-Fix-MEDIUM-LOW-issues.patch   # Consolidado (git am)
│   ├── IsaLab.spec.patch
│   ├── README.md.patch
│   ├── alembic.ini.patch
│   ├── alembic_versions_b3c4d5e6f7a8_fase6_updated_at_audit.py.patch   # ← NUEVA MIGRACIÓN
│   ├── build_app.py.patch
│   ├── config.py.patch
│   ├── database___init__.py.patch
│   ├── database_connection.py.patch
│   ├── database_models.py.patch
│   ├── database_repositories.py.patch
│   ├── gui_pyside_app.py.patch
│   ├── gui_pyside_components_components.py.patch
│   ├── gui_pyside_components_forms.py.patch
│   ├── gui_pyside_dialogs_animal_dialog.py.patch
│   ├── gui_pyside_dialogs_login_dialog.py.patch
│   ├── gui_pyside_dialogs_muestra_dialog.py.patch
│   ├── gui_pyside_splash.py.patch
│   ├── gui_pyside_utils_messages.py.patch
│   ├── gui_pyside_views_historia.py.patch
│   ├── gui_pyside_views_muestras.py.patch
│   ├── gui_pyside_views_recepcion.py.patch
│   ├── gui_pyside_views_usuarios.py.patch
│   ├── icon_manager.py.patch
│   ├── main.py.patch
│   ├── orm_models___init__.py.patch
│   ├── orm_models_animal.py.patch
│   ├── orm_models_clinica.py.patch
│   ├── schemas___init__.py.patch
│   ├── services___init__.py.patch
│   ├── services_animal_service.py.patch
│   ├── services_cirugia_service.py.patch
│   ├── services_configuracion_service.py.patch
│   ├── services_consulta_service.py.patch
│   ├── services_historia_service.py.patch
│   ├── services_muestra_service.py.patch
│   ├── services_recepcion_service.py.patch
│   ├── services_report_laboratorio.py.patch
│   ├── services_report_service.py.patch
│   ├── services_usuario_service.py.patch
│   ├── tests_test_fase3_security.py.patch
│   ├── tests_test_fase4_gui.py.patch
│   ├── tests_test_fase5_high.py.patch
│   ├── tests_test_fase6_medium_low.py.patch   # ← NUEVO (47 tests)
│   ├── utils___init__.py.patch
│   ├── utils_logger.py.patch
│   └── utils_security.py.patch
├── scripts/
│   ├── apply-phase6.sh                         # Linux / macOS
│   └── apply-phase6.ps1                        # Windows PowerShell
└── files/                                      # Copias de archivos finales para inspección
    ├── IsaLab.spec
    ├── ... (46 archivos espejo del repo)
    └── ...
```

## 🔧 Aplicar la Fase 6

### Opción A — Aplicar todo con un solo comando (recomendado)

#### En Linux / macOS
```bash
cd /ruta/a/tu/repositorio/ISALAB
bash /ruta/a/ISALAB-fase6/scripts/apply-phase6.sh
```

#### En Windows (PowerShell)
```powershell
cd C:\ruta\a\tu\repositorio\ISALAB
.\ISALAB-fase6\scripts\apply-phase6.ps1
```

El script:
1. Verifica que el repo esté limpio (sin cambios pendientes).
2. Verifica que la Fase 5 esté aplicada (commit `5098d37`).
3. Crea branch `feat/phase6-medium-low-fixes` si no existe.
4. Aplica el patch consolidado con `git am` (preserva commit message + metadata).
5. Si `git am` falla, hace fallback a `git apply --3way --reject`.
6. Verifica que no se trackearon archivos sensibles (`data/*.db`, `logs/`, etc.).
7. Verifica que la nueva migración `b3c4d5e6f7a8` esté presente.

### Opción B — Aplicar parches slim individuales

Si prefieres aplicar archivo por archivo (por ejemplo, para revisar cada cambio antes de aplicarlo), usa los parches en `patches/*.patch` con:

```bash
git apply --3way patches/orm_models_clinica.py.patch
git apply --3way patches/database_connection.py.patch
# ... etc
```

Los parches slim son diffs contra `HEAD~1` del commit `afcd7b0`, así que aplican limpio sobre `feat/phase5-high-fixes` (HEAD `5098d37`).

### Opción C — GitHub Desktop (flujo manual)

1. **Clonar el repo** (si no está clonado):
   ```bash
   git clone https://github.com/CORJAR-Computers/ISALAB.git
   cd ISALAB
   ```

2. **Crear branch** para la Fase 6:
   ```bash
   git checkout -b feat/phase6-medium-low-fixes
   ```
   En GitHub Desktop: `Branch → New Branch → feat/phase6-medium-low-fixes`.

3. **Copiar archivos** desde `ISALAB-fase6/files/` al repo (sobreescribiendo). Esto incluye:
   - Archivos modificados (sobreescribir los existentes).
   - Archivos nuevos (colocar en su ruta): `alembic/versions/b3c4d5e6f7a8_fase6_updated_at_audit.py`, `tests/test_fase6_medium_low.py`.

4. **Stage + Commit**:
   ```bash
   git add -A
   git commit -m "fix(ISALAB): Fase 6 — Fix MEDIUM/LOW issues (DB + Services + GUI + DevOps)"
   ```
   En GitHub Desktop: seleccionar todos los archivos en el panel izquierdo, escribir el mensaje abajo, y hacer click en `Commit`.

5. **Push**:
   ```bash
   git push -u origin feat/phase6-medium-low-fixes
   ```
   En GitHub Desktop: `Repository → Push`.

## 📋 Cambios por batch

### Batch DB (9-a) — 8 fixes
| ID | Descripción | Archivos afectados |
|----|-------------|-------------------|
| DB-M1 | `urgente` mapped as `Boolean` (was `Integer`) | `orm_models/clinica.py` |
| DB-M2 | `CheckConstraint` declarativas en sexo/estado/via | `orm_models/animal.py`, `orm_models/clinica.py` |
| DB-M3 | `updated_at` audit column en 9 tablas + listener `before_flush` | `orm_models/*.py`, `database/connection.py`, **nueva migración** |
| DB-M5 | `from_row` consistente con `Row._mapping.get()` | `database/models.py`, `database/repositories.py` |
| DB-M6 | `movimientos.fecha_hora` NOT NULL con `server_default` | `orm_models/clinica.py`, nueva migración |
| DB-M7 | `valor_ref` ↔ `valor_referencia` synonym | `orm_models/clinica.py` |
| DB-M8 | Package `__init__.py` con docstrings + re-exports | `orm_models/__init__.py`, `schemas/__init__.py`, `services/__init__.py`, `database/__init__.py`, `utils/__init__.py` |
| DB-M9 | `AnimalService` split en `preview_siguiente_codigo` + `consumir_codigo` | `services/animal_service.py`, `database/connection.py` |

### Batch Services/Security (9-b) — 14 fixes
| ID | Descripción | Archivos afectados |
|----|-------------|-------------------|
| S-M1 | `PermissionDeniedError` hereda de `IsaLabException` (alias `PermissionError` mantenido) | `utils/security.py` |
| S-M2 | Dead `_validar` methods eliminados (4 services) | `services/cirugia_service.py`, `consulta_service.py`, `historia_service.py`, `recepcion_service.py` |
| S-M5 | `MuestraService.generar_codigo` split en `preview_siguiente_codigo` + `consumir_codigo` | `services/muestra_service.py` |
| S-M6 | `recepciones_hoy` usa SQL WHERE (vía repo `fecha_desde`/`fecha_hasta`) | `services/recepcion_service.py`, `database/repositories.py` |
| S-M7 | `report_laboratorio` llama `muestra.es_urgente()` con paréntesis | `services/report_laboratorio.py` |
| S-M8 | `tiempo_promedio` excluye `fecha_entrega < fecha_recoleccion` | `services/report_service.py` |
| S-M9 | `tasa_cumplimiento` cuenta Completado-con-NULL como no-compliant | `services/report_service.py` |
| S-M10 | `configuracion_service` deep merge + `chmod 0o600` | `services/configuracion_service.py` |
| S-M11 | `logger` `PIIRedactionFilter` (bcrypt hashes, emails, passwords) + `chmod 0o600` | `utils/logger.py` |
| S-L2 | `actualizar_usuario` raise `ValidationError` si no hay campos whitelisted | `services/usuario_service.py` |
| S-L3 | `actualizar_usuario` valida `nombre` length (2-100) | `services/usuario_service.py` |
| S-L4 | `crear_usuario` raise `ValidationError` (no `ValueError`) para rol inválido | `services/usuario_service.py` |
| S-L5 | `validar_fortaleza_password` requiere al menos 1 símbolo | `utils/security.py` |
| S-L6 | `cambiar_password` verifica que nueva ≠ actual | `services/usuario_service.py` |

### Batch GUI (9-c) — 14 fixes
| ID | Descripción | Archivos afectados |
|----|-------------|-------------------|
| G-M1 | `app.py` `_show_view(name, factory)` consolida 9 métodos `_show_X` | `gui_pyside/app.py` |
| G-M2 | `_on_theme_changed` itera `self.views` para refrescar todas | `gui_pyside/app.py` |
| G-M3 | `muestras.py` lambda innecesario eliminado | `gui_pyside/views/muestras.py` |
| G-M4 | `recepcion.py` N+1 query resuelto (pre-fetch all historias) | `gui_pyside/views/recepcion.py` |
| G-M5 | `historia.py` rutea vía `HistoriaService.listar_historias` | `gui_pyside/views/historia.py` |
| G-M6 | `DataTable.populate` muestra empty-state cuando data está vacío | `gui_pyside/components/components.py` |
| G-M7 | `FormField.validate` extendido con `min/max_length`, `regex`, `validator` | `gui_pyside/components/forms.py` |
| G-M8 | `LoadingOverlay` usado en `muestra_dialog` PDF generation | `gui_pyside/dialogs/muestra_dialog.py` |
| G-M10 | `usuarios.py` `stateChanged` arg manejado limpio (lambda, no `*args`) | `gui_pyside/views/usuarios.py` |
| G-L1 | `LoginDialog._do_login` sanitiza error (mensaje genérico + `logger.error`) | `gui_pyside/dialogs/login_dialog.py` |
| G-L2 | `LoginDialog` toggle "Mostrar contraseña" + warning Bloq Mayús | `gui_pyside/dialogs/login_dialog.py` |
| G-L3 | `splash.py` `Qt.WindowStaysOnTopHint` agregado | `gui_pyside/splash.py` |
| G-L4 | `splash.py` `processEvents` re-entrancy guard (`_processing` flag) | `gui_pyside/splash.py` |
| G-L5 | `SearchBar._debounce_timer` parented a `self` | `gui_pyside/components/components.py` |
| G-L6 | `LoadingOverlay.showEvent` None guard | `gui_pyside/components/forms.py` |
| G-L7 | `muestra_dialog` + `animal_dialog` lazy `generar_codigo` (preview on open, consume on save) | `gui_pyside/dialogs/muestra_dialog.py`, `gui_pyside/dialogs/animal_dialog.py` |
| G-L8 | `app.py` `DEFAULT_WINDOW_SIZE` constante consistente con `setMinimumSize` | `gui_pyside/app.py` |
| G-L9 | `usuarios.py` usa `DataTable` (no `QTableWidget` directo) | `gui_pyside/views/usuarios.py` |

### Batch DevOps (9-d) — 6 fixes
| ID | Descripción | Archivos afectados |
|----|-------------|-------------------|
| D-L1 | `icon_manager` logger usa `%-format` (no f-strings) — 9 call sites | `icon_manager.py` |
| D-L2 | `config.__version__ = "1.0.0"` + `main.py` lo usa + flag `--version` | `config.py`, `main.py` |
| D-L3 | `build_app.py --debug` flag (conditional `optimize=0`, `console=True`) | `build_app.py`, `IsaLab.spec` |
| D-L4 | `IsaLab.spec` `optimize=2` (conditional en `ISALAB_DEBUG` env var) | `IsaLab.spec` |
| D-L5 | `alembic.ini` `ruff` post_write_hooks habilitado | `alembic.ini` |
| D-L6 | `IsaLab.spec` hiddenimports auditado (removidos `QtSvg`/`QtSvgWidgets` sin uso) | `IsaLab.spec` |

## 🗄️ Migración de base de datos

La nueva migración `b3c4d5e6f7a8_fase6_updated_at_audit.py`:

- **Revisión**: `b3c4d5e6f7a8`
- **Down-revision**: `c1a2b3c4d5e6` (head de Fase 5)
- **Es idempotente**: verifica existencia de columnas y constraints antes de agregarlos.
- **Es safe para datos existentes**: `updated_at` es nullable (los registros viejos quedan en NULL hasta el próximo UPDATE, cuando el listener `before_flush` lo setea).

Cambios de schema:
1. **`updated_at` column** (DateTime, nullable) agregada a: `animales`, `recepciones`, `muestras`, `cirugias`, `consultas`, `vacunaciones`, `historias_clinicas`, `movimientos`, `usuarios`.
2. **`CheckConstraint` declarativas** en: `animales.sexo`, `animales.estado`, `muestras.estado`, `recepciones.estado`, `cirugias.estado`, `vacunaciones.via`. Whitelists importadas de `config.py`.
3. **`movimientos.fecha_hora`** hecho NOT NULL con `server_default = (datetime('now'))`. Backfill previo: `UPDATE movimientos SET fecha_hora = datetime('now') WHERE fecha_hora IS NULL`.

Para aplicarla:
```bash
python -m alembic upgrade head
```

## 🧪 Tests

- **47 tests nuevos** en `tests/test_fase6_medium_low.py` cubriendo los 4 batches.
- Tests existentes actualizados para el nuevo comportamiento (S-L5 password policy, `updated_at` column en setup de tests).
- **Resultado**: 138 passed, 7 skipped (1 GUI smoke skip por falta de Qt en env headless), 1 pre-existing failure (`test_alembic_upgrade_head_no_multiple_heads` — `alembic` CLI no instalado en este sandbox, no relacionado a Phase 6).

Para correr los tests:
```bash
python -m pytest tests/ --tb=short
```

## ⚠️ Notas importantes

### Cambio de comportamiento en passwords (S-L5)
A partir de Fase 6, `validar_fortaleza_password` exige al menos **1 símbolo** (además de 8+ chars, mayúscula, minúscula, dígito). Esto afecta:
- Nuevas altas de usuario
- Cambios de contraseña
- **NO** afecta usuarios existentes (sus hashes siguen siendo válidos)

Los UI checklists en `instalador_dialog.py` y `cambiar_password_dialog.py` ya mostraban "• Al menos un símbolo" como requisito — ahora el validator lo hace cumplir de verdad.

### Cambio de comportamiento en `actualizar_usuario` (S-L2)
Antes: si no había campos whitelisted en `data`, el método retornaba `None` silenciosamente. Ahora: raise `ValidationError("No se proporcionaron campos válidos para actualizar")`. Cualquier caller que dependiera del silent no-op necesita manejar la excepción.

### Cambio de comportamiento en `cambiar_password` (S-L6)
Antes: aceptaba la misma contraseña como "nueva". Ahora: raise `ValidationError("La nueva contraseña no puede ser igual a la actual")`.

### Lazy code generation (G-L7, DB-M9, S-M5)
Los diálogos `NuevaMuestraDialog` y `AnimalDialog` ya NO consumen un código del contador al abrirse. Solo consumen al guardar. Esto significa:
- Si el usuario abre el diálogo y lo cancela, **no** se desperdicia un código.
- Si el usuario hace click en "🔄 Regenerar", se actualiza el preview (sin consumir).
- El código real se consume en el momento del INSERT.

### Logging con redacción de PII (S-M11)
El `RotatingFileHandler` ahora tiene un `PIIRedactionFilter` que reemplaza:
- Hashes bcrypt (`$2b$...`)
- Direcciones email
- Campos password en KV logs (`password=xxx` → `password=[REDACTED]`)
- Números de teléfono (conservador)

El archivo de log se crea con `chmod 0o600`.

## 📊 Estado del proyecto

| Fase | Estado | Commit |
|------|--------|--------|
| Fase 1 — Repo Hygiene + Tooling | ✅ Aplicada | `a6462da` |
| Fase 2 — DB CRITICAL fixes | ✅ Aplicada | `82dbc20` |
| Fase 3 — Security CRITICAL fixes | ✅ Aplicada | `46f979c` |
| Fase 4 — GUI CRITICAL fixes | ✅ Aplicada | `7adf0b7` |
| Fase 5 — HIGH issues | ✅ Aplicada | `5098d37` |
| **Fase 6 — MEDIUM/LOW issues** | **✅ Esta entrega** | `afcd7b0` |

### Resumen acumulado de fixes
- **5 CRITICAL DB** (Fase 2) + **3 HIGH DB** (Fase 5) + **8 MEDIUM/LOW DB** (Fase 6) = **16 DB fixes**
- **4 CRITICAL Security** (Fase 3) + **6 HIGH Services** (Fase 5) + **14 MEDIUM/LOW Services** (Fase 6) = **24 Services/Security fixes**
- **4 CRITICAL GUI** (Fase 4) + **8 HIGH GUI** (Fase 5) + **14 MEDIUM/LOW GUI** (Fase 6) = **26 GUI fixes**
- **5 CRITICAL DevOps** (Fase 1) + **6 MEDIUM/LOW DevOps** (Fase 6) = **11 DevOps fixes**

**Total: 77 issues fixed** a lo largo de 6 fases.

## 🎯 Próximos pasos recomendados

Después de aplicar Fase 6:

1. **Aplicar la migración**:
   ```bash
   python -m alembic upgrade head
   ```

2. **Correr tests** para verificar:
   ```bash
   python -m pytest tests/ --tb=short
   ```
   Esperado: 138 passed, 7 skipped, 1 pre-existing failure (alembic CLI).

3. **Probar manualmente** los flujos críticos:
   - Login con usuario existente (debe seguir funcionando).
   - Crear nuevo usuario (debe exigir símbolo en password).
   - Cambiar password (debe rechazar nueva = actual).
   - Abrir "Nueva Muestra" y cancelar (no debe consumir código LAB-XXXX).
   - Abrir "Nuevo Paciente" y cancelar (no debe consumir código PAC-XXXX).
   - Generar PDF de muestra (debe mostrar LoadingOverlay).

4. **Hacer push** del branch:
   ```bash
   git push -u origin feat/phase6-medium-low-fixes
   ```

5. **Crear Pull Request** en GitHub para revisión y merge a `master`.

6. **Tag de release** (opcional, recomendado):
   ```bash
   git tag -a v1.0.0 -m "IsaLab v1.0.0 — primera release estable tras refactor de 6 fases"
   git push origin v1.0.0
   ```

## 🐛 Troubleshooting

### "git am falló: patch does not apply"
- Verifica que estés en el branch correcto: `git branch --show-current` debe decir `feat/phase6-medium-low-fixes`.
- Verifica que la Fase 5 esté aplicada: `git log --oneline | grep 5098d37`.
- Si tienes cambios locales que entran en conflicto, haz stash: `git stash`, aplica el patch, luego `git stash pop`.

### "alembic upgrade head falló"
- Verifica tener `alembic` instalado: `pip install alembic`.
- Verifica que el archivo `alembic.ini` tenga `sqlalchemy.url =` vacío (debe ser overrideado por `env.py` desde `config.DB_PATH`).
- Si la DB ya tenía una versión parcial de la migración, usa `alembic stamp head` para marcarla como aplicada sin correrla.

### "tests fallan con `no such column: updated_at`"
- Significa que la migración no se aplicó. Corre: `python -m alembic upgrade head`.
- Si la migración aplica pero los tests siguen fallando, borra la DB de test: `rm -f /tmp/pytest-of-*/pytest-current/db/test_isalab.db` y re-corre.

### "tests fallan con `libEGL.so.1: cannot open shared object file`"
- Es un problema del entorno headless (falta libGL para Qt). No es un bug del código.
- El test `test_smoke_import_gui_modules` se salta automáticamente en este caso.
- En un entorno con Qt instalado (Windows, macOS, Linux con X11/Wayland), el test pasa.

### "importerror: cannot import name 'PermissionError' from 'utils.security'"
- Esto NO debería pasar — `PermissionError` se mantiene como alias deprecated de `PermissionDeniedError`.
- Si pasa, revisa que el archivo `utils/security.py` tenga `PermissionError = PermissionDeniedError` cerca del final.

---

**Branch**: `feat/phase6-medium-low-fixes`
**Commit**: `afcd7b0`
**Base**: `feat/phase5-high-fixes` (`5098d37`)
**Fecha**: 2026-07-21
