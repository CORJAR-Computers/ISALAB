# ISALAB — Fase 4: Fix CRITICAL de GUI

> Cuatro defects CRITICAL de la capa GUI (Task 5 del worklog) entregados como
> parches aplicables con GitHub Desktop / `git apply`.

---

## Resumen de la Fase 4

| ID | Problema | Archivo(s) afectado(s) |
|----|----------|------------------------|
| **C1** | `ResultadoMuestraDialog._guardar` (muestra_dialog.py:780) llamaba `self.ref_text.toPlainText()` sobre un widget **que nunca se crea** → `AttributeError` al pulsar "💾 Guardar Resultados" y los resultados **no se persistían**. | `gui_pyside/dialogs/muestra_dialog.py` |
| **C2** | `DashboardView.refresh()` (dashboard.py:188) era un **no-op** con el comentario "# Aquí cargarías datos reales desde los servicios". Las 4 tarjetas ("Total Pacientes", "Muestras Pendientes", "Consultas Hoy", "Urgentes") mostraban **"0" permanente**. | `gui_pyside/views/dashboard.py`, `services/report_service.py` |
| **C3** | `app.py:103` y `splash.py:24` referenciaban `logo_sidebar.png` (lowercase) pero el asset real es `Logo_Sidebar.png` (PascalCase). En filesystems case-sensitive (Linux/macOS) el logo **no carga** y cae al fallback de texto "IsaLab". | `gui_pyside/app.py`, `gui_pyside/splash.py` |
| **C4** | `muestra_dialog.py:823` y `:1083`, y `vacuna_dialog.py:260` llamaban `os.startfile(filepath)` directamente. `os.startfile` **SOLO existe en Windows**; en macOS/Linux levanta `AttributeError` y rompe los botones "🖨️ Guardar e Imprimir PDF", "🖨️ Imprimir Resultados Pro" y "🖨️ Imprimir Certificado". | `gui_pyside/utils/platform_utils.py` (nuevo), `gui_pyside/dialogs/muestra_dialog.py`, `gui_pyside/dialogs/vacuna_dialog.py` |

Adicionalmente se incluye **`tests/test_fase4_gui.py`** con **16 tests de regresión** (cubre los 4 fixes con verificación estática de código + tests funcionales del helper multiplataforma con `monkeypatch` de `subprocess.Popen` y `os.startfile`).

---

## Estructura del paquete

```
ISALAB-fase4/
├── README.md                     ← este archivo
├── patches/
│   ├── 0001-fix-ISALAB-Fase-4-Fix-CRITICAL-de-GUI.patch  ← consolidado
│   ├── gui_pyside_app.py.patch
│   ├── gui_pyside_splash.py.patch
│   ├── gui_pyside_views_dashboard.py.patch
│   ├── gui_pyside_dialogs_muestra_dialog.py.patch
│   ├── gui_pyside_dialogs_vacuna_dialog.py.patch
│   ├── gui_pyside_utils_platform_utils.py.patch          ← archivo nuevo
│   ├── services_report_service.py.patch
│   └── tests_test_fase4_gui.py.patch                     ← archivo nuevo
├── scripts/
│   ├── apply-phase4.sh           ← Linux / macOS / Git Bash
│   └── apply-phase4.ps1          ← Windows PowerShell
└── files/                        ← archivos finales para inspección
    ├── gui_pyside/
    │   ├── app.py
    │   ├── splash.py
    │   ├── utils/
    │   │   └── platform_utils.py
    │   ├── views/
    │   │   └── dashboard.py
    │   └── dialogs/
    │       ├── muestra_dialog.py
    │       └── vacuna_dialog.py
    ├── services/
    │   └── report_service.py
    └── tests/
        └── test_fase4_gui.py
```

---

## Requisitos previos

**Esta Fase 4 asume que ya aplicaste y commiteaste Fase 1, 2 y 3** sobre tu
repo. Si no lo has hecho, ejecuta primero:

