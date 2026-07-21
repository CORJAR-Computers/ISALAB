#!/usr/bin/env bash
# ============================================================================
# ISALAB — Fase 4: Fix CRITICAL de GUI
# Aplicador de parches para Linux / macOS / Git Bash
# ============================================================================
#
# USO:
#   cd /ruta/a/ISALAB          # clone con Fase 1, 2 y 3 ya aplicadas
#   bash apply-phase4.sh
#
# Este script aplica los 8 parches slim de Fase 4 sobre un repo donde
# ya se aplicaron Fase 1, 2 y 3. Los parches solo añaden/modifican
# archivos (no eliminan nada).
#
# Si todavía NO aplicaste Fase 1/2/3, aplica primero:
#   bash apply-phase1.sh && bash apply-phase2.sh && bash apply-phase3.sh
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES_DIR="$(cd "$SCRIPT_DIR/../patches" && pwd)"
REPO_DIR="$(pwd)"

# Colores
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
NC=$'\033[0m'

log()  { echo "${GREEN}[Fase 4]${NC} $*"; }
warn() { echo "${YELLOW}[Fase 4]${NC} $*"; }
err()  { echo "${RED}[Fase 4 ERROR]${NC} $*" >&2; }

# ─── Verificaciones previas ─────────────────────────────────────────────────

if [[ ! -d ".git" ]]; then
    err "No estás en un repositorio git (falta .git). Ejecuta desde la raíz del clone de ISALAB."
    exit 1
fi

if [[ ! -f "main.py" ]] || [[ ! -d "gui_pyside" ]] || [[ ! -d "services" ]]; then
    err "Parece que no estás en la raíz del repo ISALAB. Verifica que main.py, gui_pyside/ y services/ existan."
    exit 1
fi

if [[ ! -d "$PATCHES_DIR" ]]; then
    err "No encuentro el directorio de parches: $PATCHES_DIR"
    err "Descarga el ZIP completo de ISALAB-fase4/ y reintenta."
    exit 1
fi

log "Aplicando Fase 4 — Fix CRITICAL de GUI"
log "Repo: $REPO_DIR"
log "Parches: $PATCHES_DIR"
echo

# ─── Verificar que el working tree esté limpio ───────────────────────────────

if ! git diff --quiet || ! git diff --cached --quiet; then
    warn "Tienes cambios sin commit en el working tree."
    warn "Recomendación: commit o stash antes de aplicar Fase 4."
    warn "Continuando en 5 segundos... (Ctrl+C para cancelar)"
    sleep 5
    echo
fi

# ─── Aplicar parches slim uno por uno ────────────────────────────────────────

PATCHES=(
    "gui_pyside_app.py.patch"
    "gui_pyside_splash.py.patch"
    "gui_pyside_views_dashboard.py.patch"
    "gui_pyside_dialogs_muestra_dialog.py.patch"
    "gui_pyside_dialogs_vacuna_dialog.py.patch"
    "gui_pyside_utils_platform_utils.py.patch"
    "services_report_service.py.patch"
    "tests_test_fase4_gui.py.patch"
)

applied=0
failed=0
for p in "${PATCHES[@]}"; do
    patch_path="$PATCHES_DIR/$p"
    if [[ ! -f "$patch_path" ]]; then
        err "Falta parche: $p"
        failed=$((failed + 1))
        continue
    fi

    # Intentar aplicar con git apply
    if git apply --check "$patch_path" 2>/dev/null; then
        git apply --verbose "$patch_path" 2>&1 | grep -E "^(\+|-|Checking|Applied)" | head -3 || true
        log "  ✓ $p"
        applied=$((applied + 1))
    else
        # Ver si ya estaba aplicado (idempotente)
        if git apply --reverse --check "$patch_path" 2>/dev/null; then
            warn "  ⊙ $p (ya estaba aplicado, skip)"
            applied=$((applied + 1))
        else
            err "  ✗ $p (conflicto — revisa el working tree)"
            err "    Intenta: git apply --reject --verbose $patch_path"
            failed=$((failed + 1))
        fi
    fi
done

echo
log "Resumen: $applied aplicados, $failed fallidos"
echo

# ─── Verificación post-aplicación ────────────────────────────────────────────

log "Verificación post-aplicación:"

# C3: app.py usa Logo_Sidebar.png (PascalCase)
if grep -q "Logo_Sidebar.png" gui_pyside/app.py 2>/dev/null; then
    log "  ✓ C3 app.py referencia 'Logo_Sidebar.png' (PascalCase)"
