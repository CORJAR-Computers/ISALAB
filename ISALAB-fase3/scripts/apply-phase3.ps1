# ============================================================================
# ISALAB — Fase 3: Fix CRITICAL de seguridad
# Aplicador de parches para Windows PowerShell
# ============================================================================
#
# USO:
#   1. Clona el repo:  git clone https://github.com/CORJAR-Computers/ISALAB
#   2. cd ISALAB
#   3. PowerShell:     .\ruta\a\apply-phase3.ps1
#
# Este script aplica los 23 parches slim de Fase 3 sobre un clone limpio
# del repositorio público. Los parches solo añaden/modifican archivos.
# ============================================================================
#Requires -Version 5.0
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$PSStyle.Progress.View = "Classic"

$ScriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
$PatchDir  = Split-Path $ScriptDir -Parent | Join-Path -ChildPath "patches"
$RepoDir   = (Get-Location).Path

function Write-Log  { param([string]$Msg) Write-Host "[Fase 3] $Msg" -ForegroundColor Green }
function Write-Warn2{ param([string]$Msg) Write-Host "[Fase 3] $Msg" -ForegroundColor Yellow }
function Write-Err  { param([string]$Msg) Write-Host "[Fase 3 ERROR] $Msg" -ForegroundColor Red }

# ─── Verificaciones previas ─────────────────────────────────────────────────

if (-not (Test-Path ".git")) {
    Write-Err "No estás en un repositorio git (falta .git). Ejecuta desde la raíz del clone de ISALAB."
    exit 1
}
if (-not (Test-Path "main.py") -or -not (Test-Path "services") -or -not (Test-Path "utils")) {
    Write-Err "Parece que no estás en la raíz del repo ISALAB. Verifica que main.py, services\ y utils\ existan."
    exit 1
}
if (-not (Test-Path $PatchDir)) {
    Write-Err "No encuentro el directorio de parches: $PatchDir"
    Write-Err "Descarga el ZIP completo de ISALAB-fase3\ y reintenta."
    exit 1
}

Write-Log "Aplicando Fase 3 — Fix CRITICAL de seguridad"
Write-Log "Repo: $RepoDir"
Write-Log "Parches: $PatchDir"
Write-Host ""

# ─── Verificar working tree limpio ──────────────────────────────────────────

$gitStatus = git status --porcelain 2>&1
if ($gitStatus) {
    Write-Warn2 "Tienes cambios sin commit en el working tree."
    Write-Warn2 "Recomendación: commit o stash antes de aplicar Fase 3."
    Write-Warn2 "Continuando en 5 segundos... (Ctrl+C para cancelar)"
    Start-Sleep -Seconds 5
    Write-Host ""
}

# ─── Aplicar parches slim uno por uno ────────────────────────────────────────

$patches = @(
    "utils_security.py.patch",
    "services_usuario_service.py.patch",
    "services_animal_service.py.patch",
    "services_muestra_service.py.patch",
    "services_recepcion_service.py.patch",
    "services_consulta_service.py.patch",
    "services_cirugia_service.py.patch",
    "services_vacuna_service.py.patch",
    "services_historia_service.py.patch",
    "services_configuracion_service.py.patch",
    "services_report_service.py.patch",
    "services_pdf_service.py.patch",
    "services_report_laboratorio.py.patch",
    "services_report_vacunacion.py.patch",
    "services_report_historia_clinica.py.patch",
    "services_report_cirugia.py.patch",
    "services_report_consulta.py.patch",
    "services_report_consentimiento.py.patch",
    "services_report_formula_medica.py.patch",
    "reports_generators.py.patch",
    "reports_base.py.patch",
    "main.py.patch",
    "tests_test_fase3_security.py.patch"
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

# C4: PermissionDeniedError
if (Select-String -Path "utils\security.py" -Pattern "class PermissionDeniedError" -Quiet) {
    Write-Log "  ✓ C4 PermissionDeniedError definido en utils\security.py"
} else {
    Write-Err "  ✗ C4 PermissionDeniedError NO encontrado en utils\security.py"
}

# C1: set_current_user
if (Select-String -Path "utils\security.py" -Pattern "def set_current_user" -Quiet) {
    Write-Log "  ✓ C1 set_current_user definido en utils\security.py"
} else {
    Write-Err "  ✗ C1 set_current_user NO encontrado en utils\security.py"
}

# C2: contador atómico ISAL
if (Select-String -Path "services\recepcion_service.py" -Pattern "db.generar_codigo\('ISAL'\)" -Quiet) {
    Write-Log "  ✓ C2 RecepcionService.generar_codigo usa contador atómico"
} else {
    Write-Err "  ✗ C2 RecepcionService.generar_codigo NO usa contador atómico"
}

# C3: select_autoescape
if (Select-String -Path "reports\generators.py" -Pattern "select_autoescape" -Quiet) {
    Write-Log "  ✓ C3 Jinja2 autoescape activo en reports\generators.py"
} else {
    Write-Err "  ✗ C3 select_autoescape NO encontrado en reports\generators.py"
}

# C3: _safe_url_fetcher
if (Select-String -Path "reports\generators.py" -Pattern "_safe_url_fetcher" -Quiet) {
    Write-Log "  ✓ C3 url_fetcher sandboxed en reports\generators.py"
} else {
    Write-Err "  ✗ C3 _safe_url_fetcher NO encontrado en reports\generators.py"
}

# C1: main.py invoca set_current_user
if (Select-String -Path "main.py" -Pattern "set_current_user" -Quiet) {
    Write-Log "  ✓ C1 main.py invoca set_current_user tras login"
} else {
    Write-Err "  ✗ C1 main.py NO invoca set_current_user"
}

# Tests
if (Test-Path "tests\test_fase3_security.py") {
    Write-Log "  ✓ tests\test_fase3_security.py presente"
} else {
    Write-Err "  ✗ tests\test_fase3_security.py falta"
}

Write-Host ""
if ($failed -eq 0) {
    Write-Log "✅ Fase 3 aplicada correctamente."
    Write-Host ""
    Write-Log "Próximos pasos sugeridos:"
    Write-Host "  1. Revisa los cambios con:  git diff"
    Write-Host "  2. Corre los tests:         python -m pytest tests\test_fase3_security.py -v"
    Write-Host "  3. Commit en tu rama:       git add -A; git commit -m 'fix(ISALAB): Fase 3 — Fix CRITICAL de seguridad'"
    Write-Host "  4. Push a tu fork y abre PR contra master."
} else {
    Write-Err "❌ $failed parche(s) fallaron. Revisa el log arriba."
    Write-Err "Si el conflicto es por Fase 1/2 ya aplicada parcialmente, descarta el parche problemático y aplica el consolidado:"
    Write-Err "  git apply --reject $PatchDir\0001-fix-ISALAB-Fase-3-Fix-CRITICAL-de-seguridad.patch"
    exit 1
}
