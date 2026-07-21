# apply-phase5.ps1 — Aplica los parches de la Fase 5 (Fix HIGH) al repo ISALAB.
#
# Uso:
#   .\apply-phase5.ps1        # desde la raíz del repo ISALAB
#
# Requisitos:
#   - Estar en la raíz de un clone del repo ISALAB (con .git, main.py, etc.).
#   - Tener aplicadas las Fases 1, 2, 3 y 4.
#   - Working tree razonablemente limpio (advertencia si no).

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PatchDir  = Join-Path (Split-Path -Parent $ScriptDir) "patches"

Write-Host ""
Write-Host "============================================================"
Write-Host "  ISALAB — Fase 5: Fix HIGH issues (GUI + Services + DB)"
Write-Host "============================================================"
Write-Host ""

# ─── 1. Verificar raíz del repo ──────────────────────────────────────────
if (-not (Test-Path .git -PathType Container)) {
    Write-Host "ERR: No estás en la raíz de un repo git." -ForegroundColor Red
    exit 1
}
if (-not ((Test-Path main.py) -and (Test-Path config.py))) {
    Write-Host "ERR: No parece ser el repo ISALAB (falta main.py o config.py)." -ForegroundColor Red
    exit 1
}
Write-Host "OK: Repo ISALAB detectado: $(Get-Location)" -ForegroundColor Green

# ─── 2. Verificar working tree ────────────────────────────────────────────
$dirty = git status --porcelain 2>$null
if ($dirty) {
    Write-Host "WARN: El working tree tiene cambios sin commitear." -ForegroundColor Yellow
    Write-Host "  Recomendado: commitea o stash antes de aplicar."
    Write-Host "  Continuando de todas formas..."
}

# ─── 3. Aplicar parches slim ─────────────────────────────────────────────
Write-Host ""
Write-Host "-- Aplicando 21 parches slim --"
$SlimPatches = @(
    "alembic_versions_c1a2b3c4d5e6_fase5_indexes_and_password_reset_flag.py.patch",
    "gui_pyside_app.py.patch",
    "gui_pyside_components_components.py.patch",
    "gui_pyside_dialogs_cambiar_password_dialog.py.patch",
    "gui_pyside_dialogs_muestra_dialog.py.patch",
    "gui_pyside_dialogs_usuario_dialog.py.patch",
    "gui_pyside_views_dashboard.py.patch",
    "gui_pyside_views_recepcion.py.patch",
    "gui_pyside_views_usuarios.py.patch",
    "orm_models_animal.py.patch",
    "orm_models_clinica.py.patch",
    "schemas_clinica.py.patch",
    "services_cirugia_service.py.patch",
    "services_historia_service.py.patch",
    "services_recepcion_service.py.patch",
    "services_usuario_service.py.patch",
    "tests_test_fase3_security.py.patch",
    "tests_test_fase4_gui.py.patch",
    "tests_test_fase5_high.py.patch",
    "utils_security.py.patch",
    "utils_validators.py.patch"
)
$applied = 0; $skipped = 0; $failed = 0
foreach ($p in $SlimPatches) {
    $patchPath = Join-Path $PatchDir $p
    if (-not (Test-Path $patchPath)) {
        Write-Host "  ERR: $p — no encontrado en $PatchDir" -ForegroundColor Red
        $failed++; continue
    }
    # Idempotencia: si git apply --check pasa, aplicar; sino verificar si
    # ya estaba aplicado.
    $checkResult = git apply --check $patchPath 2>&1
    if ($LASTEXITCODE -eq 0) {
        git apply --verbose $patchPath 2>&1 | Out-Null
        Write-Host "  OK: $p" -ForegroundColor Green
        $applied++
    } else {
        # Heurística: si el archivo objetivo ya tiene "Fase 5", skip.
        $targetLine = Select-String -Path $patchPath -Pattern '^\+\+\+ b/' | Select-Object -First 1
        if ($targetLine) {
            $target = $targetLine.Line -replace '^\+\+\+ b/', ''
            if ((Test-Path $target) -and (Select-String -Path $target -Pattern 'Fase 5' -Quiet)) {
                Write-Host "  --: $p — ya aplicado, skip" -ForegroundColor Yellow
                $skipped++
                continue
            }
        }
        Write-Host "  ERR: $p — no se pudo aplicar" -ForegroundColor Red
        $failed++
    }
}
Write-Host ""
Write-Host "  Resumen: $applied aplicados, $skipped ya aplicados, $failed fallidos."

