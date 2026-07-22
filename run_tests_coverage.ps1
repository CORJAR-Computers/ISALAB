# ============================================
# IsaLab - Tests con Cobertura de Código
# ============================================
# Ejecutar en PowerShell: .\run_tests_coverage.ps1
# ============================================

param(
    [string]$ProjectRoot = "D:\ISALAB",
    [switch]$GenerateHtml
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IsaLab - Tests con Cobertura         " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Proyecto: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# Cambiar al directorio del proyecto
Set-Location -Path $ProjectRoot

# ============================================
# 1. VERIFICAR DEPENDENCIAS
# ============================================
Write-Host "1. Verificando dependencias..." -ForegroundColor Yellow

# Verificar pytest-cov
python -c "import pytest_cov" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Instalando pytest-cov..." -ForegroundColor Gray
    pip install pytest-cov -q
}

Write-Host "   [OK] Dependencias verificadas" -ForegroundColor Green

# ============================================
# 2. EJECUTAR TESTS CON COBERTURA
# ============================================
Write-Host "`n2. Ejecutando tests con cobertura..." -ForegroundColor Yellow
Write-Host "   Esto puede tomar unos minutos..." -ForegroundColor Gray
Write-Host ""

$startTime = Get-Date

# Construir comando de pytest con cobertura
$coverageArgs = @(
    "python", "-m", "pytest"
    "tests/"
    "-v"
    "--tb=short"
    "--cov=."
    "--cov-report=term-missing"
    "--cov-report=json:coverage.json"
)

if ($GenerateHtml) {
    $coverageArgs += "--cov-report=html:htmlcov"
}

# Ejecutar tests con cobertura
$testOutput = & python -m pytest tests/ -v --tb=short --cov=. --cov-report=term-missing --cov-report=json:coverage.json 2>&1
$exitCode = $LASTEXITCODE
$endTime = Get-Date
$duration = $endTime - $startTime

# ============================================
# 3. MOSTRAR RESULTADOS
# ============================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  RESULTADOS DE TESTS CON COBERTURA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Mostrar salida de pytest
$testOutput | ForEach-Object {
    $line = $_.ToString()
    if ($line -match "PASSED") {
        Write-Host $line -ForegroundColor Green
    } elseif ($line -match "FAILED") {
        Write-Host $line -ForegroundColor Red
    } elseif ($line -match "ERROR") {
        Write-Host $line -ForegroundColor Red
    } elseif ($line -match "SKIP") {
        Write-Host $line -ForegroundColor Yellow
    } elseif ($line -match "passed|failed|error") {
        Write-Host $line -ForegroundColor White
    } else {
        Write-Host $line -ForegroundColor Gray
    }
}

# ============================================
# 4. RESUMEN DE COBERTURA
# ============================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  RESUMEN DE COBERTURA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nDuracion total: $([math]::Round($duration.TotalSeconds, 2)) segundos" -ForegroundColor Gray

# Leer reporte JSON si existe
$coverageJson = "coverage.json"
if (Test-Path $coverageJson) {
    Write-Host "`nAnálisis de cobertura por módulo:" -ForegroundColor Yellow
    
    $coverage = Get-Content $coverageJson | ConvertFrom-Json
    
    # Mostrar cobertura total
    $totalPercent = $coverage.totals.percent_covers
    Write-Host "`nCobertura total: $([math]::Round($totalPercent, 2))%" -ForegroundColor $(if ($totalPercent -ge 50) { "Green" } else { "Red" })
    
    # Mostrar cobertura por archivo
    Write-Host "`nCobertura por archivo:" -ForegroundColor Yellow
    $coverage.files.PSObject.Properties | Sort-Object { $_.Value.summary.percent_covers } -Descending | ForEach-Object {
        $file = $_.Name
        $summary = $_.Value.summary
        $percent = [math]::Round($summary.percent_covers, 1)
        $missing = $summary.missing_lines.Count
        
        $color = if ($percent -ge 80) { "Green" } elseif ($percent -ge 50) { "Yellow" } else { "Red" }
        
        Write-Host ("  {0,-50} {1,6}% ({2} lineas sin cubrir)" -f $file, $percent, $missing) -ForegroundColor $color
    }
}

# ============================================
# 5. GENERAR HTML (OPCIONAL)
# ============================================
if ($GenerateHtml -and (Test-Path "htmlcov")) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  REPORTE HTML GENERADO" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "`nEl reporte HTML está en: htmlcov/index.html" -ForegroundColor Green
    Write-Host "Ábrelo en tu navegador para ver el reporte detallado." -ForegroundColor Gray
}

# ============================================
# 6. SUGERENCIAS
# ============================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SUGERENCIAS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($exitCode -eq 0) {
    Write-Host "`n[TODOS LOS TESTS PASARON]" -ForegroundColor Green
    
    Write-Host "`nPara mejorar la cobertura:" -ForegroundColor Yellow
    Write-Host "  1. Ejecuta con reporte HTML: .\run_tests_coverage.ps1 -GenerateHtml" -ForegroundColor White
    Write-Host "  2. Revisa htmlcov/index.html para ver líneas sin cubrir" -ForegroundColor White
    Write-Host "  3. Agrega tests para archivos con cobertura baja" -ForegroundColor White
} else {
    Write-Host "`n[ALGUNOS TESTS FALLARON]" -ForegroundColor Red
    Write-Host "Corrige los errores antes de analizar cobertura." -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan

exit $exitCode
