#!/usr/bin/env bash
# apply-phase5.sh — Aplica los parches de la Fase 5 (Fix HIGH) al repo ISALAB.
#
# Uso:
#   bash apply-phase5.sh        # desde la raíz del repo ISALAB
#
# Requisitos:
#   - Estar en la raíz de un clone del repo ISALAB (con .git, main.py, etc.).
#   - Tener aplicadas las Fases 1, 2, 3 y 4.
#   - Working tree razonablemente limpio (advertencia si no).
#
# El script:
#   1. Verifica que estás en la raíz del repo.
#   2. Verifica que el working tree esté limpio (warn, no block).
#   3. Aplica los 19 parches slim con `git apply` (idempotente).
#   4. Hace `git rm` de los 2 archivos eliminados:
#        - gui_pyside/utils/window_manager.py
#        - gui_pyside/views/boton_generar_reportes.py
#   5. Verifica 14 condiciones post-aplicación.
#   6. Sugiere próximos pasos.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES_DIR="${SCRIPT_DIR}/../patches"

# Colores para output.
if [[ -t 1 ]]; then
    GREEN='\031[0;32m'; YELLOW='\031[1;33m'; RED='\031[0;31m'; NC='\031[0m'
    OK="✓"; WARN="⚠"; ERR="✗"; INFO="⊙"
else
    GREEN=''; YELLOW=''; RED=''; NC=''
    OK="OK"; WARN="WARN"; ERR="ERR"; INFO="--"
fi

echo ""
echo "============================================================"
echo "  ISALAB — Fase 5: Fix HIGH issues (GUI + Services + DB)"
echo "============================================================"
echo ""

# ─── 1. Verificar raíz del repo ──────────────────────────────────────────
if [[ ! -d .git ]]; then
    echo -e "${RED}${ERR} No estás en la raíz de un repo git.${NC}"
    echo "  Ejecuta este script desde la raíz del clone ISALAB."
    exit 1
fi
if [[ ! -f main.py || ! -f config.py ]]; then
    echo -e "${RED}${ERR} No parece ser el repo ISALAB (falta main.py o config.py).${NC}"
    exit 1
fi
echo -e "${GREEN}${OK} Repo ISALAB detectado: $(pwd)${NC}"

# ─── 2. Verificar working tree ────────────────────────────────────────────
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo -e "${YELLOW}${WARN} El working tree tiene cambios sin commitear.${NC}"
    echo "  Recomendado: commitea o stash antes de aplicar."
    echo "  Continuando de todas formas..."
fi

# ─── 3. Aplicar parches slim (added/modified) ────────────────────────────
echo ""
echo "── Aplicando 21 parches slim ──"
SLIM_PATCHES=(
    "alembic_versions_c1a2b3c4d5e6_fase5_indexes_and_password_reset_flag.py.patch"
    "gui_pyside_app.py.patch"
    "gui_pyside_components_components.py.patch"
    "gui_pyside_dialogs_cambiar_password_dialog.py.patch"
    "gui_pyside_dialogs_muestra_dialog.py.patch"
    "gui_pyside_dialogs_usuario_dialog.py.patch"
    "gui_pyside_views_dashboard.py.patch"
    "gui_pyside_views_recepcion.py.patch"
    "gui_pyside_views_usuarios.py.patch"
    "orm_models_animal.py.patch"
    "orm_models_clinica.py.patch"
    "schemas_clinica.py.patch"
    "services_cirugia_service.py.patch"
    "services_historia_service.py.patch"
    "services_recepcion_service.py.patch"
    "services_usuario_service.py.patch"
    "tests_test_fase3_security.py.patch"
    "tests_test_fase4_gui.py.patch"
    "tests_test_fase5_high.py.patch"
    "utils_security.py.patch"
    "utils_validators.py.patch"
)
applied=0; skipped=0; failed=0
for p in "${SLIM_PATCHES[@]}"; do
    if [[ ! -f "${PATCHES_DIR}/${p}" ]]; then
        echo -e "  ${RED}${ERR} ${p} — no encontrado en ${PATCHES_DIR}${NC}"
        failed=$((failed+1)); continue
    fi
    # Idempotencia: si el primer archivo del patch ya tiene el cambio
    # aplicado, git apply fallará con "already applied" — lo tratamos
    # como skip.
    if git apply --check "${PATCHES_DIR}/${p}" 2>/dev/null; then
        git apply --verbose "${PATCHES_DIR}/${p}" >/dev/null 2>&1
        echo -e "  ${GREEN}${OK} ${p}${NC}"
        applied=$((applied+1))
    else
        # Verificar si ya estaba aplicado (buscando una línea característica).
        # Heurística simple: si el archivo objetivo ya contiene un
        # comentario "Fase 5" asociado al patch, lo consideramos aplicado.
        target=$(grep -m1 '^+++ b/' "${PATCHES_DIR}/${p}" | sed 's|^+++ b/||')
        if [[ -n "${target}" && -f "${target}" ]] && \
           grep -q 'Fase 5' "${target}" 2>/dev/null; then
            echo -e "  ${YELLOW}${INFO} ${p} — ya aplicado, skip${NC}"
            skipped=$((skipped+1))
        else
            echo -e "  ${RED}${ERR} ${p} — no se pudo aplicar${NC}"
            failed=$((failed+1))
        fi
    fi
