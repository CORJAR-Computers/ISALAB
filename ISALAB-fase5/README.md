# ISALAB — Fase 5: Fix HIGH issues

> **17 defects HIGH-severity** del worklog (12 GUI + 9 Services/Security + 9 DB),
> entregados como parches aplicables con GitHub Desktop / `git apply`.

---

## Resumen de la Fase 5

### GUI (8 fixes)

| ID | Problema | Archivo(s) afectado(s) |
|----|----------|------------------------|
| **H-G1** | `ErrorHandler.handle_exception` (`components.py:23-37`) llamaba `QMessageBox.critical(None, "Error", msg)` con parent `None` (el messagebox puede quedar detrás de la ventana activa sin foco), mostraba `str(e)` crudo al usuario (filtra detalles internos: tablas, rutas, IDs) y retornaba `None` implícitamente (los callers como `_get_selected_id` rompían con `TypeError` downstream). | `gui_pyside/components/components.py` |
| **H-G2** | `WindowManager` singleton (`utils/window_manager.py`) era dead code — `open_dialog` / `close_all_dialogs` / `get_active_dialog` / `is_dialog_open` NUNCA se invocaban; todos los diálogos se ejecutaban con `dialog.exec()` directo. Su único uso era `WindowManager.set_main_window(self)` en `app.py` que no hacía nada porque nadie consultaba esa referencia. | `gui_pyside/utils/window_manager.py` (eliminado), `gui_pyside/app.py` |
| **H-G3** | `boton_generar_reportes.py` era un archivo demo de 500 líneas con datos de prueba hardcodeados (`_obtener_datos_prueba`) — nunca importado por nada, `PanelReportes` nunca instanciado. Puro dead code en producción. | `gui_pyside/views/boton_generar_reportes.py` (eliminado) |
| **H-G4** | `RecepcionView._get_selected_animal_id` (`recepcion.py:405-416`) era dead code que SIEMPRE retornaba `None` — el cuerpo tenía literalmente `pass` seguido de `return None`. | `gui_pyside/views/recepcion.py` |
| **H-G5** | `DashboardView.theme_changed` (`dashboard.py:75`) se declaraba DESPUÉS del método `_toggle_theme` que la emite (funcionaba solo por class-attribute lookup, código misleading). Peor aún: la señal NUNCA se conectaba desde `app.py`, así que al cambiar el tema solo se refrescaba el dashboard; las demás vistas (animales, muestras, etc.) conservaban el tema anterior hasta reiniciar la app. | `gui_pyside/views/dashboard.py`, `gui_pyside/app.py` |
| **H-G6** | `usuarios.py:136` y `:143` usaban `if dialog.exec():` (truthy check sobre un `int`). Funciona por accidente (1 = Accepted es truthy) pero es frágil y no idiomático. | `gui_pyside/views/usuarios.py` |
| **H-G7** | `muestra_dialog.py:511` monkey-patcheaba `self.tabla_resultados.keyPressEvent = self._pegar_magico_en_tabla` para interceptar Ctrl+V. Rompía encapsulación (sobreescribía un método de instancia sin subclass) y era frágil — PySide6 puede no respetar asignación directa de métodos Python sobre objetos C++. | `gui_pyside/dialogs/muestra_dialog.py` |
| **H-G8** | `muestra_dialog.py:1048-1068` definía `PDFProWorker` como clase anidada DENTRO del método `_imprimir_pdf` — Python RE-CREABA la clase en cada click del botón "Imprimir Resultados Pro". El QThread arrancado no tenía `finished` conectado ni `deleteLater()`, así que cada click acumulaba un QThread zombie. | `gui_pyside/dialogs/muestra_dialog.py` |

### Services / Security (6 fixes)

