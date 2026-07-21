# ============================================
# IsaLab - Script de Commit Production Ready
# ============================================
# Ejecutar en PowerShell: .\commit_production_readiness.ps1
# ============================================

param(
    [string]$ProjectRoot = "D:\ISALAB",
    [string]$CommitMessage = "chore: Production readiness cleanup

- Update .gitignore: .coverage -> .coverage* to ignore all coverage files
- Add cleanup_production.ps1: Script to delete dead files and temp scripts
- Add run_tests.ps1: Script to run complete test suite
- Delete dead code: window_manager.py, boton_generar_reportes.py (via cleanup script)
- Remove temp scripts: fix_*.py, _cleanup_*.py, _run_tests.py (via cleanup script)
- Remove residual patches: 0001-chore-*.patch, 0001-slim-*.patch (via cleanup script)

All tests should pass after running cleanup_production.ps1"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IsaLab - Commit Production Ready     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Proyecto: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# Cambiar al directorio del proyecto
Set-Location -Path $ProjectRoot

# ============================================
# 1. VERIFICAR ESTADO DE GIT
# ============================================
Write-Host "1. Verificando estado de Git..." -ForegroundColor Yellow

# Verificar que es un repositorio Git
if (-not (Test-Path ".git")) {
    Write-Host "   [FAIL] No es un repositorio Git" -ForegroundColor Red
    exit 1
}

# Mostrar estado actual
Write-Host "   Estado actual:" -ForegroundColor Gray
git status --short

# ============================================
# 2. VERIFICAR CAMBIOS PENDIENTES
# ============================================
Write-Host "`n2. Verificando cambios pendientes..." -ForegroundColor Yellow

$changes = git status --porcelain
if ([string]::IsNullOrWhiteSpace($changes)) {
    Write-Host "   [INFO] No hay cambios pendientes para commitear" -ForegroundColor Yellow
    Write-Host "   Los cambios ya fueron commiteados anteriormente." -ForegroundColor Gray
    exit 0
}

Write-Host "   Cambios detectados:" -ForegroundColor Green
$changes | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }

# ============================================
# 3. AGREGAR CAMBIOS
# ============================================
Write-Host "`n3. Agregando cambios..." -ForegroundColor Yellow

# Agregar archivos especificos
$filesToAdd = @(
    ".gitignore",
    "cleanup_production.ps1",
    "run_tests.ps1",
    "commit_production_readiness.ps1"
)

foreach ($file in $filesToAdd) {
    if (Test-Path $file) {
        git add $file
        Write-Host "   [OK] $file agregado" -ForegroundColor Green
    }
}

# Agregar eliminacion de archivos muertos si existen
$deadFiles = @(
    "gui_pyside\utils\window_manager.py",
    "gui_pyside\views\boton_generar_reportes.py",
    "fix_f541.py",
    "fix_jinja_format.py",
    "fix_jinja_format_2.py",
    "fix_jinja_format_3.py",
    "_cleanup_isalab_fase.py",
    "_run_tests.py",
    "0001-chore-ISALAB-Fase-1-higiene-del-repositorio-setup-to.patch",
    "0001-slim-added-modified-only.patch"
)

foreach ($file in $deadFiles) {
    if (-not (Test-Path $file)) {
        # Archivo eliminado - git lo detectara
        Write-Host "   [OK] $file (eliminado)" -ForegroundColor Green
    }
}

# Agregar todos los demas cambios
git add -A

# ============================================
# 4. VERIFICAR CAMBIOS A AGREGAR
# ============================================
Write-Host "`n4. Cambios que seran commiteados:" -ForegroundColor Yellow

git diff --cached --stat

# ============================================
# 5. CREAR COMMIT
# ============================================
Write-Host "`n5. Creando commit..." -ForegroundColor Yellow

git commit -m $CommitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] Commit creado exitosamente" -ForegroundColor Green
} else {
    Write-Host "   [FAIL] Error al crear commit" -ForegroundColor Red
    exit 1
}

# ============================================
# 6. MOSTRAR RESULTADO
# ============================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  COMMIT CREADO EXITOSAMENTE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nUltimo commit:" -ForegroundColor Yellow
git log --oneline -1

Write-Host "`nArchivos en el commit:" -ForegroundColor Yellow
git diff-tree --no-commit-id --name-only -r HEAD

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SIGUIENTES PASOS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`n1. Ejecutar limpieza (si no se ha hecho):" -ForegroundColor White
Write-Host "   .\cleanup_production.ps1" -ForegroundColor Gray

Write-Host "`n2. Ejecutar tests:" -ForegroundColor White
Write-Host "   .\run_tests.ps1" -ForegroundColor Gray

Write-Host "`n3. Push a remoto (cuando este listo):" -ForegroundColor White
Write-Host "   git push origin feat/phase5-high-issues" -ForegroundColor Gray

Write-Host "`n========================================" -ForegroundColor Cyan