# ─── 4. git rm de los archivos eliminados ─────────────────────────────────
Write-Host ""
Write-Host "-- Eliminando archivos dead code --"
$Deleted = @(
    "gui_pyside/utils/window_manager.py",
    "gui_pyside/views/boton_generar_reportes.py"
)
foreach ($f in $Deleted) {
    if (Test-Path $f) {
        git rm --quiet $f
        Write-Host "  OK: git rm $f" -ForegroundColor Green
    } elseif (git ls-files --error-unmatch $f 2>$null) {
        git rm --cached --quiet $f
        Write-Host "  OK: git rm --cached $f (ya no en disco)" -ForegroundColor Green
    } else {
        Write-Host "  --: $f — ya no existe, skip" -ForegroundColor Yellow
    }
}

# ─── 5. Verificaciones post-aplicación ────────────────────────────────────
Write-Host ""
Write-Host "-- Verificaciones post-aplicación --"
$pass = 0; $fail = 0

function Check($desc, $scriptBlock) {
    try {
        & $scriptBlock | Out-Null
        if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq $null) {
            Write-Host "  OK: $desc" -ForegroundColor Green
            $script:pass++
        } else {
            Write-Host "  ERR: $desc" -ForegroundColor Red
            $script:fail++
        }
    } catch {
        Write-Host "  ERR: $desc" -ForegroundColor Red
        $script:fail++
    }
}

# H-G1
Check "H-G1: ErrorHandler sin parent=None (en código)" {
    $src = Get-Content "gui_pyside/components/components.py" -Raw
    # Quitar comentarios simples.
    $code = ($src -split "`n" | Where-Object { $_ -notmatch '^\s*#' }) -join "`n"
    if ($code -match 'QMessageBox\.critical\(None,') { throw "still uses None" }
}

# H-G2
Check "H-G2: window_manager.py eliminado" {
    if (Test-Path "gui_pyside/utils/window_manager.py") { throw "still exists" }
}
Check "H-G2: app.py no importa WindowManager" {
    $src = Get-Content "gui_pyside/app.py" -Raw
    if ($src -match 'from\s+gui_pyside\.utils\.window_manager') { throw "still imports" }
}

# H-G3
Check "H-G3: boton_generar_reportes.py eliminado" {
    if (Test-Path "gui_pyside/views/boton_generar_reportes.py") { throw "still exists" }
}

# H-G4
Check "H-G4: _get_selected_animal_id eliminado de recepcion.py" {
    $src = Get-Content "gui_pyside/views/recepcion.py" -Raw
    if ($src -match 'def\s+_get_selected_animal_id') { throw "still defined" }
}

# H-G5
Check "H-G5: theme_changed.connect en app.py" {
    $src = Get-Content "gui_pyside/app.py" -Raw
    if ($src -notmatch 'theme_changed\.connect') { throw "not connected" }
}
Check "H-G5: _on_theme_changed handler en app.py" {
    $src = Get-Content "gui_pyside/app.py" -Raw
    if ($src -notmatch '_on_theme_changed') { throw "no handler" }
}

# H-G6
Check "H-G6: QDialog.Accepted en usuarios.py" {
    $src = Get-Content "gui_pyside/views/usuarios.py" -Raw
    if ($src -notmatch 'QDialog\.Accepted') { throw "not using Accepted" }
}

# H-G7
Check "H-G7: _PegadoMagicoFilter en muestra_dialog.py" {
    $src = Get-Content "gui_pyside/dialogs/muestra_dialog.py" -Raw
    if ($src -notmatch '_PegadoMagicoFilter') { throw "no filter class" }
}
Check "H-G7: installEventFilter en muestra_dialog.py" {
    $src = Get-Content "gui_pyside/dialogs/muestra_dialog.py" -Raw
    if ($src -notmatch 'installEventFilter') { throw "no installEventFilter call" }
}

# H-G8
Check "H-G8: PDFProWorker a nivel de módulo" {
    $src = Get-Content "gui_pyside/dialogs/muestra_dialog.py" -Raw
    if ($src -notmatch '(?m)^class\s+PDFProWorker') { throw "not module-level" }
}
Check "H-G8: finished.connect(deleteLater)" {
    $src = Get-Content "gui_pyside/dialogs/muestra_dialog.py" -Raw
    if ($src -notmatch 'finished\.connect\(self\.worker\.deleteLater\)') { throw "no deleteLater" }
}

# H-S1
Check "H-S1: dummy_verify_password en utils/security.py" {
    $src = Get-Content "utils/security.py" -Raw
    if ($src -notmatch 'def\s+dummy_verify_password') { throw "no function" }
}
Check "H-S1: dummy_verify_password en autenticar" {
    $src = Get-Content "services/usuario_service.py" -Raw
    if ($src -notmatch 'dummy_verify_password\(password\)') { throw "not called" }
}