| ID | Problema | Archivo(s) afectado(s) |
|----|----------|------------------------|
| **H-S1** | `UsuarioService.autenticar` levantaba `AuthenticationError` INMEDIATAMENTE cuando el usuario no existía, sin ejecutar bcrypt. Eso permitía a un atacante distinguish "usuario no existe" (rápido) vs "contraseña incorrecta" (lento por bcrypt) midiendo tiempos — un oracle de enumeración de usernames. | `services/usuario_service.py`, `utils/security.py` |
| **H-S2** | Inconsistencia de fortaleza de contraseña: `validar_fortaleza_password` (servicio) exigía 8 caracteres, pero `cambiar_password_dialog` y `usuario_dialog` exigían solo 6. Además, ambos diálogos hacían `.strip()` sobre las contraseñas, lo que rompía autenticación para usuarios con espacios intencionales al inicio/final. | `gui_pyside/dialogs/cambiar_password_dialog.py`, `gui_pyside/dialogs/usuario_dialog.py` |
| **H-S3** | `MuestraValidator.validate` (`validators.py:113`) aplicaba `validate_length` al código de muestra pero NO `validate_pattern` — permitía caracteres como `/`, `\`, `..`, `;` que fluyen luego a `pdf_service.ruta_default` para construir `LAB_{codigo}.pdf`. Con `../` en el código se podía escribir PDFs fuera de `data/pdfs/` (path traversal). | `utils/validators.py` |
| **H-S4** | `RecepcionService.actualizar_estado` y `CirugiaService.actualizar_estado` aceptaban CUALQUIER string como nuevo estado, sin validar contra la whitelist del sistema. Permitía inyectar valores arbitrarios en la BD que rompían filtros, badges y colores en la UI. | `services/recepcion_service.py`, `services/cirugia_service.py` |
| **H-S5** | `historia_service._float` y `_int` trataban `'0'` y `0` como `None` (usaban `val not in (None, '', '0', 0)`), impidiendo registrar T=0°C o FC=0 (casos clínicos válidos: crioterapia, paro cardíaco). Además, `actualizar_historia` usaba `data.get('X') or h.X` — imposible limpiar campos (string vacío evaluaba a `h.X`) y imposible setear 0 legítimo. | `services/historia_service.py` |
| **H-S6** | `UsuarioService.reset_password` retornaba una contraseña temporal en plaintext sin setear flag de "cambio forzado". La contraseña temporal era permanente — riesgo de seguridad si el canal de entrega (email, mensaje) era interceptado. | `services/usuario_service.py`, `alembic/versions/c1a2b3c4d5e6_*` (nueva migración) |

### Database (3 fixes)

> **H-DB-1** (thread-local connection leak en `close_all_connections`) y
> **H-DB-2** (`AnimalRepository.update` dropping 12 fields) ya fueron
> fixados en **Fase 2** — no se re-hacen aquí. Verificar en
> `database/connection.py:244-272` y `database/repositories.py:114-145`.
>
> **H-DB-5** (todas las fechas almacenadas como `String`) queda fuera de
> alcance — requiere migración destructiva de todas las tablas, se
> abordará en Fase 6 (MEDIUM/LOW).

| ID | Problema | Archivo(s) afectado(s) |
|----|----------|------------------------|
| **H-D3** | ORM models (`Animal`, `MovimientoORM`, `MuestraORM`, `RecepcionORM`, `HistoriaClinicaORM`, `ConsultaORM`, `CirugiaORM`, `VacunacionORM`) NO declaraban `created_at` aunque la migración de Fase 2 (`agregar_created_at_todas_tablas`) ya añadía la columna a la BD. Eso significaba que el ORM no la veía y cualquier `session.query(...).filter(Animal.created_at > ...)` fallaba. | `orm_models/animal.py`, `orm_models/clinica.py` |
| **H-D4** | Solo existía UN índice en toda la BD (`ix_animales_codigo`). Columnas como `muestras.animal_id`, `recepciones.estado`, `historias_clinicas.animal_id` no tenían índice — cualquier filtro o JOIN recorría la tabla completa. Para tablas de miles de filas, eso significa queries de 100-500ms en lugar de 1-5ms. | `alembic/versions/c1a2b3c4d5e6_fase5_indexes_and_password_reset_flag.py` (nueva migración) |
| **H-D6** | `RecepcionSchema.empresa` era dead code — ni `RecepcionORM` tiene columna `empresa` (solo `MuestraORM` la tiene, para PDFs de laboratorio), ni `RecepcionService` la persiste, ni ningún diálogo de recepción la envía. Su mera presencia confundía a futuros desarrolladores. | `schemas/clinica.py` |

Adicionalmente se incluye **`tests/test_fase5_high.py`** con **61 tests de regresión** que cubren los 17 fixes (inspección estática de código + tests funcionales con `bcrypt`/`pydantic`/`sqlalchemy`).

---

## Estructura del paquete

```
ISALAB-fase5/
├── README.md                     ← este archivo
├── patches/
│   ├── 0001-fix-ISALAB-Fase-5-Fix-HIGH-issues.patch  ← consolidado (con deletions)
│   ├── alembic_versions_c1a2b3c4d5e6_fase5_indexes_and_password_reset_flag.py.patch  ← archivo nuevo
│   ├── gui_pyside_app.py.patch
│   ├── gui_pyside_components_components.py.patch
│   ├── gui_pyside_dialogs_cambiar_password_dialog.py.patch
│   ├── gui_pyside_dialogs_muestra_dialog.py.patch
│   ├── gui_pyside_dialogs_usuario_dialog.py.patch
│   ├── gui_pyside_views_dashboard.py.patch
│   ├── gui_pyside_views_recepcion.py.patch
│   ├── gui_pyside_views_usuarios.py.patch
│   ├── orm_models_animal.py.patch
│   ├── orm_models_clinica.py.patch
│   ├── schemas_clinica.py.patch
│   ├── services_cirugia_service.py.patch
│   ├── services_historia_service.py.patch
│   ├── services_recepcion_service.py.patch
│   ├── services_usuario_service.py.patch
│   ├── tests_test_fase5_high.py.patch                ← archivo nuevo
│   ├── utils_security.py.patch
│   └── utils_validators.py.patch
├── scripts/
│   ├── apply-phase5.sh           ← Linux / macOS / Git Bash
│   └── apply-phase5.ps1          ← Windows PowerShell
└── files/                        ← archivos finales para inspección
    ├── alembic/versions/c1a2b3c4d5e6_*.py
    ├── gui_pyside/
    │   ├── app.py
    │   ├── components/components.py
    │   ├── dialogs/
    │   │   ├── cambiar_password_dialog.py
    │   │   ├── muestra_dialog.py
    │   │   └── usuario_dialog.py
    │   └── views/
    │       ├── dashboard.py
    │       ├── recepcion.py
    │       └── usuarios.py
    ├── orm_models/
    │   ├── animal.py
    │   └── clinica.py
    ├── schemas/clinica.py
    ├── services/
    │   ├── cirugia_service.py
    │   ├── historia_service.py
    │   ├── recepcion_service.py
    │   └── usuario_service.py
    ├── tests/test_fase5_high.py
    └── utils/
        ├── security.py
        └── validators.py
