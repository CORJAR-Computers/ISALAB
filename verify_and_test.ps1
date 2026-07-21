# ============================================
# IsaLab - Verificar Limpieza y Ejecutar Tests
# ============================================
# Ejecutar en PowerShell: .\verify_and_test.ps1
# ============================================

param(
    [string]$ProjectRoot = "D:\ISALAB",
    [switch]$SkipTests
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IsaLab - Verificar y Testear        " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Proyecto: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# Cambiar al directorio del proyecto
Set-Location -Path $ProjectRoot

# ============================================
# 1. ELIMINAR ARCHIVOS MUERTOS
# ============================================
Write-Host "1. Eliminando archivos muertos..." -ForegroundColor Yellow

$deadFiles = @(
    "gui_pyside\utils\window_manager.py",
    "gui_pyside\views\boton_generar_reportes.py"
)

$eliminados = 0
foreach ($file in $deadFiles) {
    $path = Join-Path $ProjectRoot $file
    Remove-Item -Path $path -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $path)) {
        Write-Host "   [OK] $file eliminado" -ForegroundColor Green
        $eliminados++
    } else {
        Write-Host "   [FAIL] $file no se pudo eliminar" -ForegroundColor Red
    }
}

Write-Host "`n   Archivos eliminados: $eliminados/2" -ForegroundColor $(if ($eliminados -eq 2) { "Green" } else { "Red" })

# ============================================
# 2. VERIFICAR ELIMINACIÓN
# ============================================
Write-Host "`n2. Verificando eliminación..." -ForegroundColor Yellow

$allDeleted = $true
foreach ($file in $deadFiles) {
    $path = Join-Path $ProjectRoot $file
    if (Test-Path $path) {
        Write-Host "   [FAIL] $file AÚN EXISTE" -ForegroundColor Red
        $allDeleted = $false
    } else {
        Write-Host "   [OK] $file eliminado correctamente" -ForegroundColor Green
    }
}

if (-not $allDeleted) {
    Write-Host "`n[ERROR] No se pueden eliminar todos los archivos muertos" -ForegroundColor Red
    Write-Host "Verifique permisos o cierre procesos que puedan estar usando estos archivos" -ForegroundColor Yellow
    exit 1
}

# ============================================
# 3. EJECUTAR TESTS
# ============================================
if (-not $SkipTests) {
    Write-Host "`n3. Ejecutando suite de tests..." -ForegroundColor Yellow
    Write-Host "   Esto puede tomar unos minutos..." -ForegroundColor Gray
    Write-Host ""

    $startTime = Get-Date
    python -m pytest tests/ -v --tb=short --strict-markers
    $exitCode = $LASTEXITCODE
    $endTime = Get-Date
    $duration = $endTime - $startTime

    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  RESUMEN DE TESTS" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    Write-Host "`nDuracion total: $([math]::Round($duration.TotalSeconds, 2)) segundos" -ForegroundColor Gray

    if ($exitCode -eq 0) {
        Write-Host "`n[TODOS LOS TESTS PASARON]" -ForegroundColor Green
        Write-Host "El proyecto esta listo para commit." -ForegroundColor Green
        
        Write-Host "`nSiguientes pasos:" -ForegroundColor Yellow
        Write-Host "  1. Ejecutar commit:" -ForegroundColor White
        Write-Host "     .\commit_production_readiness.ps1" -ForegroundColor Gray
        Write-Host "  2. O crear commit manualmente:" -ForegroundColor White
        Write-Host "     git add -A" -ForegroundColor Gray
        Write-Host "     git commit -m 'chore: Production readiness cleanup'" -ForegroundColor Gray
    } else {
        Write-Host "`n[ALGUNOS TESTS FALLARON]" -ForegroundColor Red
        Write-Host "Revise los errores arriba y corrija antes de commitear." -ForegroundColor Yellow
        exit $exitCode
    }
} else {
    Write-Host "`n3. Tests omitidos (SkipTests activado)" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
