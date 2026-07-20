#!/usr/bin/env bash
# =============================================================================
# IsaLab — Fase 2: Aplicar parches de Fix CRITICAL de base de datos
#
# Uso:
#   1. Coloca este script y la carpeta patches/ en una subcarpeta temporal.
#   2. cd a la raíz del repo ISALAB (con Fase 1 ya aplicada).
#   3. Ejecuta:  bash /ruta/a/apply-phase2.sh
#
# Qué hace:
#   - Crea la rama 'feat/phase2-database-critical'.
#   - Aplica el parche consolidado (8 archivos).
#   - Verifica que alembic upgrade head funciona en DB temporal.
#   - Hace commit con el mensaje estándar de Fase 2.
#
# Requisitos previos:
#   - Fase 1 ya aplicada y commiteada en main o en feat/phase1-repo-hygiene.
#   - Python 3.10+ con alembic, sqlalchemy, bcrypt instalados.
# =============================================================================

set -euo pipefail

# ── Configuración ────────────────────────────────────────────────────────────
BRANCH_NAME="feat/phase2-database-critical"
COMMIT_MESSAGE="fix(ISALAB): Fase 2 — Fix CRITICAL de base de datos"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# El script vive en scripts/, los parches en ../patches/
PATCH_FILE="${SCRIPT_DIR}/../patches/0001-fix-ISALAB-Fase-2-Fix-CRITICAL-de-base-de-datos.patch"

DRY_RUN=0
SKIP_VERIFY=0

# ── Parseo de args ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)         DRY_RUN=1; shift ;;
        --skip-verify)     SKIP_VERIFY=1; shift ;;
        --branch)          BRANCH_NAME="$2"; shift 2 ;;
        --patch)           PATCH_FILE="$2"; shift 2 ;;
        -h|--help)
            cat <<EOF
Uso: $0 [opciones]

Opciones:
  --dry-run          Solo verifica, no hace commit.
  --skip-verify      No correr 'alembic upgrade head' para verificar.
  --branch NAME      Nombre de la rama (default: $BRANCH_NAME).
  --patch PATH       Ruta al .patch consolidado (default: auto-detectado).
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

[[ -f alembic.ini ]] || { err "Falta alembic.ini. ¿Fase 1 está aplicada?"; exit 1; }
ok "alembic.ini presente (Fase 1 aplicada)."

[[ -f pyproject.toml ]] || { err "Falta pyproject.toml. ¿Fase 1 está aplicada?"; exit 1; }
ok "pyproject.toml presente (Fase 1 aplicada)."

if [[ -n "$(git status --porcelain 2>&1)" ]]; then
    warn "Tienes cambios sin commitear:"
    git status --short
    warn "Recomendado: commitea o stash antes de aplicar Fase 2."
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

# ── 2. Aplicar el parche ─────────────────────────────────────────────────────
step "Aplicar parche consolidado de Fase 2"

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
        err "Falló 'git apply'. Intenta con --3way o aplica archivo por archivo."
        echo ""
        echo "Parches individuales disponibles en patches/:"
        ls patches/*.patch 2>/dev/null | grep -v "0001-" || true
        exit 1
    fi
fi

git add -A
ok "Cambios stageados."

# ── 3. Verificar que alembic upgrade head funciona ──────────────────────────
if [[ $SKIP_VERIFY -eq 0 ]] && [[ $DRY_RUN -eq 0 ]]; then
    step "Verificar alembic upgrade head en DB temporal"

    # Crear DB temporal para no tocar la real
    TMP_DB="$(mktemp -d)/isalab_test.db"
    trap 'rm -f "$TMP_DB"' EXIT

    echo "    DB temporal: $TMP_DB"

    # Verificar que alembic está instalado
    if ! command -v alembic >/dev/null 2>&1; then
        warn "alembic no está en PATH. Instala con: pip install -r requirements-dev.txt"
        warn "Saltando verificación (--skip-verify para silenciar este warning)."
    else
        # Apuntar config.DB_PATH al temporal
        export ISALAB_DB_PATH="$TMP_DB"

        # Ejecutar upgrade
        if alembic upgrade head >/tmp/alembic_verify.log 2>&1; then
            ok "alembic upgrade head completó correctamente."

            # Verificar head
            head=$(python3 -c "
import sqlite3
conn = sqlite3.connect('$TMP_DB')
for row in conn.execute('SELECT version_num FROM alembic_version'):
    print(row[0])
" 2>/dev/null || echo "?")
            ok "Head de migración: $head"

            # Verificar que usuarios tiene password_hash
            has_pwd_hash=$(python3 -c "
import sqlite3
conn = sqlite3.connect('$TMP_DB')
cols = [r[1] for r in conn.execute('PRAGMA table_info(usuarios)')]
print('password_hash' in cols)
" 2>/dev/null || echo "?")

            if [[ "$has_pwd_hash" == "True" ]]; then
                ok "Tabla usuarios tiene columna password_hash (issue C3 OK)."
            else
                err "Tabla usuarios NO tiene password_hash. Revisar migración."
                exit 1
            fi
        else
            err "alembic upgrade head falló. Log:"
            cat /tmp/alembic_verify.log
            exit 1
        fi
    fi
fi

# ── 4. Commit ────────────────────────────────────────────────────────────────
if [[ $DRY_RUN -eq 0 ]]; then
    step "Hacer commit"

    git add -A

    staged_count=$(git diff --cached --name-only | wc -l)
    if [[ $staged_count -eq 0 ]]; then
        warn "No hay cambios para commitear (¿ya estaba aplicada Fase 2?)."
    else
        git commit -m "$COMMIT_MESSAGE"
        ok "Commit creado con $staged_count archivos modificados."
        echo ""
        printf '\033[36mResumen:\033[0m\n'
        git show --stat HEAD | tail -15
    fi
fi

# ── 5. Próximos pasos ────────────────────────────────────────────────────────
step "Listo. Próximos pasos:"
cat <<EOF
    1. Revisa el commit con:       git show HEAD
    2. (Opcional) Corre los tests de regresión:
         pip install -r requirements-dev.txt
         pytest tests/test_fase2_database.py -v
    3. Sube la rama al remoto con: git push -u origin $BRANCH_NAME
    4. Abre un Pull Request en GitHub contra 'main' o 'develop'.
    5. IMPORTANTE: si tienes una DB existente con la columna 'password'
       (no 'password_hash'), la migración la renombrará automáticamente.
       Si tienes usuarios con hashes en la columna 'password', los
       hashes se preservan (solo cambia el nombre de la columna).
    6. Si tu DB existente tiene datos en la tabla animales, verifica que
       los campos propietario_tipo_doc, propietario_documento,
       propietario_direccion, propietario_oficio y empresa (en muestras)
       tengan los valores esperados después de la migración.
EOF
echo ""