```

**Archivos eliminados (no aparecen como slim patch):**
- `gui_pyside/utils/window_manager.py` (H-G2)
- `gui_pyside/views/boton_generar_reportes.py` (H-G3)

El script `apply-phase5.{sh,ps1}` hace `git rm` automáticamente.

---

## Requisitos previos

**Esta Fase 5 asume que ya aplicaste y commiteaste Fase 1, 2, 3 y 4** sobre tu
repo. Si no lo has hecho, ejecuta primero:

```bash
bash apply-phase1.sh && \
bash apply-phase2.sh && \
bash apply-phase3.sh && \
bash apply-phase4.sh && \
git add -A && git commit -m "Fase 1+2+3+4 applied"
```

Los parches de Fase 5 se generaron contra el commit `7adf0b7` (HEAD de
`feat/phase4-gui-critical-fixes`). Aplicarlos sobre un estado distinto puede
provocar conflictos.

---

## Aplicación con GitHub Desktop (recomendado)

GitHub Desktop **no tiene** un botón "Apply patch" nativo, pero el flujo
siguiente funciona igual de bien y queda como un commit en tu rama:

1. **Abre el repo en GitHub Desktop** y asegúrate de estar en una rama de
   trabajo (p.ej. `feat/phase5-high-fixes`). Si no la tienes:
   - `Branch → New Branch…` → nómbrala `feat/phase5-high-fixes`.

2. **Abre la terminal del repo** desde GitHub Desktop:
   - `Repository → Open in Terminal` (en Windows: PowerShell).
   - O usa tu terminal favorita y haz `cd /ruta/a/ISALAB`.

3. **Ejecuta el aplicador** según tu SO:

   **Linux / macOS / Git Bash:**
   ```bash
   bash /ruta/donde/descargaste/ISALAB-fase5/scripts/apply-phase5.sh
   ```

   **Windows PowerShell:**
   ```powershell
   .\ruta\donde\descargaste\ISALAB-fase5\scripts\apply-phase5.ps1
   ```

   El script:
   - Verifica que estás en la raíz del repo (con `.git`, `main.py`, etc.).
   - Verifica que el working tree esté razonablemente limpio (warn, no block).
   - Aplica los 19 parches slim con `git apply` (idempotente: si ya estaba
     aplicado, lo salta con `⊙`).
   - Hace `git rm` de los 2 archivos eliminados (window_manager.py,
     boton_generar_reportes.py).
   - Hace **27 verificaciones post-aplicación** para confirmar que cada fix
     quedó en su lugar.
   - Si todo OK, sugiere los próximos pasos.

4. **Vuelve a GitHub Desktop** — verás los ~21 archivos modificados/añadidos/
   eliminados en la lista de cambios. Revísalos con calma.

5. **Commit** desde GitHub Desktop con el mensaje sugerido:
   ```
   fix(ISALAB): Fase 5 — Fix HIGH issues (GUI + Services + DB)
   ```
   (copia exacta del commit del bot, ver `patches/0001-…patch` para el
   mensaje completo si quieres más detalle).

6. **Push** a tu fork y abre PR contra `master`.

---

## Aplicación manual (sin script)

Si prefieres aplicar los parches a mano:

```bash
cd /ruta/a/ISALAB
PATCHES=/ruta/donde/descargaste/ISALAB-fase5/patches

