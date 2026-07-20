# IsaLab — Fase 1: Parches de Higiene del Repositorio

Este paquete contiene los parches y scripts para aplicar la **Fase 1** del
roadmap de refactor de IsaLab: higiene del repositorio + setup de tooling.

---

## 📦 Contenido del paquete

```
ISALAB-fase1/
├── README.md                                    ← Este archivo
├── patches/
│   ├── 0001-slim-added-modified-only.patch      ← Parche slim (62 KB)
│   │                                              Solo archivos nuevos/modificados
│   │                                              (16 archivos). Recomendado.
│   └── 0001-chore-ISALAB-Fase-1-...patch        ← Parche consolidado (15 MB)
│                                                  Incluye eliminaciones de
│                                                  558 archivos. Solo si quieres
│                                                  aplicar TODO en un comando.
├── scripts/
│   ├── apply-phase1.ps1                         ← Script PowerShell (Windows)
│   └── apply-phase1.sh                          ← Script Bash (Linux/macOS/Git Bash)
└── files/                                       ← (vacío, se llena abajo)
```

> **Recomendación:** usa el **parche slim** + **script** (opción A abajo).
> El parche consolidado de 15 MB funciona pero es innecesariamente grande
> porque incluye las eliminaciones binarias que el script hace más limpio.

---

## 🎯 Qué hace Fase 1

### Elimina del git index (558 archivos, NO los borra del disco)

- **PII/PHI sensibles (CRITICAL):**
  - `data/isalab.db` (102 KB, contiene hash bcrypt del admin real)
  - `data/pdfs/Formato informe Ruffos.pdf`, `LAB_ISA-20260410-7801.pdf`,
    `reporte_isalab.pdf` (PHI veterinaria real)
  - `logs/isalab.log` (237 KB, usernames y paths de Windows)

- **Build artifacts:** `Analysis-00.toc`, `COLLECT-00.toc`, `EXE-00.toc`,
  `PKG-00.toc`, `PYZ-00.toc`, `PYZ-00.pyz`, `IsaLab.pkg`,
  `identifier.sqlite`, `warn-IsaLab.txt`, `icono.ico` (duplicado raíz)

- **Scripts one-shot:** `fix_f541.py`, `fix_jinja_format*.py` (4 archivos)

- **92 archivos `__pycache__/*.pyc`** huérfanos

- **14 directorios AI-tool duplicados** (435 archivos, ~9 MB):
  `.agent`, `.claude`, `.codebuddy`, `.codex`, `.continue`, `.cursor`,
  `.gemini`, `.kiro`, `.opencode`, `.qoder`, `.roo`, `.stakpak`, `.trae`,
  `.windsurf`, más `.github/prompts/`

- **Carpetas IDE:** `.idea/`, `.vscode/`

### Agrega archivos nuevos

- `pyproject.toml` — config de ruff/black/mypy/pytest/coverage
- `requirements-dev.txt` — deps de desarrollo
- `.env.example` — template de variables de entorno
- `.github/workflows/ci.yml` — pipeline CI (lint + tests + build)
- `.pre-commit-config.yaml` — hooks de git
- `ARCHITECTURE.md`, `SECURITY.md`, `LICENSE`
- `tests/conftest.py` — fixtures de pytest (DB temporal + QApplication)

### Modifica archivos existentes

- `.gitignore` — reglas adicionales para data/imagenes/, caches, etc.
- `requirements.txt` — agrega `bcrypt`, `weasyprint`, `jinja2`, `alembic`;
  elimina `customtkinter`, `tkcalendar`, `tksheet`, `reportlab`;
  pinea `pyside6` y `sqlalchemy` con rangos
- `IsaLab.spec` — quita `data/` del bundle; agrega `alembic/`; `optimize=2`;
  `console` controlado por `ISALAB_DEBUG`
- `main.py` — usa `BUNDLE_DIR` en vez de `Path.cwd()` (fix crítico .exe)
- `alembic.ini` — deja `sqlalchemy.url` vacío (lo inyecta `env.py`)
- `README.md` — corrige claims falsos (CustomTkinter, ReportLab, URL, etc.)
- `AGENTS.md` — reemplaza contenido copiado de "obra/superpowers"

---

## 🚀 Cómo aplicar (3 opciones)

### Opción A — Script automático (RECOMENDADA)

Funciona en Windows (PowerShell) y Linux/macOS/Git Bash.

#### Windows (PowerShell)

1. **Abre GitHub Desktop** y clona el repo `CORJAR-Computers/ISALAB` a una
   carpeta local (si no lo tienes ya).

2. **Abre PowerShell** y navega a la raíz del repo:
   ```powershell
   cd C:\Users\TuUsuario\GitHub\ISALAB
   ```

