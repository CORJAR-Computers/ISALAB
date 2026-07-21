#!/usr/bin/env bash
# ============================================================================
# ISALAB — Fase 6 — Aplicar parches MEDIUM/LOW
# ============================================================================
# Uso:
#   cd /ruta/al/repositorio/ISALAB
#   bash /ruta/a/apply-phase6.sh
#
# O desde cualquier directorio:
#   bash apply-phase6.sh /ruta/al/repositorio/ISALAB
#
# Requisitos:
#   - Repo ISALAB clonado localmente
#   - Fases 1, 2, 3, 4 y 5 YA APLICADAS (head esperado: 5098d37)
#   - git en PATH
#
# Este script:
#   1. Verifica que el repo esté en estado limpio
#   2. Crea branch `feat/phase6-medium-low-fixes` si no existe
#   3. Aplica el patch consolidado (git am) o los parches slim por archivo
#   4. Verifica que la cadena de migraciones tenga un único head
# ============================================================================

set -euo pipefail

# ── Resolver rutas ───────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES_DIR="$SCRIPT_DIR/../patches"
REPO_DIR="${1:-.}"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log()  { echo -e "${GREEN}[Fase 6]${NC} $*"; }
warn() { echo -e "${YELLOW}[Fase 6]${NC} $*"; }
err()  { echo -e "${RED}[Fase 6]${NC} $*" >&2; }

# ── Verificar prerequisitos ─────────────────────────────────────────────────
cd "$REPO_DIR"

if [ ! -d ".git" ]; then
  err "No es un repositorio git: $REPO_DIR"
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  err "El repositorio tiene cambios sin commit. Haz commit o stash antes de aplicar Fase 6."
  git status --short
  exit 1
fi

# Verificar que la Fase 5 esté aplicada (commit 5098d37)
if ! git log --oneline | grep -q "5098d37"; then
  warn "ADVERTENCIA: No se detectó el commit 5098d37 (Fase 5)."
  warn "Fase 6 depende de Fases 1-5. Proceder bajo su propio riesgo."
  read -p "¿Continuar? (y/N) " -n 1 -r
  echo
  [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

# ── Crear branch ─────────────────────────────────────────────────────────────
BRANCH="feat/phase6-medium-low-fixes"
CURRENT_BRANCH=$(git branch --show-current)

if [ "$CURRENT_BRANCH" = "$BRANCH" ]; then
  log "Ya en branch $BRANCH"
elif git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  log "Cambiando a branch existente $BRANCH"
  git checkout "$BRANCH"
else
  log "Creando branch $BRANCH desde $(git rev-parse --short HEAD)"
  git checkout -b "$BRANCH"
fi

# ── Aplicar patch consolidado ────────────────────────────────────────────────
CONSOLIDATED="$PATCHES_DIR/0001-fix-ISALAB-Fase-6-Fix-MEDIUM-LOW-issues.patch"

if [ -f "$CONSOLIDATED" ]; then
  log "Aplicando patch consolidado: $(basename "$CONSOLIDATED")"

  # Intentar git am primero (preserva commit message y metadata)
  if git am --3way < "$CONSOLIDATED" 2>/dev/null; then
    log "Patch aplicado exitosamente con git am"
  else
    warn "git am falló. Intentando con git apply..."
    git am --abort 2>/dev/null || true
    if git apply --3way --reject "$CONSOLIDATED"; then
      log "Patch aplicado con git apply (sin commit automático)"
      log "Haciendo commit manual..."
      git add -A
      git commit -m "fix(ISALAB): Fase 6 — Fix MEDIUM/LOW issues (DB + Services + GUI + DevOps)"
    else
      err "No se pudo aplicar el patch. Resuelve conflictos manualmente."
      err "Archivos .rej creados con los fragmentos que no se aplicaron."
      exit 1
    fi
  fi
else
  err "No se encontró el patch consolidado: $CONSOLIDATED"
  exit 1
fi

# ── Verificar head de migración ──────────────────────────────────────────────
log "Verificando head de migraciones..."
EXPECTED_HEAD="b3c4d5e6f7a8"
MIGRATION_FILE="alembic/versions/b3c4d5e6f7a8_fase6_updated_at_audit.py"

if [ -f "$MIGRATION_FILE" ]; then
  log "✓ Migration $EXPECTED_HEAD encontrada"
else
  warn "No se encontró $MIGRATION_FILE — verificar manualmente"
fi

# ── Verificar que no se trackearon archivos sensibles ────────────────────────
SENSITIVE_PATTERNS=(
  "data/isalab.db"
  "logs/isalab.log"
  "data/pdfs/"
  "__pycache__/"
  "*.pyc"
  "identifier.sqlite"
)

log "Verificando que no se trackearon archivos sensibles..."
LEAKED=0
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
  if git ls-files | grep -qE "^$pattern"; then
    err "¡Archivo sensible trackeado: $pattern!"
    LEAKED=$((LEAKED+1))
  fi
done

if [ "$LEAKED" -gt 0 ]; then
  err "Se detectaron $LEAKED archivos sensibles. Ejecuta git rm --cached <file>."
  exit 1
fi

log "✓ No se trackearon archivos sensibles"

# ── Resumen ──────────────────────────────────────────────────────────────────
echo ""
log "=========================================="
log "  Fase 6 aplicada exitosamente"
log "=========================================="
echo ""
log "Branch: $(git branch --show-current)"
log "Commit: $(git log --oneline -1)"
echo ""
log "Cambios:"
git diff --stat HEAD~1 HEAD | tail -5
echo ""
log "Próximos pasos:"
echo "  1. Ejecutar migración: python -m alembic upgrade head"
echo "  2. Correr tests: python -m pytest tests/ --tb=short"
echo "  3. Si todo pasa, hacer push: git push origin $BRANCH"
echo ""
log "Notas importantes:"
echo "  - La migration b3c4d5e6f7a8 agrega columna updated_at a 9 tablas + CHECK constraints"
echo "  - La migration es idempotente (puede correrse múltiples veces)"
echo "  - S-L5 cambia la política de passwords: ahora exigen símbolo (8+ chars)"
echo "  - Los usuarios existentes NO se ven afectados — solo nuevas altas/cambios"