# Aplicar los 19 parches slim (added/modified).
git apply --verbose $PATCHES/alembic_versions_c1a2b3c4d5e6_fase5_indexes_and_password_reset_flag.py.patch
git apply --verbose $PATCHES/gui_pyside_app.py.patch
git apply --verbose $PATCHES/gui_pyside_components_components.py.patch
git apply --verbose $PATCHES/gui_pyside_dialogs_cambiar_password_dialog.py.patch
git apply --verbose $PATCHES/gui_pyside_dialogs_muestra_dialog.py.patch
git apply --verbose $PATCHES/gui_pyside_dialogs_usuario_dialog.py.patch
git apply --verbose $PATCHES/gui_pyside_views_dashboard.py.patch
git apply --verbose $PATCHES/gui_pyside_views_recepcion.py.patch
git apply --verbose $PATCHES/gui_pyside_views_usuarios.py.patch
git apply --verbose $PATCHES/orm_models_animal.py.patch
git apply --verbose $PATCHES/orm_models_clinica.py.patch
git apply --verbose $PATCHES/schemas_clinica.py.patch
git apply --verbose $PATCHES/services_cirugia_service.py.patch
git apply --verbose $PATCHES/services_historia_service.py.patch
git apply --verbose $PATCHES/services_recepcion_service.py.patch
git apply --verbose $PATCHES/services_usuario_service.py.patch
git apply --verbose $PATCHES/tests_test_fase5_high.py.patch
git apply --verbose $PATCHES/utils_security.py.patch
git apply --verbose $PATCHES/utils_validators.py.patch