done
echo ""
echo "  Resumen: ${applied} aplicados, ${skipped} ya aplicados, ${failed} fallidos."

# ─── 4. git rm de los archivos eliminados ─────────────────────────────────
echo ""
echo "── Eliminando archivos dead code ──"
DELETED=(
    "gui_pyside/utils/window_manager.py"
    "gui_pyside/views/boton_generar_reportes.py"
)
for f in "${DELETED[@]}"; do
    if [[ -f "${f}" ]]; then
        git rm --quiet "${f}"
        echo -e "  ${GREEN}${OK} git rm ${f}${NC}"
    elif git ls-files --error-unmatch "${f}" 2>/dev/null; then
        git rm --cached --quiet "${f}"
        echo -e "  ${GREEN}${OK} git rm --cached ${f} (ya no en disco)${NC}"
    else
        echo -e "  ${YELLOW}${INFO} ${f} — ya no existe, skip${NC}"
    fi
done

# ─── 5. Verificaciones post-aplicación ────────────────────────────────────
echo ""
echo "── Verificaciones post-aplicación ──"
PASS=0; FAIL=0
check() {
    local desc="$1"; local cmd="$2"
    if eval "${cmd}" >/dev/null 2>&1; then
        echo -e "  ${GREEN}${OK} ${desc}${NC}"
        PASS=$((PASS+1))
    else
        echo -e "  ${RED}${ERR} ${desc}${NC}"
        FAIL=$((FAIL+1))
    fi
}

# H-G1: ErrorHandler sin parent=None (en código, no docstrings).
check "H-G1: ErrorHandler sin parent=None (en código)" \
    "python -c \"import re; src=open('gui_pyside/components/components.py').read(); code=re.sub(r'#.*','',src,flags=re.MULTILINE); code=re.sub(r'\\\"\\\"\\\".*?\\\"\\\"\\\"','',code,flags=re.DOTALL); assert 'QMessageBox.critical(None,' not in code\""

# H-G2: WindowManager eliminado.
check "H-G2: window_manager.py eliminado" \
    "test ! -f gui_pyside/utils/window_manager.py"
# H-G2 (cont): app.py no debe importar WindowManager en código (excluye
# comments que documentan la eliminación).
check "H-G2: app.py no importa WindowManager (código)" \
    "python -c \"import re; src=open('gui_pyside/app.py').read(); code=re.sub(r'#.*','',src,flags=re.MULTILINE); code=re.sub(r'\"\"\".*?\"\"\"','',code,flags=re.DOTALL); assert 'from gui_pyside.utils.window_manager' not in code and 'WindowManager.set_main_window' not in code\""

# H-G3: boton_generar_reportes.py eliminado.
check "H-G3: boton_generar_reportes.py eliminado" \
    "test ! -f gui_pyside/views/boton_generar_reportes.py"

# H-G4: _get_selected_animal_id eliminado.
check "H-G4: _get_selected_animal_id eliminado de recepcion.py" \
    "bash -c 'grep -q \"def _get_selected_animal_id\" gui_pyside/views/recepcion.py && exit 1 || exit 0'"

# H-G5: theme_changed conectado en app.py.
check "H-G5: theme_changed.connect en app.py" \
    "grep -q 'theme_changed.connect' gui_pyside/app.py"
check "H-G5: _on_theme_changed handler en app.py" \
    "grep -q '_on_theme_changed' gui_pyside/app.py"

# H-G6: QDialog.Accepted en usuarios.py.
check "H-G6: QDialog.Accepted en usuarios.py" \
    "grep -q 'QDialog.Accepted' gui_pyside/views/usuarios.py"

# H-G7: event filter en muestra_dialog.py.
check "H-G7: _PegadoMagicoFilter en muestra_dialog.py" \
    "grep -q '_PegadoMagicoFilter' gui_pyside/dialogs/muestra_dialog.py"
check "H-G7: installEventFilter en muestra_dialog.py" \
    "grep -q 'installEventFilter' gui_pyside/dialogs/muestra_dialog.py"

# H-G8: PDFProWorker a nivel de módulo + deleteLater.
check "H-G8: PDFProWorker a nivel de módulo" \
    "grep -E '^class PDFProWorker' gui_pyside/dialogs/muestra_dialog.py"