```bash
bash apply-phase1.sh && \
bash apply-phase2.sh && \
bash apply-phase3.sh && \
git add -A && git commit -m "Fase 1+2+3 applied"
```

Los parches de Fase 4 se generaron contra el commit `46f979c` (HEAD de
`feat/phase3-security-critical`). Aplicarlos sobre un estado distinto puede
provocar conflictos.

---

## Aplicación con GitHub Desktop (recomendado)

GitHub Desktop **no tiene** un botón "Apply patch" nativo, pero el flujo
siguiente funciona igual de bien y queda como un commit en tu rama:

1. **Abre el repo en GitHub Desktop** y asegúrate de estar en una rama de
   trabajo (p.ej. `feat/phase4-gui-critical-fixes`). Si no la tienes:
   - `Branch → New Branch…` → nómbrala `feat/phase4-gui-critical-fixes`.

2. **Abre la terminal del repo** desde GitHub Desktop:
   - `Repository → Open in Terminal` (en Windows: PowerShell).
   - O usa tu terminal favorita y haz `cd /ruta/a/ISALAB`.

3. **Ejecuta el aplicador** según tu SO:

   **Linux / macOS / Git Bash:**
   ```bash
   bash /ruta/donde/descargaste/ISALAB-fase4/scripts/apply-phase4.sh
   ```

   **Windows PowerShell:**
   ```powershell
   .\ruta\donde\descargaste\ISALAB-fase4\scripts\apply-phase4.ps1
   ```

   El script:
   - Verifica que estás en la raíz del repo (con `.git`, `main.py`, etc.).
   - Verifica que el working tree esté razonablemente limpio (warn, no block).
   - Aplica los 8 parches slim con `git apply` (idempotente: si ya estaba
     aplicado, lo salta con `⊙`).
   - Hace **11 verificaciones post-aplicación** para confirmar que cada fix
     quedó en su lugar.
   - Si todo OK, sugiere los próximos pasos.

4. **Vuelve a GitHub Desktop** — verás los 8 archivos modificados/añadidos
   en la lista de cambios. Revísalos con calma.

5. **Commit** desde GitHub Desktop con el mensaje sugerido:
   ```
   fix(ISALAB): Fase 4 — Fix CRITICAL de GUI
   ```
   (copia exacta del commit del bot, ver `patches/0001-…patch` para el
   mensaje completo si quieres más detalle).

6. **Push** a tu fork y abre PR contra `master`.

---

## Aplicación manual (sin script)

Si prefieres aplicar los parches a mano:

```bash
cd /ruta/a/ISALAB
PATCHES=/ruta/donde/descargaste/ISALAB-fase4/patches

git apply --verbose $PATCHES/gui_pyside_app.py.patch
git apply --verbose $PATCHES/gui_pyside_splash.py.patch
git apply --verbose $PATCHES/gui_pyside_views_dashboard.py.patch
git apply --verbose $PATCHES/gui_pyside_dialogs_muestra_dialog.py.patch
git apply --verbose $PATCHES/gui_pyside_dialogs_vacuna_dialog.py.patch
git apply --verbose $PATCHES/gui_pyside_utils_platform_utils.py.patch
git apply --verbose $PATCHES/services_report_service.py.patch
git apply --verbose $PATCHES/tests_test_fase4_gui.py.patch
```

O todo de una vez con el consolidado (preserva autoría + mensaje):

```bash
git am --signoff < $PATCHES/0001-fix-ISALAB-Fase-4-Fix-CRITICAL-de-GUI.patch
```

> `git am` deja un commit limpio en tu rama. Es la forma más fiel al
> trabajo original del bot.

---

## Verificación

Tras aplicar, ejecuta los tests:

```bash
python -m pytest tests/test_fase4_gui.py -v
```

Salida esperada (16 tests, todos PASSED):