# H-S2
Check "H-S2: 'len(nueva) < 8' en cambiar_password_dialog.py" {
    $src = Get-Content "gui_pyside/dialogs/cambiar_password_dialog.py" -Raw
    if ($src -notmatch 'len\(nueva\)\s*<\s*8') { throw "not 8 chars" }
}
Check "H-S2: 'len(pwd) < 8' en usuario_dialog.py" {
    $src = Get-Content "gui_pyside/dialogs/usuario_dialog.py" -Raw
    if ($src -notmatch 'len\(pwd\)\s*<\s*8') { throw "not 8 chars" }
}

# H-S3
Check "H-S3: validate_pattern en MuestraValidator" {
    $src = Get-Content "utils/validators.py" -Raw
    if ($src -notmatch 'validate_pattern') { throw "no validate_pattern" }
}

# H-S4
Check "H-S4: ESTADOS_RECEPCION en recepcion_service.py" {
    $src = Get-Content "services/recepcion_service.py" -Raw
    if ($src -notmatch 'if\s+estado\s+not\s+in\s+ESTADOS_RECEPCION') { throw "no whitelist" }
}
Check "H-S4: ESTADOS_CIRUGIA en cirugia_service.py" {
    $src = Get-Content "services/cirugia_service.py" -Raw
    if ($src -notmatch 'if\s+estado\s+not\s+in\s+ESTADOS_CIRUGIA') { throw "no whitelist" }
}

# H-S5
Check "H-S5: _coerce_or_keep en historia_service.py" {
    $src = Get-Content "services/historia_service.py" -Raw
    if ($src -notmatch '_coerce_or_keep') { throw "no helper" }
}

# H-S6
Check "H-S6: password_reset_required = 1 en reset_password" {
    $src = Get-Content "services/usuario_service.py" -Raw
    if ($src -notmatch 'password_reset_required\s*=\s*1') { throw "no flag set" }
}
Check "H-S6: requires_password_change helper existe" {
    $src = Get-Content "services/usuario_service.py" -Raw
    if ($src -notmatch 'def\s+requires_password_change') { throw "no helper" }
}

# H-D3
Check "H-D3: created_at en orm_models/animal.py" {
    $src = Get-Content "orm_models/animal.py" -Raw
    if ($src -notmatch 'created_at\s*=\s*Column') { throw "no created_at" }
}
Check "H-D3: created_at en orm_models/clinica.py (>=7 clases)" {
    $src = Get-Content "orm_models/clinica.py" -Raw
    $count = ([regex]::Matches($src, 'created_at\s*=\s*Column')).Count
    if ($count -lt 7) { throw "only $count created_at declarations" }
}

# H-D4
Check "H-D4: migración c1a2b3c4d5e6 existe" {
    if (-not (Test-Path "alembic/versions/c1a2b3c4d5e6_fase5_indexes_and_password_reset_flag.py")) { throw "no migration" }
}

# H-D6
Check "H-D6: RecepcionSchema sin campo empresa (en código)" {
    $src = Get-Content "schemas/clinica.py" -Raw
    # Localizar RecepcionSchema y verificar sin 'empresa:' en líneas no-comment.
    $match = [regex]::Match($src, '(?s)class\s+RecepcionSchema\s*\(BaseModel\)\s*:(.*?)(?=\nclass\s|\Z)')
    if (-not $match.Success) { throw "no RecepcionSchema" }
    $body = $match.Groups[1].Value
    $codeLines = ($body -split "`n" | Where-Object { $_ -notmatch '^\s*#' })
    $code = $codeLines -join "`n"
    if ($code -match 'empresa\s*:') { throw "still has empresa field" }
}

# Tests
Check "Tests: tests/test_fase5_high.py existe" {
    if (-not (Test-Path "tests/test_fase5_high.py")) { throw "no test file" }
}

Write-Host ""
Write-Host "  Resumen: $pass verificaciones OK, $fail fallaron."

# ─── 6. Próximos pasos ────────────────────────────────────────────────────
Write-Host ""
Write-Host "-- Próximos pasos --"
Write-Host "  1. Revisa los cambios con 'git diff' o en GitHub Desktop."
Write-Host "  2. Ejecuta los tests de regresión:"
Write-Host "       python -m pytest tests/test_fase5_high.py -v --no-cov"
Write-Host "  3. Aplica la migración Alembic:"
Write-Host "       python -m alembic upgrade head"
Write-Host "  4. Commit con el mensaje sugerido:"
Write-Host "       fix(ISALAB): Fase 5 — Fix HIGH issues (GUI + Services + DB)"
Write-Host "  5. Push y abre PR contra master."
Write-Host ""

if ($fail -eq 0 -and $failed -eq 0) {
    Write-Host "OK: Fase 5 aplicada correctamente. $pass verificaciones OK." -ForegroundColor Green
    exit 0
} else {
    Write-Host "ERR: Algunas verificaciones fallaron. Revisa el output arriba." -ForegroundColor Red
    exit 1
}
