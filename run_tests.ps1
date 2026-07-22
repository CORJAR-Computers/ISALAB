# ============================================
# IsaLab - Ejecutor de Tests Completo
# ============================================
# Ejecutar en PowerShell: .\run_tests.ps1
# ============================================

param(
    [string]$ProjectRoot = "D:\ISALAB",
    [switch]$WithCoverage,
    [switch]$SkipDependencyCheck
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IsaLab - Suite de Tests Completa    " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Proyecto: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# Cambiar al directorio del proyecto
Set-Location -Path $ProjectRoot

# ============================================
# 1. VERIFICAR ARCHIVOS MUERTOS (PRE-FLIGHT)
# ============================================
Write-Host "1. Verificando pre-requisitos..." -ForegroundColor Yellow

$deadFiles = @(
    "gui_pyside\utils\window_manager.py",
    "gui_pyside\views\boton_generar_reportes.py"
)

$deadFilesExist = $false
foreach ($file in $deadFiles) {
    $path = Join-Path $ProjectRoot $file
    if (Test-Path $path) {
        Write-Host "   [WARN] $file aun existe - algunos tests fallaran" -ForegroundColor Yellow
        $deadFilesExist = $true
    }
}

if ($deadFilesExist) {
    Write-Host "   Ejecute .\cleanup_production.ps1 primero para eliminar archivos muertos" -ForegroundColor Yellow
    Write-Host ""
}

# ============================================
# 2. VERIFICAR DEPENDENCIAS
# ============================================
if (-not $SkipDependencyCheck) {
    Write-Host "2. Verificando dependencias..." -ForegroundColor Yellow

    # Verificar Python
    python --version 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   [FAIL] Python no encontrado" -ForegroundColor Red
        exit 1
    }
    $pythonVersion = python --version 2>&1
    Write-Host "   [OK] $pythonVersion" -ForegroundColor Green

    # Verificar pytest
    python -m pytest --version 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   [FAIL] pytest no encontrado. Instalar con: pip install pytest" -ForegroundColor Red
        exit 1
    }
    Write-Host "   [OK] pytest instalado" -ForegroundColor Green

    # Instalar dependencias de desarrollo
    Write-Host "   Instalando dependencias de desarrollo..." -ForegroundColor Gray
    pip install -r requirements-dev.txt -q 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   [WARN] Algunas dependencias pudieron no instalarse" -ForegroundColor Yellow
    } else {
        Write-Host "   [OK] Dependencias instaladas" -ForegroundColor Green
    }
}

# ============================================
# 3. EJECUTAR TESTS
# ============================================
Write-Host "`n3. Ejecutando suite de tests..." -ForegroundColor Yellow
Write-Host "   Esto puede tomar unos minutos..." -ForegroundColor Gray
Write-Host ""

# Ejecutar tests
$startTime = Get-Date

if ($WithCoverage) {
    python -m pytest tests/ -v --tb=short --strict-markers --cov=. --cov-report=term-missing
} else {
    python -m pytest tests/ -v --tb=short --strict-markers
}

$exitCode = $LASTEXITCODE
$endTime = Get-Date
$duration = $endTime - $startTime

# ============================================
# 4. RESUMEN
# ============================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  RESUMEN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nDuracion total: $([math]::Round($duration.TotalSeconds, 2)) segundos" -ForegroundColor Gray

if ($exitCode -eq 0) {
    Write-Host "`n[TODOS LOS TESTS PASARON]" -ForegroundColor Green
    Write-Host "El proyecto esta listo para produccion." -ForegroundColor Green
    
    Write-Host "`nSiguientes pasos:" -ForegroundColor Yellow
    Write-Host "  1. Crear commit:" -ForegroundColor White
    Write-Host "     git add -A" -ForegroundColor Gray
    Write-Host "     git commit -m 'chore: Production readiness - all tests passing'" -ForegroundColor Gray
    Write-Host "`n  2. Ejecutar con cobertura (opcional):" -ForegroundColor White
    Write-Host "     .\run_tests.ps1 -WithCoverage" -ForegroundColor Gray
} else {
    Write-Host "`n[ALGUNOS TESTS FALLARON]" -ForegroundColor Red
    Write-Host "Revise los errores arriba y corrija antes de produccion." -ForegroundColor Yellow
    
    if ($deadFilesExist) {
        Write-Host "`nPosible causa: archivos muertos no eliminados" -ForegroundColor Yellow
        Write-Host "Ejecute: .\cleanup_production.ps1" -ForegroundColor Gray
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan

exit $exitCode