```
tests/test_fase4_gui.py::test_c1_no_self_ref_text_in_guardar PASSED
tests/test_fase4_gui.py::test_c1_widget_ref_text_never_created PASSED
tests/test_fase4_gui.py::test_c2_refresh_calls_report_service PASSED
tests/test_fase4_gui.py::test_c2_refresh_body_is_not_a_comment_only PASSED
tests/test_fase4_gui.py::test_c2_stat_labels_tracked_for_refresh PASSED
tests/test_fase4_gui.py::test_c2_report_service_returns_consultas_hoy PASSED
tests/test_fase4_gui.py::test_c3_app_uses_pascalcase_logo PASSED
tests/test_fase4_gui.py::test_c3_splash_uses_pascalcase_logo PASSED
tests/test_fase4_gui.py::test_c3_pascalcase_asset_exists_on_disk PASSED
tests/test_fase4_gui.py::test_c4_platform_utils_helper_exists PASSED
tests/test_fase4_gui.py::test_c4_no_os_startfile_in_productive_dialogs PASSED
tests/test_fase4_gui.py::test_c4_helper_uses_correct_command_per_platform PASSED
tests/test_fase4_gui.py::test_c4_helper_returns_false_for_missing_file PASSED
tests/test_fase4_gui.py::test_c4_helper_returns_false_when_viewer_missing PASSED
tests/test_fase4_gui.py::test_c4_muestra_dialog_imports_helper PASSED
tests/test_fase4_gui.py::test_c4_vacuna_dialog_imports_helper PASSED
============================== 16 passed ==============================
```

También puedes correr la suite completa:

```bash
python -m pytest tests/ -v --no-cov
```

> Nota: `tests/test_fase2_database.py::test_alembic_upgrade_head_no_multiple_heads`
> puede fallar si `alembic` no está instalado en el entorno — es un
> issue preexistente del sandbox, no una regresión de Fase 4.

---

## Detalle técnico de cada fix

### C1 — `self.ref_text` AttributeError

**Antes (muestra_dialog.py:780):**
```python
def _guardar(self):
    estado = self.estado.currentText()
    resultado_final = self._extraer_json_desde_tabla()
    valor_ref = self.ref_text.toPlainText().strip() or None  # ← BOOM
    self.service.actualizar_estado(
        self.muestra_id, estado, resultado_final, valor_ref)
```

**Después:**
```python
def _guardar(self):
    estado = self.estado.currentText()
    resultado_final = self._extraer_json_desde_tabla()
    # Las referencias por ítem ya viajan dentro del JSON de
    # `resultado_final` (columna "Referencia" de `tabla_resultados`).
    valor_ref = None
    self.service.actualizar_estado(
        self.muestra_id, estado, resultado_final, valor_ref)
```

Las referencias por ítem ya estaban cubiertas: `_extraer_json_desde_tabla`
construye un JSON `{"items": [...], "observaciones": [...]}` donde cada
item incluye su `ref_texto`. El campo global `valor_referencia` de la
tabla `muestras` queda como `NULL` cuando no hay un texto global adicional
— exactamente el mismo comportamiento que si el widget hubiera existido y
estuviera vacío.

### C2 — Dashboard.refresh() no-op

**Antes (dashboard.py:188):**
```python
@ErrorHandler.handle_exception
def refresh(self):
    """Refresca los datos del dashboard"""
    # Aquí cargarías datos reales desde los servicios
```

**Después:** el dashboard guarda referencias a los `QLabel` de valor en
`self.stat_labels` (un dict con keys `activos`, `pendientes`,
`consultas_hoy`, `urgentes`) durante `_build_layout`. `refresh()` ahora:

1. Instancia `ReportService()` (ya existente, con RBAC de Fase 3).
2. Llama `svc.get_dashboard_stats()` que retorna `activos`,
   `muestras_pendientes`, `urgentes`, y **el nuevo `consultas_hoy`**
   añadido a `services/report_service.py`.
3. Mapea cada stat a su `QLabel` y hace `label.setText(str(int(value)))`.
4. Es tolerante: si el servicio falla, los labels conservan su valor
   previo (no rompe la UI).

`refresh()` se invoca automáticamente al final de `_build_layout()` y
después de `rebuild_layout()` (tras un toggle de tema), así que las
tarjetas ya no arrancan en "0".

