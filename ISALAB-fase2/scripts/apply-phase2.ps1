# =============================================================================
# IsaLab — Fase 2: Aplicar parche vía PowerShell
#
# Uso:
#   1. Abre PowerShell en la raíz de tu repo ISALAB local (con Fase 1 aplicada).
#   2. Ejecuta:
#       .\apply-phase2.ps1
#
# Qué hace:
#   - Crea la rama 'feat/phase2-database-critical'.
#   - Aplica el parche consolidado.
#   - Verifica alembic upgrade head en DB temporal.
#   - Hace commit con el mensaje estándar de Fase 2.
# =============================================================================

[CmdletBinding()]
param(
    [string]$BranchName = "feat/phase2-database-critical",
    [string]$CommitMessage = "fix(ISALAB): Fase 2 - Fix CRITICAL de base de datos",
    [switch]$DryRun,
    [switch]$SkipVerify
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
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

if (-not (Test-Path "alembic.ini")) {
    Write-Err "Falta alembic.ini. ¿Fase 1 está aplicada?"
    exit 1
}
Write-Ok "alembic.ini presente (Fase 1 aplicada)."

if (-not (Test-Path "pyproject.toml")) {
    Write-Err "Falta pyproject.toml. ¿Fase 1 está aplicada?"
    exit 1
}
Write-Ok "pyproject.toml presente (Fase 1 aplicada)."

$gitStatus = git status --porcelain 2>&1
if ($gitStatus) {
    Write-Warn "Tienes cambios sin commitear en tu working tree:"
    Write-Host $gitStatus
    Write-Warn "Recomendado: commitea o stash antes de aplicar Fase 2."
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

# ── 2. Aplicar el parche ─────────────────────────────────────────────────────
Write-Step "Aplicar parche consolidado de Fase 2"

$patchFile = Join-Path (Split-Path $PSScriptRoot -Parent) "patches\0001-fix-ISALAB-Fase-2-Fix-CRITICAL-de-base-de-datos.patch"
if (-not (Test-Path $patchFile)) {
    $patchFile = Read-Host "Ruta al archivo .patch consolidado"
}

Write-Host "    Aplicando: $patchFile"
if ($DryRun) {
    git apply --check $patchFile
    if ($LASTEXITCODE -eq 0) { Write-Ok "Dry-run: el parche aplica limpiamente." }
    else                       { Write-Err "Dry-run: el parche NO aplica limpiamente."; exit 1 }
} else {
    git apply --whitespace=fix $patchFile
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Parche aplicado."
    } else {
        Write-Err "Falló 'git apply'. Intenta con --3way o aplica archivo por archivo."
        Write-Host ""
        Write-Host "Parches individuales disponibles en patches/:"
        Get-ChildItem -Path (Join-Path (Split-Path $PSScriptRoot -Parent) "patches\*.patch") |
            Where-Object { $_.Name -notlike "0001-*" } |
            ForEach-Object { Write-Host "  $($_.Name)" }
        exit 1
    }
}

git add -A
Write-Ok "Cambios stageados."

# ── 3. Verificar alembic upgrade head ─────────────────────────────────────────
if (-not $SkipVerify -and -not $DryRun) {
    Write-Step "Verificar alembic upgrade head en DB temporal"

    $tmpDir = New-Item -ItemType Directory -Path ([System.IO.Path]::GetTempPath() + "isalab_verify_" + [System.Guid]::NewGuid().ToString("N").Substring(0,8)) -Force
    $tmpDb = Join-Path $tmpDir.FullName "isalab_test.db"

    Write-Host "    DB temporal: $tmpDb"

    $alembic = Get-Command alembic -ErrorAction SilentlyContinue
    if (-not $alembic) {
        Write-Warn "alembic no está en PATH. Instala con: pip install -r requirements-dev.txt"
        Write-Warn "Saltando verificación (-SkipVerify para silenciar este warning)."
    } else {
        $env:ISALAB_DB_PATH = $tmpDb
        $logFile = [System.IO.Path]::GetTempFileName()

        try {
            alembic upgrade head 2>&1 | Out-File -FilePath $logFile -Encoding utf8
            if ($LASTEXITCODE -eq 0) {
                Write-Ok "alembic upgrade head completó correctamente."

                # Verificar head
                $head = python -c "import sqlite3; conn = sqlite3.connect('$tmpDb'); [print(r[0]) for r in conn.execute('SELECT version_num FROM alembic_version')]" 2>$null
                Write-Ok "Head de migración: $head"

                # Verificar password_hash
                $hasPwdHash = python -c "import sqlite3; conn = sqlite3.connect('$tmpDb'); cols = [r[1] for r in conn.execute('PRAGMA table_info(usuarios)')]; print('password_hash' in cols)" 2>$null
                if ($hasPwdHash -eq "True") {
                    Write-Ok "Tabla usuarios tiene columna password_hash (issue C3 OK)."
                } else {
                    Write-Err "Tabla usuarios NO tiene password_hash. Revisar migración."
                    exit 1
                }
            } else {
                Write-Err "alembic upgrade head falló. Log:"
                Get-Content $logFile
                exit 1
            }
        } finally {
            Remove-Item -Path $tmpDir.FullName -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $logFile -Force -ErrorAction SilentlyContinue
            Remove-Item Env:ISALAB_DB_PATH -ErrorAction SilentlyContinue
        }
    }
}

# ── 4. Commit ────────────────────────────────────────────────────────────────
if (-not $DryRun) {
    Write-Step "Hacer commit"

    git add -A

    $stagedCount = (git diff --cached --name-only).Count
    if ($stagedCount -eq 0) {
        Write-Warn "No hay cambios para commitear (¿ya estaba aplicada Fase 2?)."
    } else {
        git commit -m $CommitMessage
        Write-Ok "Commit creado con $stagedCount archivos modificados."
        Write-Host ""
        Write-Host "Resumen:" -ForegroundColor Cyan
        git show --stat HEAD | Select-Object -Last 15
    }
}

# ── 5. Próximos pasos ────────────────────────────────────────────────────────
Write-Step "Listo. Próximos pasos:"
Write-Host "    1. Revisa el commit con:       git show HEAD"
Write-Host "    2. (Opcional) Corre los tests de regresión:"
Write-Host "         pip install -r requirements-dev.txt"
Write-Host "         pytest tests/test_fase2_database.py -v"
Write-Host "    3. Sube la rama al remoto con: git push -u origin $BranchName"
Write-Host "    4. Abre un Pull Request en GitHub contra 'main' o 'develop'."
Write-Host "    5. IMPORTANTE: si tienes una DB existente con la columna 'password'"
Write-Host "       (no 'password_hash'), la migración la renombrará automáticamente."
Write-Host "    6. Si tu DB existente tiene datos en la tabla animales, verifica que"
Write-Host "       los campos propietario_tipo_doc, propietario_documento,"
Write-Host "       propietario_direccion, propietario_oficio y empresa (en muestras)"
Write-Host "       tengan los valores esperados después de la migración."
Write-Host ""
