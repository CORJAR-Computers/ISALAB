#!/usr/bin/env bash
# =============================================================================
# IsaLab — Fase 1: Aplicar parche vía Bash (Linux/macOS/Git Bash en Windows)
#
# Uso:
#   1. Coloca este script y la carpeta patches/ en una subcarpeta temporal
#      dentro o fuera del repo ISALAB.
#   2. cd a la raíz del repo ISALAB.
#   3. Ejecuta:  bash /ruta/a/apply-phase1.sh
#
# Qué hace:
#   - Crea la rama 'feat/phase1-repo-hygiene' (o la que pidas).
#   - Aplica el parche slim (archivos nuevos/modificados).
#   - Ejecuta 'git rm --cached' para los archivos sensibles y duplicados.
#   - Hace commit con el mensaje estándar de Fase 1.
#
# No sube nada al remoto. Tú decides cuándo hacer 'git push'.
# =============================================================================

set -euo pipefail

# ── Configuración ────────────────────────────────────────────────────────────
BRANCH_NAME="feat/phase1-repo-hygiene"
COMMIT_MESSAGE="chore(ISALAB): Fase 1 - higiene del repositorio + setup tooling"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# El script vive en scripts/, los parches en ../patches/
PATCH_FILE="${SCRIPT_DIR}/../patches/0001-slim-added-modified-only.patch"

DRY_RUN=0
SKIP_PATCH=0
SKIP_CLEANUP=0

# ── Parseo de args ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)         DRY_RUN=1; shift ;;
        --skip-patch)      SKIP_PATCH=1; shift ;;
        --skip-cleanup)    SKIP_CLEANUP=1; shift ;;
        --branch)          BRANCH_NAME="$2"; shift 2 ;;
        --patch)           PATCH_FILE="$2"; shift 2 ;;
        -h|--help)
            cat <<EOF
Uso: $0 [opciones]

Opciones:
  --dry-run          Solo verifica, no hace commit.
  --skip-patch       No aplicar el .patch (asume que ya está aplicado).
  --skip-cleanup     No ejecutar 'git rm --cached' (solo aplicar parche).
  --branch NAME      Nombre de la rama (default: $BRANCH_NAME).
  --patch PATH       Ruta al .patch slim (default: auto-detectado).
  -h, --help         Esta ayuda.
EOF
            exit 0 ;;
        *) echo "Opción desconocida: $1" >&2; exit 1 ;;
    esac
done

# ── Helpers ──────────────────────────────────────────────────────────────────
step()  { printf '\n\033[36m==> %s\033[0m\n' "$1"; }
ok()    { printf '    \033[32m[OK]\033[0m   %s\n' "$1"; }
warn()  { printf '    \033[33m[WARN]\033[0m %s\n' "$1"; }
err()   { printf '    \033[31m[ERR]\033[0m  %s\n' "$1" >&2; }

# ── 0. Verificaciones previas ────────────────────────────────────────────────
step "Verificaciones previas"

[[ -d .git ]] || { err "No estás en la raíz de un repo git (falta .git/)."; exit 1; }
ok "Estás en un repo git."

if [[ -n "$(git status --porcelain 2>&1)" ]]; then
    warn "Tienes cambios sin commitear en tu working tree:"
    git status --short
    warn "Recomendado: commitea o stash antes de aplicar Fase 1."
    read -r -p "¿Continuar igualmente? (s/N) " continue
    [[ "$continue" == "s" ]] || exit 0
fi

# ── 1. Crear rama ────────────────────────────────────────────────────────────
step "Crear rama '$BRANCH_NAME'"

current_branch=$(git rev-parse --abbrev-ref HEAD)
ok "Rama actual: $current_branch"

if [[ "$current_branch" != "$BRANCH_NAME" ]]; then
    if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME" 2>/dev/null; then
        warn "La rama '$BRANCH_NAME' ya existe. Haciendo checkout..."
        git checkout "$BRANCH_NAME"
    else
        git checkout -b "$BRANCH_NAME"
        ok "Rama '$BRANCH_NAME' creada."
    fi
fi

# ── 2. Aplicar el parche slim ────────────────────────────────────────────────
if [[ $SKIP_PATCH -eq 0 ]]; then
    step "Aplicar parche slim (archivos nuevos/modificados)"

    [[ -f "$PATCH_FILE" ]] || { err "No se encontró: $PATCH_FILE"; exit 1; }

    echo "    Aplicando: $PATCH_FILE"
    if [[ $DRY_RUN -eq 1 ]]; then
        if git apply --check "$PATCH_FILE"; then
            ok "Dry-run: el parche aplica limpiamente."
        else
            err "Dry-run: el parche NO aplica limpiamente."
            exit 1
        fi
    else
        if git apply --whitespace=fix "$PATCH_FILE"; then
            ok "Parche aplicado."
        else
            err "Falló 'git apply'. Revisa conflictos."
            exit 1
        fi
    fi

    git add -A
    ok "Cambios stageados."