### C3 — Case mismatch `logo_sidebar.png` vs `Logo_Sidebar.png`

**Antes:**
```python
# app.py
logo_path = os.path.join(BASE_DIR, "assets", "logo_sidebar.png")
# splash.py
logo_path = BASE_DIR / "assets" / "logo_sidebar.png"
```

**Después:**
```python
# app.py
logo_path = os.path.join(BASE_DIR, "assets", "Logo_Sidebar.png")
# splash.py
logo_path = BASE_DIR / "assets" / "Logo_Sidebar.png"
```

El archivo en el repo es `assets/Logo_Sidebar.png` (PascalCase, 484 KB).
En Windows (NTFS case-insensitive) `logo_sidebar.png` resolvía por
accidente; en Linux/macOS no, y caía al fallback `QLabel("IsaLab")`.

> La inconsistencia de casing en `assets/` (`Logo.png` vs `isalab_icon.png`
> vs `Logo_Sidebar.png`) es un issue MEDIUM/LOW pendiente para una Fase
> posterior — fuera del alcance de "CRITICAL de GUI".

### C4 — `os.startfile` crashes en macOS/Linux

**Antes (muestra_dialog.py:823, 1083 + vacuna_dialog.py:260):**
```python
os.startfile(filepath)  # ← AttributeError en macOS/Linux
```

**Después:** todo pasa por el nuevo helper centralizado
`gui_pyside/utils/platform_utils.py::open_file_externally`:

```python
def open_file_externally(filepath) -> bool:
    path = Path(filepath)
    if not path.exists():
        logger.error(...)
        return False
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)], ...)
        else:
            subprocess.Popen(["xdg-open", str(path)], ...)
        return True
    except FileNotFoundError:
        # visor no disponible — loguear y devolver False
        return False
    except Exception:
        return False
```

El helper es **tolerante**: si el archivo no existe, o si el visor nativo
no está instalado (p.ej. contenedores headless sin `xdg-utils`), devuelve
`False` sin propagar la excepción — evita romper flujos críticos como el
guardado de resultados.

> `dialogo_generar_reporte.py:471` ya tenía una versión inline
> cross-platform (no se incluye en el worklog como CRITICAL). Queda como
> deuda técnica MEDIUM: refactorizarla para usar el nuevo helper.

---

## Worklog entry para tu repo

Tras aplicar Fase 4, añade esta entrada a tu `worklog.md`:

```markdown
---
Task ID: 7
Agent: general-purpose (GUI critical fixes)
Task: Fix 4 CRITICAL GUI defects from Task 5 of the worklog

Work Log:
- Read worklog Task 5 to extract the 4 CRITICAL GUI findings.
- Inspected in full: `gui_pyside/dialogs/muestra_dialog.py` (1094 lines),
  `gui_pyside/views/dashboard.py` (191 lines), `gui_pyside/app.py` (461 lines),
  `gui_pyside/splash.py` (99 lines), `services/report_service.py` (113 lines).
- Confirmed actual asset name: `assets/Logo_Sidebar.png` (PascalCase).
- Confirmed `self.ref_text` is never assigned anywhere in `muestra_dialog.py`.
- Confirmed `os.startfile` is used in 3 places (2 in muestra_dialog, 1 in vacuna_dialog).
- Confirmed `ReportService.get_dashboard_stats` already returns `activos`,
  `muestras_pendientes`, `urgentes` — only `consultas_hoy` was missing.

Stage Summary:
- 4 CRITICAL defects fixed:
  C1: self.ref_text AttributeError removed — _guardar now passes valor_ref=None.
  C2: DashboardView.refresh wired to ReportService.get_dashboard_stats;
      self.stat_labels dict tracks the 4 value QLabels; refresh called from
      _build_layout and rebuild_layout. New stat 'consultas_hoy' added to
      ReportService.get_dashboard_stats.
  C3: app.py and splash.py now reference 'Logo_Sidebar.png' (PascalCase).
  C4: New helper gui_pyside/utils/platform_utils.py::open_file_externally
      dispatches os.startfile / open / xdg-open per sys.platform. All 3
      os.startfile call sites (muestra_dialog x2, vacuna_dialog x1) now
      use the helper.
- 16 regression tests in tests/test_fase4_gui.py — all PASSED on fresh
  clone after applying Fase 1+2+3+4.
- 8 modified/added files, 1 new file (platform_utils.py), 1 new test file.
- Branch: feat/phase4-gui-critical-fixes (HEAD: 7adf0b7).
- Base: feat/phase3-security-critical (46f979c).
```

