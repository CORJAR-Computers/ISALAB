# ============================================================================
# ISALAB — Fase 6 — Aplicar parches MEDIUM/LOW (PowerShell)
# ============================================================================
# Uso:
#   cd C:\ruta\al\repositorio\ISALAB
#   .\apply-phase6.ps1
#
# O desde cualquier directorio:
#   .\apply-phase6.ps1 -RepoDir C:\ruta\al\ISALAB
#
# Requisitos:
#   - Repo ISALAB clonado localmente
#   - Fases 1, 2, 3, 4 y 5 YA APLICADAS (head esperado: 5098d37)
#   - git en PATH
# ============================================================================

[CmdletBinding()]
param(
    [string]$RepoDir = "."
)

$ErrorActionPreference = "Stop"

# ── Resolver rutas ───────────────────────────────────────────────────────────
$ScriptDir = Split-Path $PSScriptRoot -Parent
$PatchDir = Join-Path $ScriptDir "patches"
$ConsolidatedPatch = Join-Path $PatchDir "0001-fix-ISALAB-Fase-6-Fix-MEDIUM-LOW-issues.patch"

function Write-PhaseLog {
    param([string]$Message, [string]$Level = "Info")
    $color = switch ($Level) {
        "Warn"  { "Yellow" }
        "Error" { "Red" }
        default { "Green" }
    }
    Write-Host "[Fase 6] " -ForegroundColor $color -NoNewline
    Write-Host $Message
}

# ── Verificar prerequisitos ──────────────────────────────────────────────────
Set-Location $RepoDir

if (-not (Test-Path ".git")) {
    Write-PhaseLog "No es un repositorio git: $RepoDir" "Error"
    exit 1
}

$status = git status --porcelain
if ($status) {
    Write-PhaseLog "El repositorio tiene cambios sin commit. Haz commit o stash antes de aplicar Fase 6." "Error"
    git status --short
    exit 1
}

# Verificar que la Fase 5 esté aplicada
$fase5Applied = git log --oneline | Select-String "5098d37"
if (-not $fase5Applied) {
    Write-PhaseLog "ADVERTENCIA: No se detectó el commit 5098d37 (Fase 5)." "Warn"
    Write-PhaseLog "Fase 6 depende de Fases 1-5. Proceder bajo su propio riesgo." "Warn"
    $continue = Read-Host "¿Continuar? (y/N)"
    if ($continue -notmatch "^[Yy]$") { exit 1 }
}

# ── Crear branch ─────────────────────────────────────────────────────────────
$Branch = "feat/phase6-medium-low-fixes"
$CurrentBranch = git branch --show-current

if ($CurrentBranch -eq $Branch) {
    Write-PhaseLog "Ya en branch $Branch"
} elseif (git show-ref --verify --quiet "refs/heads/$Branch" 2>$null) {
    Write-PhaseLog "Cambiando a branch existente $Branch"
    git checkout $Branch | Out-Null
} else {
    $headShort = git rev-parse --short HEAD
    Write-PhaseLog "Creando branch $Branch desde $headShort"
    git checkout -b $Branch | Out-Null
}

# ── Aplicar patch consolidado ────────────────────────────────────────────────
if (-not (Test-Path $ConsolidatedPatch)) {
    Write-PhaseLog "No se encontró el patch consolidado: $ConsolidatedPatch" "Error"
    exit 1
}

Write-PhaseLog "Aplicando patch consolidado: $(Split-Path $ConsolidatedPatch -Leaf)"

# Intentar git am primero
$amResult = git am --3way $ConsolidatedPatch 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-PhaseLog "Patch aplicado exitosamente con git am"
} else {
    Write-PhaseLog "git am falló. Intentando con git apply..." "Warn"
    git am --abort 2>$null | Out-Null

    $applyResult = git apply --3way --reject $ConsolidatedPatch 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-PhaseLog "Patch aplicado con git apply (sin commit automático)"
        Write-PhaseLog "Haciendo commit manual..."
        git add -A | Out-Null
        git commit -m "fix(ISALAB): Fase 6 — Fix MEDIUM/LOW issues (DB + Services + GUI + DevOps)" | Out-Null
    } else {
        Write-PhaseLog "No se pudo aplicar el patch. Resuelve conflictos manualmente." "Error"
        Write-PhaseLog "Archivos .rej creados con los fragmentos que no se aplicaron." "Error"
        Write-Host $applyResult
        exit 1
    }
}

# ── Verificar head de migración ──────────────────────────────────────────────
Write-PhaseLog "Verificando head de migraciones..."
$MigrationFile = "alembic/versions/b3c4d5e6f7a8_fase6_updated_at_audit.py"
if (Test-Path $MigrationFile) {
    Write-PhaseLog "✓ Migration b3c4d5e6f7a8 encontrada"
} else {
    Write-PhaseLog "No se encontró $MigrationFile — verificar manualmente" "Warn"
}

# ── Verificar que no se trackearon archivos sensibles ────────────────────────
Write-PhaseLog "Verificando que no se trackearon archivos sensibles..."
$SensitivePatterns = @(
    "data/isalab.db",
    "logs/isalab.log",
    "data/pdfs/",
    "__pycache__/",
    "identifier.sqlite"
)

$leaked = 0
$trackedFiles = git ls-files
foreach ($pattern in $SensitivePatterns) {
    $matches = $trackedFiles | Where-Object { $_ -like "$pattern*" }
    if ($matches) {
        Write-PhaseLog "¡Archivo sensible trackeado: $pattern!" "Error"
        $leaked++
    }
}

if ($leaked -gt 0) {
    Write-PhaseLog "Se detectaron $leaked archivos sensibles. Ejecuta git rm --cached <file>." "Error"
    exit 1
}

Write-PhaseLog "✓ No se trackearon archivos sensibles"

# ── Resumen ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-PhaseLog "=========================================="
Write-PhaseLog "  Fase 6 aplicada exitosamente"
Write-PhaseLog "=========================================="
Write-Host ""
Write-PhaseLog "Branch: $(git branch --show-current)"
Write-PhaseLog "Commit: $(git log --oneline -1)"
Write-Host ""
Write-PhaseLog "Cambios:"
git diff --stat HEAD~1 HEAD | Select-Object -Last 5
Write-Host ""
Write-PhaseLog "Próximos pasos:"
Write-Host "  1. Ejecutar migración: python -m alembic upgrade head"
Write-Host "  2. Correr tests: python -m pytest tests/ --tb=short"
Write-Host "  3. Si todo pasa, hacer push: git push origin $Branch"
Write-Host ""
Write-PhaseLog "Notas importantes:"
Write-Host "  - La migration b3c4d5e6f7a8 agrega columna updated_at a 9 tablas + CHECK constraints"
Write-Host "  - La migration es idempotente (puede correrse múltiples veces)"
Write-Host "  - S-L5 cambia la política de passwords: ahora exigen símbolo (8+ chars)"
Write-Host "  - Los usuarios existentes NO se ven afectados — solo nuevas altas/cambios"