check "H-G8: finished.connect(deleteLater)" \
    "grep -q 'finished.connect(self.worker.deleteLater)' gui_pyside/dialogs/muestra_dialog.py"

# H-S1: dummy_verify_password en utils/security.py + autenticar.
check "H-S1: dummy_verify_password en utils/security.py" \
    "grep -q 'def dummy_verify_password' utils/security.py"
check "H-S1: dummy_verify_password en autenticar" \
    "grep -q 'dummy_verify_password(password)' services/usuario_service.py"

# H-S2: 8 caracteres en diálogos.
check "H-S2: 'len(nueva) < 8' en cambiar_password_dialog.py" \
    "grep -q 'len(nueva) < 8' gui_pyside/dialogs/cambiar_password_dialog.py"
check "H-S2: 'len(pwd) < 8' en usuario_dialog.py" \
    "grep -q 'len(pwd) < 8' gui_pyside/dialogs/usuario_dialog.py"

# H-S3: validate_pattern en MuestraValidator.
check "H-S3: validate_pattern en MuestraValidator" \
    "grep -A50 'class MuestraValidator' utils/validators.py | grep -q 'validate_pattern'"

# H-S4: whitelist estado en recepcion_service y cirugia_service.
check "H-S4: ESTADOS_RECEPCION en recepcion_service.py" \
    "grep -q 'if estado not in ESTADOS_RECEPCION' services/recepcion_service.py"
check "H-S4: ESTADOS_CIRUGIA en cirugia_service.py" \
    "grep -q 'if estado not in ESTADOS_CIRUGIA' services/cirugia_service.py"

# H-S5: _coerce_or_keep en historia_service.
check "H-S5: _coerce_or_keep en historia_service.py" \
    "grep -q '_coerce_or_keep' services/historia_service.py"

# H-S6: password_reset_required en usuario_service.
check "H-S6: password_reset_required = 1 en reset_password" \
    "grep -q 'password_reset_required = 1' services/usuario_service.py"
check "H-S6: requires_password_change helper existe" \
    "grep -q 'def requires_password_change' services/usuario_service.py"

# H-D3: created_at en ORM models.
check "H-D3: created_at en orm_models/animal.py" \
    "grep -q 'created_at = Column' orm_models/animal.py"
check "H-D3: created_at en orm_models/clinica.py (>=7 clases)" \
    "python -c \"src=open('orm_models/clinica.py').read(); cnt=src.count('created_at = Column'); assert cnt >= 7, f'only {cnt} created_at declarations'\""

# H-D4: migración FK indexes existe.
check "H-D4: migración c1a2b3c4d5e6 existe" \
    "test -f alembic/versions/c1a2b3c4d5e6_fase5_indexes_and_password_reset_flag.py"

# H-D6: RecepcionSchema sin empresa.
check "H-D6: RecepcionSchema sin campo empresa (en código)" \
    "bash -c 'python -c \"import re; src=open(\\\"schemas/clinica.py\\\").read(); m=re.search(r\\\"class RecepcionSchema.*?(?:\\\\nclass|\\\\Z)\\\", src, re.DOTALL); body=m.group(0); import re as r; lines=[l for l in body.split(\\\"\\\\n\\\") if not l.strip().startswith(\\\"#\\\")]; code=\\\"\\\\n\\\".join(lines); assert \\\"empresa:\\\" not in code and \\\"empresa =\\\" not in code\"'"

# Test file existe.
check "Tests: tests/test_fase5_high.py existe" \
    "test -f tests/test_fase5_high.py"

echo ""
echo "  Resumen: ${PASS} verificaciones OK, ${FAIL} fallaron."

# ─── 6. Próximos pasos ────────────────────────────────────────────────────
echo ""
echo "── Próximos pasos ──"
echo "  1. Revisa los cambios con 'git diff' o en GitHub Desktop."
echo "  2. Ejecuta los tests de regresión:"
echo "       python -m pytest tests/test_fase5_high.py -v --no-cov"
echo "  3. Aplica la migración Alembic:"
echo "       python -m alembic upgrade head"
echo "  4. Commit con el mensaje sugerido:"
echo "       fix(ISALAB): Fase 5 — Fix HIGH issues (GUI + Services + DB)"
echo "  5. Push y abre PR contra master."
echo ""
if [[ ${FAIL} -eq 0 && ${failed} -eq 0 ]]; then
    echo -e "${GREEN}✓ Fase 5 aplicada correctamente. ${PASS} verificaciones OK.${NC}"
    exit 0
else
    echo -e "${RED}${ERR} Algunas verificaciones fallaron. Revisa el output arriba.${NC}"
    exit 1
fi