3. **Copia el paquete `ISALAB-fase1/`** a una carpeta temporal, por ejemplo
   `C:\temp\isalab-fase1\`.

4. **Ejecuta el script:**
   ```powershell
   # Si tu PowerShell bloquea scripts, habilita temporalmente:
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

   # Ejecuta:
   C:\temp\isalab-fase1\scripts\apply-phase1.ps1
   ```

5. **Verifica el dry-run primero** (opcional pero recomendado):
   ```powershell
   C:\temp\isalab-fase1\scripts\apply-phase1.ps1 -DryRun
   ```

#### Linux / macOS / Git Bash

1. **Abre terminal** y navega a la raíz del repo:
   ```bash
   cd ~/proyectos/ISALAB
   ```

2. **Ejecuta el script:**
   ```bash
   bash /ruta/a/ISALAB-fase1/scripts/apply-phase1.sh
   ```

3. **Dry-run primero** (opcional):
   ```bash
   bash /ruta/a/ISALAB-fase1/scripts/apply-phase1.sh --dry-run
   ```

El script:
- Crea la rama `feat/phase1-repo-hygiene`.
- Aplica el parche slim.
- Ejecuta `git rm --cached` para todos los archivos sensibles.
- Hace commit con mensaje Convencional Commits + tag `ISALAB`.
- **NO hace push** (tú decides cuándo).

---

### Opción B — Aplicar el parche manualmente con `git apply`

Si prefieres ver exactamente qué pasa en cada paso:

1. **Crea la rama:**
   ```bash
   git checkout -b feat/phase1-repo-hygiene
   ```

2. **Aplica el parche slim:**
   ```bash
   git apply --whitespace=fix patches/0001-slim-added-modified-only.patch
   ```

3. **Remueve los archivos sensibles del index** (NO del disco):
   ```bash
   # PII/PHI (CRITICAL)
   git rm --cached data/isalab.db
   git rm --cached "data/pdfs/Formato informe Ruffos.pdf"
   git rm --cached data/pdfs/LAB_ISA-20260410-7801.pdf
   git rm --cached data/pdfs/reporte_isalab.pdf
   git rm --cached logs/isalab.log

   # Build artifacts
   git rm --cached Analysis-00.toc COLLECT-00.toc EXE-00.toc \
                PKG-00.toc PYZ-00.toc PYZ-00.pyz \
                IsaLab.pkg identifier.sqlite warn-IsaLab.txt icono.ico

   # Scripts one-shot
   git rm --cached fix_f541.py fix_jinja_format.py \
                fix_jinja_format_2.py fix_jinja_format_3.py

   # Directorios AI-tool duplicados + IDEs
   git rm --cached -r .agent .claude .codebuddy .codex .continue \
       .cursor .gemini .kiro .opencode .qoder .roo .stakpak .trae \
       .windsurf .github/prompts .idea .vscode

   # __pycache__ y *.pyc
   git ls-files | grep -E "(__pycache__/|\.pyc$|localpycs/)" \
       | xargs git rm --cached
   ```

4. **Stagea y commitea:**
   ```bash
   git add -A
   git commit -m "chore(ISALAB): Fase 1 - higiene del repositorio + setup tooling"
   ```

---

### Opción C — Aplicar el parche consolidado en un solo comando

Si no te importa el tamaño del parche (15 MB) y quieres TODO en un comando:

```bash
git checkout -b feat/phase1-repo-hygiene
git am patches/0001-chore-ISALAB-Fase-1-higiene-del-repositorio-setup-to.patch
```

> ⚠️ `git am` aplica el parche COMO commit (incluye mensaje, autor, fecha).
> Si hay conflictos, `git am` te lo dirá y puedes resolverlos con
> `git am --continue` o `git am --abort`.

---

## 🖥️ Cómo seguir con GitHub Desktop después de aplicar el parche

Una vez que el script hizo el commit localmente:

1. **Abre GitHub Desktop.**
2. Selecciona el repo ISALAB en la lista de la izquierda.
3. Deberías ver:
   - La rama actual: `feat/phase1-repo-hygiene`
   - 1 commit nuevo "chore(ISALAB): Fase 1 - higiene..."
4. **Publica la rama** al remoto:
   - Botón **"Publish branch"** en la barra superior.
5. **Abre un Pull Request:**
   - Botón **"Pull request"** en la barra superior (o `Ctrl+R`).
   - Base: `main` (o `develop` si la usas).
   - Título: `Fase 1 — Higiene del repositorio + setup tooling`
   - En la descripción, copia el cuerpo del commit (`git log -1 --pretty=%B`).
6. **Asigna reviewers** y espera aprobación antes de mergear.

---

## ⚠️ Acciones posteriores CRÍTICAS

Estas acciones NO están en el parche (requieren coordinación humana):

### 1. Rotar el password del admin

El hash bcrypt del usuario `admin` quedó expuesto en el historial público
del commit `af39d04`. Aunque Fase 1 lo remueve del index, **sigue siendo
accesible para cualquiera que clone el repo y haga `git log -p`**.

**Acción inmediata:**
1. Inicia IsaLab en modo desarrollo.
2. Inicia sesión como `admin` con la password actual.
3. Cámbiala por una nueva fuerte (12+ caracteres, símbolos).
4. Si hay otros usuarios, verifica sus contraseñas también.

### 2. Purgar el historial con `git filter-repo` (opcional pero recomendado)

Para eliminar completamente `data/isalab.db`, `logs/isalab.log` y los PDFs
con PHI del historial público:

```bash
# Instala git-filter-repo (una sola vez):
pip install git-filter-repo

