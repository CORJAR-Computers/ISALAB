#!/usr/bin/env bash
# ============================================================================
# ISALAB — Fase 3: Fix CRITICAL de seguridad
# Aplicador de parches para Linux / macOS / Git Bash
# ============================================================================
#
# USO:
#   cd /ruta/a/ISALAB          # clone limpio de https://github.com/CORJAR-Computers/ISALAB
#   bash apply-phase3.sh
#
# Este script aplica los 23 parches slim de Fase 3 sobre un clone limpio
# del repositorio público. Los parches solo añaden/modifican archivos (no
# eliminan nada). Para Fase 3 no hay archivos que eliminar.
#
# Si ya tienes Fase 1 y Fase 2 aplicadas, este script también funciona —
# git apply es idempotente si los parches no entran en conflicto.
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

log()  { echo "${GREEN}[Fase 3]${NC} $*"; }
warn() { echo "${YELLOW}[Fase 3]${NC} $*"; }
err()  { echo "${RED}[Fase 3 ERROR]${NC} $*" >&2; }

# ─── Verificaciones previas ─────────────────────────────────────────────────

if [[ ! -d ".git" ]]; then
    err "No estás en un repositorio git (falta .git). Ejecuta desde la raíz del clone de ISALAB."
    exit 1
fi

if [[ ! -f "main.py" ]] || [[ ! -d "services" ]] || [[ ! -d "utils" ]]; then
    err "Parece que no estás en la raíz del repo ISALAB. Verifica que main.py, services/ y utils/ existan en el directorio actual."
    exit 1
fi

if [[ ! -d "$PATCHES_DIR" ]]; then
    err "No encuentro el directorio de parches: $PATCHES_DIR"
    err "Descarga el ZIP completo de ISALAB-fase3/ y reintenta."
    exit 1
fi

log "Aplicando Fase 3 — Fix CRITICAL de seguridad"
log "Repo: $REPO_DIR"
log "Parches: $PATCHES_DIR"
echo

# ─── Verificar que el working tree esté limpio ───────────────────────────────

if ! git diff --quiet || ! git diff --cached --quiet; then
    warn "Tienes cambios sin commit en el working tree."
    warn "Recomendación: commit o stash antes de aplicar Fase 3."
    warn "Continuando en 5 segundos... (Ctrl+C para cancelar)"
    sleep 5
    echo
fi

# ─── Aplicar parches slim uno por uno ────────────────────────────────────────

PATCHES=(
    "utils_security.py.patch"
    "services_usuario_service.py.patch"
    "services_animal_service.py.patch"
    "services_muestra_service.py.patch"
    "services_recepcion_service.py.patch"
    "services_consulta_service.py.patch"
    "services_cirugia_service.py.patch"
    "services_vacuna_service.py.patch"
    "services_historia_service.py.patch"
    "services_configuracion_service.py.patch"
    "services_report_service.py.patch"
    "services_pdf_service.py.patch"
    "services_report_laboratorio.py.patch"
    "services_report_vacunacion.py.patch"
    "services_report_historia_clinica.py.patch"
    "services_report_cirugia.py.patch"
    "services_report_consulta.py.patch"
    "services_report_consentimiento.py.patch"
    "services_report_formula_medica.py.patch"
    "reports_generators.py.patch"
    "reports_base.py.patch"
    "main.py.patch"
    "tests_test_fase3_security.py.patch"
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
        git apply --verbose "$patch_path" 2>&1 | grep -E "^(\+|-|Checking|Applied)" | head -5 || true
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

# C1: utils/security.py debe tener PermissionDeniedError
if grep -q "class PermissionDeniedError" utils/security.py 2>/dev/null; then
    log "  ✓ C4 PermissionDeniedError definido en utils/security.py"
else
    err "  ✗ C4 PermissionDeniedError NO encontrado en utils/security.py"
fi

# C1: utils/security.py debe tener set_current_user
if grep -q "def set_current_user" utils/security.py 2>/dev/null; then
    log "  ✓ C1 set_current_user definido en utils/security.py"
else
    err "  ✗ C1 set_current_user NO encontrado en utils/security.py"
fi

# C2: services/recepcion_service.py debe usar DatabaseManager().generar_codigo('ISAL')
if grep -q "db.generar_codigo('ISAL')" services/recepcion_service.py 2>/dev/null; then
    log "  ✓ C2 RecepcionService.generar_codigo usa contador atómico"
else
    err "  ✗ C2 RecepcionService.generar_codigo NO usa contador atómico"
fi

# C3: reports/generators.py debe tener select_autoescape
if grep -q "select_autoescape" reports/generators.py 2>/dev/null; then
    log "  ✓ C3 Jinja2 autoescape activo en reports/generators.py"
else
    err "  ✗ C3 select_autoescape NO encontrado en reports/generators.py"
fi

# C3: reports/generators.py debe tener _safe_url_fetcher
if grep -q "_safe_url_fetcher" reports/generators.py 2>/dev/null; then
    log "  ✓ C3 url_fetcher sandboxed en reports/generators.py"
else
    err "  ✗ C3 _safe_url_fetcher NO encontrado en reports/generators.py"
fi

# C1: main.py debe llamar set_current_user
if grep -q "set_current_user" main.py 2>/dev/null; then
    log "  ✓ C1 main.py invoca set_current_user tras login"
else
    err "  ✗ C1 main.py NO invoca set_current_user"
fi

# Tests de Fase 3 presentes
if [[ -f tests/test_fase3_security.py ]]; then
    log "  ✓ tests/test_fase3_security.py presente"
else
    err "  ✗ tests/test_fase3_security.py falta"
fi

echo
if [[ $failed -eq 0 ]]; then
    log "✅ Fase 3 aplicada correctamente."
    echo
    log "Próximos pasos sugeridos:"
    echo "  1. Revisa los cambios con:  git diff"
    echo "  2. Corre los tests:         python -m pytest tests/test_fase3_security.py -v"
    echo "  3. Commit en tu rama:       git add -A && git commit -m 'fix(ISALAB): Fase 3 — Fix CRITICAL de seguridad'"
    echo "  4. Push a tu fork y abre PR contra master."
else
    err "❌ $failed parche(s) fallaron. Revisa el log arriba."
    err "Si el conflicto es por Fase 1/2 ya aplicada parcialmente, descarta el parche problemático y aplica el consolidado:"
    err "  git apply --reject $PATCHES_DIR/0001-fix-ISALAB-Fase-3-Fix-CRITICAL-de-seguridad.patch"
    exit 1
fi
