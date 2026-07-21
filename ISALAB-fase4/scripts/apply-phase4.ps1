# ============================================================================
# ISALAB — Fase 4: Fix CRITICAL de GUI
# Aplicador de parches para Windows PowerShell
# ============================================================================
#
# USO:
#   1. Asegúrate de tener Fase 1, 2 y 3 aplicadas y commiteadas en tu repo.
#   2. cd ISALAB  (raíz del repo, donde está main.py)
#   3. PowerShell:     .\ruta\a\apply-phase4.ps1
#
# Este script aplica los 8 parches slim de Fase 4 sobre un repo donde
# ya se aplicaron Fase 1, 2 y 3. Los parches solo añaden/modifican
# archivos.
# ============================================================================
#Requires -Version 5.0
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$PSStyle.Progress.View = "Classic"

$ScriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
$PatchDir  = Split-Path $ScriptDir -Parent | Join-Path -ChildPath "patches"
$RepoDir   = (Get-Location).Path

function Write-Log  { param([string]$Msg) Write-Host "[Fase 4] $Msg" -ForegroundColor Green }
function Write-Warn2{ param([string]$Msg) Write-Host "[Fase 4] $Msg" -ForegroundColor Yellow }
function Write-Err  { param([string]$Msg) Write-Host "[Fase 4 ERROR] $Msg" -ForegroundColor Red }

# ─── Verificaciones previas ─────────────────────────────────────────────────

if (-not (Test-Path ".git")) {
    Write-Err "No estás en un repositorio git (falta .git). Ejecuta desde la raíz del clone de ISALAB."
    exit 1
}
if (-not (Test-Path "main.py") -or -not (Test-Path "gui_pyside") -or -not (Test-Path "services")) {
    Write-Err "Parece que no estás en la raíz del repo ISALAB. Verifica que main.py, gui_pyside\ y services\ existan."
    exit 1
}
if (-not (Test-Path $PatchDir)) {
    Write-Err "No encuentro el directorio de parches: $PatchDir"
    Write-Err "Descarga el ZIP completo de ISALAB-fase4\ y reintenta."
    exit 1
}

Write-Log "Aplicando Fase 4 — Fix CRITICAL de GUI"
Write-Log "Repo: $RepoDir"
Write-Log "Parches: $PatchDir"
Write-Host ""

# ─── Verificar working tree limpio ──────────────────────────────────────────

$gitStatus = git status --porcelain 2>&1
if ($gitStatus) {
    Write-Warn2 "Tienes cambios sin commit en el working tree."
    Write-Warn2 "Recomendación: commit o stash antes de aplicar Fase 4."
    Write-Warn2 "Continuando en 5 segundos... (Ctrl+C para cancelar)"
    Start-Sleep -Seconds 5
    Write-Host ""
}

# ─── Aplicar parches slim uno por uno ────────────────────────────────────────

$patches = @(
    "gui_pyside_app.py.patch",
    "gui_pyside_splash.py.patch",
    "gui_pyside_views_dashboard.py.patch",
    "gui_pyside_dialogs_muestra_dialog.py.patch",
    "gui_pyside_dialogs_vacuna_dialog.py.patch",
    "gui_pyside_utils_platform_utils.py.patch",
    "services_report_service.py.patch",
    "tests_test_fase4_gui.py.patch"
)

$applied = 0
$failed = 0

foreach ($p in $patches) {
    $patchPath = Join-Path $PatchDir $p
    if (-not (Test-Path $patchPath)) {
        Write-Err "Falta parche: $p"
        $failed++
        continue
    }

    # Intentar aplicar con git apply
    $checkResult = git apply --check $patchPath 2>&1
    if ($LASTEXITCODE -eq 0) {
        git apply --verbose $patchPath 2>&1 | Out-Null
        Write-Log "  ✓ $p"
        $applied++
    } else {
        # Ver si ya estaba aplicado (idempotente)
        $reverseCheck = git apply --reverse --check $patchPath 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Warn2 "  ⊙ $p (ya estaba aplicado, skip)"
            $applied++
        } else {
            Write-Err "  ✗ $p (conflicto — revisa el working tree)"
            Write-Err "    Intenta: git apply --reject --verbose $patchPath"
            $failed++
        }
    }
}

Write-Host ""
Write-Log "Resumen: $applied aplicados, $failed fallidos"
Write-Host ""

# ─── Verificación post-aplicación ────────────────────────────────────────────

Write-Log "Verificación post-aplicación:"

# C3: app.py usa Logo_Sidebar.png
if (Select-String -Path "gui_pyside\app.py" -Pattern "Logo_Sidebar\.png" -Quiet) {
    Write-Log "  ✓ C3 app.py referencia 'Logo_Sidebar.png' (PascalCase)"
} else {
    Write-Err "  ✗ C3 app.py NO referencia 'Logo_Sidebar.png'"
}