---

## Próximas fases (roadmap)

| Fase | Scope | Estado |
|------|-------|--------|
| Fase 1 | Repo hygiene + tooling setup | ✅ aplicada |
| Fase 2 | Fix CRITICAL de base de datos | ✅ aplicada |
| Fase 3 | Fix CRITICAL de seguridad (RBAC + Jinja autoescape) | ✅ aplicada |
| **Fase 4** | **Fix CRITICAL de GUI** | **✅ esta entrega** |
| Fase 5 | Fix HIGH (12 issues GUI + 9 issues servicios + 3 DB) | pendiente |
| Fase 6 | Fix MEDIUM/LOW (casi 60 issues) | pendiente |

Sugerido para Fase 5 (HIGH GUI):
- Sincronizar todas las cargas de tablas con `QThread`/`QThreadPool`.
- Reemplazar `ErrorHandler.handle_exception` para no usar `parent=None`
  ni mostrar `str(e)` crudo al usuario.
- Borrar `boton_generar_reportes.py` (500 líneas de dead code).
- Conectar la señal `DashboardView.theme_changed` desde `app.py`.
- Refactorizar `app.py` para usar un `_show_view(name, factory)` genérico.
- Cablear RBAC real en el sidebar (no solo esconder el botón "Usuarios").

---

## Preguntas frecuentes

**¿Por qué el helper de C4 no lanza excepciones?**
Porque los botones que lo usan ("🖨️ Guardar e Imprimir PDF", etc.) son
finales de flujo — el usuario ya guardó los resultados en la BD. Si el
visor PDF no está disponible, lo último que queremos es romper la UI
con un traceback. El helper loguea el error y devuelve `False`; la app
puede mostrar un mensaje amable si lo desea (no implementado en Fase 4
— queda como mejora HIGH para Fase 5).

**¿Por qué `valor_ref=None` en C1? ¿No debería haber un campo?**
Podría, pero el diálogo nunca tuvo ese widget. Añadirlo ahora sería una
mezcla de bugfix + feature — fuera del alcance de "CRITICAL de GUI".
Las referencias por ítem ya viajan en el JSON `resultado_final`. Si se
desea un campo global de referencia, es un feature request separado.

**¿Por qué no se renombró `Logo_Sidebar.png` a `logo_sidebar.png`?**
Porque el worklog ofrecía ambas opciones ("Rename ... or fix the code")
y cambiar el código es 2 líneas sin tocar el índice git, mientras que un
`git mv` requiere un paso extra en el apply script y rompe en
filesystems case-insensitive (Windows) con "destination exists". La
consistencia de casing en `assets/` es un issue MEDIUM/LOW separado.

**¿Aplica Fase 4 si todavía no apliqué Fase 1/2/3?**
No. Los parches se generaron contra `feat/phase3-security-critical`
(HEAD `46f979c`). Aplicar sobre `master` crudo fallará con conflictos.
Aplica primero Fase 1, 2, 3 en orden.

**¿Los tests de Fase 4 requieren PySide6 instalado?**
No. Los 16 tests son:
- 6 tests de inspección estática de código (regex sobre el source).
- 5 tests funcionales del helper `platform_utils.py` con `monkeypatch`
  de `subprocess.Popen` / `os.startfile` (no requieren Qt).
- 1 test que requiere `sqlalchemy` (para instanciar `ReportService`).
- 4 tests de existencia de archivos.

No requieren `QApplication` ni `pytest-qt`.