# Crea un backup del repo por si algo sale mal:
cp -r ISALAB ISALAB.backup

# Ejecuta el purge:
cd ISALAB
git filter-repo --invert-paths \
    --path data/isalab.db \
    --path "data/pdfs/Formato informe Ruffos.pdf" \
    --path data/pdfs/LAB_ISA-20260410-7801.pdf \
    --path data/pdfs/reporte_isalab.pdf \
    --path logs/isalab.log \
    --force

# Force-push al remoto (¡CUIDADO! reescribe el historial público):
git push origin --force --all
git push origin --force --tags
```

> ⚠️ **Esto reescribe el historial.** Todos los que tengan un clone del repo
> deben borrarlo y volver a clonarlo. Coordina con tu equipo antes de hacerlo.

### 3. Verificar que el CI pase

Después de mergear el PR, ve a la pestaña **Actions** del repo en GitHub y
verifica que el workflow `CI` corra en verde. Si falla:
- Revisa los logs en GitHub Actions.
- Los primeros runs pueden fallar por `mypy` (ignore_missing_imports) o
  por tests faltantes — está bien, los marcamos como no bloqueantes.

### 4. Instalar pre-commit hooks localmente

```bash
pip install pre-commit
pre-commit install
```

A partir de ahora, cada `git commit` correrá automáticamente ruff, black,
y verificaciones de higiene.

---

## 🧪 Cómo verificar que Fase 1 quedó bien aplicada

```bash
# 1. Conteo de archivos trackeados (debe ser ~124, no 682):
git ls-files | wc -l

# 2. Ningún archivo sensible en el index:
git ls-files | grep -E "(data/.*\.(db|pdf)|logs/.*\.log|\.env$|\.pyc$|__pycache__|\.idea/|\.vscode/|fix_.*\.py)"
# Debe devolver vacío.

# 3. Nuevos archivos presentes:
ls -la pyproject.toml requirements-dev.txt .env.example \
       .github/workflows/ci.yml .pre-commit-config.yaml \
       ARCHITECTURE.md SECURITY.md LICENSE tests/conftest.py

# 4. requirements.txt saneado:
grep -E "(customtkinter|tkcalendar|tksheet|reportlab)" requirements.txt
# Debe devolver vacío.

grep -E "(bcrypt|weasyprint|jinja2|alembic)" requirements.txt
# Debe devolver las 4 líneas.

# 5. Tests corren (necesitas instalar deps primero):
pip install -r requirements-dev.txt
pytest --co  # collect-only, sin ejecutar
```

---

## 🆘 Troubleshooting

### `git apply` falla con "patch does not apply"

Probablemente modificaste alguno de los archivos que el parche toca
(`README.md`, `requirements.txt`, `IsaLab.spec`, `main.py`, `alembic.ini`,
`AGENTS.md`, `.gitignore`). Opciones:

```bash
# Ver qué archivos tienen conflicto:
git apply --check patches/0001-slim-added-modified-only.patch

# Aplicar con 3-way merge (más tolerante):
git apply --3way patches/0001-slim-added-modified-only.patch

# Último recurso: aplicar archivo por archivo:
git apply --include="requirements.txt" patches/0001-slim-added-modified-only.patch
git apply --include="pyproject.toml" patches/0001-slim-added-modified-only.patch
# etc.
```

### El script PowerShell falla con "execution of scripts is disabled"

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Solo afecta a la sesión actual; no cambia la política del sistema.

### GitHub Desktop no me deja publicar la rama

Verifica que tienes permisos de `push` en el repo. Si eres colaborador
externo, haz fork primero y cambia el remote:

```bash
git remote add fork https://github.com/TU-USUARIO/ISALAB.git
git push -u fork feat/phase1-repo-hygiene
```

Luego abre el PR desde tu fork en la web de GitHub.

### Quiero deshacer todo

```bash
git checkout main
git branch -D feat/phase1-repo-hygiene
# Los archivos eliminados del index vuelven a estar trackeados:
git checkout HEAD -- .
```

---

## 📋 Issues del worklog cubiertos por Fase 1

| Severidad | Issues cubiertos |
|-----------|------------------|
| CRITICAL  | C1, C2, C3, C4, C5 (todos los de DevOps) |
| HIGH      | H1, H2, H3, H4, H5, H6, H7, H9, H10 (9 de 10) |
| MEDIUM    | M1, M8, M10, M11, M12 (parcial) |
| LOW       | L3, L4, L5, L6 |

**Pendientes para Fase 2+:** todos los issues de DB, servicios, GUI y los
MEDIUM/LOW restantes (H8 mover `icon_manager.py` a `utils/`, etc.).

---

## ❓ Dudas

Si algo no funciona, abre un issue en
https://github.com/CORJAR-Computers/ISALAB/issues con etiqueta `phase1` y
describe el error exacto (copia el output del comando que falló).