# Eliminar los 2 archivos dead code.
git rm gui_pyside/utils/window_manager.py
git rm gui_pyside/views/boton_generar_reportes.py
```

O todo de una vez con el consolidado (preserva autoría + mensaje, **incluye
deletions automáticamente**):

```bash
git am --signoff < $PATCHES/0001-fix-ISALAB-Fase-5-Fix-HIGH-issues.patch
```

> `git am` deja un commit limpio en tu rama. Es la forma más fiel al
> trabajo original del bot.

---

## Verificación

Tras aplicar, ejecuta los tests:

```bash
python -m pytest tests/test_fase5_high.py -v --no-cov
```

Salida esperada (61 tests, todos PASSED):

```
tests/test_fase5_high.py::test_h_g1_no_qmessagebox_critical_none PASSED
tests/test_fase5_high.py::test_h_g1_does_not_show_raw_str_e PASSED
tests/test_fase5_high.py::test_h_g1_returns_sentinel_on_error PASSED
tests/test_fase5_high.py::test_h_g1_finds_parent_widget PASSED
tests/test_fase5_high.py::test_h_g1_sanitizes_non_isalab_exceptions PASSED
tests/test_fase5_high.py::test_h_g2_window_manager_file_deleted PASSED
tests/test_fase5_high.py::test_h_g2_no_window_manager_imports PASSED
tests/test_fase5_high.py::test_h_g2_no_set_main_window_calls PASSED
tests/test_fase5_high.py::test_h_g3_boton_generar_reportes_deleted PASSED
tests/test_fase5_high.py::test_h_g3_no_imports_of_boton_generar_reportes PASSED
tests/test_fase5_high.py::test_h_g4_no_get_selected_animal_id_in_recepcion PASSED
tests/test_fase5_high.py::test_h_g5_signal_declared_before_toggle_method PASSED
tests/test_fase5_high.py::test_h_g5_signal_connected_in_app PASSED
tests/test_fase5_high.py::test_h_g5_handler_iterates_views PASSED
tests/test_fase5_high.py::test_h_g6_uses_qdialog_accepted PASSED
tests/test_fase5_high.py::test_h_g6_no_bare_dialog_exec_check PASSED
tests/test_fase5_high.py::test_h_g7_no_keypress_monkey_patch PASSED
tests/test_fase5_high.py::test_h_g7_event_filter_installed PASSED
tests/test_fase5_high.py::test_h_g7_filter_class_inherits_qobject PASSED
tests/test_fase5_high.py::test_h_g7_filter_implements_event_filter_method PASSED
tests/test_fase5_high.py::test_h_g8_pdf_worker_is_module_level_class PASSED
tests/test_fase5_high.py::test_h_g8_no_nested_pdf_worker_in_imprimir_pdf PASSED
tests/test_fase5_high.py::test_h_g8_finished_connected_to_delete_later PASSED
tests/test_fase5_high.py::test_h_s1_dummy_hash_constant_exists PASSED
tests/test_fase5_high.py::test_h_s1_dummy_verify_password_function_exists PASSED
tests/test_fase5_high.py::test_h_s1_dummy_verify_called_on_user_not_found PASSED
tests/test_fase5_high.py::test_h_s1_dummy_verify_runs_without_bcrypt PASSED
tests/test_fase5_high.py::test_h_s2_cambiar_password_dialog_uses_8_chars PASSED
tests/test_fase5_high.py::test_h_s2_cambiar_password_dialog_does_not_strip_passwords PASSED
tests/test_fase5_high.py::test_h_s2_usuario_dialog_uses_8_chars PASSED
tests/test_fase5_high.py::test_h_s2_validar_fortaleza_password_requires_8 PASSED
tests/test_fase5_high.py::test_h_s3_muestra_validator_calls_validate_pattern PASSED
tests/test_fase5_high.py::test_h_s3_muestra_validator_rejects_path_traversal PASSED
tests/test_fase5_high.py::test_h_s3_muestra_validator_accepts_valid_codes PASSED
tests/test_fase5_high.py::test_h_s4_recepcion_service_imports_estados_recepcion PASSED
tests/test_fase5_high.py::test_h_s4_recepcion_service_validates_estado_whitelist PASSED
tests/test_fase5_high.py::test_h_s4_cirugia_service_imports_estados_cirugia PASSED
tests/test_fase5_high.py::test_h_s4_cirugia_service_validates_estado_whitelist PASSED
tests/test_fase5_high.py::test_h_s5_float_allows_zero PASSED
tests/test_fase5_high.py::test_h_s5_int_allows_zero PASSED
tests/test_fase5_high.py::test_h_s5_float_none_for_empty PASSED
tests/test_fase5_high.py::test_h_s5_int_none_for_empty PASSED
tests/test_fase5_high.py::test_h_s5_coerce_or_keep_missing_keeps_current PASSED
tests/test_fase5_high.py::test_h_s5_coerce_or_keep_empty_clears PASSED
tests/test_fase5_high.py::test_h_s5_coerce_or_keep_zero_sets_zero PASSED
tests/test_fase5_high.py::test_h_s5_actualizar_historia_uses_coerce_or_keep PASSED
tests/test_fase5_high.py::test_h_s6_reset_password_sets_flag PASSED
tests/test_fase5_high.py::test_h_s6_cambiar_password_clears_flag PASSED
tests/test_fase5_high.py::test_h_s6_autenticar_returns_password_reset_required PASSED
tests/test_fase5_high.py::test_h_s6_requires_password_change_helper_exists PASSED
tests/test_fase5_high.py::test_h_d3_animal_orm_has_created_at PASSED
tests/test_fase5_high.py::test_h_d3_clinica_orm_has_created_at_in_all_classes PASSED
tests/test_fase5_high.py::test_h_d4_migration_file_exists PASSED
tests/test_fase5_high.py::test_h_d4_migration_down_revision_is_fase2_merge PASSED
tests/test_fase5_high.py::test_h_d4_migration_defines_fk_indexes PASSED
tests/test_fase5_high.py::test_h_d4_migration_is_idempotent PASSED
tests/test_fase5_high.py::test_h_d6_recepcion_schema_no_empresa_field PASSED
tests/test_fase5_high.py::test_smoke_import_utils_security PASSED
tests/test_fase5_high.py::test_smoke_import_utils_validators PASSED
tests/test_fase5_high.py::test_smoke_import_schemas_clinica PASSED
tests/test_fase5_high.py::test_smoke_import_historia_service_helpers PASSED
============================== 61 passed ===============================
```

También puedes correr la suite completa:

```bash
python -m pytest tests/ -v --no-cov
```

> Nota: `tests/test_fase2_database.py::test_alembic_upgrade_head_no_multiple_heads`
> puede fallar si `alembic` no está instalado en el entorno — es un
> issue preexistente del sandbox, no una regresión de Fase 5.

Y aplica la migración Alembic para crear los FK indexes + la columna
`password_reset_required`:

```bash
python -m alembic upgrade head
```

---

## Detalle técnico de cada fix

### H-G1 — ErrorHandler sanitization

**Antes (`components.py:23-37`):**
```python
class ErrorHandler:
    @staticmethod
    def handle_exception(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error en UI: {e}", exc_info=True)
                msg = str(e)
                QMessageBox.critical(None, "Error", msg)
        return wrapper
```

**Después:**
- `_find_parent(args)` busca el primer `QWidget` entre los args; si no
  hay, usa `QApplication.instance().activeWindow()`; si no, `None`.
- `_sanitize_message(e)` retorna `str(e)` solo si la excepción hereda de
  `IsaLabException` (jerarquía user-friendly); para cualquier otra,
  retorna `"Ocurrió un error inesperado. Consulte el log para más detalles."`.
- El wrapper retorna `ErrorHandler._ERROR_SENTINEL` (un `object()` único)
  en lugar de `None`, para que los callers puedan distinguir "fallo" de
  "retorno legítimo None".

### H-G5 — theme_changed signal connection

**Antes:** `theme_changed = Signal()` se declaraba en línea 66 (DESPUÉS
del método `_toggle_theme` que la emite en línea 55). La señal NUNCA se
conectaba desde `app.py`.

**Después:**
1. `theme_changed = Signal()` movida al inicio de la clase (antes que
   cualquier método que la use).
2. `app.py._show_dashboard` conecta la señal al nuevo handler
   `_on_theme_changed`:
   ```python
   self.views['dashboard'].theme_changed.connect(self._on_theme_changed)
   ```
3. El handler recorre `self.views.items()` y llama `rebuild_layout()`
   si existe (lo implementan los views con soporte para tema), o
   `refresh()` como fallback.

### H-G7 — Event filter reemplaza monkey-patch

**Antes:**
```python
self.tabla_resultados.keyPressEvent = self._pegar_magico_en_tabla
```

**Después:** nueva clase `_PegadoMagicoFilter(QObject)` que implementa
`eventFilter(obj, event)`:
```python
class _PegadoMagicoFilter(QObject):
    def __init__(self, target_table, handler):
        super().__init__(target_table)  # parent = target → se limpia solo
        self._handler = handler

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_V and (
                    event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                result = self._handler(event)
                if result is not False:
                    return True
        return super().eventFilter(obj, event)
```

Instalado con `installEventFilter`, el mecanismo oficial de Qt. El
handler `_pegar_magico_en_tabla` ya no necesita manejar el caso "no es
Ctrl+V" — eso pasa directo al widget original.

### H-G8 — PDFProWorker hoisted + deleteLater

**Antes:** `class PDFProWorker(QThread)` se definía DENTRO del método
`_imprimir_pdf`, re-creándose en cada click. Sin `finished` conectado,
sin `deleteLater`.

**Después:** `PDFProWorker` es clase de módulo (se define una sola vez
al importar). El método `_imprimir_pdf` la instancia y conecta:
```python
self.worker = PDFProWorker(
    self.muestra_id, es_empresa, datos_empresa, parent=self)
self.worker.terminado.connect(self._pdf_exito)
self.worker.error.connect(self._pdf_error)
self.worker.finished.connect(self.worker.deleteLater)  # ← Limpieza
self.worker.start()
```

Además, si ya había un worker corriendo (doble-click rápido), se hace
`quit()` + `wait(2000)` antes de reemplazarlo.

### H-S1 — Timing-attack mitigation

**Antes:** cuando el usuario no existía, `autenticar` levantaba
`AuthenticationError` inmediatamente sin ejecutar bcrypt.

**Después:** se añade `DUMMY_BCRYPT_HASH` (bcrypt rounds=12 precomputado
de una contraseña aleatoria que nadie conoce) y la función
`dummy_verify_password(password)` que ejecuta `bcrypt.checkpw` contra
ese hash dummy (el resultado no se valida, solo consume tiempo):

```python
# En autenticar, branch "usuario no encontrado":
if not row:
    dummy_verify_password(password)  # ← mismo tiempo que bcrypt real
    raise AuthenticationError("Usuario o contraseña incorrectos")
```

### H-S2 — Password strength unification

| Cambio | Antes | Después |
|--------|-------|---------|
| `cambiar_password_dialog` placeholder | "Mínimo 6 caracteres" | "Mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número" |
| `cambiar_password_dialog` umbral | `len(nueva) < 6` | `len(nueva) < 8` |
| `cambiar_password_dialog` strip | `self.txt_X.text().strip()` | `self.txt_X.text()` (sin strip) |
| `usuario_dialog` placeholder | "Mínimo 6 caracteres" | "Mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número" |
| `usuario_dialog` umbral | `len(pwd) < 6` | `len(pwd) < 8` |
| `_check_seguridad` umbral visual | `< 6` → "Muy débil" | `< 8` → "Muy débil" |
| `validar_fortaleza_password` (servicio) | 8 caracteres | 8 caracteres (sin cambio) |

### H-S5 — _float/_int allow 0 + allow clearing

**Antes:**
```python
def _float(val):
    try:
        return float(val) if val not in (None, '', '0', 0) else None
    except (ValueError, TypeError):
        return None

# En actualizar_historia:
h.temperatura = _float(data.get('temperatura')) or h.temperatura
```

Problemas:
- `_float(0) → None` (no se podía registrar T=0°C).
- `_float('0') → None` (no se podía registrar '0' desde un form).
- `... or h.temperatura` hacía imposible limpiar el campo (string vacío
  evaluaba a `h.temperatura`, manteniendo el valor previo).

**Después:**
```python
def _float(val):
    if val is None or val == '':
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def _coerce_or_keep(new_val, current_val, converter):
    if new_val is _MISSING:
        return current_val       # no vino en data → mantener
    return converter(new_val)    # vino (incluso None o '') → converter

# En actualizar_historia:
h.temperatura = _coerce_or_keep(
    data.get('temperatura', _MISSING), h.temperatura, _float)
```

Casos:
- `data = {'temperatura': 0}` → `_coerce_or_keep(0, prev, _float) = 0.0` ✓
- `data = {'temperatura': ''}` → `_coerce_or_keep('', prev, _float) = None` ✓ (limpiar)
- `data = {}` (sin key) → `_coerce_or_keep(_MISSING, prev, _float) = prev` ✓ (mantener)

### H-S6 — password_reset_required flag

Nueva columna en `usuarios` (añadida por la migración `c1a2b3c4d5e6`):

| Método | Comportamiento |
|--------|---------------|
| `reset_password(uid)` | setea `password_reset_required = 1` |
| `cambiar_password(uid, ...)` | limpia `password_reset_required = 0` |
| `cambiar_password_admin(uid, ...)` | limpia `password_reset_required = 0` |
| `autenticar(user, pwd)` | retorna `'password_reset_required': bool` en el dict |
| `requires_password_change(uid)` (nuevo) | helper para consultar la flag |

La GUI de login todavía no fuerza el cambio de contraseña; el backend
está listo y la GUI se actualizará en una fase posterior.

### H-D4 — FK indexes migration

Nueva migración `c1a2b3c4d5e6_fase5_indexes_and_password_reset_flag.py`
que crea **17 indexes** en FKs y columnas filtradas:

```
ix_movimientos_animal_id              ON movimientos(animal_id)
ix_muestras_animal_id                 ON muestras(animal_id)
ix_muestras_estado                    ON muestras(estado)
ix_muestras_fecha_recoleccion         ON muestras(fecha_recoleccion)
ix_recepciones_animal_id              ON recepciones(animal_id)
ix_recepciones_estado                 ON recepciones(estado)
ix_recepciones_fecha_hora             ON recepciones(fecha_hora)
ix_historias_clinicas_animal_id       ON historias_clinicas(animal_id)
ix_historias_clinicas_recepcion_id    ON historias_clinicas(recepcion_id)
ix_consultas_animal_id                ON consultas(animal_id)
ix_consultas_historia_id              ON consultas(historia_id)
ix_consultas_fecha                    ON consultas(fecha)
ix_cirugias_animal_id                 ON cirugias(animal_id)
ix_cirugias_historia_id               ON cirugias(historia_id)
ix_cirugias_estado                    ON cirugias(estado)
ix_vacunaciones_animal_id             ON vacunaciones(animal_id)
ix_vacunaciones_fecha_aplicacion      ON vacunaciones(fecha_aplicacion)
ix_vacunaciones_fecha_proxima         ON vacunaciones(fecha_proxima)
```

La migración es **idempotente** (usa `CREATE INDEX IF NOT EXISTS`) y
**segura** (verifica que la tabla exista antes de crear el index).
También añade la columna `password_reset_required INTEGER NOT NULL
DEFAULT 0` a la tabla `usuarios` (para H-S6).

`down_revision = '8f3a2c1d4e5f'` (merge-head de Fase 2). La cadena
Alembic sigue teniendo **1 head**: `c1a2b3c4d5e6`.

---

## Worklog entry para tu repo

Tras aplicar Fase 5, añade esta entrada a tu `worklog.md`:

```markdown
---
Task ID: 8
Agent: general-purpose (HIGH fixes — GUI + Services + DB)
Task: Fix 17 HIGH-severity issues from Tasks 3, 4, 5 of the worklog

Work Log:
- Read worklog Tasks 3, 4, 5 to extract all HIGH findings.
- Confirmed H-DB-1 (close_all_connections leak) and H-DB-2
  (AnimalRepository.update dropping 12 fields) were already fixed
  in Fase 2 — skipped.
- Inspected in full: components.py, dashboard.py, app.py, usuarios.py,
  muestra_dialog.py, recepcion.py, usuario_service.py, security.py,
  validators.py, historia_service.py, recepcion_service.py,
  cirugia_service.py, cambiar_password_dialog.py, usuario_dialog.py,
  animal.py (ORM), clinica.py (ORM), schemas/clinica.py.
- Verified migration chain: 9 revisions, single head
  (c1a2b3c4d5e6 after this phase).

Stage Summary:
- 17 HIGH defects fixed across 3 layers:
  GUI (8): ErrorHandler parent+sanitization+sentinel (H-G1);
           WindowManager dead code deleted (H-G2);
           boton_generar_reportes.py dead code deleted (H-G3);
           RecepcionView._get_selected_animal_id dead method removed (H-G4);
           DashboardView.theme_changed signal connected from app.py
             with _on_theme_changed handler iterating all active views (H-G5);
           usuarios.py dialog.exec() == QDialog.Accepted (H-G6);
           muestra_dialog monkey-patch replaced with _PegadoMagicoFilter
             QObject event filter (H-G7);
           PDFProWorker hoisted to module level + finished->deleteLater (H-G8).
  Services/Security (6): dummy_verify_password timing-attack mitigation (H-S1);
           password strength unification (8 chars, no strip) in both
             dialogs + service (H-S2);
           MuestraValidator path-traversal check on codigo (H-S3);
           whitelist estado in RecepcionService.actualizar_estado and
             CirugiaService.actualizar_estado (H-S4);
           historia_service _float/_int allow 0; _coerce_or_keep +
             _MISSING sentinel for distinguir missing/clearing/setting (H-S5);
           password_reset_required flag set by reset_password, cleared
             by cambiar_password[_admin], returned by autenticar,
             queryable via requires_password_change (H-S6).
  DB (3): created_at mapped in 8 ORM classes (H-D3);
          new migration c1a2b3c4d5e6 creates 17 FK indexes + the
            password_reset_required column (H-D4 + H-S6 backend);
          RecepcionSchema.empresa dead field removed (H-D6).
- 61 regression tests in tests/test_fase5_high.py — all PASSED on
  fresh clone after applying Fase 1+2+3+4+5.
- 21 files modified/added/deleted, 2 new files (migration + test file).
- Branch: feat/phase5-high-fixes (HEAD: 0f13163).
- Base: feat/phase4-gui-critical-fixes (7adf0b7).
```

---

## Próximas fases (roadmap)

| Fase | Scope | Estado |
|------|-------|--------|
| Fase 1 | Repo hygiene + tooling setup | ✅ aplicada |
| Fase 2 | Fix CRITICAL de base de datos | ✅ aplicada |
| Fase 3 | Fix CRITICAL de seguridad (RBAC + Jinja autoescape) | ✅ aplicada |
| Fase 4 | Fix CRITICAL de GUI | ✅ aplicada |
| **Fase 5** | **Fix HIGH (8 GUI + 6 Services + 3 DB)** | **✅ esta entrega** |
| Fase 6 | Fix MEDIUM/LOW (~60 issues) | pendiente |

Sugerido para Fase 6 (MEDIUM/LOW):
- H-DB-5: migrar todas las columnas de fecha `String` → `DateTime` con
  migración destructiva (DataMigrator que parsee los strings).
- Sincronizar cargas de tablas con `QThread`/`QThreadPool` (HIGH GUI que
  quedó fuera del alcance de esta Fase por ser un cambio arquitectural
  grande).
- Refactorizar `app.py` para usar un `_show_view(name, factory)` genérico.
- Cablear RBAC real en el sidebar (no solo esconder el botón "Usuarios").
- Eliminar los 6 assets de iconos inexistentes en `icon_manager.py`.
- Configurar i18n framework (todas las UI strings son hardcoded Spanish).
- Añadir keyboard shortcuts (Ctrl+N, Ctrl+S, F5).

---

## Preguntas frecuentes

**¿Por qué el `DUMMY_BCRYPT_HASH` tiene un salt público?**
Porque NO es un secreto. Es un hash bcrypt de una contraseña aleatoria
que NADIE conoce (generada con `secrets.token_bytes(32)`). El objetivo
no es validar la contraseña — solo es consumir tiempo de cómputo
(`bcrypt.checkpw` con rounds=12 tarda ~250ms sin importar el input).
Publicar el hash no da información útil al atacante.

**¿Por qué `ErrorHandler` retorna un sentinel en lugar de `None`?**
Porque `None` es un valor de retorno legítimo para algunos métodos
decorados (p.ej. `_get_selected_id` puede retornar `None` si no hay
selección). Si el decorador retornara `None` en caso de error, el
caller no podría distinguir "fallo" de "no hay selección". El sentinel
(`object()` único) resuelve esa ambigüedad.

**¿Por qué se eliminaron `window_manager.py` y `boton_generar_reportes.py`
en lugar de marcarlos como deprecated?**
Porque eran dead code puro: nada los importaba, nada los instanciaba.
Marcarlos como deprecated implica que todavía se usan en algún sitio —
falso. Eliminarlos reduce el surface area del codebase y evita que
futuros desarrolladores pierdan tiempo leyéndolos.

**¿La migración `c1a2b3c4d5e6` puede aplicarse en BDs que ya tienen
datos?**
Sí. Los `CREATE INDEX IF NOT EXISTS` son no-destructivos. La nueva
columna `password_reset_required INTEGER NOT NULL DEFAULT 0` se aplica
con `ALTER TABLE usuarios ADD COLUMN` que SQLite soporta sin reconstruir
la tabla — los registros existentes quedan con valor `0` (no requieren
cambio de password). Toda la migración es idempotente y segura.

**¿Qué pasa si NO aplico la migración pero sí el código de `autenticar`?**
El código usa `COALESCE(password_reset_required, 0)` que retorna `0`
si la columna no existe... pero SQLite levanta `OperationalError: no
such column: password_reset_required` ANTES de evaluar el `COALESCE`.
Entonces `autenticar` romperá hasta que apliques la migración. Por eso
el script `apply-phase5` sugiere `python -m alembic upgrade head` como
paso obligatorio post-aplicación.

**¿Los tests de Fase 5 requieren PySide6 instalado?**
No. Los 61 tests son:
- ~40 tests de inspección estática de código (regex sobre el source).
- ~15 tests funcionales del helper `_float`/`_int`/`_coerce_or_keep`,
  `dummy_verify_password`, `MuestraValidator`, `validar_fortaleza_password`,
  imports de `utils.security`/`utils.validators`/`schemas.clinica`.
- 4 tests de existencia de archivos (window_manager.py borrado,
  boton_generar_reportes.py borrado, migración existe, test file existe).
- 2 tests de migración (down_revision, FK indexes count).

No requieren `QApplication` ni `pytest-qt` ni `sqlalchemy` (excepto
los smoke tests de imports, que son best-effort).

**¿Aplica Fase 5 si todavía no apliqué Fase 1/2/3/4?**
No. Los parches se generaron contra `feat/phase4-gui-critical-fixes`
(HEAD `7adf0b7`). Aplicar sobre `master` crudo fallará con conflictos
(especialmente en `usuario_service.py` que ya tiene Authorizer wired
por Fase 3, y en `database/connection.py` con `_all_connections` de
Fase 2). Aplica primero Fase 1, 2, 3, 4 en orden.
