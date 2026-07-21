# ============================================
# IsaLab - Script de Limpieza Production Ready
# ============================================
# Ejecutar en PowerShell: .\cleanup_production.ps1
# ============================================

param(
    [string]$ProjectRoot = "D:\ISALAB"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IsaLab - Limpieza Production Ready   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Proyecto: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# Contadores
$eliminados = 0
$fallidos = 0

# ============================================
# 1. ELIMINAR ARCHIVOS MUERTOS (CRÍTICO)
# ============================================
Write-Host "1. Eliminando archivos muertos (CRITICO)..." -ForegroundColor Yellow

$archivosMuertos = @(
    "gui_pyside\utils\window_manager.py",
    "gui_pyside\views\boton_generar_reportes.py"
)

foreach ($archivo in $archivosMuertos) {
    $ruta = Join-Path $ProjectRoot $archivo
    Remove-Item -Path $ruta -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $ruta)) {
        Write-Host "   [OK] $archivo eliminado" -ForegroundColor Green
        $eliminados++
    } else {
        Write-Host "   [FAIL] $archivo no se pudo eliminar" -ForegroundColor Red
        $fallidos++
    }
}

# ============================================
# 2. ELIMINAR SCRIPTS TEMPORALES
# ============================================
Write-Host "`n2. Eliminando scripts temporales..." -ForegroundColor Yellow

$scriptsTemporales = @(
    "fix_f541.py",
    "fix_jinja_format.py",
    "fix_jinja_format_2.py",
    "fix_jinja_format_3.py",
    "_cleanup_isalab_fase.py",
    "_run_tests.py"
)

foreach ($script in $scriptsTemporales) {
    $ruta = Join-Path $ProjectRoot $script
    Remove-Item -Path $ruta -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $ruta)) {
        Write-Host "   [OK] $script eliminado" -ForegroundColor Green
        $eliminados++
    } else {
        Write-Host "   [FAIL] $script no se pudo eliminar" -ForegroundColor Red
        $fallidos++
    }
}

# ============================================
# 3. ELIMINAR PATCHES RESIDUALES
# ============================================
Write-Host "`n3. Eliminando patches residuales..." -ForegroundColor Yellow

$patches = @(
    "0001-chore-ISALAB-Fase-1-higiene-del-repositorio-setup-to.patch",
    "0001-slim-added-modified-only.patch"
)

foreach ($patch in $patches) {
    $ruta = Join-Path $ProjectRoot $patch
    Remove-Item -Path $ruta -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $ruta)) {
        Write-Host "   [OK] $patch eliminado" -ForegroundColor Green
        $eliminados++
    } else {
        Write-Host "   [FAIL] $patch no se pudo eliminar" -ForegroundColor Red
        $fallidos++
    }
}

# ============================================
# 4. ELIMINAR ARCHIVOS .coverage
# ============================================
Write-Host "`n4. Eliminando archivos .coverage..." -ForegroundColor Yellow

$coverageFiles = Get-ChildItem -Path $ProjectRoot -Filter ".coverage*" -File -ErrorAction SilentlyContinue
foreach ($file in $coverageFiles) {
    Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $file.FullName)) {
        Write-Host "   [OK] $($file.Name) eliminado" -ForegroundColor Green
        $eliminados++
    } else {
        Write-Host "   [FAIL] $($file.Name) no se pudo eliminar" -ForegroundColor Red
        $fallidos++
    }
}

# ============================================
# 5. VERIFICACION FINAL
# ============================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  VERIFICACION FINAL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nArchivos eliminados: $eliminados" -ForegroundColor Green
Write-Host "Archivos con error: $fallidos" -ForegroundColor $(if ($fallidos -gt 0) { "Red" } else { "Green" })

# Verificar que los archivos criticos no existan
Write-Host "`nVerificando archivos muertos:" -ForegroundColor Yellow

$verificarArchivos = @(
    "gui_pyside\utils\window_manager.py",
    "gui_pyside\views\boton_generar_reportes.py"
)

$todoLimpio = $true
foreach ($archivo in $verificarArchivos) {
    $ruta = Join-Path $ProjectRoot $archivo
    if (Test-Path $ruta) {
        Write-Host "   [FAIL] $archivo AUN EXISTE" -ForegroundColor Red
        $todoLimpio = $false
    } else {
        Write-Host "   [OK] $archivo eliminado correctamente" -ForegroundColor Green
    }
}

# ============================================
# 6. RESUMEN
# ============================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  RESUMEN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($todoLimpio -and $fallidos -eq 0) {
    Write-Host "`n[LIMPIEZA COMPLETADA EXITOSAMENTE]" -ForegroundColor Green
    Write-Host "`nSiguientes pasos:" -ForegroundColor Yellow
    Write-Host "  1. Ejecutar tests:" -ForegroundColor White
    Write-Host "     cd $ProjectRoot" -ForegroundColor Gray
    Write-Host "     python -m pytest tests/ -v" -ForegroundColor Gray
    Write-Host "`n  2. Crear commit:" -ForegroundColor White
    Write-Host "     git add -A" -ForegroundColor Gray
    Write-Host "     git commit -m 'chore: Production readiness cleanup'" -ForegroundColor Gray
} else {
    Write-Host "`n[ADVERTENCIA] Revision manual requerida" -ForegroundColor Red
    Write-Host "  Verifique los archivos marcados como [FAIL]" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