else
    err "  ✗ C3 app.py NO referencia 'Logo_Sidebar.png'"
fi

# C3: splash.py usa Logo_Sidebar.png (PascalCase)
if grep -q "Logo_Sidebar.png" gui_pyside/splash.py 2>/dev/null; then
    log "  ✓ C3 splash.py referencia 'Logo_Sidebar.png' (PascalCase)"
else
    err "  ✗ C3 splash.py NO referencia 'Logo_Sidebar.png'"
fi

# C1: muestra_dialog.py ya no referencia self.ref_text en código
if ! grep -E "^[[:space:]]*[^#].*self\.ref_text" gui_pyside/dialogs/muestra_dialog.py 2>/dev/null | grep -v "^[[:space:]]*#"; then
    log "  ✓ C1 ResultadoMuestraDialog._guardar no referencia self.ref_text"
else
    err "  ✗ C1 muestra_dialog.py todavía referencia self.ref_text en código"
fi

# C2: dashboard.py invoca get_dashboard_stats
if grep -q "get_dashboard_stats" gui_pyside/views/dashboard.py 2>/dev/null; then
    log "  ✓ C2 DashboardView.refresh invoca ReportService.get_dashboard_stats"
else
    err "  ✗ C2 DashboardView no invoca get_dashboard_stats"
fi

# C2: dashboard.py mantiene self.stat_labels
if grep -q "self.stat_labels" gui_pyside/views/dashboard.py 2>/dev/null; then
    log "  ✓ C2 DashboardView mantiene referencias self.stat_labels"
else
    err "  ✗ C2 DashboardView no mantiene self.stat_labels"
fi

# C2: report_service.py añade consultas_hoy
if grep -q "consultas_hoy" services/report_service.py 2>/dev/null; then
    log "  ✓ C2 ReportService.get_dashboard_stats retorna consultas_hoy"
else
    err "  ✗ C2 ReportService no retorna consultas_hoy"
fi

# C4: platform_utils.py existe
if [[ -f gui_pyside/utils/platform_utils.py ]]; then
    log "  ✓ C4 gui_pyside/utils/platform_utils.py presente"
else
    err "  ✗ C4 gui_pyside/utils/platform_utils.py falta"
fi

# C4: open_file_externally definido
if grep -q "def open_file_externally" gui_pyside/utils/platform_utils.py 2>/dev/null; then
    log "  ✓ C4 open_file_externally definido en platform_utils"
else
    err "  ✗ C4 open_file_externally NO definido"
fi

# C4: muestra_dialog.py usa el helper
if grep -q "open_file_externally" gui_pyside/dialogs/muestra_dialog.py 2>/dev/null; then
    log "  ✓ C4 muestra_dialog.py usa open_file_externally"
else
    err "  ✗ C4 muestra_dialog.py no usa open_file_externally"
fi

# C4: vacuna_dialog.py usa el helper
if grep -q "open_file_externally" gui_pyside/dialogs/vacuna_dialog.py 2>/dev/null; then
    log "  ✓ C4 vacuna_dialog.py usa open_file_externally"
else
    err "  ✗ C4 vacuna_dialog.py no usa open_file_externally"
fi

# Tests de Fase 4 presentes
if [[ -f tests/test_fase4_gui.py ]]; then
    log "  ✓ tests/test_fase4_gui.py presente"
else
    err "  ✗ tests/test_fase4_gui.py falta"
fi

echo
if [[ $failed -eq 0 ]]; then
    log "✅ Fase 4 aplicada correctamente."
    echo
    log "Próximos pasos sugeridos:"
    echo "  1. Revisa los cambios con:  git diff"
    echo "  2. Corre los tests:         python -m pytest tests/test_fase4_gui.py -v"
    echo "  3. Commit en tu rama:       git add -A && git commit -m 'fix(ISALAB): Fase 4 — Fix CRITICAL de GUI'"
    echo "  4. Push a tu fork y abre PR contra master."
else
    err "❌ $failed parche(s) fallaron. Revisa el log arriba."
    err "Si el conflicto es por Fase 1/2/3 ya aplicada parcialmente, aplica el consolidado:"
    err "  git apply --reject $PATCHES_DIR/0001-fix-ISALAB-Fase-4-Fix-CRITICAL-de-GUI.patch"
    exit 1
fi