# C3: splash.py usa Logo_Sidebar.png
if (Select-String -Path "gui_pyside\splash.py" -Pattern "Logo_Sidebar\.png" -Quiet) {
    Write-Log "  ✓ C3 splash.py referencia 'Logo_Sidebar.png' (PascalCase)"
} else {
    Write-Err "  ✗ C3 splash.py NO referencia 'Logo_Sidebar.png'"
}

# C1: muestra_dialog.py no referencia self.ref_text en código
$muestraContent = Get-Content "gui_pyside\dialogs\muestra_dialog.py" -ErrorAction SilentlyContinue
$refTextInCode = $false
foreach ($line in $muestraContent) {
    $trimmed = $line.TrimStart()
    if ($trimmed.StartsWith("#")) { continue }
    if ($line -match "self\.ref_text") {
        # Quitar la parte de comentario inline
        $codePart = $line -split "#",2 | Select-Object -First 1
        if ($codePart -match "self\.ref_text") {
            $refTextInCode = $true
            break
        }
    }
}
if (-not $refTextInCode) {
    Write-Log "  ✓ C1 ResultadoMuestraDialog._guardar no referencia self.ref_text"
} else {
    Write-Err "  ✗ C1 muestra_dialog.py todavía referencia self.ref_text en código"
}

# C2: dashboard.py invoca get_dashboard_stats
if (Select-String -Path "gui_pyside\views\dashboard.py" -Pattern "get_dashboard_stats" -Quiet) {
    Write-Log "  ✓ C2 DashboardView.refresh invoca ReportService.get_dashboard_stats"
} else {
    Write-Err "  ✗ C2 DashboardView no invoca get_dashboard_stats"
}

# C2: dashboard.py mantiene self.stat_labels
if (Select-String -Path "gui_pyside\views\dashboard.py" -Pattern "self\.stat_labels" -Quiet) {
    Write-Log "  ✓ C2 DashboardView mantiene referencias self.stat_labels"
} else {
    Write-Err "  ✗ C2 DashboardView no mantiene self.stat_labels"
}

# C2: report_service.py añade consultas_hoy
if (Select-String -Path "services\report_service.py" -Pattern "consultas_hoy" -Quiet) {
    Write-Log "  ✓ C2 ReportService.get_dashboard_stats retorna consultas_hoy"
} else {
    Write-Err "  ✗ C2 ReportService no retorna consultas_hoy"
}

# C4: platform_utils.py existe
if (Test-Path "gui_pyside\utils\platform_utils.py") {
    Write-Log "  ✓ C4 gui_pyside\utils\platform_utils.py presente"
} else {
    Write-Err "  ✗ C4 gui_pyside\utils\platform_utils.py falta"
}

# C4: open_file_externally definido
if (Select-String -Path "gui_pyside\utils\platform_utils.py" -Pattern "def open_file_externally" -Quiet) {
    Write-Log "  ✓ C4 open_file_externally definido en platform_utils"
} else {
    Write-Err "  ✗ C4 open_file_externally NO definido"
}

# C4: muestra_dialog.py usa el helper
if (Select-String -Path "gui_pyside\dialogs\muestra_dialog.py" -Pattern "open_file_externally" -Quiet) {
    Write-Log "  ✓ C4 muestra_dialog.py usa open_file_externally"
} else {
    Write-Err "  ✗ C4 muestra_dialog.py no usa open_file_externally"
}

# C4: vacuna_dialog.py usa el helper
if (Select-String -Path "gui_pyside\dialogs\vacuna_dialog.py" -Pattern "open_file_externally" -Quiet) {
    Write-Log "  ✓ C4 vacuna_dialog.py usa open_file_externally"
} else {
    Write-Err "  ✗ C4 vacuna_dialog.py no usa open_file_externally"
}

# Tests
if (Test-Path "tests\test_fase4_gui.py") {
    Write-Log "  ✓ tests\test_fase4_gui.py presente"
} else {
    Write-Err "  ✗ tests\test_fase4_gui.py falta"
}

Write-Host ""
if ($failed -eq 0) {
    Write-Log "✅ Fase 4 aplicada correctamente."
    Write-Host ""
    Write-Log "Próximos pasos sugeridos:"
    Write-Host "  1. Revisa los cambios con:  git diff"
    Write-Host "  2. Corre los tests:         python -m pytest tests\test_fase4_gui.py -v"
    Write-Host "  3. Commit en tu rama:       git add -A; git commit -m 'fix(ISALAB): Fase 4 — Fix CRITICAL de GUI'"
    Write-Host "  4. Push a tu fork y abre PR contra master."
} else {
    Write-Err "❌ $failed parche(s) fallaron. Revisa el log arriba."
    Write-Err "Si el conflicto es por Fase 1/2/3 ya aplicada parcialmente, aplica el consolidado:"
    Write-Err "  git apply --reject $PatchDir\0001-fix-ISALAB-Fase-4-Fix-CRITICAL-de-GUI.patch"
    exit 1
}
