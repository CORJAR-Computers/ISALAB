# =============================================================================
# IsaLab — Fase 1: Aplicar parche vía PowerShell
#
# Uso:
#   1. Abre PowerShell en la raíz de tu repositorio ISALAB local.
#   2. Coloca este script y los .patch en una subcarpeta temporal.
#   3. Ejecuta:
#       .\apply-phase1.ps1
#
# Qué hace:
#   - Crea la rama 'feat/phase1-repo-hygiene' (o la que pidas).
#   - Aplica el parche slim (archivos nuevos/modificados).
#   - Ejecuta 'git rm --cached' para todos los archivos sensibles y
#     duplicados que no deben estar trackeados.
#   - Hace commit con el mensaje estándar de Fase 1.
#
# No sube nada al remoto. Tú decides cuándo hacer 'git push'.
# =============================================================================

[CmdletBinding()]
param(
    [string]$BranchName = "feat/phase1-repo-hygiene",
    [string]$CommitMessage = "chore(ISALAB): Fase 1 - higiene del repositorio + setup tooling",
    [switch]$DryRun,
    [switch]$SkipPatch,
    [switch]$SkipCleanup
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Write-Ok($msg)   { Write-Host "    [OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    [WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "    [ERR]  $msg" -ForegroundColor Red }

# ── 0. Verificaciones previas ────────────────────────────────────────────────
Write-Step "Verificaciones previas"

if (-not (Test-Path ".git")) {
    Write-Err "No estás en la raíz de un repo git (falta carpeta .git/)."
    exit 1
}
Write-Ok "Estás en un repo git."

$gitStatus = git status --porcelain 2>&1
if ($gitStatus) {
    Write-Warn "Tienes cambios sin commitear en tu working tree:"
    Write-Host $gitStatus
    Write-Warn "Recomendado: commitea o stash antes de aplicar Fase 1."
    $continue = Read-Host "¿Continuar igualmente? (s/N)"
    if ($continue -ne "s") { exit 0 }
}

# ── 1. Crear rama ────────────────────────────────────────────────────────────
Write-Step "Crear rama '$BranchName'"

$currentBranch = git rev-parse --abbrev-ref HEAD
Write-Ok "Rama actual: $currentBranch"

if ($currentBranch -ne $BranchName) {
    if (git show-ref --verify --quiet "refs/heads/$BranchName" 2>$null) {
        Write-Warn "La rama '$BranchName' ya existe. Haciendo checkout..."
        git checkout $BranchName
    } else {
        git checkout -b $BranchName
        Write-Ok "Rama '$BranchName' creada."
    }
}

# ── 2. Aplicar el parche slim ────────────────────────────────────────────────
if (-not $SkipPatch) {
    Write-Step "Aplicar parche slim (archivos nuevos/modificados)"

    $patchFile = Join-Path (Split-Path $PSScriptRoot -Parent) "patches\0001-slim-added-modified-only.patch"
    if (-not (Test-Path $patchFile)) {
        $patchFile = Read-Host "Ruta al archivo .patch slim"
    }

    Write-Host "    Aplicando: $patchFile"
    if ($DryRun) {
        git apply --check $patchFile
        if ($LASTEXITCODE -eq 0) { Write-Ok "Dry-run: el parche aplica limpiamente." }
        else                       { Write-Err "Dry-run: el parche NO aplica limpiamente." ; exit 1 }
    } else {
        git apply --whitespace=fix $patchFile
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Parche aplicado."
        } else {
            Write-Err "Falló 'git apply'. Revisa conflictos."
            exit 1
        }
    }

    git add -A
    Write-Ok "Cambios stageados."
}

# ── 3. Remover archivos sensibles/duplicados del index ──────────────────────
if (-not $SkipCleanup) {
    Write-Step "Remover archivos sensibles y duplicados del git index"

    # Nota: 'git rm --cached' NO borra el archivo del disco, solo lo quita
    # del index. Los archivos siguen existiendo localmente para dev.

    # 3a. PII / PHI (issue C1, C3)
    $sensitiveFiles = @(
        "data/isalab.db",
        "data/pdfs/Formato informe Ruffos.pdf",
        "data/pdfs/LAB_ISA-20260410-7801.pdf",
        "data/pdfs/reporte_isalab.pdf",
        "logs/isalab.log"
    )
    foreach ($f in $sensitiveFiles) {
        if (git ls-files --error-unmatch $f 2>$null) {
            git rm --cached -q $f
            Write-Ok "Removido del index: $f"
        } else {
            Write-Warn "No estaba trackeado: $f"
        }
    }

    # 3b. Build artifacts (issue C5, M1)
    $artifacts = @(
        "Analysis-00.toc", "COLLECT-00.toc", "EXE-00.toc",
        "PKG-00.toc", "PYZ-00.toc", "PYZ-00.pyz",
        "IsaLab.pkg", "identifier.sqlite", "warn-IsaLab.txt",
        "icono.ico", "xref-IsaLab.html"
    )
    foreach ($f in $artifacts) {
        if (git ls-files --error-unmatch $f 2>$null) {
            git rm --cached -q $f
            Write-Ok "Removido del index: $f"
        }
    }

    # 3c. Scripts one-shot (issue H1)
    $fixScripts = @(
        "fix_f541.py",
        "fix_jinja_format.py",
        "fix_jinja_format_2.py",
        "fix_jinja_format_3.py"
    )
    foreach ($f in $fixScripts) {
        if (git ls-files --error-unmatch $f 2>$null) {
            git rm --cached -q $f
            Write-Ok "Removido del index: $f"
        }
    }

    # 3d. Directorios AI-tools duplicados (issue M4) + IDEs (issue L3, L4)
    $dirs = @(
        ".agent", ".claude", ".codebuddy", ".codex", ".continue",
        ".cursor", ".gemini", ".kiro", ".opencode", ".qoder",
        ".roo", ".stakpak", ".trae", ".windsurf",
        ".github/prompts", ".idea", ".vscode"
    )
    foreach ($d in $dirs) {
        if (Test-Path $d) {
            # Verificar que esté trackeado antes de intentar remover
            $tracked = git ls-files $d 2>$null
            if ($tracked) {
                git rm --cached -r -q $d
                Write-Ok "Removido del index: $d/"
            }
        }
    }

    # 3e. __pycache__ y *.pyc (issue C5)
    $pycFiles = git ls-files | Where-Object { $_ -match "(__pycache__/|\.pyc$|localpycs/)" }
    if ($pycFiles) {
        $pycFiles | ForEach-Object { git rm --cached -q $_ 2>$null }
        Write-Ok "Removidos $($pycFiles.Count) archivos __pycache__/*.pyc"
    }
}

# ── 4. Commit ────────────────────────────────────────────────────────────────
if (-not $DryRun) {
    Write-Step "Hacer commit"

    git add -A

    $stagedCount = (git diff --cached --name-only).Count
    if ($stagedCount -eq 0) {
        Write-Warn "No hay cambios para commitear (¿ya estaba aplicada Fase 1?)."
    } else {
        git commit -m $CommitMessage
        Write-Ok "Commit creado con $stagedCount cambios."
        Write-Host ""
        Write-Host "Resumen:" -ForegroundColor Cyan
        git show --stat HEAD | Select-Object -Last 10
    }
}

# ── 5. Próximos pasos ────────────────────────────────────────────────────────
Write-Step "Listo. Próximos pasos:"
Write-Host "    1. Revisa el commit con:       git show HEAD"
Write-Host "    2. Sube la rama al remoto con: git push -u origin $BranchName"
Write-Host "    3. Abre un Pull Request en GitHub contra 'main' o 'develop'."
Write-Host "    4. IMPORTANTE: rota el password del admin 'admin' porque el"
Write-Host "       hash bcrypt ya está en el historial público del repo."
Write-Host "    5. Pendiente (fuera de Fase 1): ejecutar 'git filter-repo' para"
Write-Host "       purgar data/ y logs/ del historial. Requiere force-push."
Write-Host ""