fi

# ── 3. Remover archivos sensibles/duplicados del index ──────────────────────
if [[ $SKIP_CLEANUP -eq 0 ]]; then
    step "Remover archivos sensibles y duplicados del git index"

    # Nota: 'git rm --cached' NO borra el archivo del disco, solo lo quita
    # del index. Los archivos siguen existiendo localmente para dev.

    # 3a. PII / PHI (issue C1, C3)
    sensitive_files=(
        "data/isalab.db"
        "data/pdfs/Formato informe Ruffos.pdf"
        "data/pdfs/LAB_ISA-20260410-7801.pdf"
        "data/pdfs/reporte_isalab.pdf"
        "logs/isalab.log"
    )
    for f in "${sensitive_files[@]}"; do
        if git ls-files --error-unmatch "$f" 2>/dev/null 1>&2; then
            git rm --cached -q "$f"
            ok "Removido del index: $f"
        else
            warn "No estaba trackeado: $f"
        fi
    done

    # 3b. Build artifacts (issue C5, M1)
    artifacts=(
        "Analysis-00.toc" "COLLECT-00.toc" "EXE-00.toc"
        "PKG-00.toc" "PYZ-00.toc" "PYZ-00.pyz"
        "IsaLab.pkg" "identifier.sqlite" "warn-IsaLab.txt"
        "icono.ico" "xref-IsaLab.html"
    )
    for f in "${artifacts[@]}"; do
        if git ls-files --error-unmatch "$f" 2>/dev/null 1>&2; then
            git rm --cached -q "$f"
            ok "Removido del index: $f"
        fi
    done

    # 3c. Scripts one-shot (issue H1)
    fix_scripts=("fix_f541.py" "fix_jinja_format.py" "fix_jinja_format_2.py" "fix_jinja_format_3.py")
    for f in "${fix_scripts[@]}"; do
        if git ls-files --error-unmatch "$f" 2>/dev/null 1>&2; then
            git rm --cached -q "$f"
            ok "Removido del index: $f"
        fi
    done

    # 3d. Directorios AI-tools duplicados (issue M4) + IDEs (issue L3, L4)
    dirs=(
        ".agent" ".claude" ".codebuddy" ".codex" ".continue"
        ".cursor" ".gemini" ".kiro" ".opencode" ".qoder"
        ".roo" ".stakpak" ".trae" ".windsurf"
        ".github/prompts" ".idea" ".vscode"
    )
    for d in "${dirs[@]}"; do
        if [[ -d "$d" ]] && [[ -n "$(git ls-files "$d" 2>/dev/null)" ]]; then
            git rm --cached -r -q "$d"
            ok "Removido del index: $d/"
        fi
    done

    # 3e. __pycache__ y *.pyc (issue C5)
    pyc_count=$(git ls-files | grep -cE "(__pycache__/|\.pyc$|localpycs/)" || true)
    if [[ $pyc_count -gt 0 ]]; then
        git ls-files | grep -E "(__pycache__/|\.pyc$|localpycs/)" | xargs -r git rm --cached -q
        ok "Removidos $pyc_count archivos __pycache__/*.pyc"
    fi
fi

# ── 4. Commit ────────────────────────────────────────────────────────────────
if [[ $DRY_RUN -eq 0 ]]; then
    step "Hacer commit"

    git add -A

    staged_count=$(git diff --cached --name-only | wc -l)
    if [[ $staged_count -eq 0 ]]; then
        warn "No hay cambios para commitear (¿ya estaba aplicada Fase 1?)."
    else
        git commit -m "$COMMIT_MESSAGE"
        ok "Commit creado con $staged_count cambios."
        echo ""
        printf '\033[36mResumen:\033[0m\n'
        git show --stat HEAD | tail -10
    fi
fi

# ── 5. Próximos pasos ────────────────────────────────────────────────────────
step "Listo. Próximos pasos:"
cat <<EOF
    1. Revisa el commit con:       git show HEAD
    2. Sube la rama al remoto con: git push -u origin $BRANCH_NAME
    3. Abre un Pull Request en GitHub contra 'main' o 'develop'.
    4. IMPORTANTE: rota el password del admin 'admin' porque el
       hash bcrypt ya está en el historial público del repo.
    5. Pendiente (fuera de Fase 1): ejecutar 'git filter-repo' para
       purgar data/ y logs/ del historial. Requiere force-push.
EOF
echo ""
